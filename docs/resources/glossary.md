---
id: glossary
title: Thuật ngữ (Anh-Việt)
sidebar_position: 2
description: Bảng tra cứu nhanh các thuật ngữ chuyên ngành Anh-Việt.
---

# Thuật ngữ Anh-Việt

> **Hướng dẫn**: dùng `Ctrl+F` để tìm nhanh thuật ngữ.

## A

- **Abstract Interpretation** (diễn giải trừu tượng): kỹ thuật static analysis tính over-approximation của state space.
- **Access Control**: kiểm soát truy cập.
- **Assertion**: phát biểu kiểm tra (ví dụ `assert(x > 0)`).
- **Atomic Operation**: phép toán nguyên tử, không bị chia cắt.
- **Authenticity** (xác thực): tính chất danh tính người gửi đúng.
- **Authorization**: cấp quyền (sau khi authentication).
- **Availability** (sẵn sàng): tính chất hệ thống trả lời khi được yêu cầu hợp lệ.

## B

- **Backtracking**: thuật toán quay lui (trong SAT solver hoặc regex engine).
- **Bit-blasting**: kỹ thuật chuyển bitvector formula thành SAT.
- **Bounded Model Checking (BMC)**: kiểm chứng có giới hạn depth.
- **Buffer Overflow** (tràn bộ đệm): ghi quá biên mảng.

## C

- **Canary** (chim hoàng yến, stack canary): giá trị ngẫu nhiên chèn trước return address.
- **CFG (Control Flow Graph)**: đồ thị luồng điều khiển.
- **CIA Triad**: bộ ba Confidentiality, Integrity, Availability.
- **Concurrency**: tính chất chương trình đa luồng.
- **Confidentiality** (bí mật): tính chất thông tin chỉ lộ cho người được phép.
- **Counterexample** (phản ví dụ): trace cụ thể vi phạm property.

## D

- **Decision Procedure**: thuật toán quyết định cho một theory cụ thể trong SMT.
- **DPLL**: thuật toán Davis-Putnam-Logemann-Loveland cho SAT.

## E

- **Encoding**: dịch chương trình thành công thức logic.
- **Entity** (XML entity): macro thay thế trong XML.

## F

- **Floating-Point Theory**: theory SMT cho số dấu phẩy động.
- **Formal Verification**: kiểm chứng hình thức.
- **Fuzzing**: kỹ thuật test với input ngẫu nhiên hoặc có hướng dẫn.

## I

- **Integer Overflow**: tràn dải số nguyên.
- **Integrity** (toàn vẹn): tính chất dữ liệu không bị sửa trái phép.
- **Invariant**: bất biến (giá trị luôn đúng tại một điểm trong chương trình).

## L

- **Liveness Property**: tính chất "điều tốt sẽ xảy ra", counterexample vô hạn.
- **LTL (Linear Temporal Logic)**: logic thời gian tuyến tính.

## M

- **MAC (Message Authentication Code)**: mã xác thực thông điệp.
- **Memory-Safe Language**: ngôn ngữ an toàn bộ nhớ (Rust, Go, Java).
- **Model Checking**: kiểm chứng mô hình.

## N

- **Non-repudiation** (chống chối bỏ): tính chất người gửi không thể chối là đã gửi.

## P

- **Property** (tính chất): mệnh đề mà chương trình phải thoả.

## R

- **Race Condition**: lỗi do thứ tự thực thi giữa thread.
- **Reflected XSS**: XSS qua URL/form, server echo lại trong response.

## S

- **Safety Property**: tính chất "điều xấu không xảy ra", counterexample hữu hạn.
- **SAT (Satisfiability)**: bài toán thoả được boolean.
- **Sanitization**: làm sạch input.
- **SMT (Satisfiability Modulo Theories)**: mở rộng SAT với theory.
- **Soundness**: tính chất "nói OK thì thực sự OK".
- **SQL Injection (SQLi)**: tấn công inject SQL qua input.
- **SSA (Static Single Assignment)**: dạng chuẩn mỗi biến gán đúng 1 lần.
- **Stored XSS**: XSS lưu trên server, tự kích hoạt mọi user.

## T

- **Theorem Proving**: chứng minh định lý bằng prover (Coq, Isabelle).
- **TOCTOU (Time Of Check, Time Of Use)**: dạng race giữa check và use.

## U

- **Undefined Behavior (UB)**: hành vi không xác định theo chuẩn C/C++.
- **UNSAT (Unsatisfiable)**: công thức không có nghiệm.

## V

- **V&V (Verification and Validation)**: kiểm chứng và xác thực.
- **Vulnerability** (lỗ hổng): bug có thể bị khai thác để vi phạm security property.

## X

- **XSS (Cross-Site Scripting)**: tấn công inject script vào HTML.
- **XXE (XML External Entity)**: tấn công qua entity ngoại trong XML.
