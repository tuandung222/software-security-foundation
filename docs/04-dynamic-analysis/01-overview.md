---
id: 01-overview
title: 5.1 Tổng quan Lecture 5
sidebar_position: 1
description: Giới thiệu cụm Dynamic Analysis về testing, monitoring và fuzzing.
---

# Lecture 5: Dynamic Analysis (Testing, Monitoring, Fuzzing)

> **Tóm tắt một dòng**: Khi không thể chứng minh "không có bug", ta tìm bug bằng cách chạy chương trình. Cụm này giới thiệu coverage criteria, runtime monitoring với LTL/Büchi automata, và đặc biệt là **fuzzing**, công cụ tìm bug hiệu quả nhất trong thực tế.

:::info Đang biên soạn
Nội dung chi tiết cụm này đang được biên soạn.
:::

## Lộ trình cụm

1. **Security testing**: vì sao kiểm thử security khó hơn kiểm thử functionality.
2. **Coverage criteria**: statement, decision, condition, MC/DC.
3. **Runtime monitoring với LTL và Büchi automata**: theo dõi property khi chương trình chạy.
4. **Fuzzing basics**: random testing và giới hạn của nó.
5. **Black-box fuzzing**: grammar-based và mutation-based.
6. **White-box fuzzing**: dynamic symbolic execution, SAGE.
7. **BMC for test generation**: dùng BMC theo cách "ngược" để sinh test case có coverage cao.

[Quay lại Cụm 1: Lecture 1-2](../01-introduction/01-overview) hoặc đợi nội dung chi tiết.
