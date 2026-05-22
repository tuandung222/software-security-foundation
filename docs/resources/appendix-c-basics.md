---
id: appendix-c-basics
title: Phụ lục - C basics cho người không quen
sidebar_position: 4
description: "Phụ lục giải thích C cơ bản (pointer, stack, heap, malloc, UB) vừa đủ để đọc hiểu các ví dụ trong tài liệu mà không cần background lập trình hệ thống."
---

# Phụ lục: C basics cho người không quen

> **Tóm tắt một dòng**: Phụ lục này giải thích các khái niệm C cốt lõi (pointer, stack, heap, malloc, undefined behavior) vừa đủ để bạn đọc hiểu mọi ví dụ trong tài liệu. Không nhằm dạy C đầy đủ, chỉ là "C minimum viable" cho người làm Data Science, ML hoặc web/backend dùng ngôn ngữ cao hơn.

## Vì sao tài liệu này dùng nhiều C?

Hầu hết ví dụ về vulnerability trong tài liệu viết bằng C. Lý do:

1. **C là ngôn ngữ của system**: kernel, driver, embedded, crypto library (OpenSSL, libsodium) đều viết C.
2. **C để lộ rõ memory**: pointer, malloc, free là first-class concept. Memory bug "hiển nhiên" trong C, ẩn trong Python/Java.
3. **BMC tool target C**: CBMC, ESBMC chủ yếu cho C/C++. Verify code C là use case phổ biến nhất.
4. **70% CVE là memory bug**: và memory bug phần lớn là C/C++. Hiểu C giúp hiểu cause của vast majority of security CVE.

Nếu background của bạn là Python, JavaScript, hay Java, một số khái niệm C có thể lạ. Phụ lục này lấp gap đó.

## 1. Variable và Type

C có **strict typing**: mỗi biến có kiểu cố định, size cố định.

```c
int x = 5;          // int (32-bit thường)
long y = 100;       // long (64-bit trên x86-64)
char c = 'A';       // char (8-bit, ASCII)
float f = 3.14;     // float (32-bit, IEEE 754)
double d = 3.14;    // double (64-bit, IEEE 754)
unsigned int u = 100;  // unsigned (không âm)
```

Khác Python: Python `int` có precision arbitrary, không overflow. C `int` có wrap-around (đã thấy chi tiết ở [bài 1.3](../01-introduction/03-vulnerabilities-catalog)).

```c
int x = 2147483647;  // INT_MAX
x = x + 1;            // x = -2147483648 (wrap), UB trong C standard
```

## 2. Pointer

Pointer là biến **chứa địa chỉ** của một biến khác.

```c
int x = 42;
int *p = &x;     // p chứa địa chỉ của x

printf("%d\n", *p);   // 42 (dereference: đọc giá trị tại địa chỉ)
*p = 100;             // ghi vào địa chỉ, làm x = 100
printf("%d\n", x);    // 100
```

Hai phép toán:

- `&x`: lấy địa chỉ của `x`.
- `*p`: dereference, đọc/ghi giá trị tại địa chỉ trong `p`.

Phép loại suy: nếu `x` là một ngôi nhà, `&x` là địa chỉ ghi trên giấy, `p` là một mảnh giấy có địa chỉ. `*p` là người ở trong ngôi nhà có địa chỉ đó.

### Pointer arithmetic

```c
int arr[5] = {10, 20, 30, 40, 50};
int *p = arr;     // p trỏ tới arr[0]

printf("%d\n", *p);       // 10
printf("%d\n", *(p+1));   // 20 (p+1 = arr[1])
printf("%d\n", *(p+2));   // 30
```

`p+1` không phải `p` + 1 byte, mà `p` + `sizeof(int)` byte (4 byte trên hầu hết platform). Compiler tự nhân theo size của type.

`arr[i]` là syntactic sugar cho `*(arr+i)`. Hai cách viết tương đương.

### NULL pointer

```c
int *p = NULL;   // p không trỏ gì cả

if (p != NULL) {
    *p = 5;      // an toàn, không dereference NULL
}
```

Dereference NULL pointer là **Undefined Behavior**. Trên hầu hết OS, crash với segfault. Trong an toàn-critical, không crash, mà có thể behavior không xác định.

## 3. Stack vs Heap

Memory của một chương trình C có nhiều "vùng":

| Vùng | Nội dung | Lifetime |
|---|---|---|
| **Text** | Code (instruction) | Toàn chương trình |
| **Data** | Biến global, static có initial value | Toàn chương trình |
| **BSS** | Biến global, static chưa init (zero) | Toàn chương trình |
| **Heap** | `malloc()` allocate | Từ malloc đến free |
| **Stack** | Biến local, parameter, return address | Từ enter function đến exit |

### Stack

Mỗi function call tạo một **stack frame** chứa:
- Local variable.
- Parameter.
- Return address (đi đâu sau function exit).
- Saved register.

Stack tự động "pop" khi function return. Local variable mất.

```c
void f() {
    int x = 5;       // x trên stack của f
    int arr[10];     // arr trên stack
    // ...
    // f return: stack pop, x và arr "biến mất"
}
```

Không cần `free()` cho stack variable. Tự động.

**Bug điển hình**: return pointer tới stack variable.

```c
int* bad() {
    int x = 5;
    return &x;   // BUG: x bị destroy khi return, pointer dangling
}

int main() {
    int *p = bad();
    printf("%d\n", *p);   // UB, p trỏ tới stack vùng đã destroy
}
```

### Heap

Heap dùng cho dữ liệu cần lifetime lâu hơn function.

```c
int* good() {
    int *p = malloc(sizeof(int));   // allocate 4 byte trên heap
    *p = 5;
    return p;   // OK, p trỏ tới heap, lifetime kéo dài
}

int main() {
    int *p = good();
    printf("%d\n", *p);   // 5
    free(p);              // bắt buộc free để return memory
}
```

Quy tắc: mỗi `malloc` phải có một `free` tương ứng. Quên `free` = **memory leak**.

## 4. Array và String

C không có "string type". String chỉ là array of `char` kết thúc bằng `'\0'` (null byte).

```c
char s[] = "hello";   // 6 byte: 'h', 'e', 'l', 'l', 'o', '\0'
```

Khi function nhận string, thực ra nhận **pointer** tới byte đầu tiên:

```c
void print(char *s) {
    while (*s != '\0') {
        putchar(*s);
        s++;
    }
}
```

Function `print` duyệt từng byte tới khi gặp `'\0'`. Đây là cách hầu hết string function (`strlen`, `strcpy`) hoạt động.

### Bug điển hình: thiếu null terminator

```c
char buf[5] = {'h', 'e', 'l', 'l', 'o'};   // KHÔNG có '\0'
printf("%s\n", buf);   // UB: printf đọc tràn ra ngoài buf
```

`buf` chỉ có 5 byte, không có null. `printf("%s")` đọc tới khi gặp `'\0'`, có thể đọc 100 byte sau buf, in ra random data hoặc crash.

Quy tắc: string trong C luôn cần có `'\0'` cuối.

## 5. `strcpy`, `strncpy`, `snprintf`: ba hàm hay nhầm

Đã thấy ở [bài 1.3](../01-introduction/03-vulnerabilities-catalog), nhắc lại:

**`strcpy(dst, src)`**: copy đến khi gặp `'\0'`, không check size. Dễ overflow.

```c
char dst[5];
strcpy(dst, "hello world");   // ghi 12 byte vào dst 5 byte, BUFFER OVERFLOW
```

**`strncpy(dst, src, n)`**: copy tối đa n byte. Nhưng **không tự thêm `'\0'`** nếu src dài hơn n.

```c
char dst[5];
strncpy(dst, "hello world", 5);   // dst = "hello", không có '\0'
printf("%s", dst);   // UB: đọc tràn
```

**`snprintf(dst, n, "%s", src)`**: an toàn. Copy tối đa n-1 byte, tự thêm `'\0'`.

```c
char dst[5];
snprintf(dst, sizeof(dst), "%s", "hello world");
printf("%s\n", dst);   // "hell" (4 byte + '\0')
```

Recommend: **luôn dùng snprintf** thay strcpy/strncpy.

## 6. Undefined Behavior (UB)

UB là một concept rất quan trọng và rất nguy hiểm trong C. **UB nghĩa là chuẩn C không định nghĩa hành vi của chương trình**. Compiler được phép làm gì cũng được.

Các nguồn UB phổ biến:

| Pattern | Vì sao UB |
|---|---|
| Signed integer overflow (`INT_MAX + 1`) | Standard không định nghĩa |
| Dereference NULL pointer | Standard không định nghĩa |
| Use after free | Standard không định nghĩa |
| Out-of-bounds array access | Standard không định nghĩa |
| Use of uninitialized variable | Standard không định nghĩa |
| Modification of string literal | Standard không định nghĩa |
| Sequence point violation (`i = i++`) | Standard không định nghĩa |

Hậu quả UB:

- **"Có vẻ work"**: trên 1 compiler, 1 OS, 1 day. Đổi sang compiler khác, crash.
- **Crash**: lý tưởng vì developer phát hiện ngay.
- **Silent corruption**: program tiếp tục chạy nhưng kết quả sai. Bug ẩn lâu.
- **Time-travel UB**: compiler thấy code phải có UB (vd `*NULL`), assume "code này không bao giờ chạy", **xoá bỏ branch**. Behavior không thể đoán trước.

Ví dụ time-travel UB:

```c
int *p = NULL;
if (cond) {
    *p = 5;   // UB nếu cond true
}
printf("hello\n");
```

Compiler có thể reason: "nếu cond true, code này UB. UB không thể xảy ra. Vậy cond luôn false." Compiler **xoá** `if (cond)` khỏi binary. `printf` luôn chạy. Nhưng nếu intent của developer là chỉ printf khi cond false, behavior mới không khớp.

Bài học: **tránh UB bằng mọi giá**. Tool ESBMC, CBMC bắt được hầu hết UB. Compiler flag `-fsanitize=undefined` (UBSan) bắt UB runtime.

## 7. Common Memory Bug

### Buffer overflow

Đã thấy. Ghi quá biên buffer.

```c
char buf[10];
strcpy(buf, "this is way too long");   // overflow
```

### Use after free

Dùng pointer sau khi free.

```c
int *p = malloc(sizeof(int));
*p = 5;
free(p);
*p = 10;   // use after free
```

### Double free

Free 2 lần cùng pointer.

```c
int *p = malloc(sizeof(int));
free(p);
free(p);   // double free, crash hoặc heap corruption
```

### Memory leak

Quên free.

```c
int *p = malloc(sizeof(int));
*p = 5;
return;   // forgot free(p), leak
```

### Uninitialized variable

```c
int x;       // uninitialized, value undefined
if (x > 0) { ... }   // UB
```

### Off-by-one

```c
char buf[10];
for (int i = 0; i <= 10; i++) {   // <= chứ không phải <, ghi đè byte 10
    buf[i] = '\0';
}
```

### Format string

```c
char user_input[100];
fgets(user_input, 100, stdin);
printf(user_input);   // BUG: user input là format string
```

User nhập `%s%s%s%s%s%s%s`, printf đọc 7 pointer từ stack, dereference, crash. Hoặc `%n` ghi vào memory tuỳ ý.

Fix: `printf("%s", user_input)`.

## 8. Tools để bắt bug C

**Compiler warning**: `-Wall -Wextra -Werror` bật mọi warning, treat as error.

**Sanitizer** (clang/gcc):
- **AddressSanitizer (ASan)**: bắt buffer overflow, use after free.
- **MemorySanitizer (MSan)**: bắt uninitialized variable use.
- **UndefinedBehaviorSanitizer (UBSan)**: bắt signed overflow, null deref, ...
- **ThreadSanitizer (TSan)**: bắt data race.

Bật khi build debug:
```bash
gcc -fsanitize=address,undefined -g program.c
```

**Static analyzer**: Clang Static Analyzer, Coverity, Infer.

**BMC**: CBMC, ESBMC (đã học chi tiết trong tài liệu).

**Fuzzer**: AFL, libFuzzer (đã học chi tiết).

## 9. Modern alternative: Rust

Vì C có quá nhiều UB, modern alternative đang nổi:

**Rust**: ngôn ngữ memory-safe bằng compile-time check (borrow checker). Zero-cost abstraction, gần performance của C, nhưng không có UB của memory.

Microsoft đang chuyển Windows kernel sang Rust. Linux kernel đã accept Rust driver.

Nếu start project mới có thể chọn ngôn ngữ, Rust thường tốt hơn C cho security-critical code.

## Tóm tắt

- **Variable**: typed, fixed size, có overflow.
- **Pointer**: chứa địa chỉ, `&x` để lấy, `*p` để dereference.
- **Stack** cho local var, auto destroy. **Heap** cho `malloc`/`free`.
- **String** là char array kết thúc `'\0'`.
- **snprintf** > strcpy/strncpy.
- **Undefined Behavior** (UB): tránh bằng mọi giá, compiler có thể làm bất ngờ.
- **Memory bug**: overflow, UAF, double free, leak, uninitialized, off-by-one, format string.
- **Tools**: -Wall, sanitizer, static analyzer, BMC, fuzzer.
- **Modern alternative**: Rust safer hơn C.

Sau khi đọc phụ lục này, bạn nên hiểu mọi ví dụ C trong tài liệu. Nếu vẫn lạ, đọc thêm: K&R "The C Programming Language" hoặc "Modern C" by Jens Gustedt.
