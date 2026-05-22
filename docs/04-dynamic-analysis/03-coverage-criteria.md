---
id: 03-coverage-criteria
title: 5.3 Coverage criteria
sidebar_position: 3
description: "Bốn cấp coverage criteria từ yếu tới mạnh (statement, decision, condition, MC/DC), ví dụ minh hoạ, vì sao MC/DC là chuẩn cho avionics."
---

# 5.3 Coverage criteria: đo "test đã đủ chưa?"

> **Tóm tắt một dòng**: Coverage criteria là tiêu chuẩn đo mức độ "phủ" của test suite trên code. Bốn cấp từ yếu tới mạnh: **Statement** (mỗi dòng), **Decision** (mỗi nhánh if), **Condition** (mỗi sub-condition), **MC/DC** (Modified Condition/Decision). MC/DC là chuẩn bắt buộc trong avionics (DO-178C) vì balance giữa rigor và practicality.

## Vấn đề: khi nào test "đủ"?

Một câu hỏi rất thực tế của project manager: "test bao nhiêu là đủ?". Đáp án naive: "khi nào không còn bug". Nhưng làm sao biết không còn bug?

Trả lời thực dụng: dùng **coverage criteria**. Coverage đo mức độ "đụng tới" code của test. Coverage cao đảm bảo code đã được chạm, ít bug ẩn. Coverage thấp đảm bảo có chỗ chưa test, có thể có bug ẩn.

Quan trọng: **coverage cao không đảm bảo không bug**. Test có thể chạm code nhưng không trigger bug edge case. Tuy nhiên coverage thấp **đảm bảo** test chưa đủ. Đây là điều kiện cần, không phải đủ.

## Bốn cấp coverage criteria

Hãy đi từ yếu tới mạnh.

### 1. Statement coverage

**Định nghĩa**: mỗi statement (dòng code thực thi) phải được chạy ít nhất 1 lần bởi test suite.

Ví dụ:

```c
void abs(int x) {
    if (x < 0)
        x = -x;
    printf("%d\n", x);
}
```

Để cover mọi statement:
- Statement `if (x < 0)`: bất kỳ test nào cũng chạy.
- Statement `x = -x`: cần test với `x < 0`.
- Statement `printf`: bất kỳ test nào.

Test suite `{x = -5}` cover hết. Statement coverage = 100%.

Nhưng test này không kiểm tra branch `x >= 0`. Bug có thể ẩn ở đó.

### 2. Decision coverage (branch coverage)

**Định nghĩa**: mỗi nhánh của if/else, switch case, while/for condition phải được chọn cả true và false ít nhất 1 lần.

Ví dụ tương tự, để decision cover:
- `if (x < 0)` phải có test với `x < 0` (true) và `x >= 0` (false).

Test suite `{x = -5, x = 5}` cover decision. Decision coverage = 100%.

Decision **mạnh hơn** statement: branch false cũng được test.

### 3. Condition coverage

**Định nghĩa**: trong compound condition (có `&&`, `||`), mỗi sub-condition phải được true và false ít nhất 1 lần.

Ví dụ:

```c
if (a > 0 && b > 0) {
    do_something();
}
```

Để condition cover:
- `a > 0` phải có test true và test false.
- `b > 0` phải có test true và test false.

Test suite:
- `{a = 1, b = 1}`: `a > 0` = true, `b > 0` = true.
- `{a = -1, b = -1}`: `a > 0` = false, `b > 0` = false.

Cover hết. Nhưng chú ý: `a > 0` true với `a = 1`, false với `a = -1`. Tương tự `b`.

Condition coverage **không** đảm bảo decision coverage trong mọi case. Ví dụ trên cover condition nhưng decision chỉ false (cả 2 test đều cho overall expression false, vì `a = 1 && b = 1` true thực ra... wait, đó là true). Let me re-check.

`{a = 1, b = 1}`: `(a > 0) && (b > 0)` = true && true = true.
`{a = -1, b = -1}`: false && false = false.

Decision: true và false đều có. Decision cover.

Ví dụ tinh tế hơn:

```c
if (a > 0 || b > 0) {
    do_something();
}
```

Test suite `{a = 1, b = -1}` (true || false = true) và `{a = -1, b = 1}` (false || true = true).

- `a > 0`: true (test 1), false (test 2). Cover.
- `b > 0`: false (test 1), true (test 2). Cover.

Condition cover. Nhưng decision chỉ true cả 2 lần. Decision không cover false.

Đây là điểm tinh tế: condition coverage **không strictly mạnh hơn** decision coverage.

### 4. Modified Condition/Decision Coverage (MC/DC)

**Định nghĩa**: với mỗi sub-condition, phải có cặp test sao cho:
- Hai test giống nhau ở mọi sub-condition khác.
- Hai test khác nhau ở sub-condition đang xét.
- Decision tổng cũng khác nhau.

Nói cách khác, mỗi sub-condition phải **độc lập ảnh hưởng** outcome.

Ví dụ:

```c
if (a > 0 && b > 0) {
    do_something();
}
```

Để MC/DC cover:
- Sub-condition `a > 0`:
  - Cặp test (`{a=1, b=1}`, `{a=-1, b=1}`): a thay đổi, b giữ. Outcome: true → false. OK.
- Sub-condition `b > 0`:
  - Cặp test (`{a=1, b=1}`, `{a=1, b=-1}`): b thay đổi, a giữ. Outcome: true → false. OK.

Cần ít nhất 3 test: `{a=1,b=1}, {a=-1,b=1}, {a=1,b=-1}`. (Có thể cần 4 cho compound phức tạp.)

**Tính chất quan trọng**: với $n$ sub-condition, MC/DC cần $n + 1$ test thay vì $2^n$ (full coverage). Tăng tuyến tính, tractable.

## Bảng so sánh

| Criterion | Số test (compound 4 sub-conditions) | Rigor | Speed |
|---|---|---|---|
| Statement | ~1 | Yếu | Nhanh |
| Decision | 2 | Trung bình | Nhanh |
| Condition | $\leq 8$ (mỗi sub × 2) | Trung bình | Nhanh |
| MC/DC | $\leq 5$ ($n + 1$) | Mạnh | Trung bình |
| Multiple Condition (full) | $2^4 = 16$ | Rất mạnh | Chậm, không scale |

**MC/DC là sweet spot**: gần "full coverage" về rigor nhưng số test tuyến tính, scale được.

## Ví dụ MC/DC chi tiết

Decision: `(A && B) || C`.

Mỗi sub-condition (A, B, C) phải độc lập ảnh hưởng outcome. Bảng truth:

| Test | A | B | C | (A && B) | (A && B) || C |
|---|---|---|---|---|---|
| T1 | T | T | T | T | T |
| T2 | T | T | F | T | T |
| T3 | T | F | T | F | T |
| T4 | T | F | F | F | F |
| T5 | F | T | T | F | T |
| T6 | F | T | F | F | F |
| T7 | F | F | T | F | T |
| T8 | F | F | F | F | F |

Để chứng minh A ảnh hưởng outcome:
- Cần cặp test có A khác nhau, B và C giữ, outcome khác.
- T2 (T,T,F) vs T6 (F,T,F): A khác, B=T, C=F giữ. Outcome T vs F. **OK**.

Để chứng minh B ảnh hưởng outcome:
- Cần cặp test có B khác, A và C giữ, outcome khác.
- T2 (T,T,F) vs T4 (T,F,F): B khác, A=T, C=F giữ. Outcome T vs F. **OK**.

Để chứng minh C ảnh hưởng outcome:
- Cần cặp test có C khác, A và B giữ, outcome khác.
- T4 (T,F,F) vs T3 (T,F,T): C khác, A=T, B=F giữ. Outcome F vs T. **OK**.

Cần ít nhất các test: T2, T3, T4, T6. Bốn test cho 3 sub-condition. MC/DC = $n + 1$ trong trường hợp tốt.

## MC/DC là chuẩn cho avionics

**DO-178C** (chuẩn cho phần mềm avionics) yêu cầu MC/DC cho Level A software (catastrophic failure consequences). Các project thực tế:

- Phần mềm điều khiển bay Boeing 787, Airbus A380.
- Hệ thống fly-by-wire F-22.
- ATM, autopilot.

Vì sao MC/DC được chọn?
- **Soundness**: nếu MC/DC pass, có rất ít chance miss bug logic.
- **Scalability**: tuyến tính theo $n$, tractable cho code lớn.
- **Auditability**: dễ kiểm tra "test này có đạt MC/DC không?", quan trọng cho certification.

ISO 26262 (automotive) và IEC 61508 (industrial control) cũng tham chiếu MC/DC cho safety-critical level.

## Trong thực tế: tool đo coverage

| Tool | Ngôn ngữ | Criterion hỗ trợ |
|---|---|---|
| **gcov** | C/C++ | Statement, branch, function |
| **lcov** | C/C++ | Same as gcov, frontend đẹp |
| **JaCoCo** | Java | Statement, branch, complexity |
| **coverage.py** | Python | Statement, branch |
| **Istanbul/nyc** | JS | Statement, branch, function |
| **VectorCAST** | C/C++ aviation | MC/DC, certification grade |
| **LDRA** | Multi | MC/DC, DO-178C compliant |

Hầu hết tool free hỗ trợ statement/branch. MC/DC tool thường commercial (VectorCAST, LDRA), giá hàng chục nghìn USD/seat.

## Cảnh báo: Coverage không phải mục tiêu

Có hai sai lầm phổ biến khi đo coverage:

**Sai lầm 1: "100% coverage = không bug"**. Sai. Coverage chỉ đo code đã được chạm, không đo bug đã được catch. Test "chạm code" nhưng không assert kết quả là vô dụng.

**Sai lầm 2: "Coverage thấp → team kém"**. Cũng sai. Coverage thấp có thể vì:
- Code có nhiều defensive check (xử lý case hiếm).
- Code có integration với external service khó test.
- Test viết focus integration thay vì unit.

Coverage là **một** trong nhiều metric, không phải duy nhất. Best practice: theo dõi xu hướng (coverage tăng/giảm theo thời gian), đặt threshold tối thiểu (60-80%), nhưng không obsess.

## Tóm tắt

- Coverage criteria đo mức độ phủ test trên code.
- Từ yếu tới mạnh: **Statement, Decision, Condition, MC/DC**.
- **MC/DC** đặc biệt: mỗi sub-condition độc lập ảnh hưởng outcome.
- MC/DC tuyến tính theo $n$ ($n+1$ test), scale tốt, dùng cho avionics.
- Coverage cao là điều kiện **cần** (không đủ) cho test suite tốt.

## Mini-quiz

<details>
<summary>Q1. Vì sao 100% statement coverage không đảm bảo không có bug?</summary>

Statement coverage chỉ check "code đã được chạy", không check "kết quả đúng".

Ví dụ:

```c
int divide(int a, int b) {
    return a / b;
}
```

Test `divide(10, 2)` → 5. Statement cover 100%. Pass.

Nhưng có bug: `divide(10, 0)` crash (div by zero). Test không cover edge case này.

Cần thêm:
- Boundary value test (b = 0).
- Branch coverage trên các nhánh.
- Assertion check `result * b == a`.

Coverage là điều kiện cần (test chạm code), không đủ (test phát hiện bug).
</details>

<details>
<summary>Q2. Vì sao MC/DC tốt hơn full multiple condition cho code có nhiều sub-condition?</summary>

Full multiple condition cần test mọi tổ hợp $2^n$ giá trị. Với $n = 10$, là 1024 test. Với $n = 20$, là 1 triệu test. Không scale.

MC/DC cần $n + 1$ test. Với $n = 10$, là 11 test. Với $n = 20$, là 21 test. Tractable.

MC/DC vẫn đảm bảo mỗi sub-condition **độc lập ảnh hưởng** outcome. Đây là "tinh thần" của full multiple condition (chứng minh logic của mỗi sub không thừa), đạt được với chi phí tuyến tính thay vì mũ.

Đây là lý do MC/DC được DO-178C chọn: rigor cao + scale.
</details>

<details>
<summary>Q3. Tính MC/DC test cho decision `(A || B) && C`.</summary>

Truth table:

| A | B | C | (A \|\| B) | (A \|\| B) && C |
|---|---|---|---|---|
| T | T | T | T | T |
| T | T | F | T | F |
| T | F | T | T | T |
| T | F | F | T | F |
| F | T | T | T | T |
| F | T | F | T | F |
| F | F | T | F | F |
| F | F | F | F | F |

Để A độc lập ảnh hưởng:
- B và C giữ, A thay đổi, outcome khác.
- Tìm cặp: B=F, C=T. A=T: outcome T. A=F: outcome F. Cặp T3 vs T7. **OK**.

Để B độc lập ảnh hưởng:
- A và C giữ, B thay đổi.
- A=F, C=T. B=T: outcome T. B=F: outcome F. Cặp T5 vs T7. **OK**.

Để C độc lập ảnh hưởng:
- A và B giữ, C thay đổi.
- Bất kỳ A, B làm (A || B) = T. Lấy A=T, B=F. C=T: T. C=F: F. Cặp T3 vs T4. **OK**.

Test set: T3, T4, T5, T7. **4 test** cho 3 sub-condition. Đúng $n + 1$.
</details>

---

**Tiếp theo**: [5.4 Monitoring với LTL và Büchi automata](./04-monitoring-ltl-buchi)
