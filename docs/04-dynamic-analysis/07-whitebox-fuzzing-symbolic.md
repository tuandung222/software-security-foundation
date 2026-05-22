---
id: 07-whitebox-fuzzing-symbolic
title: 5.7 White-box fuzzing (dynamic symbolic execution)
sidebar_position: 7
description: "Dynamic Symbolic Execution (DSE) và white-box fuzzing như SAGE. Concolic execution kết hợp concrete + symbolic, generational search, ứng dụng tìm bug deep."
---

# 5.7 White-box fuzzing: dùng symbolic execution để sinh input

> **Tóm tắt một dòng**: White-box fuzzing **đọc và phân tích code** để sinh input một cách thông minh. Kỹ thuật chính là **Dynamic Symbolic Execution (DSE)**, hay còn gọi **concolic execution**: chạy chương trình với input concrete, đồng thời track symbolic constraint, dùng SMT solver sinh input mới khám phá path chưa thấy.

## Vì sao cần white-box?

AFL (bài 5.6) là king cho hầu hết tình huống. Nhưng có những bug **rất sâu** AFL không tìm được dù chạy hàng tuần.

Ví dụ:

```c
int parse(char *input) {
    if (input[0] != 'M') return 0;
    if (input[1] != 'A') return 0;
    if (input[2] != 'G') return 0;
    if (input[3] != 'I') return 0;
    if (input[4] != 'C') return 0;
    // ... critical code ở đây, có bug ...
}
```

AFL với random mutation: xác suất hit "MAGIC" là $1/256^5 \approx 10^{-12}$. Có thể không bao giờ.

White-box: phân tích code, biết để vào critical, input cần `MAGIC`. SMT solver sinh input đó trong 1 query. Tìm bug nhanh hơn 12 bậc.

Đây là động lực cho DSE.

## Dynamic Symbolic Execution (DSE)

DSE còn gọi là **concolic execution** = **conc**rete + symb**olic**.

### Ý tưởng

Chạy chương trình với input cụ thể (concrete) như testing thông thường. **Đồng thời**, track input là symbolic variable, accumulate path constraint khi đi qua mỗi branch.

Khi chương trình kết thúc, có:
1. **Concrete trace**: chương trình đã chạy đường nào.
2. **Path constraint**: công thức SMT mô tả mọi input có cùng đường đó.

Để khám phá đường khác:
1. Phủ định một branch constraint.
2. Gọi SMT solver: tìm input thoả constraint mới.
3. Solver trả input concrete cho path mới.
4. Chạy lại với input mới, repeat.

### Ví dụ chạy DSE

```c
int f(int x, int y) {
    if (x > 5) {
        if (y < 10) {
            assert(x + y != 100);
        }
    }
    return 0;
}
```

**Iteration 1**: chạy với input $x = 0, y = 0$.

Trace: `f(0, 0)`. Symbolic: $x = x_0, y = y_0$.
- Tại `if (x > 5)`: $x_0 > 5$ false. Path: `(x_0 \leq 5)`. Đi vào else (trống), return 0.

Path constraint cho path này: $x_0 \leq 5$.

Để khám phá path khác, phủ định: $x_0 > 5$. Gọi solver:

```
SMT: find x_0 thoả x_0 > 5
Solver: x_0 = 6
```

**Iteration 2**: chạy với $x = 6, y = 0$.

Trace: vào nhánh `if (x > 5)`. Tại `if (y < 10)`: $y_0 < 10$ true. Path: `(x_0 > 5) AND (y_0 < 10)`. Đi vào assert.

Assertion `x + y != 100`: $x_0 + y_0 \neq 100$. Với $x_0 = 6, y_0 = 0$, $6 + 0 = 6 \neq 100$. Assert pass.

Path constraint: $x_0 > 5 \land y_0 < 10$.

Để khám phá assertion fail, thêm constraint **phủ định assertion**: $x_0 + y_0 = 100$.

```
SMT: find x_0, y_0 thoả (x_0 > 5) AND (y_0 < 10) AND (x_0 + y_0 = 100)
Solver: x_0 = 91, y_0 = 9 (one of many solutions)
```

**Iteration 3**: chạy với $x = 91, y = 9$. Assertion fail. **Bug found.**

DSE tìm bug trong 3 iteration. So với AFL random mutation cần $\approx 10^{18}$ iteration để hit $x + y = 100$ với $x > 5, y < 10$.

## DSE vs Symbolic Execution thuần

Symbolic execution (KLEE, Klee) chạy chương trình với **chỉ symbolic input**, không concrete. Tại mỗi branch, fork:

- Khám phá cả 2 nhánh: số path nổ lên (path explosion).
- Khi gặp loop, fork mỗi iteration: vô hạn path nếu loop unbounded.
- Khi gặp call ngoài (libc, syscall), không biết model như thế nào: stuck.

DSE giải quyết:
- **Concrete value cho external call**: dùng giá trị concrete khi DSE đi vào libc. Không cần model.
- **Path explosion controlled**: mỗi iteration chỉ chạy 1 path (concrete). Tổng số iteration = số path khám phá.
- **Loop bounded**: chạy concrete tới khi exit. Không vô hạn.

DSE practical hơn symbolic execution thuần cho code thực.

## SAGE: white-box fuzzer của Microsoft

**SAGE** (Scalable Automated Guided Execution), 2008. White-box fuzzer cho Windows binary.

### Architecture

SAGE giả định binary already compiled. Dùng x86 emulator (Nirvana) để chạy concrete + track symbolic.

```
seed input → concrete run → trace với symbolic constraint
                    ↓
            generational search over branches
                    ↓
            for each branch:
                phủ định branch, gọi Z3
                Z3 trả input mới
                add input vào queue
            ↓
            next iteration: pick input từ queue
```

### Generational search

SAGE không khám phá depth-first hay breadth-first. Dùng **generational search**:

- Generation 0: seed input.
- Generation 1: mọi input sinh từ generation 0 (phủ định mỗi branch của seed run).
- Generation 2: mọi input sinh từ generation 1 input.
- ...

Mỗi generation, pick input có "score" cao nhất (theo coverage potential, depth, etc.).

### Kết quả thực tế

SAGE chạy on Windows codebase từ 2007. Đã tìm hàng trăm bug trong Office, Windows kernel, Internet Explorer. Microsoft công bố SAGE tìm "30% security bug" của Windows 7 trong giai đoạn pre-release.

Một thành công cụ thể: 2009, SAGE tìm bug parsing trong ANI cursor format, bug đã có từ Windows 95. Bug tồn tại 14 năm, AFL không tìm được, SAGE tìm trong vài giờ.

## Driller: hybrid AFL + DSE

**Driller** (2016): combine AFL với DSE.

- AFL chạy chính, fast coverage exploration.
- Khi AFL stuck (coverage không tăng trong N giờ), invoke DSE để break through hard constraint.
- DSE sinh input vượt qua "wall", feed về AFL.

Driller tìm bug trong DARPA Cyber Grand Challenge (2016): autonomous CTF, máy tự pwn binary.

## Khó khăn của DSE

### Path explosion

Mỗi branch nhân đôi số path. Chương trình có $n$ branch có $2^n$ path. Với $n = 30$, đã $10^9$ path, vượt khả năng explore.

Mitigation:
- **Path merging**: gộp path tương tự thành 1 (giảm số state).
- **State pruning**: bỏ path "không hứa hẹn".
- **Function summarization**: thay gọi function bằng summary precomputed.

### External call

DSE gặp `printf`, `malloc`, `system`: không track symbolic được. Phải:
- **Concretize**: dùng concrete value, lose symbolic info.
- **Model**: viết tay model của libc function, mất công.
- **Stub**: skip function, giả định không có side effect.

KLEE có model cho hầu hết libc, vẫn limited.

### Memory model

Pointer aliasing trong DSE phức tạp. `*p = 5` với `p` symbolic: solver phải case split trên possible aliases. Có thể cực chậm.

### Float

Symbolic float với SMT FP theory rất chậm. Hầu hết DSE concretize float, mất sound.

## DSE tools

**KLEE** (Stanford, 2008): symbolic execution cho LLVM IR. Open source. Tìm bug trong coreutils, libc. Khoảng 50+ paper sử dụng KLEE.

**SAGE** (Microsoft): commercial, không open. Track record impressive trong Microsoft codebase.

**Mayhem** (CMU spin-off): hybrid SE + fuzz. Won DARPA Cyber Grand Challenge.

**S2E** (EPFL): symbolic execution cho whole-system (kernel + userland). Test driver.

**angr** (UCSB): Python framework cho binary analysis + symbolic execution. Popular trong CTF.

**Manticore** (Trail of Bits): smart contract symbolic execution (Ethereum, EVM).

## Tóm tắt

- **DSE = concolic execution**: chạy concrete + track symbolic.
- Sinh input mới bằng cách phủ định branch, gọi SMT solver.
- Giải quyết external call và loop bằng concrete run.
- **SAGE** là exemplar: Microsoft dùng từ 2007, tìm hàng trăm bug.
- **Driller** hybrid AFL + DSE: AFL fast, DSE break "wall".
- Khó khăn: path explosion, external call, memory aliasing, float.

## Mini-quiz

<details>
<summary>Q1. DSE và pure symbolic execution khác nhau cốt lõi ở điểm nào?</summary>

**Pure symbolic execution** (KLEE original): mọi value symbolic. Tại mỗi branch, fork cả 2 path. Không có "concrete" trace.

**DSE (concolic)**: chạy concrete trace cụ thể, đồng thời track symbolic constraint **dọc theo trace**. Mỗi iteration là 1 path concrete + 1 path constraint. Để khám phá path khác, phủ định branch, gọi solver, có input concrete mới, chạy lại.

Sự khác biệt thực dụng:

| Tiêu chí | Pure SE | DSE |
|---|---|---|
| Path explosion | Vấn đề chính | Quản lý bằng chọn path explore |
| External call | Khó (cần model) | Dùng concrete value, work as-is |
| Loop unbounded | Vô hạn fork | Concrete run, hữu hạn |
| Soundness | Sound (cover all paths) | Sound trong path đã explore |

DSE practical hơn cho code thực với libc, IO, syscall.
</details>

<details>
<summary>Q2. Vì sao "MAGIC" check là ví dụ kinh điển white-box thắng black-box?</summary>

```c
if (input[0] != 'M') return;
if (input[1] != 'A') return;
if (input[2] != 'G') return;
if (input[3] != 'I') return;
if (input[4] != 'C') return;
// critical code here
```

Mỗi byte có 256 giá trị. Để vào critical code, cần đúng `MAGIC` (5 byte). Xác suất random: $1/256^5 \approx 10^{-12}$.

AFL với 10000 test/giây cần $10^{12} / 10^4 = 10^8$ giây $\approx 3$ năm để có 50% cơ hội hit.

White-box DSE: chạy 1 input ngẫu nhiên, fail ở byte đầu. Phủ định constraint `input[0] != 'M'`. Solver trả input có `input[0] = 'M'`. Chạy, fail ở byte 2. Phủ định, solver trả input có `MA`. Sau 5 iteration, có `MAGIC`. Vào critical code, bắt đầu fuzz deep.

DSE thắng AFL bằng cách "directed search" thay vì random. Đặc biệt mạnh khi code có nhiều check kiểu này (parser format có magic, checksum, ...).
</details>

<details>
<summary>Q3. Driller hybrid AFL + DSE thế nào? Khi nào DSE được invoke?</summary>

Driller architecture:

1. **AFL chạy chính**: fast fuzzing, scale cao.
2. **Coverage tracker**: theo dõi coverage growth.
3. **Stall detector**: nếu coverage không tăng trong N giờ, AFL stuck.
4. **DSE invoke**: feed seed corpus cho DSE engine.
5. **DSE explore**: dùng concolic để break "hard constraint" (như MAGIC).
6. **Sync corpus**: input mới DSE tạo được feed lại cho AFL.
7. **AFL tiếp tục**: với corpus richer, AFL có thể explore xa hơn.

Insight: AFL fast nhưng stupid (random mutation). DSE slow nhưng smart (solver). Combine: AFL handle 90% công việc, DSE giúp 10% còn lại (hard constraint).

Tỷ lệ time: AFL ~95%, DSE ~5%. Nhưng 5% DSE đó tìm được bug AFL không bao giờ thấy.

Đây là pattern modern fuzzing: AFL + DSE + grammar + tất cả integrate. Khả năng tự tuning trở thành quan trọng vì configuration manually rất khó.
</details>

:::tip[DS perspective]
Dynamic Symbolic Execution **literally** là PyTorch autograd nhưng cho boolean/integer constraint thay vì float gradient. **Symbolic variable** ≈ tensor với `requires_grad=True`. **Path constraint accumulation** ≈ backward pass accumulating gradient. **Z3 solve for input** ≈ gradient descent for adversarial input (FGSM, PGD). **Concolic execution** (concrete + symbolic) ≈ **PGD attack** (concrete starting point + gradient step). **Hybrid AFL+DSE (Driller)** ≈ **hybrid genetic + gradient** optimizer (CMA-ES warm-started by gradient). Bạn quen autograd = quen 80% concept symbolic execution.
:::

---

**Tiếp theo**: [5.8 BMC for test generation](./08-bmc-for-test-generation)
