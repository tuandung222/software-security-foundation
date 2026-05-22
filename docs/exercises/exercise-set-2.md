---
id: exercise-set-2
title: "Bộ 2: Phân tích code C tìm bug"
sidebar_position: 2
description: "Bộ 7 bài tập phân tích code C, mỗi bài có code, câu hỏi, và đáp án chi tiết. Cover buffer overflow, integer overflow, race condition, uninitialized variable, alignment."
---

# Bộ bài tập 2: Phân tích code C tìm bug

> **Hướng dẫn**: với mỗi đoạn code dưới đây, đọc kỹ rồi trả lời: chương trình có đúng không? Nếu sai, chỉ rõ chỗ sai và giải thích cơ chế. Lời giải nằm trong thẻ `<details>` để bạn tự suy nghĩ trước khi xem.

Mọi bài giả định:
- Compile với `gcc -O0 -m64` trên x86-64 Linux.
- `int` = 32-bit, `long` = 64-bit, `size_t` = 64-bit.
- `sizeof(int) = 4`, `sizeof(int*) = 8`, `sizeof(long) = 8`.

## Bài 1

```c
#include <string.h>

void greet(char *name) {
    char buf[16];
    sprintf(buf, "Hello, %s!", name);
    printf("%s\n", buf);
}

int main(int argc, char **argv) {
    if (argc > 1) {
        greet(argv[1]);
    }
    return 0;
}
```

Chương trình có đúng không? Nếu sai, giải thích.

<details>
<summary>Đáp án</summary>

**Sai. Có buffer overflow.**

`buf` chỉ 16 byte. `sprintf` ghi `"Hello, " + name + "!" + '\0'` = `8 + strlen(name) + 1 + 1` = `10 + strlen(name)` byte.

Nếu `name` dài > 6 ký tự, total > 16, overflow.

Ví dụ: chạy với `./program "tuandungtuandungtuandung"`. `name` dài 24 byte. `sprintf` ghi 34 byte vào `buf` 16 byte. 18 byte tràn ra ngoài stack frame, có thể đè saved return address.

**Cơ chế**:
- `sprintf` không có size check.
- Stack layout: `[buf 16 byte][saved RBP][return address]`. Overflow đè saved RBP rồi return address.
- Attacker control `name`, control return address, control luồng thực thi.

**Fix**:

```c
void greet(char *name) {
    char buf[16];
    snprintf(buf, sizeof(buf), "Hello, %s!", name);
    printf("%s\n", buf);
}
```

`snprintf` tự truncate nếu output dài quá. Không overflow.

**Mở rộng**: `snprintf` return số byte muốn ghi (kể cả khi truncate). Nếu cần check truncate:

```c
int n = snprintf(buf, sizeof(buf), "Hello, %s!", name);
if (n >= sizeof(buf)) {
    // truncated, handle accordingly
}
```
</details>

---

## Bài 2

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void* alloc_buffer(size_t count, size_t size) {
    size_t total = count * size;
    void *p = malloc(total);
    if (p == NULL) {
        return NULL;
    }
    memset(p, 0, total);
    return p;
}

int main() {
    void *p = alloc_buffer(0x100000000, 8);   // 4 tỷ * 8
    if (p) printf("allocated\n");
    free(p);
    return 0;
}
```

Có bug gì?

<details>
<summary>Đáp án</summary>

**Sai. Integer overflow trong tính `total`.**

`count = 0x100000000 = 2^32`, `size = 8`. `count * size = 2^32 * 8 = 2^35`.

Trên 64-bit, `size_t` là 64-bit, có thể chứa $2^{35}$. **Không có overflow trên platform này.**

Tuy nhiên, code có vấn đề khác: nếu platform là 32-bit (`size_t` = 32-bit), `2^35` không fit trong `size_t`, wrap về một số nhỏ hơn. `malloc` allocate ít hơn yêu cầu. `memset` ghi `total` byte nhưng `total` đã wrap → ghi đè memory ngoài buffer.

**Bug trên 32-bit**:
- `count * size = 2^35 mod 2^32 = 2^35 - 2^32 = 2^32 * 7 = 0`. Wait, $2^{35} = 8 \cdot 2^{32}$, mod $2^{32} = 0$. `total = 0`. `malloc(0)` return non-NULL với 0 byte. `memset(p, 0, 0)` không ghi gì. **Coincidentally safe.**

Lấy ví dụ khác: `count = 0x40000000`, `size = 16`. Total = $2^{30} \cdot 2^4 = 2^{34}$. Mod $2^{32} = 2^{34} - 2^{32} = 3 \cdot 2^{32} = $ 12884901888. Mod $2^{32} = $ 0.

Hmm. Ví dụ cụ thể: `count = 0x40000001`, `size = 4`. Total = $4 \cdot (2^{30} + 1) = 2^{32} + 4$. Mod $2^{32}$ = 4. `malloc(4)` cấp 4 byte. `memset(p, 0, 4)` ghi 4 byte. Nhưng caller tin tưởng có $\approx 4$GB. Sau đó nếu caller `arr[100]`, **truy cập out-of-bounds**.

**Fix**: check overflow trước multiplication:

```c
void* alloc_buffer(size_t count, size_t size) {
    if (size != 0 && count > SIZE_MAX / size) {
        return NULL;   // overflow detected
    }
    size_t total = count * size;
    void *p = malloc(total);
    if (p == NULL) {
        return NULL;
    }
    memset(p, 0, total);
    return p;
}
```

Hoặc dùng `calloc(count, size)` (libc đã handle overflow check).
</details>

---

## Bài 3

```c
#include <stdio.h>
#include <pthread.h>

int counter = 0;

void* worker(void *arg) {
    for (int i = 0; i < 100000; i++) {
        counter++;
    }
    return NULL;
}

int main() {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, worker, NULL);
    pthread_create(&t2, NULL, worker, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("%d\n", counter);
    return 0;
}
```

Kết quả in ra là bao nhiêu? Có đúng 200000 không? Vì sao?

<details>
<summary>Đáp án</summary>

**Không đúng 200000.** Có **data race** trên `counter`.

**Cơ chế**:

`counter++` không atomic. Compiler dịch thành 3 instruction:

```
1. LOAD counter -> reg
2. ADD reg, 1
3. STORE reg -> counter
```

Hai thread chạy song song có thể interleave:

```
Thread 1: LOAD counter -> reg1   (reg1 = 100)
Thread 2: LOAD counter -> reg2   (reg2 = 100)
Thread 1: ADD reg1, 1            (reg1 = 101)
Thread 1: STORE reg1 -> counter  (counter = 101)
Thread 2: ADD reg2, 1            (reg2 = 101)
Thread 2: STORE reg2 -> counter  (counter = 101)
```

Hai increment, counter tăng chỉ 1. Final value < 200000.

Trên máy tôi (Linux x86-64), chạy thường cho kết quả trong khoảng $[100000, 200000]$, hiếm khi đạt 200000.

**Thêm vào đó, code có Undefined Behavior** vì C11 standard nói "data race là UB". Compiler có quyền làm bất kỳ điều gì, kể cả optimize away increment.

**Fix 1: dùng mutex**:

```c
#include <pthread.h>

int counter = 0;
pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;

void* worker(void *arg) {
    for (int i = 0; i < 100000; i++) {
        pthread_mutex_lock(&m);
        counter++;
        pthread_mutex_unlock(&m);
    }
    return NULL;
}
```

Đúng nhưng chậm (lock overhead).

**Fix 2: dùng atomic**:

```c
#include <stdatomic.h>

_Atomic int counter = 0;

void* worker(void *arg) {
    for (int i = 0; i < 100000; i++) {
        atomic_fetch_add(&counter, 1);
    }
    return NULL;
}
```

Nhanh hơn mutex. CPU có atomic instruction (`LOCK XADD` trên x86).
</details>

---

## Bài 4

```c
#include <stdio.h>
#include <string.h>

char* get_message(int kind) {
    char buf[64];
    switch (kind) {
        case 1: strcpy(buf, "info"); break;
        case 2: strcpy(buf, "warning"); break;
        case 3: strcpy(buf, "error"); break;
        default: strcpy(buf, "unknown");
    }
    return buf;
}

int main() {
    char *msg = get_message(2);
    printf("%s\n", msg);
    return 0;
}
```

Có bug gì?

<details>
<summary>Đáp án</summary>

**Sai. Return pointer tới stack variable (dangling pointer).**

`buf` là local trên stack của `get_message`. Khi function return, stack frame pop, `buf` không còn valid. Pointer trả về (`buf`) trỏ tới vùng memory đã bị "free".

`printf("%s", msg)` đọc memory đã invalid. Có thể:
- In ra "warning" nếu memory chưa bị overwrite (lucky).
- In ra garbage nếu memory đã overwrite (more likely).
- Crash với segfault.

Đây là Undefined Behavior. **Behavior khác nhau tuỳ compiler, OS, optimization level.**

Với `-O0` (no optimization), thường print đúng "warning" vì stack chưa được reuse.

Với `-O2`, compiler có thể inline function, return value chứa garbage, behavior unpredictable.

**Fix 1: dùng static buffer**:

```c
char* get_message(int kind) {
    static char buf[64];   // static = lifetime toàn chương trình
    // ...
    return buf;
}
```

Nhược: không thread-safe (mọi call dùng cùng buffer).

**Fix 2: caller provide buffer**:

```c
void get_message(int kind, char *buf, size_t size) {
    switch (kind) {
        case 1: snprintf(buf, size, "info"); break;
        // ...
    }
}

int main() {
    char msg[64];
    get_message(2, msg, sizeof(msg));
    printf("%s\n", msg);
}
```

Thread-safe, caller control lifetime.

**Fix 3: return string literal**:

```c
const char* get_message(int kind) {
    switch (kind) {
        case 1: return "info";     // string literal, lifetime mãi mãi
        case 2: return "warning";
        case 3: return "error";
        default: return "unknown";
    }
}
```

Đơn giản, đúng. Nhưng có constraint không sửa được string trả về (read-only).

**Fix 4: malloc**:

```c
char* get_message(int kind) {
    char *buf = malloc(64);
    snprintf(buf, 64, "...");
    return buf;
}
// caller phải free(msg) sau khi dùng
```

Caller phải nhớ free. Memory leak nếu quên.

Recommend: Fix 3 (string literal) cho case này, đơn giản nhất.
</details>

---

## Bài 5

```c
#include <stdio.h>

void print_array(int *arr, size_t n) {
    for (size_t i = 0; i <= n; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}

int main() {
    int arr[5] = {10, 20, 30, 40, 50};
    print_array(arr, 5);
    return 0;
}
```

In ra cái gì? Có đúng `10 20 30 40 50` không?

<details>
<summary>Đáp án</summary>

**Sai. Off-by-one trong loop condition.**

Loop `for (size_t i = 0; i <= n; i++)` chạy với `i = 0, 1, 2, 3, 4, 5`. Sáu lần.

`arr[0]` tới `arr[4]` là valid (5 phần tử). `arr[5]` là **out-of-bounds access**.

`arr[5]` đọc memory ngoài array. Có thể:
- In ra random integer (memory chưa init).
- Đọc local variable khác trên stack (nếu compiler đặt arr cạnh int khác).
- Crash với segfault (hiếm cho stack array nhỏ, common cho heap).

Đây là Undefined Behavior. C standard không đảm bảo gì.

Trên máy tôi: in ra `10 20 30 40 50 5` (in 5 vì `n` được store cạnh `arr` trên stack, đọc được như int).

**Fix**: đổi `<=` thành `<`.

```c
for (size_t i = 0; i < n; i++) {
    printf("%d ", arr[i]);
}
```

**Bài học**: off-by-one là một trong những bug C phổ biến nhất. Quy tắc: dùng `<` với half-open interval `[0, n)`, dùng `<=` với closed interval `[0, n]` rất hiếm khi đúng.
</details>

---

## Bài 6

```c
#include <stdio.h>
#include <stdint.h>

struct Packet {
    uint8_t type;
    uint32_t length;
    uint8_t data[64];
};

int main() {
    struct Packet p;
    p.type = 0x01;
    p.length = 0xCAFEBABE;
    p.data[0] = 0xFF;

    uint8_t *raw = (uint8_t*) &p;
    printf("type at offset 0: 0x%02X\n", raw[0]);
    printf("length at offset 1: 0x%02X\n", raw[1]);
    printf("data[0] at offset 5: 0x%02X\n", raw[5]);
    printf("sizeof(struct Packet) = %zu\n", sizeof(struct Packet));

    return 0;
}
```

Output là gì? `sizeof(struct Packet)` là 1 + 4 + 64 = 69 không?

<details>
<summary>Đáp án</summary>

**Compiler pad struct để align field.** `sizeof` lớn hơn 69.

**Cơ chế alignment**:

Trên x86-64, `uint32_t` (4 byte) thường align 4-byte boundary. `uint8_t data[64]` align 1 byte.

Layout của `struct Packet`:

```
Offset 0:  uint8_t  type       (1 byte)
Offset 1:  PADDING  (3 byte)    <- để length align 4
Offset 4:  uint32_t length     (4 byte)
Offset 8:  uint8_t  data[64]   (64 byte)
Offset 72: kết thúc
```

`sizeof(struct Packet) = 72`, không phải 69. Có 3 byte padding giữa `type` và `length`.

**Hệ quả của bài**:

- `raw[0]` đúng là `type` = `0x01`.
- `raw[1]` là **byte đầu của padding**, không phải byte đầu của `length`. Padding chưa init, value undefined.
- `raw[5]` cũng không phải `data[0]`. `data[0]` ở offset 8, không 5.

**Output thực tế** (tuỳ compiler):
- `type at offset 0: 0x01` (đúng).
- `length at offset 1: 0x??` (random, vì là padding).
- `data[0] at offset 5: 0x??` (random, vì offset 5 là padding/length byte).

**Fix**: tránh dependency vào struct layout. Nếu cần serialize struct sang byte:

```c
// Pack struct (compiler-specific, GCC/Clang)
struct __attribute__((packed)) Packet {
    uint8_t type;
    uint32_t length;
    uint8_t data[64];
};
// Giờ sizeof = 69, không padding.
```

Hoặc serialize/deserialize bằng tay:

```c
void serialize(struct Packet *p, uint8_t *buf) {
    buf[0] = p->type;
    buf[1] = (p->length >> 24) & 0xFF;
    buf[2] = (p->length >> 16) & 0xFF;
    buf[3] = (p->length >> 8) & 0xFF;
    buf[4] = p->length & 0xFF;
    memcpy(buf + 5, p->data, 64);
}
```

**Bài học**: padding là source của nhiều bug:
- Network protocol parse: nếu sender pack, receiver không, mismatch.
- `memcmp(struct1, struct2)` không bằng nếu padding khác (init = uninit).
- Memory leak qua padding: sensitive data có thể trong padding bytes của struct, dump struct = leak.
</details>

---

## Bài 7

Câu hỏi trắc nghiệm: compiler có pad struct dưới đây không? Vì sao?

```c
struct A {
    uint32_t x;
    uint32_t y;
    uint32_t z;
};

struct B {
    uint8_t  c;
    uint8_t  d;
    uint16_t e;
};

struct C {
    uint64_t x;
    uint32_t y;
};
```

Tính `sizeof` cho mỗi struct.

<details>
<summary>Đáp án</summary>

**Struct A**: 3 field uint32_t, mỗi 4 byte, align 4 byte boundary. Không padding cần.

```
Offset 0: x (4)
Offset 4: y (4)
Offset 8: z (4)
sizeof = 12
```

**Struct B**: uint8_t (1) + uint8_t (1) + uint16_t (2). 

`uint16_t` align 2-byte boundary. Offset của `e`: phải là multiple của 2. Sau 2 byte uint8_t, offset = 2, đã align. Không padding.

```
Offset 0: c (1)
Offset 1: d (1)
Offset 2: e (2)
sizeof = 4
```

**Struct C**: uint64_t (8) + uint32_t (4).

`uint64_t x` align 8-byte boundary, ở offset 0. `uint32_t y` ở offset 8, align 4-byte boundary. OK.

Nhưng **sizeof phải là multiple của max alignment** của struct (để array of struct align đúng). Max alignment = 8 (uint64_t). 

Sau `y` (offset 12), cần pad đến offset 16 để total = 16, multiple của 8.

```
Offset 0: x (8)
Offset 8: y (4)
Offset 12: PADDING (4)
sizeof = 16
```

**Tổng kết**:
- `sizeof(struct A) = 12`.
- `sizeof(struct B) = 4`.
- `sizeof(struct C) = 16` (có 4 byte padding cuối).

**Bài học**: order field để minimize padding. `struct C` có thể tối ưu thành:

```c
struct C_opt {
    uint32_t y;   // offset 0
    // 4 byte padding để x align 8
    uint64_t x;   // offset 8
};
// sizeof = 16 (cùng, padding ở giữa thay vì cuối)
```

Hoặc nếu có 2 uint32:

```c
struct D {
    uint64_t x;
    uint32_t y;
    uint32_t z;
};
// sizeof = 16, không padding
```

Compiler **không tự reorder field** trong C (vì C standard yêu cầu field declaration order = memory order). Đây là khác biệt với Rust (compiler có thể reorder để minimize).
</details>

---

## Tổng kết

7 bài tập cover các bug C kinh điển:

1. **Buffer overflow** với sprintf không size check.
2. **Integer overflow** trong size calculation.
3. **Data race** trên biến chia sẻ.
4. **Dangling pointer** return stack address.
5. **Off-by-one** trong loop condition.
6. **Struct padding** ảnh hưởng layout.
7. **Alignment** quyết định sizeof.

Mỗi bug trong số này từng gây CVE trong code production. Hiểu được chúng là bước đầu để viết code C an toàn.

**Để thực hành tiếp**: download CBMC, viết test program nhỏ với bug tương tự, chạy CBMC với `--bounds-check --pointer-check --signed-overflow-check`. Xem CBMC bắt được bug không.

---

**Quay lại**: [Danh sách bài tập](/docs/exercises/)
