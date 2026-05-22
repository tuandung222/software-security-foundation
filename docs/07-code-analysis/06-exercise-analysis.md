---
id: 06-exercise-analysis
title: 8.6 Phân tích Exercise Set 2 với tool
sidebar_position: 6
description: "Đi qua 7 bài Exercise Set 2 với góc nhìn formal verification: cách CBMC/ASan/UBSan bắt bug, CWE classification, mức nghiêm trọng CVSS."
---

# 8.6 Phân tích Exercise Set 2 với tool

> **Tóm tắt một dòng**: 7 bài trong [Exercise Set 2](../exercises/exercise-set-2) đã có đáp án dạng manual review. Bài này quay lại từng bài với góc nhìn **tool automation**: chạy CBMC/ASan/UBSan để chứng minh bug, classify CWE, đánh giá CVSS, và liệt kê fix pattern. Mục tiêu: thấy mỗi bài thủ công có thể được automated trong CI.

## Bài 1: sprintf buffer overflow

**Code gốc** (tóm tắt):

```c
void greet(char *name) {
    char buf[16];
    sprintf(buf, "Hello, %s!", name);
    printf("%s\n", buf);
}
```

### Phân tích

| Thuộc tính | Giá trị |
|---|---|
| **Bug class** | Stack buffer overflow |
| **CWE** | CWE-121 Stack-based Buffer Overflow |
| **CVSS 3.1** | 8.8 High (vector: AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H) |
| **Tool bắt được** | Compiler warning, ASan, CBMC --bounds-check, GCC FORTIFY_SOURCE |

### Verify bằng tool

**Method 1: ASan runtime**

```bash
clang -fsanitize=address -g bai1.c -o bai1
./bai1 "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
```

Output:

```
=================================================================
==12345==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x...
    #0 0x... in sprintf
    #1 0x... in greet bai1.c:5
SUMMARY: AddressSanitizer: stack-buffer-overflow bai1.c:5 in greet
```

ASan bắt ngay khi runtime.

**Method 2: CBMC formal**

Cần wrap thành harness vì `argv[1]` là từ environment:

```c
#include <string.h>
#include <stdio.h>

void greet(char *name);

int main(void) {
    char name[20];
    for (int i = 0; i < 19; i++) name[i] = nondet_char();
    name[19] = '\0';
    greet(name);
    return 0;
}
```

```bash
cbmc harness.c bai1.c --bounds-check --pointer-check
```

```
[greet.array_bounds.1] line 5 array `buf' upper bound: FAILURE
```

**Method 3: FORTIFY_SOURCE compile-time**

```bash
gcc -O2 -D_FORTIFY_SOURCE=2 bai1.c -o bai1
./bai1 "AAAAAAAAAAAAAAAAAAAAAA"
```

Output:

```
*** buffer overflow detected ***: terminated
Aborted (core dumped)
```

FORTIFY_SOURCE replace `sprintf` bằng `__sprintf_chk` check size.

### Bài học

1 dòng fix: `sprintf` → `snprintf(buf, sizeof(buf), ...)`. ASan + FORTIFY_SOURCE bắt trong CI thường lệ.

## Bài 2: Integer overflow trong calloc

**Code gốc**:

```c
void* alloc_buffer(size_t count, size_t size) {
    size_t total = count * size;
    void *p = malloc(total);
    if (p == NULL) return NULL;
    memset(p, 0, total);
    return p;
}
```

### Phân tích

| Thuộc tính | Giá trị |
|---|---|
| **Bug class** | Integer overflow trong allocation |
| **CWE** | CWE-190 Integer Overflow + CWE-680 |
| **CVSS** | 9.8 Critical (RCE potential nếu attacker control count, size) |
| **Tool** | UBSan, CBMC --unsigned-overflow-check |

### Verify

**UBSan**:

```bash
clang -fsanitize=undefined,address bai2.c -o bai2
./bai2
```

UBSan bắt unsigned overflow runtime:

```
bai2.c:5:21: runtime error: unsigned integer overflow: 4294967296 * 8 cannot be represented in type 'size_t'
```

Wait, trên 64-bit thì `4294967296 * 8 = 34359738368` không overflow `size_t` (64-bit max ~`1.8e19`). UBSan **không bắt** vì không thực sự overflow.

Pattern này nguy hiểm trên **32-bit** (size_t = 4 byte) hoặc với operand lớn hơn:

```c
alloc_buffer(0x100000000ULL, 0x10);   // 0x10_00000000 trên 64-bit OK, nhưng
alloc_buffer(0xFFFFFFFFFFFFFFFFULL, 2);  // overflow guaranteed
```

**CBMC formal**:

```c
int main(void) {
    size_t count = nondet_size_t();
    size_t size = nondet_size_t();
    alloc_buffer(count, size);
    return 0;
}
```

```bash
cbmc harness.c bai2.c --unsigned-overflow-check
```

```
[alloc_buffer.overflow.1] line 5 arithmetic overflow on unsigned * in count * size: FAILURE
```

CBMC khám phá mọi `count * size` overflow.

**Fix chuẩn**: dùng `__builtin_mul_overflow`:

```c
void* alloc_buffer(size_t count, size_t size) {
    size_t total;
    if (__builtin_mul_overflow(count, size, &total)) return NULL;
    void *p = malloc(total);
    if (p == NULL) return NULL;
    memset(p, 0, total);
    return p;
}
```

Hoặc đơn giản dùng `calloc(count, size)` (POSIX guarantee overflow check):

```c
return calloc(count, size);
```

### Bài học

`calloc(n, s)` chuẩn POSIX bắt buộc check overflow. Dùng `calloc` thay vì `malloc(n * s)`. Custom allocator dùng `__builtin_mul_overflow`.

## Bài 3: Uninitialized variable

**Code gốc** (giả định, pattern phổ biến):

```c
int compute_total(int *items, int count) {
    int sum;
    for (int i = 0; i < count; i++) {
        sum += items[i];   // BUG: sum uninitialized
    }
    return sum;
}
```

### Phân tích

| Thuộc tính | Giá trị |
|---|---|
| **Bug class** | Uninitialized read |
| **CWE** | CWE-457 Use of Uninitialized Variable |
| **CVSS** | 4-7 Medium-High (depends on what data leaks) |
| **Tool** | MSan, CBMC, compiler -Wuninitialized |

### Verify

**Compiler warning**:

```bash
gcc -Wall -Wuninitialized bai3.c
```

```
bai3.c:5:9: warning: 'sum' is used uninitialized
```

Modern compiler bắt 95% case này.

**MemorySanitizer**:

```bash
clang -fsanitize=memory bai3.c -o bai3
./bai3
```

```
==12345==WARNING: MemorySanitizer: use-of-uninitialized-value
    #0 in compute_total bai3.c:5
```

MSan bắt mọi uninitialized read runtime, kể cả khi compiler không thấy (e.g., heap memory chưa init).

**CBMC**:

CBMC track "uninit" qua propagation. Symbolic value của uninit variable không constrain, bất kỳ assertion về `sum` đều fail.

### Fix

```c
int sum = 0;   // explicit init
```

Hoặc designated init:

```c
struct Config cfg = {0};   // tất cả field = 0
```

C++ initialize tự động cho object có constructor. C không, phải nhớ init thủ công.

### Bài học

Enable `-Wall -Wuninitialized` trong CI. MSan run trên test suite catch heap case. Mọi declaration nên đi kèm initialization (constraint coding style).

## Bài 4: Off-by-one trong loop

**Code gốc** (pattern):

```c
void fill_array(int *arr, int n) {
    for (int i = 0; i <= n; i++) {   // BUG: <= n, should be < n
        arr[i] = 0;
    }
}
```

### Phân tích

| Thuộc tính | Giá trị |
|---|---|
| **Bug class** | Off-by-one OOB |
| **CWE** | CWE-193 Off-by-one Error |
| **CVSS** | 7.5 High (memory corruption) |
| **Tool** | CBMC --bounds-check, ASan |

### Verify

**CBMC**:

```c
int main(void) {
    int arr[10];
    fill_array(arr, 10);
    return 0;
}
```

```bash
cbmc harness.c bai4.c --bounds-check
```

```
[fill_array.array_bounds.1] line 3 array `arr' upper bound: FAILURE
```

`i = 10` ghi `arr[10]`, out of bounds.

**ASan**: tương tự, bắt runtime.

### Fix

```c
for (int i = 0; i < n; i++)   // < thay vì <=
```

Pattern Loop "for i = 0 to n": **luôn dùng `<`, không `<=`**.

### Bài học

Off-by-one là 1 trong 3 bug "easy to write, hard to spot": tested 100 lần có thể hit, hoặc không hit. CBMC bắt exhaustively trong bound.

## Bài 5: Race condition đơn giản

**Code gốc** (pattern):

```c
#include <pthread.h>

int counter = 0;

void* worker(void *arg) {
    for (int i = 0; i < 1000; i++) counter++;
    return NULL;
}

int main(void) {
    pthread_t t[4];
    for (int i = 0; i < 4; i++) pthread_create(&t[i], NULL, worker, NULL);
    for (int i = 0; i < 4; i++) pthread_join(t[i], NULL);
    assert(counter == 4000);   // FAIL
    return 0;
}
```

### Phân tích

| Thuộc tính | Giá trị |
|---|---|
| **Bug class** | Data race |
| **CWE** | CWE-362 Concurrent Execution using Shared Resource |
| **CVSS** | Varies 4-9 (depends on consequence) |
| **Tool** | TSan, CBMC --pthread |

### Verify

**TSan**:

```bash
clang -fsanitize=thread -g bai5.c -o bai5
./bai5
```

```
WARNING: ThreadSanitizer: data race
  Write of size 4 at 0x... by thread T2:
    #0 worker bai5.c:7
  Previous write of size 4 at 0x... by thread T1:
    #0 worker bai5.c:7
```

TSan detect race ngay lần chạy đầu.

**CBMC**:

```bash
cbmc bai5.c --pthread --unwind 3
```

CBMC khám phá interleaving, bắt counter < 4000 schedule.

### Fix

```c
#include <stdatomic.h>
atomic_int counter = 0;

void* worker(void *arg) {
    for (int i = 0; i < 1000; i++) atomic_fetch_add(&counter, 1);
    return NULL;
}
```

### Bài học

TSan = first line of defense cho race. Run unit test với TSan trong CI. CBMC formal cho critical concurrent code.

## Bài 6: Use-after-free trong linked list

**Code gốc** (pattern):

```c
typedef struct Node { int val; struct Node *next; } Node;

void process_list(Node *head) {
    Node *curr = head;
    while (curr != NULL) {
        free(curr);
        curr = curr->next;   // BUG: UAF read
    }
}
```

### Phân tích

| Thuộc tính | Giá trị |
|---|---|
| **Bug class** | Use After Free |
| **CWE** | CWE-416 Use After Free |
| **CVSS** | 9.8 Critical (memory corruption → RCE) |
| **Tool** | ASan, CBMC --pointer-check |

### Verify

**ASan**:

```bash
clang -fsanitize=address bai6.c -o bai6
./bai6
```

```
==12345==ERROR: AddressSanitizer: heap-use-after-free
  READ of size 8 at 0x... thread T0
    #0 process_list bai6.c:7
```

ASan track free, bắt subsequent read.

**CBMC**:

CBMC track allocation, bắt UAF qua object_id và validity bit.

### Fix

```c
void process_list(Node *head) {
    Node *curr = head;
    while (curr != NULL) {
        Node *next = curr->next;   // save next BEFORE free
        free(curr);
        curr = next;
    }
}
```

### Bài học

Pattern "traverse and free": **lưu `next` trước khi `free` current**. Đây là idiom chuẩn cho linked list cleanup.

## Bài 7: Struct padding và alignment

**Code gốc** (từ exercise 7):

```c
struct Foo {
    char a;
    int b;
    char c;
};

int main(void) {
    printf("sizeof(struct Foo) = %zu\n", sizeof(struct Foo));
    return 0;
}
```

### Phân tích

Đây không phải bug, mà là **đặc tính ABI** của C: compiler chèn padding để align field.

**Layout trên x86-64**:

```
Offset 0: a (char, 1 byte)
Offset 1-3: PADDING (3 byte, để int align 4)
Offset 4-7: b (int, 4 byte)
Offset 8: c (char, 1 byte)
Offset 9-11: PADDING (3 byte, struct size align 4)
Total: 12 byte
```

`sizeof(struct Foo) = 12`, không phải `1+4+1 = 6`.

### Pitfall

Padding gây vấn đề khi:

1. **Network serialize**: send raw struct qua socket → padding gửi cả → leak memory data.
2. **Memcmp**: `memcmp(&foo1, &foo2, sizeof(foo))` compare padding cũng → false negative.
3. **Struct hash**: hash raw bytes → padding ảnh hưởng → cùng data, khác hash.

### Fix patterns

**Pattern 1: pack struct** (loại bỏ padding):

```c
struct __attribute__((packed)) Foo {
    char a;
    int b;
    char c;
};
sizeof = 6
```

Nhưng access unaligned int → slow trên x86, crash trên ARM strict.

**Pattern 2: reorder field theo size decreasing** (tự nhiên align):

```c
struct Foo {
    int b;       // 4 byte
    char a;      // 1 byte
    char c;      // 1 byte
    char pad[2]; // explicit pad
};
sizeof = 8
```

**Pattern 3: explicit serialize**:

```c
void serialize_foo(struct Foo *f, uint8_t *buf) {
    buf[0] = f->a;
    memcpy(buf + 1, &f->b, 4);
    buf[5] = f->c;
}
```

Đảm bảo wire format independent of compiler padding.

### Bài học

Struct layout có **padding implicit**. Network code, hash, memcmp phải aware. Tool `pahole` (Linux) print struct layout chi tiết.

## Bảng tóm tắt 7 bài

| Bài | Bug class | CWE | CVSS | Tool đề xuất |
|---|---|---|---|---|
| 1 | Buffer overflow | CWE-121 | 8.8 H | ASan, snprintf, FORTIFY |
| 2 | Integer overflow | CWE-190 | 9.8 C | UBSan, CBMC, `__builtin_mul_overflow` |
| 3 | Uninitialized | CWE-457 | 4-7 M-H | MSan, -Wuninitialized |
| 4 | Off-by-one | CWE-193 | 7.5 H | CBMC, ASan |
| 5 | Data race | CWE-362 | varies | TSan, CBMC --pthread |
| 6 | UAF | CWE-416 | 9.8 C | ASan, smart pointer |
| 7 | Padding ABI | (no CWE) | - | pahole, code review |

7 bài này = 7 CWE category quan trọng nhất cho C/C++.

## CI workflow tích hợp

Đề xuất `.github/workflows/security.yml` cho project C/C++:

```yaml
name: Security checks
on: [push, pull_request]

jobs:
  asan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: clang -fsanitize=address,undefined -g src/*.c -o test
      - run: ./test

  msan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: clang -fsanitize=memory -g src/*.c -o test
      - run: ./test

  tsan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: clang -fsanitize=thread -g src/*.c -o test
      - run: ./test

  cbmc:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt install cbmc
      - run: |
          for f in src/*_harness.c; do
            cbmc "$f" --bounds-check --pointer-check --signed-overflow-check
          done
```

4 job song song, chạy ~5 phút. Block PR nếu fail. Catch ~95% bug class trong 7 bài tập trên.

## Tóm tắt cụm 8 (Code Analysis)

Sau khi đọc **5 bài** trong cụm này, bạn đã review:

- **10 sample Cụm 1** (vulnerabilities catalog).
- **8 sample Cụm 2** (BMC encoding).
- **8 sample Cụm 3** (concurrency).
- **6 sample Cụm 4** (testing/fuzzing).
- **7 bài exercise** (CWE categorization).

Tổng cộng **39 code pattern** với analysis chi tiết, fix gợi ý, tool verification. Bạn giờ có:

1. **Vocabulary CWE/CVSS** cho công việc thực tế (CVE triage, security audit).
2. **Reflexes review code** với checklist 5-6 điểm.
3. **Knowledge tool stack**: CBMC, ASan, MSan, TSan, UBSan, libFuzzer, FORTIFY_SOURCE.
4. **CI integration blueprint** áp dụng được ngay.
5. **Pattern fix** cho mỗi class bug (RAII, smart pointer, snprintf, builtin_overflow).

Đây là **kỹ năng practical** quan trọng nhất sau khi đã có vocabulary từ Lec 1-7.

---

**Kết thúc Cụm 8 (Code Analysis).** Bạn đã hoàn thành toàn bộ curriculum: 7 cụm lý thuyết + 1 cụm phân tích code thực hành. Quay về [trang chính](/docs/intro) hoặc xem [Cross-reference](../resources/cross-reference) để điều hướng nâng cao.
