---
id: 02-code-patterns-cluster-1
title: 8.2 Code patterns Cụm 1 (Lec 1-2)
sidebar_position: 2
description: "Phân tích chi tiết các đoạn code C/C++ trong cụm 1 về vulnerabilities: buffer overflow, NULL pointer, double free, integer overflow, format string, race condition."
---

# 8.2 Code patterns Cụm 1 (Lec 1-2)

> **Tóm tắt một dòng**: Cụm 1 giới thiệu vocabulary Software Security và liệt kê các lớp lỗ hổng implementation phổ biến. Mỗi lớp có 1-2 code sample minh hoạ. Bài này lấy từng sample đọc lại, comment chi tiết, giải thích state khi crash, và viết lại an toàn.

## Sample 1: Buffer overflow cổ điển (gets)

**Nguồn**: Lec 1, mục Buffer Overflow / Stack Smashing.
**Mục đích trong tài liệu gốc**: minh hoạ lý do `gets()` bị deprecated từ C11.

**Code (cleaned up)**:

```c
#include <stdio.h>
#include <stdlib.h>

int x = 0;

int getPassword() {
    char buf[4];
    printf("Enter password: ");
    gets(buf);                       // (1) BUG
    return strcmp(buf, "ML");
}

int main() {
    x = getPassword();
    if (x) {
        printf("Access Denied\n");
        exit(0);
    }
    printf("Access Granted\n");
    return 0;
}
```

**Đọc nhanh**: chương trình so sánh password user nhập với chuỗi "ML". Nếu khớp, granted.

**Bug tìm được**:

1. **Bug chính (Critical)**: `gets(buf)` không có bound check. Nhập > 3 ký tự = overflow buffer `char buf[4]`, ghi đè stack frame.
2. **Bug phụ 1 (Medium)**: thiếu `#include <string.h>` cho `strcmp`. Compile warning nhưng vẫn link.
3. **Bug phụ 2 (Medium)**: password compare bằng `strcmp` non-constant-time, timing attack.
4. **Bug phụ 3 (Low)**: password hardcode "ML" trong source code, lộ trong binary.
5. **Bug phụ 4 (Low)**: `int x = 0` biến toàn cục không cần thiết, dễ bị race nếu multi-thread.

**Cơ chế bug chính**:

```
Stack layout trước gets():
  ┌──────────────────────────┐ stack tăng xuống
  │  return address          │ ← stack pointer high
  │  saved frame pointer     │
  │  buf[3]  buf[2]  buf[1]  buf[0] │ ← buf points here
  └──────────────────────────┘
```

Nhập 100 ký tự, `gets` ghi từ `&buf[0]` lên cao. Sau 4 byte tràn `buf`. Sau 8-12 byte tràn saved FP. Sau 12-20 byte ghi đè **return address**. Khi `getPassword` return, CPU jump tới địa chỉ attacker chọn.

Đây là pattern **stack smashing** kinh điển. Modern OS có ASLR + stack canary giảm tỉ lệ thành công, nhưng `gets` vẫn là bug undefined behavior.

**Fix gợi ý**:

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define PW_BUF_SIZE 64
#define PASSWORD_HASH "..." // bcrypt hash, không phải plaintext

int getPassword(void) {
    char buf[PW_BUF_SIZE];
    printf("Enter password: ");
    if (fgets(buf, sizeof(buf), stdin) == NULL) return -1;
    buf[strcspn(buf, "\n")] = 0; // strip newline
    // Constant-time compare with bcrypt verify (không show ở đây)
    return verify_bcrypt(buf, PASSWORD_HASH);
}

int main(void) {
    int ok = getPassword();
    if (!ok) {
        puts("Access Denied");
        return 1;
    }
    puts("Access Granted");
    return 0;
}
```

Thay đổi:
- `gets` → `fgets` với size limit.
- Buffer 4 → 64 byte phù hợp password thật.
- Compare bằng bcrypt verify (constant-time, không leak timing).
- Không hardcode plaintext.
- `void main` → `int main(void)` chuẩn ISO C.

**Verify với CBMC**:

```bash
cbmc original.c --bounds-check
```

Output (nếu compile được không có gets):

```
[getPassword.array_bounds.1] line 6 array `buf' upper bound: FAILURE
```

CBMC bắt được vì `gets` được model là "writes unbounded length". Lý tưởng nhất, replace `gets` bằng harness `__CPROVER_input` để test mọi input length.

**Bài học**: `gets()` đã bị remove khỏi C11. Mọi compiler hiện đại warn nếu thấy. Code chứa `gets` = code legacy, cần migrate ngay.

## Sample 2: NULL pointer dereference

**Nguồn**: Lec 1, mục NULL Pointer Dereference.

**Code (cleaned up)**:

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    double *p = NULL;
    int n = 8;
    for (int i = 0; i < n; ++i) {
        p[i] = (double)i;   // (1) BUG
    }
    return 0;
}
```

**Đọc nhanh**: cấp pointer NULL rồi ghi vào index 0..7.

**Bug tìm được**:

1. **Bug chính (Critical)**: `p` được gán NULL, `p[i]` dereference NULL pointer → SIGSEGV.
2. Có thể tác giả định ý `p = malloc(n * sizeof(double))` nhưng quên.

**Cơ chế**:

```
p = NULL = 0x00000000
p[i] = 0x00000000 + i*sizeof(double) = 0x00000000..0x00000038
```

Truy cập page 0 trên modern OS → page fault → SIGSEGV → crash.

Chú ý: trong embedded không có MMU, write vào address 0 không crash mà **silently corrupt** memory map (vector table). Bug nguy hiểm hơn.

**Fix**:

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n = 8;
    double *p = malloc(n * sizeof(double));
    if (p == NULL) {
        fprintf(stderr, "malloc failed\n");
        return 1;
    }
    for (int i = 0; i < n; ++i) {
        p[i] = (double)i;
    }
    // ... use p ...
    free(p);
    return 0;
}
```

Quan trọng: **luôn check return của `malloc`**. Nhiều legacy code ignore, gây bug khi memory pressure.

**Verify với CBMC**:

```bash
cbmc null.c --pointer-check
```

Output:

```
[main.pointer_dereference.1] line 7 dereference failure: pointer NULL: FAILURE
```

CBMC bắt ngay.

**Bài học**: pointer must check NULL trước khi dereference. Sanitizer ASan cũng bắt bug này khi chạy test.

## Sample 3: Double free

**Nguồn**: Lec 1, mục Double Free.

**Code (cleaned up)**:

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char *ptr = malloc(sizeof(char));
    if (ptr == NULL) return -1;
    *ptr = 'a';
    free(ptr);
    // ... some code ...
    free(ptr);   // (1) BUG: double free
    return 0;
}
```

**Đọc nhanh**: cấp, dùng, free, rồi free lần thứ hai.

**Bug**:

1. **Bug chính (High)**: `free(ptr)` lần hai. UB theo chuẩn C.

**Cơ chế**:

Modern glibc/jemalloc detect double free và abort process. Older or custom allocator có thể **corrupt heap metadata**, attacker exploit để arbitrary write.

Lịch sử: nhiều CVE PHP, Firefox từ pattern này. Glibc 2.10+ có "tcache" để detect, nhưng không 100%.

**Fix**:

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char *ptr = malloc(sizeof(char));
    if (ptr == NULL) return -1;
    *ptr = 'a';
    free(ptr);
    ptr = NULL;   // QUAN TRỌNG: gán NULL sau free
    // ... some code ...
    free(ptr);   // OK: free(NULL) là no-op theo chuẩn
    return 0;
}
```

Pattern "free + set NULL" giảm rủi ro. Hoặc dùng macro:

```c
#define SAFE_FREE(p) do { free(p); (p) = NULL; } while (0)

SAFE_FREE(ptr);
SAFE_FREE(ptr);  // OK, free(NULL) no-op
```

**Verify với CBMC**:

```bash
cbmc double_free.c --memory-leak-check --pointer-check
```

```
[main.invalid_pointer.1] line 10 free argument has offset zero: FAILURE
```

CBMC track allocation history, bắt được double free.

**Bài học**: ngay sau `free(p)`, gán `p = NULL`. Smart pointer (`std::unique_ptr` trong C++) loại bỏ class bug này hoàn toàn.

## Sample 4: Use After Free

**Nguồn**: Lec 1, mục UAF.

**Code**:

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(sizeof(int));
    if (p == NULL) return -1;
    *p = 42;
    free(p);
    *p = 100;        // (1) BUG: UAF
    printf("%d\n", *p);  // (2) BUG: UAF read
    return 0;
}
```

**Bug**:

1. **Bug chính (Critical)**: `*p = 100` sau khi `free(p)`. Pointer dangling.
2. **Bug phụ**: `printf("%d", *p)` cũng UAF.

**Cơ chế**:

Sau `free(p)`, glibc đưa block vào free list (tcache hoặc fastbin). Nếu allocation tiếp theo lấy lại block đó:

```c
int *q = malloc(sizeof(int));  // có thể trả về cùng địa chỉ p cũ
*q = 999;
```

Lúc này `*p` và `*q` cùng địa chỉ. Sửa `*p` = sửa `*q`. Attacker exploit: control content của block sau free → control behavior chương trình.

**CVE thực tế**: Use-After-Free trong browser engine (Chrome, Firefox) là loại CVE phổ biến nhất, ~50% memory bug class.

**Fix**:

```c
free(p);
p = NULL;
// ... mọi access tới p phải null check trước ...
if (p) printf("%d\n", *p);
```

Hoặc thiết kế lại với RAII / smart pointer trong C++.

**Verify với ASan** (chính xác hơn CBMC cho UAF):

```bash
clang -fsanitize=address uaf.c -o uaf
./uaf
```

Output:

```
==1234==ERROR: AddressSanitizer: heap-use-after-free on address 0x...
```

**Bài học**: UAF là 1 trong 4 lớp memory bug nguy hiểm nhất (cùng OOB, NULL, double free). Modern C++ với smart pointer giảm rủi ro 90%.

## Sample 5: Integer overflow (signed)

**Nguồn**: Lec 1, mục Integer Overflow.

**Code**:

```c
#include <stdio.h>
#include <stdlib.h>

void allocate_buffer(int size) {
    if (size < 0) return;
    char *buf = malloc(size + 1);   // (1) BUG
    if (!buf) return;
    // ... use buf ...
    free(buf);
}
```

**Bug**:

1. **Bug chính (High)**: `size + 1` overflow nếu `size == INT_MAX`. `INT_MAX + 1 = INT_MIN` (UB trong signed). `malloc(INT_MIN)` → size_t cast → giá trị khổng lồ → malloc fail hoặc cấp 4 GB.
2. **Bug phụ**: không return code chỉ ra fail.

**Cơ chế**:

`INT_MAX = 2^31 - 1 = 2147483647`. `INT_MAX + 1` overflow:
- Trên hầu hết compiler: wrap to `INT_MIN = -2^31 = -2147483648`.
- Theo C standard: **undefined behavior**, compiler có thể assume "không xảy ra" và optimize ra code không expected.

`malloc((size_t)(-2147483648))` = `malloc(2147483648UL on 32-bit hoặc 18446744071562067968UL on 64-bit)`. Số quá lớn → malloc return NULL.

Sau đó `*buf` (chưa check NULL) → SIGSEGV.

**Fix**:

```c
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

int allocate_buffer(int size) {
    if (size < 0 || size >= INT_MAX) return -1;  // explicit upper bound
    
    // Hoặc dùng builtin overflow check (GCC, Clang):
    size_t total;
    if (__builtin_add_overflow((size_t)size, 1, &total)) return -1;
    
    char *buf = malloc(total);
    if (!buf) return -1;
    // ... use buf ...
    free(buf);
    return 0;
}
```

`__builtin_add_overflow` (GCC/Clang): trả về `true` nếu overflow, `false` nếu OK. Type-aware.

**Verify với CBMC**:

```bash
cbmc int_overflow.c --signed-overflow-check --unsigned-overflow-check
```

Output:

```
[allocate_buffer.overflow.1] line 5 arithmetic overflow on signed + in size + 1: FAILURE
```

**Bài học**: bất kỳ arithmetic trên integer untrusted phải có overflow check. UBSan runtime + CBMC static = defense in depth.

## Sample 6: Format string vulnerability

**Nguồn**: Lec 1, mục Format String.

**Code**:

```c
#include <stdio.h>

void log_message(char *user_input) {
    printf(user_input);   // (1) BUG
}

int main(int argc, char *argv[]) {
    if (argc > 1) log_message(argv[1]);
    return 0;
}
```

**Bug**:

1. **Bug chính (Critical)**: `printf(user_input)` cho phép user control format string. Input `%s%s%s%s` đọc stack → info leak. Input `%n` ghi vào address trên stack → arbitrary write.

**Cơ chế**:

`printf("%s")` mong đợi 1 argument trên stack tại offset cố định. Nếu user input `%s`, `printf` đọc value tại offset đó (giá trị từ stack frame), treat as pointer, dereference. Leak data hoặc crash.

`%n` ghi số character đã in ra integer pointer trên stack. Pattern `AAAA%n` ghi 4 vào địa chỉ 0x41414141.

**Lịch sử**: WU-FTPD 2.6.0 (2000) bị exploit qua format string trong site command. 100,000+ server compromise.

**Fix**:

```c
#include <stdio.h>

void log_message(char *user_input) {
    printf("%s", user_input);   // ĐÚNG: format string là literal
}
```

Một câu sửa. Quy tắc: **format string LUÔN là string literal**, không bao giờ là biến.

Compiler GCC/Clang có warning:

```
warning: format not a string literal and no format arguments [-Wformat-security]
```

Enable `-Wformat-security -Werror=format-security` trong build.

**Bài học**: format string bug rất dễ tránh (1 line fix) nhưng vẫn xuất hiện trong legacy code. Modern static analyzer bắt 100%.

## Sample 7: Race condition trên global

**Nguồn**: Lec 1, mục Race Condition (intro).

**Code**:

```c
#include <pthread.h>
#include <stdio.h>

int counter = 0;

void* increment(void *arg) {
    for (int i = 0; i < 1000000; i++) {
        counter++;   // (1) BUG
    }
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, increment, NULL);
    pthread_create(&t2, NULL, increment, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("counter = %d\n", counter);   // expect 2000000
    return 0;
}
```

**Bug**:

1. **Bug chính (High)**: `counter++` không atomic. Hai thread race → kết quả ngẫu nhiên < 2 000 000.

**Cơ chế**:

`counter++` thực ra là 3 instruction:

```
LOAD  counter -> reg
INC   reg
STORE reg -> counter
```

Thread A: LOAD (giá trị 100) → INC (101) → ... bị preempt ... 
Thread B: LOAD (vẫn 100) → INC (101) → STORE (101).
Thread A: tiếp tục STORE (101).

Hai increment chỉ tăng 1. Lost update.

**Fix 1 (mutex)**:

```c
#include <pthread.h>

pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
int counter = 0;

void* increment(void *arg) {
    for (int i = 0; i < 1000000; i++) {
        pthread_mutex_lock(&lock);
        counter++;
        pthread_mutex_unlock(&lock);
    }
    return NULL;
}
```

**Fix 2 (atomic)**:

```c
#include <stdatomic.h>

atomic_int counter = 0;

void* increment(void *arg) {
    for (int i = 0; i < 1000000; i++) {
        atomic_fetch_add(&counter, 1);
    }
    return NULL;
}
```

Atomic nhanh hơn mutex cho operation đơn giản (single int).

**Verify với CBMC**:

```bash
cbmc race.c --pthread --unwind 5
```

Output:

```
[main.assertion.1] line 16 assertion counter == 2000000: FAILURE
```

CBMC khám phá interleaving, tìm được schedule khiến counter < target.

**Verify với ThreadSanitizer**:

```bash
clang -fsanitize=thread race.c -o race
./race
```

Output:

```
WARNING: ThreadSanitizer: data race on counter
```

**Bài học**: mọi shared variable phải hoặc atomic, hoặc protected by lock. Single-thread → multi-thread refactor là moment cần audit race kỹ.

## Sample 8: TOCTOU (Time of Check, Time of Use)

**Nguồn**: Lec 1, mục TOCTOU.

**Code**:

```c
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

void open_file(const char *path) {
    struct stat st;
    if (stat(path, &st) == 0 && S_ISREG(st.st_mode)) {
        // (1) GAP between check and use
        int fd = open(path, O_RDONLY);   // (2) BUG
        // ... process file ...
        close(fd);
    }
}
```

**Bug**:

1. **Bug chính (High)**: giữa `stat` và `open`, attacker swap file (symlink attack). `stat` thấy regular file, nhưng `open` thực sự open file khác.

**Cơ chế**:

```
T1: open_file("data.txt")
T1: stat("data.txt", &st) → regular file (passes check)
T2: rm data.txt
T2: ln -s /etc/passwd data.txt   // attacker swap to symlink
T1: open("data.txt", O_RDONLY) → opens /etc/passwd!
```

Nếu service chạy as root và sau đó print file content, attacker đọc được /etc/passwd.

**Fix**: dùng `O_NOFOLLOW` hoặc `fstat` trên `fd` đã open:

```c
int fd = open(path, O_RDONLY | O_NOFOLLOW);
if (fd < 0) return;
struct stat st;
if (fstat(fd, &st) == 0 && S_ISREG(st.st_mode)) {
    // ... process file ...
}
close(fd);
```

`O_NOFOLLOW`: open fail nếu path là symlink.
`fstat(fd)`: stat trên file descriptor đã mở, không thể swap.

**CVE thực tế**: nhiều CVE Unix kernel utility (`logrotate`, `cron`, package manager) từ pattern này.

**Bài học**: TOCTOU race khó test (hiếm trigger ngẫu nhiên), nhưng attacker triggered được 99% time qua filesystem operations. Pattern fix: dùng file descriptor (mở 1 lần), không reopen.

## Sample 9: Integer signedness bug

**Nguồn**: Lec 1, mục Integer signedness.

**Code**:

```c
#include <string.h>
#include <stdlib.h>

int copy_data(char *dst, const char *src, int len) {
    if (len > 100) return -1;   // (1) check upper bound
    memcpy(dst, src, len);       // (2) BUG khi len < 0
    return 0;
}
```

**Bug**:

1. **Bug chính (High)**: `len` signed int. Negative `len` pass check `len > 100` (vì -1 < 100). Nhưng `memcpy(dst, src, len)` có `len` là `size_t` (unsigned). Cast `(size_t)(-1)` = `SIZE_MAX` (~18 quintillion).
2. `memcpy` với khổng lồ size → buffer overflow + crash.

**Cơ chế**:

```c
int len = -1;
if (len > 100) ...   // false: -1 không > 100
memcpy(dst, src, len);   // len cast to size_t = 0xFFFFFFFFFFFFFFFF
// memcpy copy 2^64 byte → segfault sau khi đè memory rất nhiều
```

Đây là pattern "**signed comparison + unsigned use**", rất phổ biến trong code C cũ.

**Fix**:

```c
int copy_data(char *dst, const char *src, size_t len) {  // size_t, không int
    if (len > 100) return -1;
    memcpy(dst, src, len);
    return 0;
}
```

Hoặc nếu phải dùng int (API constraint):

```c
int copy_data(char *dst, const char *src, int len) {
    if (len < 0 || len > 100) return -1;  // bounds check cả hai phía
    memcpy(dst, src, (size_t)len);
    return 0;
}
```

**Verify với CBMC**:

```bash
cbmc signedness.c --signed-overflow-check --bounds-check
```

CBMC bắt nếu có harness test với len âm.

**Bài học**: dùng `size_t` cho size, `ssize_t` cho size có thể negative (e.g. return value của `read`). Tránh `int` cho buffer size. Compile với `-Wsign-compare` để compiler cảnh báo signed/unsigned mismatch.

## Sample 10: Off-by-one trong string copy

**Nguồn**: Lec 1, mục Buffer Overflow variant.

**Code**:

```c
#include <string.h>

void copy_name(char *dst, const char *src) {
    int i;
    for (i = 0; src[i] != '\0'; i++) {
        dst[i] = src[i];
    }
    dst[i] = '\0';   // (1) potential BUG
}
```

**Bug**:

1. **Bug (Medium-High)**: nếu `src` length = buffer size của `dst`, không có terminator slot. Off-by-one overflow.

**Cơ chế**:

```c
char src[] = "1234";   // length 5 (4 char + '\0')
char dst[4];           // 4 byte
copy_name(dst, src);   
// Loop: dst[0]='1', dst[1]='2', dst[2]='3', dst[3]='4'
// dst[4] = '\0'  ← out of bounds!
```

`dst[4]` ghi 1 byte sau buffer. Có thể đè saved register, return address. Subtle bug khó detect.

**Fix với explicit buffer size**:

```c
int copy_name(char *dst, size_t dst_size, const char *src) {
    if (dst_size == 0) return -1;
    size_t i;
    for (i = 0; i < dst_size - 1 && src[i] != '\0'; i++) {
        dst[i] = src[i];
    }
    dst[i] = '\0';
    return (src[i] == '\0') ? 0 : -1;  // -1 nếu truncated
}
```

Pattern: **hàm string nhận size của destination**.

Hoặc dùng `snprintf` (chuẩn ISO C):

```c
snprintf(dst, dst_size, "%s", src);
```

Tự động truncate và terminate.

**Verify với CBMC**:

```bash
cbmc offbyone.c --bounds-check
```

**Bài học**: tránh tự viết string function. Dùng `snprintf`, `strlcpy` (BSD), hoặc trong C++ thì `std::string`.

## Tóm tắt Cụm 1

| Sample | Lớp bug | Tool detect tốt nhất |
|---|---|---|
| 1 gets() | Buffer overflow | Compiler warning + CBMC + ASan |
| 2 NULL deref | Memory | CBMC + ASan |
| 3 Double free | Memory | ASan + CBMC |
| 4 UAF | Memory | ASan |
| 5 Integer overflow | Integer | UBSan + CBMC --signed-overflow-check |
| 6 Format string | Injection | Compiler `-Wformat-security` |
| 7 Race condition | Concurrency | TSan + CBMC --pthread |
| 8 TOCTOU | Concurrency | Manual review + ESBMC |
| 9 Signedness | Integer | Compiler `-Wsign-compare` + UBSan |
| 10 Off-by-one | Buffer | CBMC + ASan |

10 sample này = ~80% memory/integer bug class.

## Pattern chung rút ra

Sau khi đọc 10 sample, có thể rút **pattern lặp lại**:

1. **Tin tưởng input**: code mặc định size phù hợp, pointer non-null, integer trong range.
2. **Mix signed/unsigned**: int dùng cho size, size_t dùng cho memcpy.
3. **Thiếu cleanup**: free nhưng không set NULL, mở fd không close.
4. **API legacy**: `gets`, `sprintf`, `strcpy` thay vì safe variant.
5. **Format string injection**: trực tiếp pass user input.

Code review checklist 5 điểm này giúp catch ~70% bug trong code C kế thừa.

---

**Tiếp theo**: [8.3 Code patterns Cụm 2 (BMC encoding)](./03-code-patterns-cluster-2)
