---
id: 01-overview
title: 5.1 Tổng quan Lecture 5
sidebar_position: 1
description: Giới thiệu cụm Dynamic Analysis với hai họ kỹ thuật chính (monitoring và fuzzing), khi nào dùng dynamic vs static, và cầu nối ngược về BMC.
---

# Lecture 5: Dynamic Analysis (Testing, Monitoring, Fuzzing)

> **Tóm tắt một dòng**: Khi không chứng minh được "không có bug" bằng formal verification, ta chuyển sang tìm bug bằng cách **chạy chương trình**. Hai họ kỹ thuật chính: **monitoring** theo dõi property tại runtime, và **fuzzing** tự động sinh input để khám phá hành vi. Cuối cùng, hai họ này gặp nhau khi BMC được dùng **ngược** để sinh test case.

## Vì sao cần Lecture 5 sau khi đã có Lec 3-4?

Lecture 3 và 4 đã đầu tư rất nhiều vào static analysis: encode chương trình, gọi SMT solver, chứng minh property. Vậy tại sao vẫn cần dynamic?

Vài lý do thực tế:

**Thứ nhất, static analysis có giới hạn**. Định lý Rice (đã thấy ở [bài 1.5](../01-introduction/05-formal-verification-intro)) nói mọi property non-trivial về Turing-complete program đều undecidable. Mọi tool BMC phải trade-off: scope giới hạn, soundness vs completeness, scalability. Có những chương trình mà BMC timeout hoặc không scale tới.

**Thứ hai, static analysis phụ thuộc vào model**. Tool BMC encode chương trình theo một model nào đó: SC memory model, fixed-size integers, không xét external environment. Bug có thể đến từ chỗ model khác thực tế: một thư viện hệ điều hành cụ thể, một CPU bug, một interrupt timing. Dynamic chạy code thật, bắt được những thứ này.

**Thứ ba, dynamic dễ hiểu hơn**. Counterexample của BMC là một input trừu tượng, đôi khi khó hiểu. Crash report từ fuzzer kèm core dump, stack trace, có thể debug trực tiếp.

**Thứ tư, hai họ bổ sung nhau**. Một code base modern dùng BMC verify các module critical (driver, crypto), fuzzer test các thành phần lớn (parser, network protocol), monitor production để bắt bug edge case. Mỗi phần đóng vai trò riêng.

## Hai họ kỹ thuật chính của Lecture 5

### Monitoring

**Monitoring** theo dõi chương trình khi nó chạy, check property tại từng bước. Khác fuzzing ở chỗ: monitoring không sinh input, chỉ quan sát chương trình hoạt động (có thể là production traffic hoặc test).

Property cho monitoring thường là **temporal**: "luôn", "rồi sẽ", "nếu A thì rồi B". Diễn đạt bằng **LTL (Linear Temporal Logic)**. Implementation: chuyển LTL formula thành **Büchi automaton**, automaton này chạy song song với chương trình, transition theo event observed.

Tool: AspectJ (Java), DTrace (Solaris/macOS), eBPF (Linux), Splunk monitoring (production).

### Fuzzing

**Fuzzing** sinh input một cách tự động để khám phá hành vi chương trình. Mục tiêu: tìm input gây crash, hang, hoặc vi phạm assertion.

Hai loại lớn:

- **Black-box fuzzing**: không biết code internal, chỉ feed input ngẫu nhiên hoặc theo grammar. Tools: Peach, Sulley.
- **White-box fuzzing**: dùng symbolic execution để sinh input có path coverage cao. Tools: SAGE (Microsoft), KLEE.

Hybrid: **AFL** và **libFuzzer** dùng **coverage-guided mutation**: input nào khám phá branch mới được ưu tiên, mutate tiếp.

### Coverage criteria

Để đánh giá fuzzing đã "đủ" hay chưa, dùng coverage criteria:
- Statement coverage: mỗi statement chạy ít nhất 1 lần.
- Branch coverage: mỗi if/else branch được chọn ít nhất 1 lần.
- Condition coverage: mỗi sub-condition được true và false ít nhất 1 lần.
- MC/DC (Modified Condition/Decision Coverage): kết hợp condition và decision, tiêu chuẩn cho avionics (DO-178C).

### BMC for Test Generation

Cuối cùng, ta dùng BMC **ngược**: thay vì chứng minh property holds, dùng BMC sinh input đạt một goal coverage. Encode goal là một assertion ngược ("không bao giờ đến điểm X"), BMC trả counterexample (input đến X). Counterexample chính là test case.

Ý tưởng này gắn kết Lec 3-4 với Lec 5: cùng một tool BMC, dùng theo hai cách khác nhau cho hai mục tiêu khác nhau.

## Lộ trình cụm

| Bài | Chủ đề | Vì sao cần |
|---|---|---|
| 5.1 | Tổng quan (bài này) | Đặt context |
| 5.2 | Security testing | Phân biệt với functional testing |
| 5.3 | Coverage criteria | Đo "test đủ chưa", chuẩn industry |
| 5.4 | Monitoring với LTL + Büchi | Theo dõi property tại runtime |
| 5.5 | Fuzzing basics | Random testing và giới hạn |
| 5.6 | Black-box fuzzing (grammar + mutation, AFL) | Fuzz mà không biết code |
| 5.7 | White-box fuzzing (dynamic symbolic execution) | Fuzz với guidance từ code |
| 5.8 | BMC for test generation | Cầu nối ngược về static |

## Trước khi bắt đầu

Cụm này giả định bạn đã quen với:

- Khái niệm property, assertion ([bài 1.5](../01-introduction/05-formal-verification-intro)).
- Khái niệm cơ bản BMC, SMT, counterexample ([bài 1.6](../01-introduction/06-bmc-and-smt-basics)).
- (Tuỳ chọn) Quen với LTL từ Logic and Modelling.

Nếu chưa quen LTL, bài 5.4 sẽ giới thiệu lại đủ để hiểu.

Sẵn sàng? Bắt đầu với [bài 5.2: Security testing](./02-security-testing).
