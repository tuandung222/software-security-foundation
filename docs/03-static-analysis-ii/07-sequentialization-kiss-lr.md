---
id: 07-sequentialization-kiss-lr
title: 4.7 Sequentialization (KISS, LR)
sidebar_position: 7
description: Dịch chương trình multi-threaded thành sequential program tương đương, cho phép dùng lại tool BMC tuần tự. KISS (Keep It Sequential, Stupid) của Qadeer-Wu và LR (Lal-Reps) sequentialization.
---

# 4.7 Sequentialization: dịch multi-thread về sequential

> **Tóm tắt một dòng**: Sequentialization là kỹ thuật dịch một chương trình $k$-thread thành sequential program tương đương, nơi mọi vi phạm property của bản gốc đều có vi phạm tương ứng trong bản dịch. Sau dịch, ta dùng tool BMC tuần tự (CBMC) để verify. KISS và LR là hai phương pháp khác nhau với trade-off khác nhau.

## Vì sao cần sequentialization?

Concurrency verification có một thực tế khó chịu: hầu hết tool BMC mạnh nhất (CBMC, Z3, CVC5) được thiết kế cho **sequential program**. Mở rộng chúng cho multi-thread cần code thêm, test thêm, debug thêm. Nhiều tool concurrency riêng (Chess, JPF) không có cùng độ mature.

**Sequentialization** là idea: thay vì viết tool concurrency mới, **dịch** multi-thread thành sequential, rồi dùng tool sequential có sẵn. Vừa tận dụng tool mature, vừa không cần học framework mới.

Câu hỏi cốt lõi: có thể dịch không, và dịch như thế nào để bảo toàn semantics?

## KISS: Keep It Sequential, Stupid

**KISS** (Qadeer-Wu, 2004) là sequentialization đầu tiên cho CBA. Ý tưởng: encode mỗi "round" của round-robin schedule thành một block sequential.

### Round-robin schedule

Round-robin với $K$ context switch: chia execution thành $K+1$ round. Trong mỗi round, các thread chạy theo thứ tự cố định, mỗi thread chạy một số instruction (variable) rồi yield cho thread tiếp theo.

Ví dụ với 2 thread, $K = 2$:

```
Round 0: T1 chạy n_1 instruction (nondet) -> T2 chạy n_2 instruction
Round 1: T1 chạy n_3 -> T2 chạy n_4
Round 2: T1 chạy n_5 -> T2 chạy n_6
```

Tổng: $K+1 = 3$ round, mỗi round T1 và T2 đều chạy 1 phase. Mỗi phase có độ dài nondet (variable).

### Encoding KISS

Sequential program tương đương:

```c
int round = 0;
int t1_pc = 0, t2_pc = 0;   // program counter

void main() {
    while (round < K + 1) {
        // T1 chạy phase trong round này
        int t1_phase_length = nondet_int();
        for (int i = 0; i < t1_phase_length; i++) {
            execute_one_instruction_of_t1();
            t1_pc++;
            if (t1_done()) break;
        }
        // T2 chạy phase
        int t2_phase_length = nondet_int();
        for (int i = 0; i < t2_phase_length; i++) {
            execute_one_instruction_of_t2();
            t2_pc++;
            if (t2_done()) break;
        }
        round++;
    }
}
```

Cho CBMC encode đoạn này. Tool sẽ khám phá mọi schedule có $\leq K$ context switch (vì có $K+1$ round, mỗi round có T1 rồi T2, tổng $2(K+1) - 1 = 2K+1$ thread transition, nhưng số context switch chỉ là $K$).

### Hạn chế KISS

KISS đơn giản nhưng có nhược điểm:

1. **Round-robin cố định**: T1 luôn chạy trước T2 trong mỗi round. Nếu bug cần T2 chạy trước T1 trong round nào đó, KISS không tìm được. Để cover: chạy KISS với mọi permutation của thread order, hoặc fix bằng cách cho choose order nondet ở đầu mỗi round.

2. **Variable phase length**: phase có thể có 0 instruction (thread không chạy gì trong round). Tăng số schedule khám phá nhưng cũng tạo redundancy.

3. **Memory blowup**: với $K$ lớn, phải duplicate trạng thái cho mỗi round.

## LR: Lal-Reps sequentialization

**LR** (Lal-Reps, 2008) là sequentialization tinh tế hơn, dựa trên ý tưởng **explicit context switch**.

### Ý tưởng

Thay vì round-robin, LR cho phép sequential program "switch" giữa thread tại bất kỳ điểm nào. Mỗi switch là một point trong sequential code.

Implementation: mỗi thread được encode như một function `execute_t_i(state, K_remaining)`. Hàm này chạy thread cho tới khi:
- Thread kết thúc, hoặc
- Quyết định switch (nondet, giảm `K_remaining`).

Sequential main:

```c
void main() {
    state = initial();
    K_remaining = K;
    
    // chọn thread bắt đầu nondet
    int starting_thread = nondet_int() % NUM_THREADS;
    execute_t[starting_thread](state, K_remaining);
}

void execute_t_i(state, K_remaining) {
    while (true) {
        if (t_i.done()) return;
        
        // chạy 1 instruction
        execute_one_instruction(state, i);
        
        // có thể switch?
        if (K_remaining > 0 && nondet_bool()) {
            int next_thread = nondet_int() % NUM_THREADS;
            if (next_thread != i) {
                K_remaining--;
                execute_t[next_thread](state, K_remaining);
            }
        }
    }
}
```

Recursive calls model context switches. Mỗi switch trừ 1 từ `K_remaining`. Tổng tối đa $K$ switch.

### Ưu điểm LR

1. **Linh hoạt hơn KISS**: không bó hẹp round-robin. Schedule bất kỳ trong $K$ switch đều khám phá.
2. **Soundness rõ ràng**: dễ chứng minh tương đương semantics.
3. **Áp dụng được cho async program**: model `async/await` của C#, Python, JS qua sequentialization.

### Hạn chế LR

1. **Recursion depth**: với $K$ lớn, recursion sâu, tốn stack. Mỗi switch thêm một stack frame.
2. **State explosion**: phải duplicate state cho mỗi nhánh nondet.

## So sánh KISS và LR

| Tiêu chí | KISS | LR |
|---|---|---|
| Cấu trúc | Round-robin | Explicit switch |
| Số schedule cover | Subset (bound theo round structure) | Toàn bộ trong $K$ switch |
| Implementation | Đơn giản | Phức tạp hơn (recursive) |
| Recursion depth | $O(K)$ | $O(K)$ nhưng dễ overflow stack |
| Pháp lý cho async | Không | Có |
| Tool hỗ trợ | CSeq, Lazy-CSeq | CSeq, ESBMC |

Trong thực tế, LR là chuẩn cho concurrency verification modern.

## Một ví dụ chạy LR đầy đủ

Cho code multi-threaded:

```c
int x = 0;
int y = 0;

void* t1() {
    x = 1;
    y = 1;
}

void* t2() {
    if (y == 1) {
        assert(x == 1);
    }
}
```

Property: `x == 1` khi `y == 1`. Trực giác: T1 set $x$ trước $y$, nên khi $y = 1$ ta đã có $x = 1$. Nhưng SC reordering: nếu T1 reorder thành "y=1; x=1", T2 đọc $y = 1$ thì $x$ có thể vẫn = 0.

LR sequentialization:

```c
int x = 0, y = 0;
int K = 2;
int K_remaining = K;

void execute_t1() {
    x = 1;
    if (K_remaining > 0 && nondet_bool()) {
        K_remaining--;
        execute_t2();
    }
    y = 1;
    if (K_remaining > 0 && nondet_bool()) {
        K_remaining--;
        execute_t2();
    }
}

void execute_t2() {
    int local_y = y;
    if (K_remaining > 0 && nondet_bool()) {
        K_remaining--;
        execute_t1();
    }
    if (local_y == 1) {
        int local_x = x;
        assert(local_x == 1);
    }
}

int main() {
    int starting = nondet_int() % 2;
    if (starting == 0) execute_t1();
    else execute_t2();
    return 0;
}
```

Đưa cho CBMC. CBMC khám phá schedule:

1. Bắt đầu T1: `x = 1`. Switch sang T2: `local_y = y = 0`. Switch về T1: `y = 1`. T2 tiếp: `local_y == 1`? No (local_y vẫn = 0 vì đã đọc trước). Assertion không check.

2. Bắt đầu T1: `x = 1`. Không switch. `y = 1`. T1 done. T2 chạy: `local_y = 1`. `local_x = x = 1`. Assertion `local_x == 1` pass.

3. Bắt đầu T2: `local_y = 0`. Switch sang T1: `x = 1; y = 1`. T2 tiếp: `local_y == 1`? No. Pass.

4. Bắt đầu T2: `local_y = 0`. T2 done (vì if false). T1 chạy: `x = 1; y = 1`. Pass.

Mọi schedule, assertion pass (với SC). UNSAT.

Nếu model TSO (cho phép T1 reorder x = 1 và y = 1), tool tìm được counterexample.

## Tools sequentialization

**CSeq** (Imperial College, UK): family of sequentialization tool. Bao gồm Lazy-CSeq (lazy variant), AsyncCSeq (cho async), DPDA-CSeq (cho concurrent data structures).

**ESBMC**: tích hợp sequentialization riêng, không gọi tool ngoài.

**SMACK**: LLVM-based, sequentialization cho LLVM IR.

## Khi nào dùng sequentialization vs native concurrency mode?

**Dùng sequentialization khi**:
- Bạn đã quen tool sequential, không muốn học framework concurrency.
- Code có cấu trúc đơn giản, ít thread.
- Cần verify trên LLVM IR hoặc C/C++ thuần.

**Dùng native concurrency mode khi**:
- Code dùng feature đặc biệt (atomic, memory order specific).
- Cần model weak memory model (TSO, RMO).
- Có nhiều thread (> 4), recursion depth của LR là vấn đề.

## Tóm tắt

- **Sequentialization** dịch multi-thread thành sequential để verify bằng tool tuần tự.
- **KISS** (Qadeer-Wu): round-robin, đơn giản nhưng cứng nhắc.
- **LR** (Lal-Reps): explicit switch, linh hoạt hơn, áp dụng async.
- Tool: CSeq, ESBMC, SMACK.
- Trade-off với native concurrency: sequentialization tận dụng tool sequential mature, native có thể chính xác hơn với memory model.

## Mini-quiz

<details>
<summary>Q1. Vì sao sequentialization gọi là "translation" mà không phải "simulation"?</summary>

**Simulation** là chạy chương trình trong môi trường giả lập (như SPIN simulator), không tạo ra một chương trình mới.

**Translation** là **biến đổi syntactic** từ chương trình multi-thread thành chương trình sequential mới. Code mới có thể compile, có thể chạy, có thể verify bằng tool khác.

Sequentialization là translation: input là source code multi-thread, output là source code sequential. Mọi đặc tính của output là một chương trình C bình thường.

Đây là điểm mạnh: output có thể đẩy qua bất kỳ tool sequential nào, không cần tool concurrency-aware.
</details>

<details>
<summary>Q2. KISS bị giới hạn ở round-robin. Bug nào KISS không tìm được mà LR tìm được?</summary>

KISS round-robin: trong mỗi round, T1 luôn chạy trước T2. Nếu schedule "T2 chạy trước T1 trong round 0, T1 chạy trước T2 trong round 1" cần thiết để lộ bug, KISS không tìm được trừ khi run lại với thread order khác.

Ví dụ bug:

```c
int x = 0, y = 0;

void* t1() {
    if (y == 0) {     // round 0: y vẫn = 0
        x = 1;
    }
}

void* t2() {
    if (x == 0) {     // cần x vẫn = 0 khi T2 đọc
        y = 1;
    }
}
```

Bug đáng nhẽ: cả hai nhánh `if` đều có thể vào, dẫn tới `x = 1` và `y = 1`. Để cover, schedule cần T2 chạy trước T1 trong round 0 (để T2 đọc x = 0 trước khi T1 set).

KISS với round-robin "T1 first" miss này. LR khám phá mọi schedule, tìm được.

Workaround cho KISS: chạy 2 lần với 2 thread order, hoặc nondet thread order ở đầu round.
</details>

<details>
<summary>Q3. LR dùng recursion để model context switch. Vấn đề gì có thể xảy ra với $K$ rất lớn?</summary>

Mỗi context switch thêm một stack frame. Với $K$ context switch, recursion depth tới $K+1$. Mỗi frame chứa local variables, return address, có thể vài KB.

Với $K = 5$ (sweet spot CBA), depth 6, không vấn đề.

Với $K = 50$ hoặc 100, stack depth 100+, có thể stack overflow trên CBMC default config (CBMC giới hạn stack frame để tránh state explosion).

Hai workaround:

1. **Tăng stack limit**: `cbmc --depth 1000` cho phép recursion sâu hơn.
2. **Dùng iterative version của LR**: thay recursion bằng explicit stack (mảng simulating). Phức tạp hơn implement nhưng scale tốt.

Trong thực tế, $K$ trong CBA thường nhỏ (2-5), không cần worry.
</details>

---

**Kết thúc Phần 3 (Lecture 4).** Bạn đã hiểu các kỹ thuật cốt lõi để xử lý concurrency: bit-blasting, CBA, lazy exploration, schedule recording, sequentialization. Chuyển sang [Lecture 5: Dynamic Analysis (Testing, Monitoring, Fuzzing)](../04-dynamic-analysis/01-overview).
