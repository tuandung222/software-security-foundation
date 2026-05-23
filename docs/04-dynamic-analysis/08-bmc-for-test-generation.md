---
id: 08-bmc-for-test-generation
title: 5.8 BMC for test generation
sidebar_position: 8
description: "Dùng BMC theo cách 'ngược': thay vì chứng minh property holds, dùng để sinh test case đạt coverage cao. Encode goal thành assertion ngược, counterexample là test."
---

# 5.8 BMC for test generation: cầu nối ngược về static

> **Tóm tắt một dòng**: BMC được thiết kế để chứng minh property holds. Nhưng nó cũng có thể được dùng **ngược** để sinh test case: encode goal coverage (ví dụ "đến được dòng X") thành assertion ngược ("không bao giờ đến X"), BMC trả counterexample (input đến X), counterexample chính là test case. Đây là cầu nối thanh lịch giữa Lec 3-4 (static) và Lec 5 (dynamic).

## Vì sao đây là bài cuối Lec 5?

Khi bắt đầu Lec 5, ta phân biệt static (Lec 3-4) và dynamic (Lec 5) như hai họ kỹ thuật khác nhau:
- Static: chứng minh không bug.
- Dynamic: tìm bug bằng chạy code.

Bài này show rằng phân biệt đó **không hoàn toàn rigid**. BMC, vốn là tool static, có thể được dùng để sinh input concrete, từ đó hỗ trợ dynamic testing. Đây là "elegant unification" giữa hai họ.

Bài này dạy:

1. Cách encode goal coverage thành assertion ngược.
2. Quy trình sinh test case từ counterexample.
3. Program instrumentation để track coverage trong BMC.
4. Ưu nhược so với fuzzing thuần.

## Ý tưởng cơ bản

BMC trả lời câu hỏi: "có input vi phạm assertion không?". Nếu vi phạm, trả counterexample (input cụ thể).

Đảo bài toán: muốn tìm input đi tới dòng X, viết assertion "không đi tới X". BMC nói "có thể đi tới X" (counterexample), chính là input ta muốn.

Code minh hoạ:

```c
int classify(int x) {
    if (x < 0) return -1;       // line A
    else if (x == 0) return 0;  // line B
    else if (x < 100) return 1; // line C
    else return 2;              // line D
}
```

Muốn sinh test case đạt **statement coverage 100%**: cần test reach A, B, C, D.

### Goal 1: reach A (`x < 0`)

Instrument code:

```c
int classify(int x) {
    if (x < 0) {
        // GOAL 1 REACHED
        __CPROVER_assert(0, "goal_A");   // assertion luôn false
        return -1;
    }
    // ...
}
```

`__CPROVER_assert(0, "goal_A")` luôn fail nếu đến đó. BMC tìm input làm assertion fail → counterexample là input dẫn tới A.

Solver trả: `x = -1` (hoặc số âm khác). Đây là test case 1.

### Goal 2: reach B (`x == 0`)

Instrument tương tự ở line B. Solver trả: `x = 0`.

### Goal 3: reach C (`x < 100` nhưng `x != 0` và `x >= 0`)

Solver trả: `x = 50`.

### Goal 4: reach D (`x >= 100`)

Solver trả: `x = 100`.

Cuối: test suite `{-1, 0, 50, 100}` đạt statement coverage 100%.

## Quy trình hình thức

Cho chương trình $P$ và tập goal $G = \{g_1, g_2, \ldots, g_n\}$:

```
test_suite = []
for goal in G:
    P_instr = instrument(P, goal)   # thêm assert(0) tại goal
    result = BMC(P_instr)
    if result == SAT:
        input = extract_input(result)
        test_suite.append((input, goal))
    else:
        unreachable.append(goal)
return test_suite, unreachable
```

Output:
- **test_suite**: list (input, goal) tuples. Input đi tới goal.
- **unreachable**: list goal mà BMC chứng minh không reach được. Đây là **dead code** (statement không thể chạy).

Quy trình này:
1. **Tự động**: không cần human chọn input.
2. **Sound** trong bound: nếu goal reach được trong $k$ steps, BMC tìm được.
3. **Cho ra dead code analysis miễn phí**: unreachable goal là dead code.

## Program instrumentation

Chi tiết hơn về cách instrument code cho từng loại coverage criteria.

### Statement coverage

Thêm assert(0) tại mỗi statement:

```c
// Original
x = x + 1;

// Instrumented
__CPROVER_assert(0, "statement_5");  // line 5
x = x + 1;
```

Run BMC. Mỗi assertion fail tương ứng 1 test case đi tới line 5.

### Branch coverage

Tại mỗi if/else, thêm assert ở cả 2 nhánh:

```c
// Original
if (cond) { body_true; } else { body_false; }

// Instrumented
if (cond) {
    __CPROVER_assert(0, "branch_T_5");
    body_true;
} else {
    __CPROVER_assert(0, "branch_F_5");
    body_false;
}
```

Mỗi branch ID có 1 test case riêng.

### MC/DC

Phức tạp hơn. Cần track combination của sub-condition values. Có thể implement bằng **counter variable**:

```c
// Original
if (a > 0 && b > 0) { ... }

// Instrumented
bool a_pos = (a > 0);
bool b_pos = (b > 0);
__CPROVER_assert(!(a_pos == 1 && b_pos == 1), "mcdc_TT");
__CPROVER_assert(!(a_pos == 1 && b_pos == 0), "mcdc_TF");
__CPROVER_assert(!(a_pos == 0 && b_pos == 1), "mcdc_FT");
__CPROVER_assert(!(a_pos == 0 && b_pos == 0), "mcdc_FF");
if (a_pos && b_pos) { ... }
```

Solve riêng cho mỗi assert. Test cases cover MC/DC.

## So sánh với fuzzing

BMC for test generation và fuzzing đều sinh test case tự động. So sánh:

| Tiêu chí | BMC for test gen | Fuzzing |
|---|---|---|
| Coverage guarantee | Sound (đảm bảo reach nếu khả thi) | Best-effort (có thể miss) |
| Scale | Limited (BMC chậm cho code lớn) | Tốt (AFL chạy hàng nghìn test/giây) |
| Bug detection | Cần explicit assertion | Implicit (crash, sanitizer) |
| External code | Cần model | Chạy as-is |
| Cost | Solver expensive | Solver-free |

**Best of both**:

- Dùng BMC for test gen để **bootstrap corpus** cho fuzzer. BMC sinh input đi tới các deep branch khó hit bằng random.
- Sau đó fuzzer (AFL) chạy lâu với corpus đó, tìm bug runtime (memory corruption, ...).

Đây là pattern Driller (bài 5.7) generalize.

## Goal coverage cho complex code

Ví dụ phức tạp hơn:

```c
int validate(char *input, int len) {
    if (len < 8) return -1;
    if (input[0] != 'X') return -2;
    if (input[1] != 'Y') return -2;
    int checksum = 0;
    for (int i = 2; i < len; i++) checksum += input[i];
    if (checksum != 42) return -3;
    return 0;
}
```

Muốn test case reach `return 0`. Đây là goal khó cho fuzzer (cần `XY` ở đầu + checksum đúng).

BMC encode:
- `len >= 8`
- `input[0] == 'X'`
- `input[1] == 'Y'`
- `sum(input[2..len]) == 42`

Solver trả: `len = 8, input = "XY......"` với `input[2..7]` cộng = 42. Ví dụ `input = "XY*\x00\x00\x00\x00\x00"` (vì `'*'` = 42).

Test case generated. Fuzzer cần triệu iteration; BMC giải trong giây.

## Path coverage

Ngoài statement/branch, BMC còn sinh test case cho **path coverage** (mọi path qua chương trình).

Số path có thể mũ (mỗi if nhân 2). Với loop, vô hạn. BMC bound số path khám phá bằng cách unwind loop.

Sinh test cho path coverage:
1. Enumerate path tree tới depth $k$.
2. Mỗi path $p$: convert thành path constraint $\phi_p$ (sequence of branch conditions).
3. Solve $\phi_p$: input concrete cho path $p$.
4. Repeat.

Tool: **PathCrawler** (CEA, France) dùng BMC cho path coverage. CBMC có flag `--cover paths`.

## Ứng dụng thực tế

**EvoSuite** (University of Sheffield): test generation cho Java. Hybrid BMC + genetic algorithm. Sinh JUnit test cho mọi method, mục tiêu coverage cao.

**Pex** (Microsoft Research, deprecated): white-box test gen cho .NET. SAGE technology applied to test generation.

**KLEE** + harness: KLEE thiết kế chính cho exploration, nhưng có thể adapt cho test gen.

**CBMC** với `--cover` flag: native support cho coverage-driven test gen.

**KLEE** + `--write-test`: output test case khi gặp branch mới.

Trong industry, BMC test gen thường dùng để bootstrap initial test suite, sau đó developer review và augment manually.

## Hạn chế

**Scale**: BMC chậm cho code > vài nghìn LOC. Mỗi assertion là 1 query SMT, costs add up.

**External**: BMC cần model libc, syscall. Code có heavy IO khó test gen.

**Path explosion**: nếu cần path coverage (không chỉ statement), số path mũ.

**Equality with fuzzing**: cho code có nhiều UB-like bug (out-of-bounds, use after free), fuzzer + sanitizer thường tốt hơn vì detect được mà không cần explicit assertion.

## Tóm tắt

- BMC for test generation: dùng BMC **ngược**, sinh input đến goal.
- Encode goal là assertion ngược (`assert(0)` tại goal).
- BMC counterexample là test case.
- Hỗ trợ statement, branch, MC/DC, path coverage.
- Cho dead code analysis miễn phí (unreachable goal).
- Tool: CBMC, KLEE, EvoSuite, Pex.
- Best combine với fuzzing: BMC bootstrap corpus, AFL khai thác.

## Mini-quiz

<details>
<summary>Q1. Vì sao gọi là "BMC ngược"? Differences với BMC for verification?</summary>

**BMC for verification** (chuẩn, đã thấy trong Lec 3): user viết assertion `assert(property)` để check. BMC thêm `assume(not property)` để tìm counterexample. Mục tiêu: chứng minh không có counterexample (property holds).

**BMC for test generation** (bài này): user định nghĩa goal (line cần reach, branch cần cover). BMC thêm `assert(0)` tại goal. Mục tiêu: tìm input dẫn tới goal (=counterexample của `assert(0)`).

Tại sao "ngược": BMC verification mong UNSAT (proof). BMC test gen mong SAT (counterexample/input).

Cùng tool, cùng technique, hai mục tiêu trái ngược. Đây là tính linh hoạt của BMC.
</details>

<details>
<summary>Q2. Cho code:</summary>

```c
int f(int x, int y) {
    if (x > 100) {
        if (y < x) {
            return x - y;  // line A
        }
    }
    return 0;
}
```

Sinh test case đến line A bằng BMC test gen. Input là gì?

Encode goal: `assert(0)` tại line A.

Path constraint để đến A:
- `x > 100`
- `y < x`

BMC + SMT solve:
- $x > 100$
- $y < x$

Solver trả minimal: $x = 101, y = 0$ (hoặc bất kỳ tổ hợp thoả).

Test case: `f(101, 0)` reach line A. Verify: `101 > 100` true, `0 < 101` true, vào A. Return `101 - 0 = 101`.

Test này cover branch A. Combined với test cho branch không đến A (ví dụ `f(0, 0)`), đạt branch coverage 100%.
</details>

<details>
<summary>Q3. Khi nào BMC test gen tốt hơn fuzzing, khi nào tệ hơn?</summary>

**BMC tốt hơn khi**:
- Code có "hard constraint" (magic check, checksum) mà random gần như không hit.
- Goal coverage là statement/branch/path specific.
- Cần test case minimal (input nhỏ nhất).
- Cần dead code analysis (BMC tự động phát hiện unreachable).

**Fuzzing tốt hơn khi**:
- Code lớn (hàng vạn LOC), BMC không scale.
- Bug là runtime (memory corruption, race), fuzzer + sanitizer detect tự nhiên.
- Cần chạy continuously (24/7 trong CI), fuzz scale tốt.
- Code có heavy IO/external call, BMC khó model.

**Best practice**: combine. BMC sinh seed corpus cho fuzzer (giúp fuzzer pass "wall" như MAGIC), fuzzer chạy lâu với corpus đó tìm bug runtime. Đây chính là Driller pattern (bài 5.7).

Trong industry: Google ClusterFuzz dùng fuzzer chính, plus seed corpus từ symbolic exec. Microsoft SAGE dùng cả hai. Modern fuzzing không là "AFL alone", là một orchestration of multiple techniques.
</details>

:::tip[DS perspective]
BMC-for-test-gen tương tự **active learning với query strategy "maximum disagreement"** - chọn input mà model uncertain nhất (high entropy). Ở đây "uncertain" = chưa cover branch. **CEGAR loop** (counterexample-guided abstraction refinement) ≈ **iterative active learning loop**: query input mới khi gặp gap. Combine BMC + fuzzing (Driller) ≈ **hybrid sampling strategy**: solver giải "hard constraint" (analog của ill-conditioned region), fuzzer cover "easy region" nhanh. Cùng triết lý: smart probe cho hard case, brute force cho easy case.
:::

---

**Kết thúc Phần 4 (Lecture 5).** Bạn đã hoàn thành toàn bộ chương trình kỹ thuật! Từ khái niệm cơ bản Software Security (Phần 1), tới BMC + SMT cho sequential (Phần 2), concurrency (Phần 3), dynamic analysis với fuzzing (Phần 4). Để thấy các kỹ thuật này áp dụng vào tư vấn dự án thực tế, đọc tiếp [Phần 5: Case Studies](../05-case-study/01-overview).
