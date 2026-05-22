---
id: 02-loop-unwinding-and-safety
title: 4.2 Loop unwinding và safety conditions
sidebar_position: 2
description: Cách BMC xử lý vòng lặp bằng unwinding, unwinding assertion, k-induction, và các loại safety condition phổ biến (array bounds, division by zero, null deref).
---

# 4.2 Loop unwinding và safety conditions

> **Tóm tắt một dòng**: Vòng lặp là thách thức cốt lõi của BMC: không thể encode trực tiếp vòng lặp vô hạn thành công thức hữu hạn. Giải pháp là **unwinding** (mở vòng lặp ra thành dãy instruction tuần tự đến độ sâu $k$), kèm theo **unwinding assertion** để báo nếu loop cần chạy quá $k$. **K-induction** mở rộng kỹ thuật này để chứng minh cho mọi depth.

## Đặt vấn đề: tại sao loop khó?

Trong [bài 1.6](../01-introduction/06-bmc-and-smt-basics), ta đã thấy ý tưởng cốt lõi của BMC: encode chương trình thành công thức $\Phi_k$ rồi giải bằng SMT. Một câu hỏi tự nhiên: nếu chương trình có vòng lặp, mà vòng lặp có thể chạy vô hạn, làm sao encode thành công thức **hữu hạn**?

Câu trả lời ngắn: **unwinding** (mở vòng lặp).

Câu trả lời dài: đó là cả một câu chuyện về trade-off giữa soundness, completeness, và practicality. Bài này kể câu chuyện đó.

## Unwinding cơ bản: ý tưởng

Cho một vòng `while`:

```c
while (cond) {
    body;
}
```

Unwind tới depth $k$ nghĩa là viết lại thành:

```c
if (cond) {
    body;
    if (cond) {
        body;
        if (cond) {
            body;
            // ... lặp k lần ...
            if (cond) {
                body;
                // hết k iteration
            }
        }
    }
}
```

Mỗi `if` tương ứng kiểm tra điều kiện loop trước khi vào iteration tiếp theo. Sau khi unwind, đoạn code là **tuần tự thuần** không có loop, encode được trực tiếp thành công thức SMT.

### Ví dụ cụ thể

Code gốc:

```c
int sum = 0;
int i = 0;
while (i < 3) {
    sum += i;
    i++;
}
assert(sum == 3);
```

Unwind $k = 3$:

```c
int sum = 0;
int i = 0;
if (i < 3) {       // iter 0
    sum += i;
    i++;
    if (i < 3) {   // iter 1
        sum += i;
        i++;
        if (i < 3) { // iter 2
            sum += i;
            i++;
        }
    }
}
assert(sum == 3);
```

Convert sang SSA (giả định loop đã unwind):

```
sum_0 = 0, i_0 = 0
// iter 0
guard_0 = (i_0 < 3) = true
sum_1 = sum_0 + i_0 = 0
i_1 = i_0 + 1 = 1
// iter 1
guard_1 = (i_1 < 3) = true
sum_2 = sum_1 + i_1 = 1
i_2 = i_1 + 1 = 2
// iter 2
guard_2 = (i_2 < 3) = true
sum_3 = sum_2 + i_2 = 3
i_3 = i_2 + 1 = 3
// exit
sum_final = ite(guard_2, sum_3, ite(guard_1, sum_2, ite(guard_0, sum_1, sum_0)))
            = sum_3 = 3
assert(sum_final == 3)
```

SMT solver check `(not (= sum_final 3))` $\Rightarrow$ UNSAT. Property đúng.

## Vấn đề: bound $k$ phải đủ lớn

Nếu bound $k$ ta chọn nhỏ hơn số iteration thực sự cần, có hai trường hợp.

**Trường hợp 1: chương trình chỉ chạy $\le k$ iteration**. Mọi thứ ổn. Unwind đủ, encode đầy đủ, kết quả chính xác.

**Trường hợp 2: chương trình cần chạy $> k$ iteration**. BMC chỉ encode tới $k$, không "thấy" hành vi sau đó. Có thể miss bug.

Ví dụ:

```c
int x = 0;
while (x < 100) {
    x++;
}
assert(x == 100);
```

Nếu unwind $k = 50$, ta chỉ encode 50 iteration. Sau 50 iteration, `x = 50`. Assertion `x == 100` fail trong encoding (vì `x = 50, không 100`). Tool báo SAT với counterexample "x cuối = 50". Nhưng counterexample này **không phải bug thật**: chương trình thực sự chạy đủ 100 iteration và assertion pass.

Đây là **false positive** do bound không đủ.

## Unwinding assertion: giải pháp cho bound không đủ

Để tránh false positive, BMC tool thêm một assertion đặc biệt sau iteration thứ $k$: **unwinding assertion**.

Sau khi unwind $k$ lần:

```c
if (cond) {
    body;
    if (cond) {
        body;
        // ... iter k ...
        assert(!cond);   // <-- UNWINDING ASSERTION
    }
}
```

Ý nghĩa: "sau $k$ iteration, điều kiện loop phải sai (loop kết thúc tự nhiên)". Nếu assertion này fail, nghĩa là loop thực sự cần chạy quá $k$, và BMC không thể quyết định property cho execution dài hơn.

Tool báo: "unwinding assertion failed at line X", nghĩa "tôi đã giới hạn loop $k$ iteration, nhưng chương trình cần nhiều hơn. Tăng bound đi."

### Ví dụ với unwinding assertion

Trở lại code trên với $k = 50$:

```
// sau 50 iter:
assert(not (x < 100));   // unwinding assertion
```

Với $x = 50$ sau 50 iter, `not (50 < 100)` là `not true` = false. Assertion fail. Tool báo: "loop iteration insufficient, increase --unwind". User tăng `--unwind 101` rồi chạy lại. Lần này unwinding assertion pass (loop kết thúc tự nhiên ở $x = 100$), property pass.

Quy trình này đảm bảo **soundness trong bound** $k$: nếu BMC nói "an toàn" và unwinding assertion không fail, an toàn cho mọi execution dài $\le k$. Nếu cần loop dài hơn, tool báo rõ.

## CBMC unwind options

CBMC có 3 flag chính cho unwinding:

```bash
cbmc --unwind 10 program.c           # mọi loop unwind 10 lần
cbmc --unwindset main.0:5,main.1:20  # loop 0 trong main unwind 5, loop 1 unwind 20
cbmc --unwind 10 --no-unwinding-assertions  # tắt unwinding assertion (nguy hiểm)
```

`--no-unwinding-assertions` tắt assertion, kết quả "an toàn" chỉ có nghĩa "an toàn trong bound $k$", không nói gì về execution dài hơn. Chỉ dùng khi bạn biết chắc loop không bao giờ chạy quá bound (ví dụ loop có upper bound rõ ràng do constraint trước đó).

## K-induction: chứng minh cho mọi $k$

Unwinding chỉ chứng minh property trong bound. Để chứng minh cho **mọi** $k$, dùng k-induction.

### Ý tưởng

Tương tự induction toán học, nhưng "step" rộng hơn:

- **Base case**: property đúng cho mọi execution dài $\le k$.
- **Inductive step**: nếu property đúng cho $k$ iteration liên tiếp gần đây, thì cũng đúng cho iteration thứ $k+1$.

Nếu chứng minh được cả hai, property đúng cho **mọi** depth.

### Format hình thức

Cho safety property $\phi$ (luôn đúng) và transition $T$:

$$\text{Base}: \quad I \land T^0 \land T^1 \land \cdots \land T^{k-1} \implies \phi_0 \land \phi_1 \land \cdots \land \phi_{k-1}$$

$$\text{Step}: \quad \phi_0 \land \phi_1 \land \cdots \land \phi_{k-1} \land T^0 \land \cdots \land T^{k-1} \implies \phi_k$$

trong đó $I$ là initial state, $T^i$ là transition tại step $i$, $\phi_i$ là property holds at step $i$.

Base case là BMC với bound $k$ kiểm tra property thoả trong $k$ bước đầu. Step case là một query SMT khác kiểm tra "giả sử property holds trong $k$ bước, có thể fail ở bước $k+1$ không?".

Nếu cả hai pass, dùng induction kết luận: property holds cho mọi $n \geq 0$.

### Ưu điểm

- **Tự động hoàn toàn**: không cần user cung cấp invariant.
- **Sound cho mọi depth**: chứng minh thật sự, không chỉ bound.

### Hạn chế

- Không phải mọi property k-inductive với $k$ nhỏ. Một số property cần $k$ rất lớn, không tractable.
- Step case có thể fail do **spurious counterexample**: trạng thái giả định "an toàn trong $k$ bước" nhưng thực ra unreachable từ initial. Cần kỹ thuật **invariant strengthening** để loại.

ESBMC và 2LS hỗ trợ k-induction tự động. CBMC chưa native nhưng có wrapper.

## Safety conditions: ngoài user assertion

User viết `assert(...)` để check property. Nhưng BMC còn check **nhiều property khác** tự động (gọi là **automatic safety conditions** hoặc **built-in checks**). Đây là các lớp bug phổ biến mà tool có thể detect không cần user chỉ định.

### Array out-of-bounds

```c
int arr[10];
int i = nondet_int();
arr[i] = 5;
```

BMC thêm assertion tự động: `assert(0 <= i && i < 10)`. Nếu solver tìm được $i$ vi phạm, báo "array out of bounds".

Trong CBMC: `--bounds-check` (default enabled).

### Division by zero

```c
int x = 10;
int y = nondet_int();
int z = x / y;
```

BMC thêm: `assert(y != 0)`. Nếu fail, báo "division by zero".

Trong CBMC: `--div-by-zero-check`.

### Null pointer dereference

```c
int *p = malloc(sizeof(int));
*p = 5;   // p có thể là NULL nếu malloc fail
```

BMC thêm: `assert(p != NULL)`. Nếu fail, báo "null dereference".

Trong CBMC: `--pointer-check`.

### Signed integer overflow

```c
int x = nondet_int();
int y = x + 1;
```

BMC thêm: `assert(x != INT_MAX)` (vì `INT_MAX + 1` overflow, UB trong C). Nếu solver tìm `x = INT_MAX`, báo "signed overflow".

Trong CBMC: `--signed-overflow-check`.

### Use after free

```c
int *p = malloc(sizeof(int));
free(p);
*p = 5;
```

BMC track "freed object set". Trước mọi dereference, check object trong set không. Nếu có, báo "use after free".

Trong CBMC: `--memory-leak-check`, `--memory-cleanup-check`.

### Memory leak

```c
int *p = malloc(sizeof(int));
return;   // không free
```

Tại điểm exit, check mọi allocated object đã free. Nếu không, báo leak.

### Race condition (chỉ với concurrency option bật)

Hai thread cùng write một biến không có lock. CBMC + concurrency support: `--lockset-check`.

## Tổng kết các flag CBMC quan trọng

```bash
cbmc program.c \
    --unwind 20 \
    --bounds-check \
    --pointer-check \
    --div-by-zero-check \
    --signed-overflow-check \
    --unsigned-overflow-check \
    --memory-leak-check \
    --no-unwinding-assertions   # nếu chắc loop không quá 20
```

Chạy lệnh này, CBMC kiểm tra mọi loại bug built-in cho mỗi loop unwind tới 20 iteration. Output liệt kê các check pass/fail và counterexample cho fail.

## Tóm tắt

- **Loop unwinding** là kỹ thuật cốt lõi để BMC xử lý vòng lặp: mở thành dãy tuần tự đến depth $k$.
- **Unwinding assertion** bảo đảm soundness: báo lỗi nếu loop cần chạy quá $k$, tránh false positive.
- **K-induction** chứng minh property cho **mọi depth**, không chỉ bound.
- **Safety conditions** là property tự động: array bounds, div-by-zero, null deref, integer overflow, use after free, leak.
- CBMC có rất nhiều flag để bật/tắt từng check. Production code nên bật hết để max coverage.

## Mini-quiz

<details>
<summary>Q1. Vì sao unwinding assertion quan trọng?</summary>

Unwinding assertion phân biệt hai trường hợp:
1. BMC chứng minh property đúng vì loop thực sự kết thúc trong bound $k$.
2. BMC "có vẻ" chứng minh được property, nhưng thực ra chỉ vì cắt cụt loop, không thấy execution dài hơn.

Không có unwinding assertion, tool có thể trả "an toàn" trong trường hợp 2, dẫn tới **false negative** (miss bug thật cần loop dài hơn).

Có unwinding assertion, nếu loop cần chạy quá $k$, tool báo rõ "tăng bound đi", user có thể tăng `--unwind` rồi thử lại.
</details>

<details>
<summary>Q2. K-induction tự động bao gồm hai bước. Vì sao bước "step" có thể fail với spurious counterexample?</summary>

Step case kiểm tra: "giả sử property đúng cho $k$ bước, có thể fail ở bước $k+1$ không?". Trong query này, **trạng thái sau $k$ bước có thể là bất kỳ** (không nhất thiết reachable từ initial).

Tool có thể tìm được một trạng thái $s_k$ "có vẻ thoả property" nhưng từ $s_k$ một bước nữa fail property. **Tuy nhiên $s_k$ có thể không bao giờ reachable** từ initial state.

Đây là spurious counterexample. Để loại, cần **invariant strengthening**: thêm điều kiện cho $s_k$ phải reachable (đó chính là invariant). Tool như IC3/PDR tự động hoá strengthening này.
</details>

<details>
<summary>Q3. Bạn dùng CBMC verify một code, tool báo "unwinding assertion failed" tại loop có comment "loop chạy tối đa 100 iteration". Bạn xử lý thế nào?</summary>

Hai khả năng:

**Khả năng 1**: bound CBMC đặt nhỏ hơn 100. Giải pháp: chạy lại với `--unwind 101` hoặc `--unwindset main.0:100` (chỉ cho loop đó).

**Khả năng 2**: comment trong code sai, loop thực sự có thể chạy quá 100 do edge case (nondet input). Đọc kỹ code, có thể có path mà loop chạy 1000 hay vô hạn iteration. Cần fix code (thêm break condition) hoặc thêm precondition (assume input nhỏ).

Quy trình debug:
1. Đọc counterexample mà CBMC cung cấp (input values dẫn tới loop dài).
2. Nếu input đó hợp lệ trong thực tế: bug. Fix code.
3. Nếu input không thể xảy ra (vì hệ thống lớn filter trước): thêm `__CPROVER_assume(input < N)` trước loop để loại trừ.
4. Chạy lại.
</details>

---

**Tiếp theo**: [4.3 Bit-blasting và arrays](./03-bit-blasting-and-arrays)
