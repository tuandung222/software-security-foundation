---
id: 01-overview
title: 4.1 Tổng quan Lecture 4
sidebar_position: 1
description: Giới thiệu phần Static Analysis II về concurrency verification, vì sao multi-threaded khó hơn nhiều so với sequential, và các kỹ thuật chính giảm state explosion.
---

# Lecture 4: Static Analysis II (Concurrency)

> **Tóm tắt một dòng**: Khi chương trình có nhiều thread, không gian state bùng nổ theo số interleaving khả dĩ. Phần này giới thiệu các kỹ thuật khéo léo để xử lý vấn đề này: bit-blasting đúng cách, context-bounded analysis, lazy exploration, schedule recording, và sequentialization (dịch multi-thread thành sequential để dùng lại tool tuần tự).

## Vì sao concurrency lại khó đến vậy?

Ở Lecture 3, ta đã thấy chương trình tuần tự được encode thành công thức logic, đẩy cho SMT solver, trả về SAT/UNSAT. Việc đó đã đủ phức tạp. Khi thêm concurrency, mọi thứ trở nên khó hơn nhiều bậc.

Hãy hình dung một chương trình đơn giản với hai thread, mỗi thread chỉ có 10 instruction. Trong sequential, có **1 lịch trình** duy nhất: thread chạy 10 instruction từ đầu tới cuối. Trong concurrent, OS có thể chuyển thread tại bất kỳ instruction nào. Số lịch trình khả dĩ là số cách "trộn" 10 instruction của thread 1 với 10 instruction của thread 2 sao cho thứ tự nội bộ mỗi thread giữ nguyên. Đây là số tổ hợp:

$$\binom{20}{10} = 184{,}756$$

Mỗi lịch trình tương ứng một execution có thể, mỗi execution có thể vi phạm hoặc không vi phạm property. Phải khám phá hết 184756 schedule để biết chắc.

Nhân lên với 4 thread, mỗi thread 100 instruction:

$$\frac{400!}{(100!)^4} \approx 10^{198}$$

Số nhiều hơn số nguyên tử trong vũ trụ ($\approx 10^{80}$). Không có máy tính nào liệt kê hết.

Đây chính là **state explosion problem trong concurrency**, mạnh hơn cả state explosion mà chúng ta đã thấy trong [bài 3.3](../02-static-analysis-i/03-state-space-exploration). Phần Lecture 4 tập trung vào các kỹ thuật để **vượt qua** state explosion này.

## Bốn ý tưởng lớn của phần

### Ý tưởng 1: Bit-blasting hiệu quả cho lower-level encoding

Để hiểu vì sao tool BMC nhanh hay chậm, ta cần biết SMT solver chuyển bitvector thành SAT như thế nào (bit-blasting). Bài 4.2 và 4.3 đào sâu vào kỹ thuật này, cùng với cách xử lý array (memory) một cách scalable.

### Ý tưởng 2: Context-bounded analysis

Quan sát thực tế: hầu hết bug concurrency thực tế chỉ xuất hiện với **một vài lần context switch**, không phải sau hàng nghìn. Vì thế, thay vì khám phá mọi lịch trình, ta **giới hạn số context switch tối đa** thành một hằng $K$ nhỏ (thường $K = 2$ tới $5$).

Số lịch trình với $K$ context switch là **đa thức** theo $n$, không phải mũ. Đây là đột phá lớn của Qadeer và Rehof (2005), giúp concurrency verification trở nên thực dụng.

Bài 4.5 đi sâu vào CBA.

### Ý tưởng 3: Lazy exploration và schedule recording

Hai chiến lược cụ thể để khám phá không gian schedule:

- **Lazy exploration** (lazy interleaving): chỉ "fork" thread khi cần thiết, tức khi gặp shared memory access. Giảm số schedule phải xét.

- **Schedule recording**: ghi lại lịch trình đã khám phá, tránh khám phá lại schedule tương đương. Liên quan tới partial-order reduction.

Bài 4.6 giải thích chi tiết.

### Ý tưởng 4: Sequentialization

Cách tiếp cận hoàn toàn khác: thay vì verify multi-threaded program trực tiếp, **dịch** nó thành sequential program tương đương (theo nghĩa bảo toàn mọi vi phạm property), rồi dùng tool tuần tự verify.

Hai kỹ thuật chính: **KISS** (Keep It Sequential, Stupid) của Qadeer-Wu và **LR sequentialization** (Lal-Reps). Bài 4.7 đi sâu.

## Lộ trình phần

| Bài | Chủ đề | Vì sao cần |
|---|---|---|
| 4.1 | Tổng quan (bài này) | Đặt context |
| 4.2 | Loop unwinding và safety conditions | Nền tảng dùng lại từ Lec 3 |
| 4.3 | Bit-blasting và arrays | Cách SAT solver "thấy" bitvector và memory |
| 4.4 | Concurrency verification | Data race, atomicity violation, memory model |
| 4.5 | Context-bounded analysis | Đột phá lớn nhất của concurrency verification |
| 4.6 | Lazy exploration vs schedule recording | Hai chiến lược khám phá schedule |
| 4.7 | Sequentialization (KISS, LR) | Reduce multi-thread về single-thread |

## Trước khi bắt đầu

Phần này giả định bạn đã quen với:

- BMC + SMT cơ bản (bài 2.2, Lecture 3 toàn bộ).
- Race condition cơ bản (bài 1.3).
- Khái niệm thread, mutex, atomic operation ở mức lập trình C/C++ (đọc man page `pthread_mutex_lock` là đủ).

Nếu cần ôn nhanh về race condition, đọc lại [bài 1.3 phần Race condition](../01-introduction/03-vulnerabilities-catalog).

Sẵn sàng? Bắt đầu với [bài 4.2: Loop unwinding và safety conditions](./02-loop-unwinding-and-safety).
