---
id: 05-context-bounded-analysis
title: 4.5 Context-bounded analysis (CBA)
sidebar_position: 5
description: Đột phá của Qadeer-Rehof về verify chương trình đa luồng. Giới hạn số context switch, transformation thuật toán mũ thành đa thức, ứng dụng thực tế.
---

# 4.5 Context-Bounded Analysis: đột phá của concurrency verification

> **Tóm tắt một dòng**: Quan sát thực nghiệm: hầu hết bug concurrency thực tế chỉ cần **vài context switch** để lộ. Thay vì khám phá mọi schedule (mũ), giới hạn context switch xuống $K$ nhỏ và chỉ khám phá schedule trong giới hạn đó. Số schedule giảm từ mũ xuống đa thức.

## Khám phá thực nghiệm: bug chỉ cần vài context switch

Năm 2005, Qadeer và Rehof công bố một observation đột phá: **hầu hết bug concurrency trong code thực tế lộ ra với ít hơn 2-3 context switch**.

Họ phân tích các bug đã được report trong code Microsoft, Linux kernel, và các thư viện lớn. Kết quả: 95% bug có thể tái tạo với chỉ 2 context switch giữa các thread. Bug cần > 5 context switch cực kỳ hiếm.

Trực giác đằng sau observation này: programmer khi viết code đa luồng đã (vô tình hoặc cố ý) "đồng bộ" code đủ tốt để bug "đơn giản" (cần ít context switch) được loại. Bug còn lại thường liên quan tới việc bỏ sót một sync ở chỗ ít ngờ tới, lộ ra ngay khi có một schedule "xấu". Schedule "xấu" này không cần phức tạp.

Observation này dẫn tới ý tưởng: **giới hạn số context switch khi verify**.

## Context switch là gì?

**Context switch** là khi scheduler dừng một thread và bắt đầu (hoặc tiếp tục) một thread khác. Tại một context switch, "context" (program counter, register, stack) của thread cũ được lưu và của thread mới được khôi phục.

Ví dụ schedule:

```
Thread 1: [instr_1] [instr_2] | Thread 2: [instr_a] [instr_b] | Thread 1: [instr_3] | Thread 2: [instr_c]
```

Có **3 context switch** trong schedule này: từ T1 sang T2, từ T2 sang T1, từ T1 sang T2.

## Context-Bounded Analysis (CBA)

**CBA**: cho hằng $K$, chỉ khám phá các schedule có $\leq K$ context switch.

Định lý của Qadeer-Rehof: nếu chương trình có bug lộ ra với $\leq K$ context switch, CBA tìm được. Nếu CBA không tìm được, **có thể** không có bug, hoặc bug cần nhiều context switch hơn.

CBA là **không sound** (có thể miss bug cần $> K$ context switch), nhưng theo observation, $K = 2$ hoặc $3$ đã đủ tìm hầu hết bug thực tế.

## Số schedule với $K$ context switch

Với $n$ thread, mỗi thread $m$ instruction, $K$ context switch:

- Số "đoạn" (segments) trong schedule: $K + 1$.
- Mỗi đoạn thuộc về 1 thread, độ dài variable.
- Số schedule: đa thức theo $m$, mũ theo $K$ (nhưng $K$ nhỏ và cố định).

Cụ thể: $O(m^K \cdot n^K)$ schedule với $K$ cố định.

So sánh với enumerate đầy đủ:

| Thông số | Full enumeration | CBA với $K = 2$ |
|---|---|---|
| 2 thread, 10 inst | $\binom{20}{10} \approx 184K$ | $\binom{2}{2} \cdot 10^2 = 100$ |
| 4 thread, 100 inst | $\approx 10^{198}$ | $\approx 4^2 \cdot 100^2 = 160K$ |

Sự giảm là khổng lồ. Từ "bất khả" xuống "tractable trong vài giây".

## Cách hiện thực CBA

Có nhiều cách implement CBA. Hai cách phổ biến:

### Cách 1: Sequentialization với round-robin

Dịch chương trình multi-threaded thành sequential program có $K$ "round". Mỗi round, thread chạy hết một "phase" (đoạn liên tục), rồi context switch.

Pseudo-implementation:

```
for round in 0..K:
    chọn thread thr nondet
    chạy thr từ checkpoint cuối cho tới một điểm context switch nondet
    lưu checkpoint
```

Sequential program kết quả có thể verify bằng tool BMC thông thường (CBMC).

Bài 4.7 đi sâu vào sequentialization KISS và LR.

### Cách 2: Direct encoding

Encode trực tiếp vào SMT formula các "transition" của mỗi thread, kèm context switch counter. Constraint: counter $\leq K$.

Tool: CBMC với `--unwind K`, ESBMC.

## Ví dụ: chứng minh data race lộ trong 1 context switch

```c
int x = 0;
int y = 0;

void* t1(void *arg) {
    if (x == 1)
        y = 1;
}

void* t2(void *arg) {
    if (y == 1)
        x = 1;
}

int main() {
    pthread_t a, b;
    pthread_create(&a, NULL, t1, NULL);
    pthread_create(&b, NULL, t2, NULL);
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    assert(x == 0 || y == 0);   // ít nhất một biến vẫn là 0
}
```

Verify assertion. Trực giác: ta khởi tạo cả $x = 0, y = 0$. Để $x = 1$, cần $y = 1$ trước (vì T2 chỉ set $x = 1$ khi $y = 1$). Để $y = 1$, cần $x = 1$ trước. Vòng tròn, không cách nào cả hai biến cùng = 1.

Nhưng có bug tinh tế: TSO memory model cho phép store-load reordering. Trên x86, code biên dịch ra ASM có thể bị CPU reorder. Nếu T1 reorder thành "load x, store y" thành "store y, load x", T1 set $y = 1$ rồi check $x$ sau. Tương tự T2. Có thể đạt cả $x = y = 1$.

CBA với $K = 0$ (mọi thread chạy hoàn chỉnh, không switch giữa chừng): không bug. T1 chạy hết, T2 chạy hết, hoặc ngược lại. Cả hai case đều giữ ít nhất 1 biến = 0.

CBA với $K = 1$ (1 context switch): có thể switch giữa "check" và "set" của T1, cho phép T2 chạy. Tool tìm schedule:
1. T1 check `x == 1`: false, không set `y`.
2. Context switch sang T2.
3. T2 check `y == 1`: false, không set `x`.

Vẫn không có bug. Vì với SC memory model, dù schedule thế nào, assertion vẫn pass.

CBA + TSO memory model: có thể model reordering. Lúc đó tool tìm được bug.

Bài học: CBA + memory model đúng cho phép phát hiện bug tinh tế của weak memory.

## Ứng dụng CBA: tools thực tế

**Chess** (Microsoft Research, 2007): tool đầu tiên dùng CBA scale lớn. Verify Windows kernel module, tìm hàng chục bug data race chưa được phát hiện. Code-base: triệu dòng C.

**CBMC concurrency mode**: CBMC hỗ trợ pthread, có flag `--unwind K` cho context-bound. Limit: mặc định model SC, không weak memory.

**ESBMC**: hỗ trợ pthread, OpenMP, có model TSO, RMO, SC. Flag `--context-switch` cho CBA.

**Inspect** (Yang, 2007): dynamic CBA, exploration trong testing framework. Tìm bug trong Apache HTTPD, Mozilla Firefox.

**Concuerror** (Erlang): dynamic CBA cho code Erlang/Elixir.

## Trade-off của CBA

**Ưu điểm**:
- Scale tới chương trình lớn (triệu dòng) với $K$ nhỏ.
- Trong thực tế tìm hầu hết bug.
- Dễ implement: sequentialization hoặc direct encoding.

**Nhược điểm**:
- **Không sound**: miss bug cần $> K$ context switch (hiếm nhưng có thể).
- $K$ phải user chọn: chọn quá nhỏ miss bug, quá lớn slow.
- Một số bug "deep" cần > 5 switch, CBA không tìm được trong reasonable time.

Trong thực tế, $K = 2$ là sweet spot cho hầu hết bug. Cho dependability-critical code, có thể tăng lên 5-10.

## Mối quan hệ với Partial-Order Reduction (POR)

CBA và POR là hai kỹ thuật **khác nhau** nhưng đều giảm số schedule cần khám phá.

**POR**: dựa trên observation rằng nếu hai instruction từ hai thread "độc lập" (không cùng biến, không cùng lock), giao hoán cho cùng kết quả. Chỉ cần khám phá 1 thứ tự.

**CBA**: giới hạn số context switch trong schedule.

Có thể **kết hợp** CBA + POR: giới hạn context switch, **và** trong các context switch khả dĩ, gộp các schedule tương đương theo POR.

Tool modern (ESBMC, CBMC, Maude-NPA) thường dùng cả hai.

## Tóm tắt

- **Observation Qadeer-Rehof**: 95% bug concurrency lộ với $\leq 2-3$ context switch.
- **CBA**: giới hạn schedule khám phá theo số context switch $K$.
- Số schedule giảm từ mũ ($O(m!^n)$) xuống đa thức ($O(m^K n^K)$) với $K$ cố định.
- Hiện thực: **sequentialization** hoặc **direct encoding** trong SMT.
- Không sound (miss bug $> K$ switch), nhưng thực dụng cho hầu hết tool BMC.
- Kết hợp với POR cho hiệu quả tối đa.

## Mini-quiz

<details>
<summary>Q1. Vì sao CBA "không sound"? Cho ví dụ một bug CBA $K=2$ sẽ miss.</summary>

CBA chỉ khám phá schedule có $\leq K$ context switch. Bug cần $> K$ context switch sẽ bị bỏ qua.

Ví dụ một bug cần $K \geq 5$:

```c
int counter = 0;
mutex m;

void* threadA() {
    lock(m);
    int x = counter;
    int y = counter + 1;
    int z = counter + 2;
    counter = x + y + z;   // sai, nhưng cần A đọc, B ghi, A ghi
    unlock(m);
}

void* threadB() { /* simiar */ }
```

Một bug "deep" cần B chen vào giữa 3 read của A và lúc A write. Nhưng A trong mutex, B không thể chen vào. CBA bất kể $K$ không tìm được vì bug không có ở SC.

Một bug **thật sự cần $K > 2$**: race khi 3 thread cùng update một queue, schedule cần $T_1 \to T_2 \to T_3 \to T_1 \to T_2$ (5 segment = 4 context switch). CBA với $K = 2$ miss.

Trong thực tế hiếm, nhưng tồn tại. Tài liệu Qadeer-Rehof có dataset benchmark cho các bug "deep" này.
</details>

<details>
<summary>Q2. Tại sao quan sát "95% bug lộ với $\leq 2-3$ context switch" lại đúng trong thực tế?</summary>

Có nhiều giả thuyết:

**Giả thuyết 1**: Programmer đã (tay) đồng bộ code đủ tốt để các "schedule dễ" (ít context switch) không lộ bug. Bug còn lại thường là **bỏ sót một sync** ở một chỗ nhỏ. Một schedule "tấn công" chỗ đó chỉ cần switch ngay tại điểm bỏ sót.

**Giả thuyết 2**: Bug concurrency thường liên quan **một cặp instruction** từ hai thread không sync. Để lộ, chỉ cần thread A chạy một instruction, switch sang B, B chạy instruction xung đột. Đó là 1 context switch.

**Giả thuyết 3**: Programmer test code đa luồng, dù ít, cũng tự nhiên ép một số schedule. Bug cần schedule rất đặc biệt ($> 5$ switch) chưa được test ra nhưng có thể chạy đúng trong production nếu OS không tạo schedule đó.

Tổng kết: observation chỉ là statistical, có exception, nhưng đủ mạnh để justify $K = 2-3$ làm default cho CBA.
</details>

<details>
<summary>Q3. So sánh CBA và Partial-Order Reduction. Có cần dùng cả hai cùng lúc không?</summary>

**CBA**: giới hạn theo **độ dài schedule** (số context switch).

**POR**: giới hạn theo **tính độc lập** (instruction giao hoán chỉ cần khám phá 1 thứ tự).

Hai kỹ thuật **orthogonal**: CBA giảm số schedule (theo chiều ngoài), POR gộp các schedule tương đương (theo chiều trong).

Kết hợp: CBA cho ra danh sách schedule có $\leq K$ switch. POR gộp các schedule trong danh sách đó nếu equivalent.

Ví dụ với $K = 2$, có thể có 1000 schedule cần khám phá. POR phát hiện nhiều cặp tương đương, gộp lại còn 200 schedule "thực sự khác nhau". Tăng tốc 5x.

Tool ESBMC, Chess đều dùng cả hai. Pattern này là best practice cho concurrency verification.
</details>

---

**Tiếp theo**: [4.6 Lazy exploration vs schedule recording](./06-lazy-vs-schedule-recording)
