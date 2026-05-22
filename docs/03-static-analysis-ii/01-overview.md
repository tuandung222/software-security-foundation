---
id: 01-overview
title: 4.1 Tổng quan Lecture 4
sidebar_position: 1
description: Giới thiệu cụm Static Analysis II về concurrency verification.
---

# Lecture 4: Static Analysis II (Concurrency)

> **Tóm tắt một dòng**: Khi nhiều thread chạy song song, không gian state nổ tung theo cấp số nhân. Cụm này giới thiệu các kỹ thuật khéo léo để xử lý: context-bounded analysis, lazy exploration, schedule recording, và sequentialization.

:::info Đang biên soạn
Nội dung chi tiết cụm này đang được biên soạn. Các bài sẽ xuất hiện trong sidebar khi sẵn sàng.

Để chuẩn bị, bạn nên ôn lại [bài 1.6 (BMC và SMT basics)](../01-introduction/06-bmc-and-smt-basics) và đảm bảo hiểu rõ phần race condition trong [bài 1.3](../01-introduction/03-vulnerabilities-catalog).
:::

## Lộ trình cụm

1. **Loop unwinding và safety conditions**: nền tảng từ Lecture 3 áp dụng cho chương trình tuần tự.
2. **Bit-blasting và arrays**: kỹ thuật mã hoá thấp hơn nữa cho SAT solver.
3. **Concurrency verification**: vì sao multi-threaded program đặc biệt khó verify.
4. **Context-bounded analysis (CBA)**: giới hạn số lần chuyển thread để giảm không gian.
5. **Lazy exploration vs schedule recording**: hai chiến lược khám phá không gian schedule.
6. **Sequentialization (KISS, LR)**: dịch chương trình đa luồng về chương trình tuần tự để dùng lại tool BMC.

[Quay lại Cụm 1: Lecture 1-2](../01-introduction/01-overview) hoặc đợi nội dung chi tiết.
