---
id: 03-code-patterns-cluster-2
title: 8.3 Code patterns Phần 2 (Lec 3 - BMC encoding)
sidebar_position: 3
description: "Phân tích các đoạn code C trong Lec 3 dùng làm input cho BMC: array bounds, pointer arithmetic, float, encoding integer/pointer/memory."
---

# 8.3 Code patterns Phần 2 (Lec 3 - BMC encoding)

> **Tóm tắt một dòng**: Code trong Lec 3 dùng làm **input để demo BMC encoding**. Mỗi sample là chương trình nhỏ có bug subtle mà BMC bắt được nhưng test ngẫu nhiên có thể miss. Phân tích lại để hiểu vì sao BMC quan trọng và cách encode chính xác.

## Sample 1: Array bounds với index từ symbolic

**Nguồn**: Lec 3, mục State Space Exploration / BMC intro.

**Code (cleaned up)**:

```c
#include <assert.h>

int nondet_int(void);

int main(void) {
    int a[2], i, x;
    i = nondet_int();
    x = nondet_int();
    if (x == 0)
        a[i] = 0;
    else
        a[i] = 1;
    assert(a[i + 1] == 1);   // (1) BUG nếu i + 1 >= 2
    return 0;
}
```

**Đọc nhanh**: hai biến nondet `i, x`. Gán `a[i]` theo `x`. Assert `a[i+1] == 1`.

**Bug tìm được**:

1. **Bug chính (Critical)**: `i` không bound. Nếu `i == 0`, `a[1]` được assert. Nhưng `a[1]` chưa khởi tạo (uninitialized) → undefined value, assert có thể fail.
2. **Bug phụ (Critical)**: nếu `i >= 1`, `a[i+1]` OOB. Read OOB = UB.
3. **Bug phụ (High)**: nếu `i < 0`, `a[i] = ...` OOB write. Memory corruption.

**Cơ chế BMC bắt**:

BMC encode chương trình thành SMT:

```smt
(declare-fun a () (Array Int Int))
(declare-fun i () Int)
(declare-fun x () Int)

; Path 1: x == 0
(assert (=> (= x 0) (= a_new (store a i 0))))
; Path 2: x != 0  
(assert (=> (not (= x 0)) (= a_new (store a i 1))))

; Property: a_new[i+1] == 1
(assert (not (= (select a_new (+ i 1)) 1)))

(check-sat)  ; SAT → counterexample tồn tại
```

Z3 trả về `i = 0, x = 0`: assertion fail vì `a[1]` không được gán (giá trị mặc định trong SMT array là arbitrary, có thể khác 1).

**Fix gợi ý** (nếu intent là test concept BMC, không phải production):

```c
#include <assert.h>

int nondet_int(void);

int main(void) {
    int a[2] = {0, 0};   // khởi tạo
    int i = nondet_int();
    int x = nondet_int();
    
    // Constraint i trong range hợp lệ
    if (i < 0 || i >= 1) return 0;  // chỉ test i = 0
    
    if (x == 0)
        a[i] = 0;
    else
        a[i] = 1;
    
    // Bây giờ a[i+1] luôn là 0 (chưa modify)
    assert(a[i + 1] == 0);  // assertion đúng
    return 0;
}
```

**Verify với CBMC**:

```bash
cbmc bounds.c --bounds-check
```

Output cho code gốc:

```
[main.array_bounds.1] line 11 array `a' upper bound: FAILURE
```

**Bài học**: code dùng làm BMC harness phải **rõ ràng về range của input**. `nondet_int()` không bound = BMC explore mọi int 32-bit. Dùng `__CPROVER_assume(0 <= i && i < N)` để focus.

## Sample 2: Pointer arithmetic và alias

**Nguồn**: Lec 3, mục Encoding Pointers and Memory.

**Code**:

```c
#include <assert.h>

int nondet_int(void);

int main(void) {
    int a[2], i, x, *p;
    p = a;
    i = nondet_int();
    x = nondet_int();
    
    if (x == 0)
        a[i] = 0;
    else
        a[i] = 1;
    
    assert(*(p + 2) == 1);   // (1) BUG
    return 0;
}
```

**Đọc nhanh**: tương tự sample 1 nhưng truy cập qua pointer.

**Bug**:

1. **Bug chính (Critical)**: `*(p + 2)` = `a[2]`, OOB (mảng size 2, valid index 0..1).
2. **Bug phụ**: `p = a` gán không cần ép kiểu (OK), nhưng `*(p + i + 1)` cũng OOB nếu `i >= 1`.

**Cơ chế encoding pointer trong BMC**:

CBMC dùng "**pointer encoding**" gồm 2 field:
- Object ID: identifier của allocated block.
- Offset: byte offset trong block.

```
p = a:
  object_id(p) = object_id(a)
  offset(p) = 0

p + 2:
  object_id(p+2) = object_id(p)
  offset(p+2) = offset(p) + 2 * sizeof(int) = 8

*(p+2):
  Read at object_id=a, offset=8
  
  Array a has size 2 * sizeof(int) = 8.
  Valid offset: 0..7.
  Offset 8 = OOB!
```

CBMC bắt OOB qua check `offset < object_size`.

**Fix**: tương tự sample 1, hoặc tăng buffer size:

```c
int a[3];   // đủ chỗ cho a[2]
```

Nhưng nếu intent là demo BMC bắt OOB, code giữ nguyên là **input demo đúng**.

**Verify**:

```bash
cbmc pointer_arith.c --pointer-check --bounds-check
```

```
[main.pointer_dereference.1] line 12 dereference failure: object boundaries: FAILURE
```

**Bài học**: BMC encode pointer chính xác (object + offset). Tool detect mọi OOB qua pointer arithmetic, không chỉ array index syntax.

## Sample 3: Floating-point encoding

**Nguồn**: Lec 3, mục Encoding Floats / IEEE 754.

**Code**:

```c
#include <assert.h>
#include <math.h>

double nondet_double(void);

int main(void) {
    double a = 0.1;
    double b = 0.2;
    double c = a + b;
    assert(c == 0.3);   // (1) BUG: float không exact
    return 0;
}
```

**Đọc nhanh**: kiểm tra `0.1 + 0.2 == 0.3`.

**Bug**:

1. **Bug chính (Logic)**: `0.1` và `0.2` **không biểu diễn được chính xác trong IEEE 754 double**. `0.1 + 0.2` ≈ 0.30000000000000004, không bằng `0.3` (cũng ≈ 0.29999999999999998).

**Cơ chế**:

IEEE 754 double dùng base 2 mantissa. Số `0.1` trong base 2 là tuần hoàn vô hạn: `0.0001100110011...`. Cần round → mất chính xác.

```python
>>> 0.1 + 0.2
0.30000000000000004
>>> 0.1 + 0.2 == 0.3
False
```

Bug này xuất hiện trong tài chính (lãi suất compound), khoa học (simulation), ML (gradient).

**Fix tuỳ context**:

**Option A: compare với epsilon**

```c
#include <math.h>

#define EPS 1e-9

if (fabs(c - 0.3) < EPS) {
    // c "approximately equal" 0.3
}
```

**Option B: dùng decimal arithmetic**

C không có built-in decimal. Dùng library hoặc C++ `boost::multiprecision::cpp_dec_float`.

**Option C: dùng integer (cents)**

Tài chính nên dùng integer biểu diễn cents thay vì float biểu diễn dollars:

```c
int64_t cents_a = 10;   // $0.10
int64_t cents_b = 20;   // $0.20
int64_t cents_c = cents_a + cents_b;   // 30 cents = $0.30, exact
```

**Verify với CBMC**:

```bash
cbmc float.c --float-overflow-check
```

CBMC dùng theory FP (IEEE 754), detect được assertion sai.

**Bài học**: KHÔNG dùng `==` cho float. KHÔNG dùng float cho money. KaBoom 1-2 sai sót trong domain critical.

## Sample 4: Float comparison subtle

**Nguồn**: Lec 3, ví dụ float edge case.

**Code**:

```c
#include <math.h>
#include <assert.h>

int main(void) {
    double x = 1.0 / 0.0;   // +Infinity
    double y = -1.0 / 0.0;  // -Infinity
    double n = 0.0 / 0.0;   // NaN
    
    assert(x > y);          // (1) OK: +Inf > -Inf
    assert(n != n);         // (2) Đúng! NaN != NaN
    assert(n == n);         // (3) BUG: this fails
    return 0;
}
```

**Đọc nhanh**: demo edge case IEEE 754 (+Inf, -Inf, NaN).

**Bug**:

1. Assertion 1 OK.
2. Assertion 2 đúng (NaN không equal anything, kể cả chính nó).
3. **Assertion 3 SAI**: `n == n` is `false` vì n là NaN. Assertion fail.

**Cơ chế**:

IEEE 754 đặc biệt:
- `1.0 / 0.0 = +∞` (positive infinity), không raise exception trong default mode.
- `0.0 / 0.0 = NaN` (not a number).
- `NaN op anything = NaN`.
- `NaN == NaN = false` (theo design, để detect NaN qua `x != x`).

**Fix** (cách check NaN đúng):

```c
#include <math.h>

if (isnan(n)) {
    // n là NaN
}
```

`isnan()` là macro chuẩn C99.

**Bài học**: code dùng float phải có NaN handling. CBMC `--nan-check` bắt operation tạo ra NaN.

## Sample 5: SSA conversion example

**Nguồn**: Lec 3, mục SSA encoding (concept).

**Code gốc**:

```c
int x = 0;
if (cond) {
    x = 1;
} else {
    x = 2;
}
y = x;
```

**Đọc nhanh**: gán x dựa trên cond, rồi assign y.

Đây không phải bug code, mà là **input để BMC convert sang SSA**.

**SSA form**:

```c
int x_0 = 0;
int x_1, x_2;
if (cond) {
    x_1 = 1;
} else {
    x_2 = 2;
}
int x_3 = cond ? x_1 : x_2;   // phi-node
y_0 = x_3;
```

Mỗi assignment tạo version mới của biến. Tại merge point (sau if-else), phi-node chọn version đúng.

**SMT encoding tương đương**:

```smt
(declare-const cond Bool)
(declare-const x_1 Int)
(declare-const x_2 Int)
(declare-const x_3 Int)
(declare-const y_0 Int)

(assert (=> cond (= x_1 1)))
(assert (=> (not cond) (= x_2 2)))
(assert (= x_3 (ite cond x_1 x_2)))
(assert (= y_0 x_3))
```

**Sample minh hoạ phi-node confusion**:

```c
int main(void) {
    int x = 0;
    if (cond) {
        x = 1;
    }
    // x_2 = phi(x_1, x_0)
    
    int y = x;
    // y == 0 hoặc 1, không xác định tại compile time
    
    assert(y == 0);   // BUG nếu cond = true
}
```

**Verify với CBMC**:

```bash
cbmc ssa.c
```

Output:

```
[main.assertion.1] line 8 assertion y == 0: FAILURE
Counterexample: cond = true → y = 1, assertion fail
```

**Bài học**: SSA là **internal representation** của compiler/BMC, không phải bug. Hiểu SSA giúp đọc CBMC output có "x_1, x_2, x_3" trong counterexample.

## Sample 6: Array assignment với index nondet

**Nguồn**: Lec 3, mục Array theory.

**Code**:

```c
#include <assert.h>

int nondet_int(void);

int main(void) {
    int a[10];
    int i = nondet_int();
    int v = nondet_int();
    
    if (i >= 0 && i < 10) {
        a[i] = v;
        assert(a[i] == v);   // (1) OK?
    }
    return 0;
}
```

**Đọc nhanh**: nondet i và v, gán a[i] = v, assert a[i] = v.

**Phân tích**: assertion **luôn đúng** (write-then-read same index = giá trị vừa ghi).

Nhưng nếu thay đổi nhẹ:

```c
a[i] = v;
a[j] = v + 1;   // j cũng nondet
assert(a[i] == v);   // (2) BUG nếu i == j
```

Khi `i == j`, `a[j] = v+1` đè lên giá trị vừa ghi. `a[i]` giờ là `v+1`, assertion fail.

**Cơ chế array theory**:

SMT array theory với axiom:
- `select(store(a, i, v), j) = v` nếu `i == j`.
- `select(store(a, i, v), j) = select(a, j)` nếu `i != j`.

BMC apply axiom này khi solve, bắt được trường hợp `i == j`.

**Fix**:

```c
if (i != j) {
    a[i] = v;
    a[j] = v + 1;
    assert(a[i] == v);   // OK
}
```

**Verify**:

```bash
cbmc array_alias.c
```

```
[main.assertion.1] line 11 assertion a[i] == v: FAILURE
Counterexample: i = j = 5, v = 0
```

**Bài học**: array alias (hai index có thể equal) là pattern subtle. BMC handle đúng nhờ array theory.

## Sample 7: Memory model với multiple pointer

**Nguồn**: Lec 3, mục Encoding pointers and memory.

**Code**:

```c
#include <assert.h>

int main(void) {
    int x = 10;
    int *p = &x;
    int *q = &x;
    
    *p = 20;
    assert(*q == 20);   // (1) OK vì p và q alias
    
    *q = 30;
    assert(x == 30);    // (2) OK
    return 0;
}
```

**Đọc nhanh**: hai pointer cùng trỏ x, mutate qua p, read qua q.

**Phân tích**: assertion đều đúng nếu compiler không optimize sai (volatile-like).

Bug subtle:

```c
int x = 10;
int *p = &x;
int *q = (int*)((char*)&x + 1);   // misaligned pointer
*p = 0;
*q = 1;
assert(x == 0);   // Behavior phụ thuộc memory layout
```

`q` không aligned cho int. Behavior **undefined**. Trên x86 thường work nhưng slow, trên ARM strict alignment crash.

**Cơ chế memory model**:

CBMC có 3 memory model:
- `--mm fixed`: object có fixed address.
- `--mm align`: object align theo type.
- `--mm offset`: track offset chính xác trong object.

Default là `align`, đủ cho hầu hết code C đúng.

**Bài học**: pointer alias đúng (cùng object, aligned) OK. Pointer **misaligned hoặc cross-object** là UB. CBMC bắt qua `--pointer-check`.

## Sample 8: Encoding integer division

**Nguồn**: Lec 3, mục Encoding numbers.

**Code**:

```c
#include <assert.h>
#include <limits.h>

int nondet_int(void);

int main(void) {
    int a = nondet_int();
    int b = nondet_int();
    
    int c = a / b;   // (1) BUG nếu b == 0
    int d = a % b;   // (2) BUG nếu b == 0
    
    int e = INT_MIN / -1;   // (3) BUG: signed overflow!
    
    assert(c * b + d == a);   // (4) Math identity: thường đúng
    return 0;
}
```

**Bug**:

1. **Bug 1 (Critical)**: division by zero là UB.
2. **Bug 2 (Critical)**: modulo by zero là UB.
3. **Bug 3 (High)**: `INT_MIN / -1` overflow vì `|INT_MIN| > INT_MAX`. Crash trên x86 (FPE).
4. Identity thường đúng nhưng có thể fail nếu b âm với mod convention khác (C99 uses truncated division).

**Cơ chế CBMC**:

```bash
cbmc div.c --div-by-zero-check --signed-overflow-check
```

```
[main.division-by-zero.1] line 8 division by zero: FAILURE
[main.division-by-zero.2] line 9 modulo by zero: FAILURE
[main.overflow.1] line 11 arithmetic overflow on signed division: FAILURE
```

CBMC bắt cả 3 bug.

**Fix**:

```c
if (b == 0) return -1;
if (a == INT_MIN && b == -1) return -1;  // overflow case

int c = a / b;
int d = a % b;
```

**Bài học**: division by zero và `INT_MIN / -1` là 2 case ít người nhớ. BMC bắt cả 2.

## Tóm tắt Phần 2

| Sample | Lớp bug | Tool detect |
|---|---|---|
| 1 Array bounds nondet | OOB | CBMC --bounds-check |
| 2 Pointer arith OOB | OOB | CBMC --pointer-check |
| 3 Float compare | Logic | CBMC --float-overflow-check |
| 4 NaN handling | Logic | CBMC --nan-check |
| 5 SSA / phi-node | (concept) | CBMC trace |
| 6 Array alias | Logic | CBMC array theory |
| 7 Pointer alias | Memory | CBMC --pointer-check |
| 8 Division overflow | Integer | CBMC --signed-overflow-check |

8 sample này demo **mọi loại check** mà BMC tool cung cấp built-in.

## Pattern lập harness BMC tốt

Sau khi đọc 8 sample, có thể đúc kết **best practice viết harness cho BMC**:

1. **Khởi tạo rõ ràng**: `int a[10] = {0}` thay vì uninitialized.
2. **Bound input**: `__CPROVER_assume(0 <= i && i < N)` để focus.
3. **Một assertion / harness**: dễ debug counterexample.
4. **Enable mọi check**: `--bounds-check --pointer-check --signed-overflow-check ...`
5. **Set unwind đủ lớn**: loop bound > thực tế ít nhất 2x.
6. **Lưu seed**: nếu counterexample đẹp, lưu làm regression test.

Code production thường khó verify trực tiếp. Tạo "**verification harness**" riêng, gọi target function với input nondet bounded.

---

**Tiếp theo**: [8.4 Code patterns Phần 3 (concurrency)](./04-code-patterns-cluster-3)
