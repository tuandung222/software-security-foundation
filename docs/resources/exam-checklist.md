---
id: exam-checklist
title: Checklist tự kiểm tra
sidebar_position: 3
description: Danh sách điểm kiến thức cần nắm vững sau mỗi phần bài giảng để tự đánh giá.
---

# Checklist tự kiểm tra kiến thức

Sau khi đọc xong mỗi phần bài giảng, hãy quay lại trang này và tự đánh dấu xem bạn đã nắm vững các điểm dưới đây chưa. Nếu một mục bạn không trả lời được, quay lại bài tương ứng đọc thêm.

## Sau Phần 1 (Lecture 1-2): Foundation

- [ ] Phát biểu CIA Triad và cho ví dụ vi phạm mỗi thuộc tính.
- [ ] Phân biệt Safety và Security trong một câu kèm ví dụ minh hoạ.
- [ ] Giải thích vì sao Cryptography không đủ để bảo đảm Software Security (Heartbleed example).
- [ ] So sánh Implementation Vulnerability và Design Vulnerability.
- [ ] Mô tả cơ chế buffer overflow trên stack với layout cụ thể (canary, return address).
- [ ] Phân biệt `strcpy`, `strncpy`, `strlcpy`, `snprintf` và biết khi nào dùng cái nào.
- [ ] Giải thích integer overflow và cách phòng tránh bằng `__builtin_add_overflow`.
- [ ] Phân biệt data race và TOCTOU race condition.
- [ ] Mô tả tấn công SQL Injection cơ bản và cách phòng tránh bằng parameterized query.
- [ ] Liệt kê 3 biến thể XSS (reflected, stored, DOM-based) và biện pháp phòng (encoding, CSP, HttpOnly).
- [ ] Giải thích XXE attack và cách tắt external entity.
- [ ] Mô tả ReDoS và pattern regex nguy hiểm.
- [ ] Phát biểu định lý Dijkstra về testing.
- [ ] Phân biệt Soundness và Completeness, kèm ví dụ tool thiếu mỗi tính chất.
- [ ] Phân biệt Safety property và Liveness property.
- [ ] Liệt kê 3 họ kỹ thuật formal verification (model checking, theorem proving, abstract interpretation).
- [ ] Viết công thức BMC tổng quát $\Phi_k$.
- [ ] Chuyển một chương trình C 5 dòng sang SSA và encode SMT-LIB.
- [ ] Giải thích vì sao encoding bằng theory Int khác bằng BitVec cho cùng chương trình.

## Sau Phần 2 (Lecture 3): Static Analysis I (BMC + SMT)

- [ ] Phân biệt Verification và Validation, cho ví dụ.
- [ ] Phân biệt Static V và Dynamic V; biết tool nào phổ biến cho mỗi loại.
- [ ] Vẽ V-model và chỉ vị trí của BMC.
- [ ] Mô tả quy trình debug 5 bước sau khi tool tìm bug.
- [ ] Phân biệt BFS và DFS, biết khi nào dùng cái nào.
- [ ] Giải thích state explosion problem với ví dụ định lượng.
- [ ] Phân biệt symbolic execution và BMC.
- [ ] Phát biểu bài toán SAT và định nghĩa CNF.
- [ ] Mô tả thuật toán DPLL với unit propagation và branching.
- [ ] Giải thích CDCL: conflict analysis, learning, non-chronological backjumping.
- [ ] Giải thích kiến trúc DPLL(T) (lazy SMT).
- [ ] Liệt kê các theory phổ biến: EUF, LIA, LRA, BV, Array, FP, String.
- [ ] Mô tả Nelson-Oppen combination, biết điều kiện áp dụng.
- [ ] Encode một phép `+, -, *` 32-bit thành bitvector formula.
- [ ] Phân biệt `bvslt` và `bvult`, cho ví dụ khác kết quả.
- [ ] Mô tả IEEE 754 float layout (sign, exponent, mantissa).
- [ ] Giải thích vì sao $0.1 + 0.2 \neq 0.3$ trong float.
- [ ] Mô tả array theory với read-over-write axiom.
- [ ] Phân biệt 3 memory model của ESBMC: fixed, align, offset.
- [ ] Giải thích cách BMC detect use-after-free và double free.

## Sau Phần 3 (Lecture 4): Static Analysis II (Concurrency)

- [ ] Giải thích vì sao concurrency verification khó hơn sequential (state explosion mạnh hơn).
- [ ] Tính số schedule khả dĩ với $k$ thread, $n$ instruction.
- [ ] Mô tả loop unwinding và unwinding assertion.
- [ ] Phân biệt k-induction với loop unwinding.
- [ ] Liệt kê safety conditions tự động của CBMC (bounds, div0, null, overflow, UAF).
- [ ] Mô tả bit-blasting cho phép cộng, nhân, chia.
- [ ] Phân biệt eager SMT và lazy DPLL(T) cho BV.
- [ ] Giải thích array theory với axiom instantiation và lambda-term.
- [ ] Phân biệt các loại bug concurrency: data race, atomicity violation, deadlock, livelock, order violation.
- [ ] Mô tả memory model: SC, TSO, weak (ARM/POWER).
- [ ] Phát biểu observation của Qadeer-Rehof về context switch.
- [ ] Mô tả Context-Bounded Analysis (CBA) và lý do hiệu quả.
- [ ] Phân biệt lazy interleaving và schedule recording.
- [ ] Giải thích Mazurkiewicz trace và vector clock.
- [ ] Mô tả DPOR (Dynamic Partial Order Reduction).
- [ ] Phân biệt KISS và LR sequentialization, biết khi nào dùng cái nào.

## Sau Phần 4 (Lecture 5): Dynamic Analysis (Testing + Fuzzing)

- [ ] Phân biệt Security testing với Functional testing.
- [ ] Liệt kê các loại oracle gián tiếp cho security testing.
- [ ] Phân biệt vulnerability scanning, pen testing, security regression.
- [ ] Phân biệt 4 cấp coverage criteria: statement, decision, condition, MC/DC.
- [ ] Tính số test MC/DC cho 1 decision với $n$ sub-condition.
- [ ] Giải thích vì sao MC/DC tốt hơn full multiple condition cho code lớn.
- [ ] Phát biểu LTL operator: $G, F, X, U$.
- [ ] Mô tả Büchi automaton và vì sao accept infinite word.
- [ ] Phân biệt online và offline monitoring.
- [ ] Giải thích bounded liveness và lý do dùng.
- [ ] Mô tả pipeline fuzzing 4 bước (seed, generate, run, feedback).
- [ ] Phân biệt random testing thuần và coverage-guided fuzzing.
- [ ] Mô tả 4 ý tưởng của AFL: instrumentation, forkserver, energy schedule, mutation strategy.
- [ ] Phân biệt mutation-based và grammar-based fuzzing.
- [ ] Giải thích Dynamic Symbolic Execution (concolic execution).
- [ ] Phân biệt DSE và pure symbolic execution.
- [ ] Mô tả Driller (hybrid AFL + DSE).
- [ ] Giải thích BMC for test generation: encode goal là `assert(0)`.
- [ ] Phân biệt khi nào dùng BMC cho test gen vs fuzzing.

## Sau Phần 5 (Lecture 6 - Case Study)

- [ ] Liệt kê 5 bước tiếp cận tư vấn security (Context, Threat, Risk, Mitigation, Trade-off).
- [ ] Phát biểu STRIDE và áp dụng cho 1 component cụ thể.
- [ ] Phân biệt threat modeling và risk assessment.
- [ ] Liệt kê 7 nguyên tắc chung: Least Privilege, Zero Trust, Secure by Default, ...
- [ ] Mô tả OWASP Top 10 (2021) ở cấp list.
- [ ] Áp dụng STRIDE cho 1 dự án Web/SaaS startup.
- [ ] Liệt kê PCI-DSS 12 requirement chính.
- [ ] Mô tả key hierarchy (Master, KEK, DEK) và HSM.
- [ ] Phân biệt KYC và AML, vai trò trong fintech.
- [ ] Mô tả secure boot với chain of trust.
- [ ] Mô tả OTA update requirement (signed, atomic, rollback, mandatory).
- [ ] Mô tả Zero Trust Network và microsegmentation.
- [ ] Mô tả ransomware mitigation (3-2-1 backup, immutable, air-gapped).
- [ ] Liệt kê common pitfall của mỗi domain (web, fintech, IoT, enterprise).

## Tổng kết khi học hết

- [ ] Có thể giải thích các kỹ thuật cốt lõi cho người không học chuyên: BMC, SAT, fuzzing.
- [ ] Có thể chạy CBMC trên 1 chương trình C và đọc output.
- [ ] Có thể viết test case cover MC/DC cho 1 decision phức tạp.
- [ ] Có thể tư vấn security cho 1 dự án giả định (1 trong 4 domain case study).
- [ ] Có thể đọc 1 CVE report và phân loại được lớp lỗ hổng.
- [ ] Có thể áp dụng STRIDE để liệt kê threat cho hệ thống mới.

Khi bạn tick được hết các mục, bạn đã nắm vững toàn bộ tài liệu này.
