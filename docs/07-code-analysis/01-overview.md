---
id: 01-overview
title: 8.1 Tổng quan phân tích code
sidebar_position: 1
description: "Phương pháp đọc và phân tích lại các đoạn code C/C++ minh hoạ trong tài liệu, kèm cách phát hiện bug bằng tool và cách viết lại an toàn."
---

# Lecture 8: Phân tích code C/C++ trong tài liệu

> **Tóm tắt một dòng**: Cụm này quay lại từng đoạn code C/C++ xuất hiện trong các cụm trước (Lec 1-5) và các đề bài tập, đọc kỹ từng dòng, chỉ ra cụ thể chỗ sai, giải thích cơ chế lỗi, đề xuất cách viết lại, và minh hoạ cách CBMC/ESBMC bắt được bug nếu có. Mục tiêu: nâng cấp khả năng **đọc code C/C++ kiểu kỹ sư an ninh**, không chỉ kiểu lập trình viên thông thường.

## Vì sao cần một chương riêng phân tích code?

Trong 7 cụm trước, code xuất hiện rải rác làm minh hoạ cho concept. Người đọc thường tập trung vào concept, lướt qua code. Nhưng:

1. **Bug thật nằm trong code thật**: hiểu concept "buffer overflow" khác xa với việc **đọc đúng** code có buffer overflow và chỉ ra dòng nào sai.
2. **Code C/C++ trong tài liệu mặc định cô đọng**: nhiều đoạn lược bỏ header, error handling, để focus vào điểm minh hoạ. Người đọc cần học cách **lấp những lỗ hổng này** trong đầu khi review code production.
3. **Mỗi đoạn code có nhiều bug, không chỉ một**: tài liệu thường chỉ một bug chính. Nhưng cùng đoạn code có thể còn 2-3 bug khác mà người đọc cần thấy.
4. **Code review là kỹ năng practical**: lý thuyết BMC không thay được khả năng human reviewer đọc 200 dòng C và nhận ra UAF tiềm ẩn.

Chương này tổng hợp **toàn bộ pattern code** từ Lec 1-5, đọc chậm, comment chi tiết, đề xuất tool verify.

## Phương pháp đọc code 6 bước

Mỗi đoạn code, tôi sẽ áp dụng quy trình sau:

### Bước 1: Đọc lần một, hiểu chức năng

Code đang **cố làm gì**? Trước khi tìm bug, phải hiểu intent. Bug = "code làm khác intent".

### Bước 2: Liệt kê assumption ngầm

Code C/C++ thường có **assumption ngầm** mà không kiểm tra:
- Input size phù hợp với buffer.
- Pointer không null.
- Integer không overflow.
- File tồn tại.
- Quyền đọc/ghi đã có.

Mỗi assumption không kiểm tra = một bug tiềm năng.

### Bước 3: Tìm bug theo checklist

Đi qua các lớp lỗ hổng quen thuộc:
- Memory: buffer overflow, UAF, double free, memory leak.
- Integer: overflow, sign error, narrowing conversion.
- Logic: race condition, TOCTOU, off-by-one.
- Crypto: hardcoded key, weak random, predictable token.
- Injection: SQL, command, format string.
- Auth: missing check, IDOR.

### Bước 4: Phân loại nghiêm trọng

Bug tìm được thuộc loại nào theo CVSS?
- Critical: RCE, full data leak.
- High: privilege escalation, partial data leak.
- Medium: DoS, info disclosure.
- Low: configuration weakness.

Quyết định "fix ngay" hay "backlog".

### Bước 5: Viết fix

Fix phải:
- Đúng (không introduce bug mới).
- Tối thiểu (không thay đổi semantics khác).
- Có comment giải thích vì sao.
- Có test (regression).

### Bước 6: Verify với tool

CBMC/ESBMC trên code mới: chứng minh bug đã fix.
SAST trên codebase: pattern không lặp lại nơi khác.

## Cấu trúc 5 bài trong cụm này

| Bài | Nguồn code phân tích | Số sample | Lớp bug |
|---|---|---|---|
| [8.2 Code patterns Cụm 1](./02-code-patterns-cluster-1) | Lec 1-2 (intro, vulnerabilities) | ~10 | Buffer overflow, UAF, integer overflow, format string, race |
| [8.3 Code patterns Cụm 2](./03-code-patterns-cluster-2) | Lec 3 (BMC, SMT encoding) | ~8 | Bug để demo BMC bắt: array bounds, pointer, float |
| [8.4 Code patterns Cụm 3](./04-code-patterns-cluster-3) | Lec 4 (concurrency) | ~8 | Data race, atomicity, deadlock, memory model |
| [8.5 Code patterns Cụm 4](./05-code-patterns-cluster-4) | Lec 5 (testing, fuzzing) | ~6 | Coverage demo, fuzzing target |
| [8.6 Exercise analysis](./06-exercise-analysis) | Exercise Set 2 (7 bài) | 7 | Mix: memory, integer, struct alignment |

## Format chung của mỗi sample

Mỗi sample được trình bày theo template:

````markdown
### Sample N: <tên ngắn>

**Nguồn**: Lec X, mục Y.
**Mục đích trong tài liệu gốc**: minh hoạ <concept>.

**Code (cleaned up)**:
```c
... code đã làm sạch ...
```

**Đọc nhanh** (1-2 câu mô tả intent).

**Bug tìm được**:
1. **Bug chính**: ...
2. **Bug phụ**: ...

**Cơ chế**:
giải thích step-by-step cách bug xảy ra, kèm memory layout/state nếu cần.

**Fix gợi ý**:
```c
... code đã sửa ...
```

**Verify với CBMC** (nếu áp dụng):
```bash
cbmc sample.c --bounds-check ...
```
Output mong đợi.

**Bài học**: 1-2 câu chốt.
````

## Lưu ý về code gốc

Code trong tài liệu nguồn thường:

- **Thiếu header**: `#include <stdio.h>`, `#include <string.h>` không có. Tôi sẽ thêm cho compile được.
- **Macro/định nghĩa ẩn**: ví dụ `nondet_int()` không khai báo, hiểu ngầm là input bất kỳ.
- **Compilation warning**: mixed declaration, void main(), implicit int. Sẽ giữ lại để chỉ ra warning là **bug pattern**.
- **OCR artifact**: kí tự `–`, `ꢀ` từ PDF extraction. Sẽ clean.

Tất cả code đã được tôi reformat để compile được với `gcc -std=c99` hoặc `clang -fsyntax-only`. Code "as-is" trong tài liệu có thể không compile, đó là điểm thứ nhất cần chú ý khi review code published.

## Mục tiêu cuối cụm

Sau khi đọc hết 5 bài, bạn sẽ:

- Nhớ ~40 code pattern xuất hiện trong tài liệu, biết bug của mỗi pattern.
- Đọc một đoạn C/C++ 50 dòng và liệt kê được 3-5 issue trong 10 phút.
- Viết được fix cho mỗi loại bug, kèm explain.
- Biết tool nào (CBMC, ASan, fuzzer) phù hợp cho từng loại.

Đây là kỹ năng **code review formal** cho security.

Sẵn sàng? Bắt đầu với [bài 8.2: Code patterns Cụm 1](./02-code-patterns-cluster-1).
