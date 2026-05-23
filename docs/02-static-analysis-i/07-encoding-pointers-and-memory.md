---
id: 07-encoding-pointers-and-memory
title: 3.7 Encoding pointers và memory
sidebar_position: 7
description: Cách BMC tool model bộ nhớ, pointer, malloc, array access bằng array theory. Memory model của ESBMC, alignment, aliasing analysis.
---

# 3.7 Encoding pointers và memory: phần khó nhất

> **Tóm tắt một dòng**: Memory trong C là chỗ khó nhất để encode vì pointer có thể trỏ tới bất cứ đâu, hai pointer có thể alias (cùng trỏ một địa chỉ), và allocator động (`malloc`) tạo ra object mới tại runtime. BMC tool dùng **array theory** kết hợp với **alias analysis** để model memory một cách tractable nhưng vẫn chính xác.

## Vì sao memory khó?

Hãy nhìn vào một đoạn code C đơn giản:

```c
int x = 5;
int y = 10;
int *p = &x;
int *q = (rand() % 2) ? &x : &y;
*p = 100;
assert(*q == 100 || *q == 10);
```

Câu hỏi: assertion đúng không?

Trực giác: `*q` là `x` (= 100 sau gán) hoặc `y` (= 10). Cả hai đều thoả assertion.

Đúng. Nhưng để **chứng minh** điều này một cách tự động, BMC tool phải:

1. Biết `&x` và `&y` là hai địa chỉ **khác nhau**.
2. Biết `p` chắc chắn trỏ tới `x`.
3. Biết `q` có thể trỏ tới `x` hoặc `y` (do `rand()`).
4. Biết khi gán `*p = 100`, chỉ giá trị tại địa chỉ `&x` thay đổi, không phải `&y`.
5. Suy ra `*q` là `100` (nếu `q = &x`) hoặc `10` (nếu `q = &y`).

Điểm 4 là khó nhất. Trong C, gán `*p = 100` chỉ thay đổi 1 word memory. Encoding sai (ví dụ "thay đổi toàn bộ memory") cho false negative; encoding chính xác đòi hỏi biết `*p` chính xác đến đâu, tức **alias analysis**.

Bài này dạy cách BMC tool giải quyết các vấn đề trên.

## Phần 1: Array theory để model memory

### Ý tưởng cơ bản

Trong array theory:
- `(select arr i)` đọc phần tử thứ `i`.
- `(store arr i v)` tạo mảng mới giống `arr` nhưng phần tử `i` là `v`.

Áp dụng cho memory:
- Mọi memory là một mảng huge: `memory: Array (BitVec 64) (BitVec 8)`. Index là địa chỉ 64-bit, value là byte.
- Đọc memory: `(select memory addr)` cho byte tại địa chỉ `addr`.
- Ghi memory: `(store memory addr value)` cập nhật byte.

Mỗi gán trong C tạo ra một version mới của `memory` (đúng SSA spirit):

```c
*p = 100;
```

Thành:

```
memory_2 = store(memory_1, addr(p), 100_as_4_bytes)
```

Read-over-write axiom: nếu đọc địa chỉ vừa ghi, được giá trị mới. Đọc địa chỉ khác, giữ nguyên giá trị cũ. Đây chính là cách array theory **suy luận về aliasing** tự nhiên.

### Multi-byte read/write

Memory là array của **byte**, nhưng C có `int` (4 byte), `long` (8 byte), `double` (8 byte). Đọc một `int` từ memory cần:

```
read_int(memory, addr) = concat(
    select(memory, addr+0),
    select(memory, addr+1),
    select(memory, addr+2),
    select(memory, addr+3)
)
```

Tương tự cho ghi:

```
write_int(memory, addr, value) = 
    store(store(store(store(memory, 
        addr+0, value[7:0]),
        addr+1, value[15:8]),
        addr+2, value[23:16]),
        addr+3, value[31:24])
```

(Giả sử little-endian như x86.)

Encoding 4 store/select cho mỗi `int` truy cập làm formula lớn. Optimization: dùng **multi-byte array theory** (mảng `BitVec 64 → BitVec 32` hoặc `BitVec 64 → BitVec 8`) tuỳ tool.

## Phần 2: Encoding pointer

### Pointer là gì trong logic?

Trong C, pointer là một địa chỉ 64-bit (trên x86-64). Tự nhiên ta encode bằng:

```scheme
(declare-const p (_ BitVec 64))
```

Đọc qua pointer: `*p` thành `read_int(memory, p)`.

Nhưng có một vấn đề. Trong C, pointer còn mang thông tin về **object** mà nó trỏ tới, không chỉ địa chỉ. Ví dụ:

```c
int arr[10];
int *p = arr;
p += 100;     // out of bounds, nhưng C standard nói UB
*p = 5;       // UB!
```

Code này có UB vì `p` trỏ ngoài `arr`. Nhưng nếu chỉ encode bằng địa chỉ thuần, BMC có thể "miss" vì $p + 400$ vẫn là một địa chỉ hợp lệ trong memory map.

Để giải quyết, một số tool (ESBMC, CBMC modern) dùng **two-level encoding** cho pointer:

```scheme
(declare-datatype Pointer (
    (mk-ptr (object Int) (offset (_ BitVec 64)))
))
```

Pointer là một cặp `(object_id, offset)`. `object_id` là ID duy nhất của object (mỗi `int x` có ID khác, mỗi `malloc` có ID khác). `offset` là vị trí trong object.

Khi `p += 100`, offset tăng nhưng object_id giữ nguyên. Khi dereference, tool check `offset` có nằm trong bound của object không, báo lỗi nếu vượt.

### Two-level memory model của ESBMC

ESBMC dùng một biến thể của hai cấp:

- **Object table**: mỗi object có entry chứa `(object_id, size, address_base)`.
- **Memory array**: như trên, nhưng indexed bởi `(object_id, offset)` thay vì địa chỉ thuần.

Cấu trúc này cho phép:
- Detect out-of-bounds tự động (offset >= size).
- Aliasing analysis chính xác: hai pointer alias khi và chỉ khi cùng `object_id` và cùng `offset`.
- Symbolic pointer arithmetic dễ hơn.

Nhược điểm: model phức tạp hơn, query SMT chậm hơn so với "flat memory" thuần.

## Phần 3: Malloc và động học bộ nhớ

### Encode malloc

`malloc(n)` tạo một object mới có kích thước `n` byte. Trong BMC:

```c
int *p = malloc(40);
```

Thành:

```
new_object_id = unique_fresh_id()
p = mk-ptr(new_object_id, 0)
object_table = extend(object_table, new_object_id, size=40, base=fresh_addr)
```

Khi `free(p)`:

```
mark_freed(object_table, object(p))
```

Mọi access sau free phải báo "use after free" assertion.

### Detect use-after-free

```c
int *p = malloc(40);
*p = 5;
free(p);
*p = 10;   // use after free!
```

Encode:

```
obj1 = fresh_id()
p = (obj1, 0)
memory_1 = store(memory_0, &(obj1, 0), 5_4bytes)
freed_1 = set_add(freed_0, obj1)
assert(not (obj1 in freed_1))   ; check trước khi write
memory_2 = store(memory_1, &(obj1, 0), 10_4bytes)
```

Assertion fail tại bước check, BMC trả counterexample.

### Detect double free

```c
int *p = malloc(40);
free(p);
free(p);   // double free!
```

Encode:

```
freed_1 = set_add(freed_0, obj1)
assert(not (obj1 in freed_1))   ; trước free thứ hai
freed_2 = set_add(freed_1, obj1)
```

Assertion fail.

### Detect memory leak

Leak là khi một object được allocate nhưng không free trước khi pointer cuối cùng trỏ tới nó bị overwrite/out-of-scope. Detect leak khó hơn vì cần "garbage collector" trong BMC, không phải lúc nào cũng làm.

CBMC có flag `--memory-leak-check` để bật leak detection. ESBMC tương tự.

## Phần 4: Aliasing analysis

### Vì sao aliasing khó?

Hai pointer **alias** khi cùng trỏ một địa chỉ. Aliasing quan trọng vì:

```c
void f(int *p, int *q) {
    *p = 5;
    *q = 10;
    int x = *p;   // x = 10 (nếu p, q alias) hoặc 5 (nếu không)
}
```

Tool cần biết `p` và `q` có alias không. Có 3 case:
- **Must-alias**: chắc chắn alias (ví dụ `q = p` trước đó).
- **No-alias**: chắc chắn không alias (ví dụ `&x` và `&y` của 2 local var khác nhau).
- **May-alias**: có thể alias, có thể không (ví dụ pointer từ function call).

### Anderson và Steensgaard

Hai thuật toán cơ bản:

**Andersen analysis** (inclusion-based): mỗi pointer có một "points-to set". Khi `p = &x`, thêm `x` vào set của `p`. Khi `q = p`, set của `q` chứa set của `p`. Phân tích chính xác hơn nhưng $O(n^3)$.

**Steensgaard analysis** (union-based): mỗi assignment hợp nhất các points-to set. Nhanh hơn ($O(n \cdot \alpha(n))$) nhưng kém chính xác.

Tool BMC thường dùng aliasing analysis ở pre-processing để giảm encoding size, rồi để SMT solver xử lý phần residual.

### Encode alias precisely với array theory

Nếu không pre-analyze, BMC vẫn handle alias chính xác qua array theory. Ví dụ:

```c
int x = 5, y = 10;
int *p = &x;
int *q = (cond) ? &x : &y;
*p = 100;
int r = *q;
```

Encode:

```
mem_0: ban đầu, có x = 5 tại addr_x, y = 10 tại addr_y
p = addr_x
q = ite(cond, addr_x, addr_y)
mem_1 = store(mem_0, p, 100) = store(mem_0, addr_x, 100)
r = select(mem_1, q) = select(store(mem_0, addr_x, 100), q)

Áp dụng read-over-write:
r = ite(q == addr_x, 100, select(mem_0, q))
  = ite(cond, 100, ite(addr_y == addr_x, 100, 10))   ; q expand
  = ite(cond, 100, 10)   ; addr_y != addr_x
```

Kết quả: `r = 100` nếu cond true, `r = 10` nếu false. Chính xác.

Array theory tự động handle aliasing qua axiom read-over-write. Không cần aliasing analysis riêng, dù pre-analysis làm encoding nhanh hơn.

## Phần 5: Alignment và padding

C compiler chèn padding để align field của struct. Ví dụ:

```c
struct S {
    char c;     // offset 0
    int i;      // offset 4 (padding 3 byte ở 1-3)
};
```

`sizeof(struct S) = 8`, không phải 5.

BMC tool phải model padding chính xác. Đọc `c` cho byte 0. Đọc `i` cho byte 4-7. Byte 1-3 là padding (giá trị không xác định).

Nếu encoding sai (giả định không padding), BMC có thể miss bug. Ví dụ:

```c
struct S s;
s.c = 'A';
s.i = 0x12345678;
char *p = (char*) &s;
char x = p[2];   // đọc padding byte 2 (UB!)
```

`x` là byte padding, không xác định. Code có UB. BMC chuẩn (như ESBMC với `--memory-model fixed`) phát hiện và báo "non-deterministic value access".

## Phần 6: ESBMC memory model trong thực tế

ESBMC cung cấp ba memory model qua flag:

| Flag | Memory model | Speed | Precision |
|---|---|---|---|
| `--memory-model fixed` | Flat byte array với layout C cố định | Trung bình | Cao |
| `--memory-model align` | Aligned-only access | Nhanh hơn | Trung bình |
| `--memory-model offset` | Object-offset two-level | Chậm hơn | Cao nhất |

Cho production code, `fixed` là default tốt. Cho code có nhiều pointer arithmetic phức tạp (kernel driver, allocator), `offset` chính xác hơn.

CBMC cũng có thiết kế tương tự với flags `--object-bits N` (số bit dùng cho object_id).

## Tóm tắt

- **Array theory** model memory như mảng huge từ địa chỉ (BitVec 64) sang byte (BitVec 8).
- Multi-byte read/write phân rã thành nhiều `select`/`store`.
- **Pointer** encode bằng cặp `(object_id, offset)` để track object identity, phát hiện out-of-bounds.
- **Malloc/free/leak** model qua object_table, freed_set.
- **Aliasing**: array theory tự handle qua read-over-write; pre-analysis (Andersen, Steensgaard) tăng tốc.
- **Padding và alignment** phải model chính xác để khớp semantics C.
- ESBMC có ba memory model: `fixed` (default), `align`, `offset`.

## Mini-quiz

<details>
<summary>Q1. Vì sao gọi memory model là "two-level"?</summary>

Một cấp là **địa chỉ tuyến tính** (số 64-bit). Cấp khác là **object identity + offset** (cặp). 

Cấp địa chỉ tuyến tính tự nhiên với phần cứng (CPU thực sự dùng địa chỉ flat). Cấp object-offset tự nhiên với semantics C (mỗi `malloc`, mỗi local var là một object riêng).

Two-level encoding kết hợp cả hai: pointer là cặp `(object_id, offset)`, có thể compute thành địa chỉ tuyến tính khi cần. Tool BMC dùng object identity để track bounds, dùng địa chỉ tuyến tính để model pointer arithmetic across object (UB nhưng vẫn phải model).
</details>

<details>
<summary>Q2. Read-over-write axiom giúp giải quyết aliasing như thế nào?</summary>

Read-over-write: `select(store(arr, i, v), j)` bằng `v` nếu `i == j`, bằng `select(arr, j)` nếu `i != j`.

Khi BMC encode hai pointer access `*p` và `*q`, nó không cần biết trước `p` và `q` có alias không. Nó encode:

```
mem_1 = store(mem_0, p, val_p)   ; gán *p
result = select(mem_1, q)         ; đọc *q
       = ite(p == q, val_p, select(mem_0, q))
```

SMT solver sau đó tự suy luận: liệu `p == q` (alias) hay không. Nếu solver chứng minh được `p != q`, simplify thành `select(mem_0, q)`. Nếu không chắc, giữ ite, để alias là biến boolean.

Cách này **chính xác**: bắt được mọi case alias mà không cần aliasing analysis riêng. Đánh đổi: formula lớn, solver tốn công.
</details>

<details>
<summary>Q3. Tại sao detect memory leak khó hơn detect use-after-free?</summary>

**Use-after-free** là property local: tại mỗi access, check object đã free chưa. Đơn giản encode bằng `freed_set`.

**Memory leak** là property global: tại điểm chương trình kết thúc, mọi allocated object phải đã free hoặc còn pointer trỏ tới. Cần:
1. Track mọi allocation (đã có).
2. Track mọi pointer hiện đang trỏ tới mỗi object (khó: pointer copy, store vào struct, pass qua function).
3. Tại exit, check object nào không còn pointer trỏ tới nó.

Bước 2 yêu cầu **escape analysis** hoặc **reachability** từ root set (global var, stack var). Đây là phân tích đắt.

CBMC và ESBMC có `--memory-leak-check` nhưng chậm hơn nhiều và đôi khi không sound (miss leak hoặc báo nhầm) trong code phức tạp.
</details>

---

**Kết thúc Phần 2 (Lecture 3).** Bạn đã hiểu sâu cách BMC + SMT thực sự hoạt động bên trong. Chuyển sang [Lecture 4: Static Analysis II (Concurrency)](../03-static-analysis-ii/01-overview) để xem cách xử lý chương trình đa luồng.
