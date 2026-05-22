---
id: 01-overview
title: 3.1 Tổng quan Lecture 3
sidebar_position: 1
description: Giới thiệu cụm Static Analysis I, mục tiêu, các kỹ thuật sẽ học và mối quan hệ với Lecture 1-2.
---

# Lecture 3: Static Analysis I (BMC + SMT chi tiết)

> **Tóm tắt một dòng**: Cụm này đi sâu vào cách dịch một chương trình C thành công thức logic và để SMT solver kiểm tra. Bạn sẽ thấy cách CBMC và ESBMC thực sự hoạt động bên trong.

:::info Đang biên soạn
Nội dung chi tiết cụm này đang được biên soạn. Các bài đã hoàn thành sẽ xuất hiện trong sidebar bên trái khi sẵn sàng.

Trong thời gian này, bạn có thể quay lại [Cụm 1 (Lecture 1-2)](../01-introduction/01-overview) để củng cố nền tảng, đặc biệt là bài [1.6 BMC và SMT basics](../01-introduction/06-bmc-and-smt-basics) là bài dẫn nhập trực tiếp cho cụm này.
:::

## Lộ trình cụm

Cụm Lecture 3 sẽ đi qua bảy chủ đề chính theo thứ tự logic:

1. **Verification và Validation**: phân biệt hai khái niệm thường bị nhầm, và vị trí của BMC trong V&V plan.
2. **State space exploration**: BFS, DFS, các kỹ thuật giảm không gian state.
3. **SAT và DPLL**: thuật toán cốt lõi mà SMT solver dùng cho phần boolean.
4. **SMT theories**: kết hợp boolean với số, mảng, hàm.
5. **Encoding số nguyên và floating-point**: cách dịch `int`, `float`, `double` thành bitvector và floating-point theory.
6. **Encoding pointer và memory**: phần khó nhất, dịch `*p`, `malloc`, `&x[i]` thành array theory.

Sau cụm này, bạn sẽ đủ kiến thức để **chạy CBMC trên code C** và **hiểu output của nó**.

[Quay lại Cụm 1: Lecture 1-2](../01-introduction/01-overview) hoặc đợi nội dung chi tiết.
