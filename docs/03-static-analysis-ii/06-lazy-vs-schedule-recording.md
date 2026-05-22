---
id: 06-lazy-vs-schedule-recording
title: 4.6 Lazy exploration vs Schedule recording
sidebar_position: 6
description: "Hai chiến lược cụ thể để khám phá schedule space một cách hiệu quả: lazy interleaving chỉ fork khi cần, và schedule recording lưu trữ schedule đã thử để tránh redundancy."
---

# 4.6 Lazy exploration và Schedule recording: hai chiến lược khám phá

> **Tóm tắt một dòng**: Sau khi đã giảm không gian bằng Context-Bounded Analysis (bài 4.5), ta vẫn cần khám phá hàng nghìn schedule. Hai kỹ thuật giúp khám phá hiệu quả: **lazy interleaving** chỉ fork thread khi gặp shared access; **schedule recording** ghi schedule đã thử để tránh khám phá lại tương đương.

## Bối cảnh: lazy thay vì eager

Cách "ngây thơ" để verify multi-threaded code là **eager exploration**: tại mỗi instruction, fork mọi schedule khả dĩ. Số nhánh bùng nổ ngay từ instruction đầu tiên.

Ví dụ với 2 thread, mỗi thread 10 instruction. Eager fork tại instruction 1: 2 nhánh (T1 chạy trước hay T2). Tại instruction 2: 4 nhánh. Tại instruction 10: $2^{10} = 1024$ nhánh. Tại instruction 20: $\binom{20}{10}$ = 184756 lá.

Quan sát: hầu hết instruction là **local** (không truy cập shared memory). Nếu T1 đang làm $x_{local} = x_{local} + 1$ với biến local, T2 chạy hay không không ảnh hưởng. Chỉ cần fork tại **shared access**.

Đây là ý tưởng **lazy interleaving**: chỉ fork schedule khi gặp shared memory access (read hoặc write), không fork tại local instruction.

## Lazy interleaving: hoạt động

Pseudocode:

```
def lazy_explore(state, thread_active):
    while True:
        next_inst = state.threads[thread_active].next_instruction()
        if next_inst is None:
            # thread đã xong, chuyển thread khác hoặc kết thúc
            return choose_next_thread_or_finish(state)
        
        if next_inst is local_access:
            # không cần fork, chạy luôn
            state.execute(next_inst, thread_active)
        else:
            # shared access: fork cho mọi thread khác có thể chạy trước
            for other_thread in state.runnable_threads:
                if other_thread != thread_active:
                    fork_with(other_thread)
            state.execute(next_inst, thread_active)
```

Hiệu quả: nếu chương trình có $n$ shared access tổng, số nhánh lazy là $O(n^K)$ với $K$ thread. Nhiều ít hơn $O(L^K)$ với $L$ tổng instruction.

## Ví dụ minh hoạ lazy

```c
int shared = 0;

void* t1(void *arg) {
    int local1 = 1;
    int local2 = 2;
    int local3 = local1 + local2;   // 3 instruction local
    shared = local3;                 // SHARED ACCESS
    int local4 = 10;
    int local5 = local4 * 2;         // 2 instruction local
    return NULL;
}

void* t2(void *arg) {
    int local6 = 5;
    shared = local6;                 // SHARED ACCESS
}
```

Số instruction tổng: T1 có 6, T2 có 2.

Eager: fork tại mỗi instruction, số nhánh $\binom{8}{2} = 28$ schedule.

Lazy: chỉ fork tại 2 shared access. Số nhánh effective: 2 (T1 ghi trước hay T2 ghi trước). Tốc độ tăng 14 lần với example nhỏ này.

Trong code thực, tỷ lệ shared access / total thường rất thấp (< 5%), nên lazy tăng tốc 10-100 lần.

## Vấn đề của lazy: deadlock detection

Lazy gặp khó khi cần detect deadlock. Deadlock liên quan tới lock acquisition order, không nhất thiết là "shared memory access" theo nghĩa local-vs-global thuần.

Giải pháp: coi `lock()` và `unlock()` là shared access. Mỗi `lock(m)` fork điểm interleaving với mọi thread khác có thể đang chờ `m`.

## Schedule recording: không khám phá lại

Vấn đề thứ hai: cùng một state có thể đến từ nhiều schedule khác nhau (nếu các instruction giữa chừng giao hoán). Khám phá lại state đã thấy là lãng phí.

**Schedule recording** lưu danh sách các schedule đã thử. Trước khi explore schedule mới, check nó có tương đương schedule đã thử không. Nếu có, skip.

### Equivalence theo Mazurkiewicz trace

Hai schedule "tương đương" nếu chúng cùng kết quả với mọi instruction giao hoán. Định nghĩa hình thức dùng **Mazurkiewicz trace**: equivalence class của các schedule dưới relation "có thể swap các instruction giao hoán liền kề".

Ví dụ schedule:

```
S1: T1.a -> T1.b -> T2.c -> T2.d
S2: T1.a -> T2.c -> T1.b -> T2.d
```

Nếu T1.b và T2.c không xung đột (không cùng biến, không cùng lock), S1 và S2 cho cùng kết quả. Chúng cùng Mazurkiewicz trace.

Schedule recording chỉ khám phá 1 trace per equivalence class. Tiết kiệm số lần gọi solver.

### Implementation: vector clock

Để check equivalence hiệu quả, dùng **vector clock**. Mỗi thread có một counter, mỗi instruction tăng counter của thread tương ứng.

Hai event $e_1$ và $e_2$:
- **Happens-before**: $e_1 \to e_2$ nếu vector clock của $e_1$ component-wise nhỏ hơn của $e_2$.
- **Concurrent**: $e_1 \parallel e_2$ nếu không $e_1 \to e_2$ cũng không $e_2 \to e_1$.

Instruction concurrent có thể swap. Schedule chỉ khác ở swap concurrent là equivalent.

## Dynamic Partial Order Reduction (DPOR)

Combine lazy exploration + schedule recording + vector clock = **DPOR**, kỹ thuật state-of-the-art cho concurrency exploration.

Thuật toán cao cấp:

```
def DPOR(state):
    if state is terminal:
        check property
        return
    
    next_events = compute_next_events(state)
    persistent_set = compute_persistent_set(state, next_events)
    
    for event in persistent_set:
        DPOR(state.execute(event))
        
        # backtrack: try alternative events that could race
        for other_event in next_events:
            if races_with(event, other_event):
                add_to_explore_later(other_event)
```

**Persistent set**: tập tối thiểu các event cần khám phá tại state hiện tại sao cho mọi reachable state vẫn được cover.

DPOR optimal: khám phá ít schedule nhất có thể (tính theo equivalence class).

Tool: **rcmc** (race condition model checker), implementation của DPOR cho LLVM IR.

## Lazy vs Eager: trade-off

| Tiêu chí | Eager | Lazy |
|---|---|---|
| Implementation | Đơn giản | Phức tạp (track shared) |
| Số nhánh khám phá | $O(L^K)$ | $O(n^K)$ với $n$ = shared access |
| Memory | Nhiều state | Ít state (skip local) |
| Hỗ trợ weak memory | Khó | Khó hơn |
| Mature tools | Nhiều | DPOR-based |

Trong thực tế, lazy là default cho hầu hết tool BMC concurrency hiện đại.

## Schedule recording trong thực tế

**Chess** (Microsoft): schedule recording với chronological backtracking. Verify Windows driver.

**Iterative Context Bounding (ICB)**: variant của Chess, iteratively tăng $K$ và record schedule đã thử.

**JPF** (Java Pathfinder): dynamic schedule exploration cho Java bytecode.

**SPIN**: model checker classic, có optimization partial order reduction tích hợp.

## Tóm tắt

- **Lazy interleaving**: chỉ fork tại shared memory access, không local. Giảm số nhánh đáng kể.
- **Schedule recording**: tránh khám phá lại schedule equivalent. Implement bằng Mazurkiewicz trace + vector clock.
- **DPOR**: combine cả hai, optimal về số schedule khám phá.
- **Tool thực tế**: Chess, JPF, SPIN, rcmc. Hầu hết tool BMC modern đều có DPOR.

## Mini-quiz

<details>
<summary>Q1. Vì sao lazy interleaving an toàn (không miss bug)?</summary>

Lazy không fork tại local access vì local access **không tương tác** với thread khác. Bất kể thread khác chạy lúc nào, local access cho cùng kết quả.

Hình thức: nếu instruction $i$ của T1 và instruction $j$ của T2 cùng là local (không cùng biến shared), chúng **giao hoán**. Schedule "T1.i -> T2.j" và "T2.j -> T1.i" cho cùng state cuối.

Vì giao hoán, chỉ khám phá 1 thứ tự đủ. Lazy implicitly áp dụng partial order reduction cho local instruction.

Bug concurrency luôn liên quan tới ít nhất 2 thread cùng truy cập một shared variable. Lazy fork tại đó, không miss bug nào.
</details>

<details>
<summary>Q2. Vector clock là gì? Cho ví dụ với 3 thread.</summary>

Vector clock: mảng counter có size = số thread. Mỗi thread tăng counter của mình khi thực hiện một event.

Ví dụ với 3 thread:

```
Initial: T1=[0,0,0], T2=[0,0,0], T3=[0,0,0]

T1 event A: T1=[1,0,0]
T2 event B: T2=[0,1,0]
T1 sends message to T3 (vector [1,0,0]):
  T3 receives, merges: T3=[max(0,1), max(0,0), 0+1] = [1,0,1]
T3 event C: T3=[1,0,2]
```

Happens-before relation:
- Event A có clock [1,0,0]. Event C có clock [1,0,2]. Component-wise A ≤ C, nên A → C.
- Event B có clock [0,1,0]. Event C có clock [1,0,2]. Không có A ≤ B (vì A[0]=1 > B[0]=0 sai, nhưng B[1]=1 > C[1]=0). Không component-wise nhỏ hơn, nên B ∥ C (concurrent).

Sử dụng: nếu B ∥ C, swap thứ tự B và C cho cùng kết quả. Schedule recording dùng để gộp các trace tương đương.
</details>

<details>
<summary>Q3. DPOR tại sao gọi là "optimal"?</summary>

DPOR khám phá **chính xác** một schedule cho mỗi Mazurkiewicz equivalence class. Số class này là lower bound của số schedule mà bất kỳ thuật toán correct nào phải khám phá (vì nếu skip class, có thể miss bug trong class đó).

Vì DPOR khám phá đúng số tối thiểu, gọi là optimal.

Định lý formal: Flanagan & Godefroid (POPL 2005) chứng minh DPOR là optimal trong nghĩa "không có thuật toán correct nào khám phá ít schedule hơn".

Tuy nhiên optimal về số schedule không có nghĩa là nhanh nhất về wall-clock time. Có nhiều variant (Source-DPOR, Optimal-DPOR, TruPR) với trade-off khác nhau giữa số schedule và overhead computation.
</details>

---

**Tiếp theo**: [4.7 Sequentialization (KISS, LR)](./07-sequentialization-kiss-lr)
