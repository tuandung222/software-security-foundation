---
id: 01-overview
title: 3.1 Tổng quan Lecture 3
sidebar_position: 1
description: Giới thiệu phần Static Analysis I, mục tiêu, các kỹ thuật sẽ học và mối quan hệ với Lecture 1-2.
---

# Lecture 3: Static Analysis I (BMC + SMT chi tiết)

> **Tóm tắt một dòng**: Phần này đi sâu vào cách dịch một chương trình C thành công thức logic và để SMT solver kiểm tra. Bạn sẽ thấy cách CBMC và ESBMC thực sự hoạt động bên trong, từ thuật toán SAT/DPLL ở tầng thấp cho tới encoding pointer ở tầng cao.

## Bài 2.2 đã dạy gì và tại sao ta cần đi tiếp

Ở [bài 2.2](../01-introduction/06-bmc-and-smt-basics), chúng ta đã có một cái nhìn tổng quát về Bounded Model Checking: dịch chương trình sang SSA, encode thành SMT formula, đẩy cho solver, đọc kết quả. Tuy nhiên có rất nhiều thứ ta đã bỏ qua hoặc giấu dưới lớp trừu tượng "solver". Chẳng hạn:

- SMT solver thực sự làm gì bên trong? Khi nó gặp một công thức bitvector 32-bit có hàng triệu biến boolean ngầm, thuật toán nào giúp nó quyết định SAT/UNSAT trong vài giây?
- Khi C cấp phát `malloc(100)` rồi truy cập `*(p + 50)`, làm thế nào encode được "memory" thành một đối tượng mà solver hiểu?
- Số `0.1 + 0.2` trong C trả về `0.30000000000000004` thay vì `0.3`. Làm thế nào encode chính xác semantics của floating-point để verifier không miss bug?
- Khi chương trình có nhiều file, nhiều function, làm thế nào BMC ghép hết các function lại để verify một property global?

Mỗi câu hỏi trên là một bài trong phần này.

## Lộ trình phần

Phần Lecture 3 sẽ đi qua bảy chủ đề chính theo thứ tự logic:

| Bài | Chủ đề | Tại sao cần |
|---|---|---|
| 3.1 | Tổng quan (bài này) | Đặt context và kết nối với Lecture 1-2 |
| 3.2 | Verification và Validation | Phân biệt rõ V&V, vị trí của BMC trong V-model |
| 3.3 | State space exploration | Hai chiến lược cốt lõi: BFS và DFS, cùng giới hạn của explicit-state |
| 3.4 | SAT và DPLL | Thuật toán mà SMT solver gọi ở tầng thấp nhất |
| 3.5 | SMT theories | Cách combining SAT với theory cho số, mảng, hàm |
| 3.6 | Encoding numbers và floats | Phần thực dụng nhất: dịch `int`, `float`, `double` C sang bitvector và FP theory |
| 3.7 | Encoding pointers và memory | Phần khó nhất: dịch `*p`, `malloc`, `&x[i]` sang array theory |

Sau phần này, bạn sẽ đủ kiến thức để:

- Chạy CBMC hoặc ESBMC trên code C của mình và **hiểu output** (không chỉ thấy "PASS" hoặc "FAIL").
- Đọc paper trong lĩnh vực formal verification mà không bị choáng với các thuật ngữ "DPLL(T)", "Nelson-Oppen", "Lazy SMT".
- Đánh giá khi nào dùng theory nào để cân bằng giữa tốc độ verification và độ chính xác.

## Mối quan hệ với Lecture 4

Phần Lecture 3 này tập trung **chương trình tuần tự**. Khi chương trình có nhiều thread, không gian state nhân lên theo số interleaving khả dĩ giữa các thread, và state explosion trở thành vấn đề nghiêm trọng hơn nhiều. [Lecture 4](../03-static-analysis-ii/01-overview) sẽ giới thiệu các kỹ thuật chuyên biệt cho concurrency: context-bounded analysis, lazy exploration, sequentialization.

Lecture 4 giả định bạn đã hiểu rõ Lecture 3, vì các kỹ thuật concurrency phần lớn là **mở rộng** của các kỹ thuật tuần tự, không phải thay thế.

## Trước khi bắt đầu

Nếu bạn chưa thoải mái với các khái niệm dưới đây, hãy quay lại các bài liên quan của Lecture 1-2 trước:

- **Property, safety vs liveness**: [bài 2.1](../01-introduction/05-formal-verification-intro).
- **Soundness, completeness**: [bài 2.1](../01-introduction/05-formal-verification-intro).
- **SSA form, encoding một chương trình C đơn giản**: [bài 2.2](../01-introduction/06-bmc-and-smt-basics).
- **Khái niệm SAT, SMT, theory**: [bài 2.2](../01-introduction/06-bmc-and-smt-basics).

Sẵn sàng rồi? Bắt đầu với [bài 3.2: Verification và Validation](./02-verification-vs-validation).
