---
id: 03-vulnerabilities-catalog
title: 1.3 Catalog lỗ hổng phần mềm
sidebar_position: 3
description: Phân loại lỗ hổng theo implementation vs design, đi sâu buffer overflow, integer overflow, race condition với ví dụ C có giải thích từng dòng.
---

# 1.3 Catalog các lớp lỗ hổng phần mềm

> **Tóm tắt một dòng**: Lỗ hổng chia thành hai họ: **Implementation Vulnerability** (sai trong code) và **Design Vulnerability** (sai trong kiến trúc). Tài liệu tập trung họ đầu vì nó có thể tự động phát hiện được, đi sâu ba lớp kinh điển là buffer overflow, integer overflow và race condition.

## Vì sao phải phân loại lỗ hổng?

Nếu bạn vào trang [CVE Details](https://www.cvedetails.com) hoặc [NVD](https://nvd.nist.gov), bạn sẽ thấy hàng trăm nghìn lỗ hổng đã được công bố. Nếu cứ học thuộc lòng từng CVE, ta không bao giờ học hết. Vì thế, ngành an toàn phần mềm cần một cách **phân loại** giúp ta nhìn nhiều CVE khác nhau như những biến thể của một số ít **patterns** gốc.

Có hai trục phân loại thường dùng:

**Trục thứ nhất** chia theo **tầng phát sinh lỗi**: lỗi nằm trong code cụ thể (implementation) hay trong kiến trúc tổng thể (design). Trục này quan trọng với chúng ta vì nó quyết định **công cụ nào có thể phát hiện**: implementation bug thì static/dynamic analysis bắt được, design bug thì không.

**Trục thứ hai** chia theo **thuộc tính CIA bị vi phạm**, đã giới thiệu ở bài 1.2.

Trong bài này, ta đi sâu vào trục thứ nhất và mổ xẻ ba lớp implementation vulnerability kinh điển. Ba lớp đó được chọn vì chúng minh hoạ rõ nhất ba cơ chế "tràn ranh giới" khác nhau trong code: tràn ranh giới của bộ nhớ (buffer overflow), tràn ranh giới của dải số (integer overflow), tràn ranh giới của thời gian (race condition).

## Implementation vs Design

Để hiểu sự khác biệt, hãy lấy hai ví dụ song song.

Ví dụ implementation bug: hàm `strcpy(dst, src)` trong C không kiểm tra kích thước `dst`. Nếu `src` dài hơn không gian cấp phát cho `dst`, dữ liệu tràn ra ngoài, ghi đè vùng nhớ kế bên. Đây là lỗi **trong code cụ thể**. Khi ta sửa, ta chỉ cần đổi `strcpy` thành `strncpy` (kèm điều kiện) hoặc `snprintf`. Design tổng thể của chương trình không thay đổi.

Ví dụ design bug: một web app dùng **MD5 không kèm salt** để băm password trước khi lưu vào database. Code thực thi MD5 hoàn toàn đúng, không có off-by-one, không có buffer overflow. Nhưng kiến trúc sai: MD5 quá nhanh nên attacker có thể brute force, không có salt nên rainbow table attack hiệu quả. Để sửa, ta phải đổi sang `bcrypt` hoặc `argon2`, tức là **thay đổi kiến trúc** của hàm hash password. Việc đó thường kéo theo migration: viết lại bảng users, thiết lập policy đổi password cho user cũ.

Tóm tắt bằng bảng:

| Tiêu chí | Implementation Vulnerability | Design Vulnerability |
|---|---|---|
| Vị trí lỗi | Trong code cụ thể, design đúng | Trong kiến trúc, dù code đúng |
| Ví dụ | Buffer overflow trong `strcpy`, off-by-one | MD5 không salt cho password, thiếu rate limit |
| Cách phát hiện | Static/dynamic analysis tự động | Threat modelling, security review thủ công |
| Chi phí sửa | Thay vài dòng code | Thường phải refactor lớn, migration |

Cùng một bug có thể được phân loại khác nhau tuỳ ngữ cảnh. Ví dụ thiếu rate limit khi check OTP: nếu OTP là 6 số, attacker brute force 10^6 lần trong vài giây và đoán được. Bạn có thể gọi đây là implementation bug (thiếu `if (attempts > 5) ban`) hoặc design bug (thiếu rate limiting layer). Cả hai cách phân loại đều dẫn tới cách sửa khác nhau: implementation thì thêm `if`, design thì đặt một Redis-based rate limiter trước endpoint.

:::warning[Bài học thực tế]
Một sự thật khó chịu: **chỉ implementation bug mới tự động phát hiện được**. Một static analyser dù mạnh đến đâu cũng không "biết" rằng dùng MD5 cho password là sai, vì nó không có khái niệm "password phải khó brute force". Việc phát hiện design bug đòi hỏi con người và quy trình (threat model, security review, pen test). Vì thế, tài liệu này tập trung implementation: đây là phần **kỹ thuật có thể formalize**.
:::

## Buffer overflow

### Cơ chế

Trong C, một mảng không có thông tin về kích thước tại runtime. Khi bạn khai báo `char buf[16]`, compiler chỉ cấp phát 16 byte trên stack và lưu địa chỉ bắt đầu vào `buf`. Mọi truy cập `buf[i]` được dịch thành `*(buf + i)` mà không có kiểm tra `0 <= i < 16`. Hậu quả: nếu ta `buf[100] = 'A'`, chương trình ghi vào địa chỉ `buf + 100`, vị trí có thể là biến cục bộ khác, frame pointer, hay **return address** của hàm hiện tại.

Tại sao điều này nguy hiểm? Vì return address quyết định **chương trình nhảy đi đâu sau khi hàm kết thúc**. Nếu attacker kiểm soát được return address, attacker kiểm soát được luồng thực thi. Đây là cơ sở của hàng loạt kỹ thuật khai thác như shellcode injection, return-to-libc, return-oriented programming.

### Ví dụ kinh điển

Đoạn code dưới đây có chứa lỗ hổng buffer overflow rất rõ:

```c
#include <stdio.h>
#include <string.h>

void vulnerable(char *input) {
    char buf[16];
    strcpy(buf, input);
    printf("Hello %s\n", buf);
}

int main(int argc, char **argv) {
    if (argc > 1) vulnerable(argv[1]);
    return 0;
}
```

Ta đi qua từng dòng để hiểu vì sao đoạn này nguy hiểm.

Dòng `char buf[16]` cấp phát 16 byte trên stack của hàm `vulnerable`. Compiler đặt 16 byte này ngay sát frame của hàm gọi, nghĩa là rất gần với return address.

Dòng `strcpy(buf, input)` copy từ `input` sang `buf`. Vấn đề là `strcpy` không có argument "max length". Nó copy từng byte cho tới khi gặp `'\0'`. Nếu `input` dài đúng 15 ký tự kèm `'\0'`, mọi việc bình thường. Nếu `input` dài 16 ký tự, byte `'\0'` rơi ra ngoài `buf`, ghi đè byte đầu tiên của vùng nhớ kế bên. Nếu `input` dài 100 ký tự, 84 byte vượt quá `buf` ghi đè đủ thứ.

Dòng `printf("Hello %s\n", buf)` chỉ là decoy: bug đã xảy ra ở `strcpy`. Khi hàm `vulnerable` return, CPU pop return address từ stack. Nếu attacker đã đè return address bằng giá trị tuỳ chọn, CPU nhảy tới đó.

### Layout stack trước và sau overflow

Để hiểu trực quan, hãy hình dung stack frame của `vulnerable`:

```
TRƯỚC khi gọi vulnerable("AAA"):
+------------------+ địa chỉ cao
|  return addr     | <- nơi sẽ nhảy về sau khi vulnerable() return
+------------------+
|  saved RBP       |
+------------------+
|  buf[16]         | <- AAA\0 vừa khít
|                  |
+------------------+ địa chỉ thấp

SAU khi gọi vulnerable("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"):
+------------------+
|  0x41414141      | <- return addr bị ghi đè bằng 'A' (ASCII 0x41)
+------------------+
|  0x41414141      | <- saved RBP cũng bị đè
+------------------+
|  AAAAAAAAAAAAAAAA <- buf đầy
|  AAAAAAAAAAAAAAAA <- tràn xuống tiếp
+------------------+
```

Sau khi `vulnerable` thực hiện `ret`, CPU lấy giá trị tại đỉnh stack làm địa chỉ nhảy. Giá trị đó giờ là `0x41414141` (bốn byte 'A'). CPU nhảy tới địa chỉ đó, gây segfault, hoặc, nếu attacker tinh tế hơn, nhảy đúng tới shellcode họ đã chèn vào buffer.

### Vì sao bug này tồn tại tới ngày nay?

Bạn có thể hỏi: vấn đề đơn giản như vậy, sao C không sửa? Câu trả lời nằm ở triết lý của C: ngôn ngữ này được thiết kế để mỏng nhẹ, gần phần cứng, không có runtime check để giữ tốc độ. Việc kiểm tra bounds mỗi lần access mảng có thể giảm tốc độ 20-50%. Trong những năm 1970, khi CPU rất chậm, người ta chấp nhận đánh đổi.

Hệ quả là sau 50 năm, ngành phải xây hàng loạt **lớp phòng vệ** để bù đắp:

| Lớp phòng vệ | Phía nào? | Cách hoạt động |
|---|---|---|
| Bounds checking thủ công | Code | Dùng `strncpy`, `snprintf`, hoặc tự kiểm tra trước khi copy |
| Stack canary | Compiler | Chèn giá trị ngẫu nhiên trước return addr, check trước khi return |
| ASLR | OS | Randomize địa chỉ stack, heap, libraries để attacker không đoán được |
| DEP / NX | CPU + OS | Đánh dấu vùng data không thể thực thi |
| CFI (Control Flow Integrity) | Compiler + Runtime | Chỉ cho phép jump tới các đích đã định nghĩa lúc compile |
| Memory-safe languages | Language | Rust, Go, Java không cho raw pointer arithmetic |

Trong các lớp trên, **memory-safe language là giải pháp triệt để**. Microsoft công bố năm 2019 rằng 70% CVE của họ trong 12 năm qua là memory safety bug, và đó là lý do Microsoft chuyển dần Windows kernel sang Rust. Google công bố tương tự với Android.

:::tip[Phân biệt strcpy, strncpy, strlcpy]
Ba hàm tên giống nhau nhưng hành vi khác nhau, gây nhầm lẫn rất nhiều:

- `strcpy(dst, src)`: nguy hiểm, không bounds check. **Đừng dùng**.
- `strncpy(dst, src, n)`: copy tối đa `n` byte, nhưng **không tự thêm `\0`** nếu `src` dài hơn `n`. Sau đó nếu code dùng `dst` như C-string sẽ chạy quá vùng. **Bẫy ngầm**.
- `strlcpy(dst, src, n)`: BSD extension, copy tối đa `n-1` byte rồi thêm `\0`. **An toàn nhất** nhưng không có sẵn trên glibc.
- `snprintf(dst, n, "%s", src)`: an toàn, có sẵn ở mọi nơi. **Lựa chọn portable tốt nhất**.
:::

## Integer overflow

### Cơ chế

Số nguyên trên máy tính có dải giá trị hữu hạn. Khi tính toán cho kết quả vượt dải, kết quả "wrap-around":

| Kiểu | Dải | Hành vi khi tràn |
|---|---|---|
| `int8_t` (signed) | $-128 \ldots 127$ | $127 + 1 = -128$ |
| `uint8_t` (unsigned) | $0 \ldots 255$ | $255 + 1 = 0$ |
| `int32_t` | $-2^{31} \ldots 2^{31}-1$ | $2^{31}-1 + 1 = -2^{31}$ |
| `uint32_t` | $0 \ldots 2^{32}-1$ | $2^{32}-1 + 1 = 0$ |
| `size_t` (64-bit) | $0 \ldots 2^{64}-1$ | tương tự |

Một điểm tinh tế: trong chuẩn C, **signed integer overflow là Undefined Behavior**. Compiler được phép giả định không bao giờ xảy ra, dẫn tới tối ưu hoá có thể "biến mất" code check overflow. Còn **unsigned overflow** được định nghĩa rõ ràng là wrap-around. Trong thực tế, hầu hết bug integer overflow security xảy ra với `size_t` và `unsigned int`.

### Ví dụ nguy hiểm

```c
void copy_data(uint8_t *src, size_t src_len, uint8_t *dst, size_t dst_len) {
    size_t total = src_len + 8;
    if (total > dst_len) {
        printf("buffer too small\n");
        return;
    }
    memcpy(dst, src, src_len);
}
```

Hàm này nhận buffer source kèm độ dài, đích kèm độ dài, dự định copy thêm 8 byte header. Trông có vẻ an toàn vì có check `total > dst_len`. Nhưng hãy thử kịch bản attacker.

Attacker gửi `src_len = SIZE_MAX - 4`, tức gần $2^{64}$. Khi tính `total = src_len + 8`, kết quả wrap-around về một giá trị rất nhỏ (cụ thể là 3 hoặc 4 tuỳ kiến trúc). Check `total > dst_len` qua được dễ dàng vì giờ `total` chỉ bằng 3. Dòng `memcpy(dst, src, src_len)` sau đó chạy với `src_len = SIZE_MAX - 4`, copy gần $2^{64}$ byte. Bộ nhớ bị ghi đè khổng lồ, chương trình crash hoặc attacker kiểm soát.

### Phòng tránh

Cách đúng là **kiểm tra overflow trước khi cộng**:

```c
if (src_len > SIZE_MAX - 8) return;
size_t total = src_len + 8;
if (total > dst_len) return;
```

Hoặc dùng built-in của GCC/Clang để compiler tự tạo check:

```c
size_t total;
if (__builtin_add_overflow(src_len, 8, &total)) return;
if (total > dst_len) return;
```

Built-in này dịch thành một single instruction trên x86 (kiểm tra overflow flag), không tốn thêm hiệu năng đáng kể. Nó cũng cover được mọi kiểu integer, signed lẫn unsigned.

## Race condition

### Hai dạng race condition

Race condition xảy ra khi kết quả chương trình phụ thuộc vào **thứ tự thực thi** của nhiều thread hoặc nhiều process. Có hai dạng phổ biến mà sinh viên cần phân biệt.

**Data race** là khi hai thread truy cập cùng một biến chia sẻ, ít nhất một là write, mà không có cơ chế đồng bộ (mutex, atomic). Ví dụ kinh điển là counter:

```c
int counter = 0;
void* increment(void *arg) {
    for (int i = 0; i < 1000000; i++) counter++;
    return NULL;
}
```

Nếu chạy hai thread cùng `increment`, kết quả cuối thường **nhỏ hơn** 2000000. Lý do: `counter++` không atomic, thực ra là ba bước (load, add, store). Hai thread có thể load cùng một giá trị rồi store đè lên nhau. Đây là chủ đề lớn của Lecture 4.

**TOCTOU (Time Of Check, Time Of Use)** tinh tế hơn. Chương trình check một điều kiện, rồi dùng tài nguyên dựa trên giả định điều kiện vẫn đúng. Nhưng giữa hai bước đó, attacker thay đổi state, làm giả định sai.

### Ví dụ TOCTOU kinh điển

Đoạn code dưới đây là một trong những TOCTOU bug nổi tiếng nhất trong giáo trình:

```c
#include <unistd.h>
#include <stdio.h>

int main(int argc, char **argv) {
    const char *path = argv[1];

    if (access(path, R_OK) != 0) {
        printf("permission denied\n");
        return 1;
    }

    FILE *f = fopen(path, "r");
}
```

Kịch bản tấn công như sau. Giả sử chương trình này được cài đặt với quyền `setuid root`, nghĩa là chạy với quyền root nhưng có một số check để chỉ phục vụ user gọi nó. User thường không được đọc `/etc/shadow`, nhưng có quyền đọc file của họ trong `/tmp`.

Bước một: user tạo file `/tmp/myfile` thuộc về user, nội dung vô hại. User chạy chương trình với argument `/tmp/myfile`. Hàm `access()` check quyền của **real UID** (chính là UID của user), kết luận user có quyền đọc, trả về 0.

Bước hai: trong khoảng thời gian rất ngắn (microsecond) giữa `access` và `fopen`, attacker chạy nhanh:

```bash
rm /tmp/myfile && ln -s /etc/shadow /tmp/myfile
```

Bước ba: chương trình tiếp tục, gọi `fopen("/tmp/myfile", "r")`. Nhưng giờ `/tmp/myfile` là symlink trỏ tới `/etc/shadow`. `fopen` chạy với **effective UID** (root), mở thành công `/etc/shadow`, đọc nội dung. Chương trình in cho user. Toàn bộ password hash của hệ thống lộ.

### Phòng tránh

Cách triệt để là **không tách check và use**. Thay vì hỏi "tôi có quyền đọc path này không?" rồi mới mở, hãy mở ngay rồi check trên file descriptor:

```c
int fd = open(path, O_RDONLY | O_NOFOLLOW);
if (fd < 0) {
    perror("open failed");
    return 1;
}
struct stat st;
if (fstat(fd, &st) != 0) { close(fd); return 1; }
if (st.st_uid != getuid()) {
    fprintf(stderr, "not your file\n");
    close(fd);
    return 1;
}
```

Hai thay đổi quan trọng. Một là `O_NOFOLLOW` báo `open` không follow symlink, attack qua `ln -s` không còn hoạt động. Hai là check uid qua `fstat(fd, ...)` trên file descriptor đã mở, không phải qua `stat(path, ...)` (vốn vẫn TOCTOU vì path có thể đã đổi). File descriptor đã mở thì gắn vĩnh viễn vào inode đó, attacker không thể "swap" nữa.

## Bảng so sánh ba lớp lỗ hổng

Để tổng kết, đây là bức tranh chung của ba lớp implementation vulnerability vừa học:

| Tiêu chí | Buffer overflow | Integer overflow | Race condition |
|---|---|---|---|
| Nguyên nhân gốc | Thiếu bounds check khi truy cập mảng | Wrap-around của arithmetic | Thiếu sync giữa thread/process |
| Khó phát hiện bằng test? | Trung bình (fuzzing tốt) | Khó (cần input rất lớn) | Rất khó (timing-dependent) |
| Phát hiện bằng BMC? | Tốt (CBMC, ESBMC có check sẵn) | Tốt (overflow check built-in) | Cần model concurrency, xem Lecture 4 |
| Phòng bằng compiler? | Stack canary, ASLR, FORTIFY_SOURCE | `-ftrapv`, `__builtin_*_overflow` | Hạn chế (ThreadSanitizer ở runtime) |
| Phòng bằng language? | Rust, Go, Java | Rust với `checked_add` | Rust ownership, Go race detector |

Nhìn vào bảng này, bạn sẽ thấy một mô hình: **các bug càng phụ thuộc thời gian thì càng khó phát hiện tự động**. Buffer overflow độc lập với thời gian nên fuzzer dễ tìm. Integer overflow cần input đặc biệt nhưng cũng độc lập thời gian. Race condition vừa cần input đặc biệt vừa cần lịch trình thread đặc biệt, dẫn tới combinatorial explosion. Đây chính là lý do Lecture 4 phải dùng các kỹ thuật riêng như context-bounded analysis.

## Mini-quiz

<details>
<summary>Q1. Stack canary chống được loại tấn công nào của buffer overflow và không chống được loại nào?</summary>

**Chống được**: stack-based buffer overflow đè lên return address. Cơ chế: compiler chèn một giá trị ngẫu nhiên (canary) giữa local variables và saved return address. Trước khi `ret`, hàm kiểm tra canary còn nguyên hay không. Nếu attacker ghi tràn buffer, canary bị đè, check fail, chương trình abort.

**Không chống được**:
- **Heap overflow**: canary chỉ có trên stack.
- **Đọc tràn** (như Heartbleed): canary chỉ kiểm tra ghi đè, không ngăn đọc.
- **Format string attack** đè precise vị trí (có thể skip canary nếu attacker biết offset).
- **Return-oriented programming** sau khi đã có một lỗ hổng khác để leak canary.
</details>

<details>
<summary>Q2. Vì sao `strncpy(dst, src, sizeof dst)` vẫn không an toàn?</summary>

`strncpy` có hai vấn đề ngầm. Một là nếu `src` dài hơn `n`, hàm không tự thêm `'\0'`, dẫn tới `dst` không phải C-string hợp lệ. Code sau đó dùng `dst` với `printf("%s", dst)` hoặc `strlen(dst)` sẽ đọc tràn ra ngoài `dst`. Hai là nếu `src` ngắn hơn `n`, `strncpy` tự pad `'\0'` lên hết `n` byte, gây lãng phí hiệu năng với buffer lớn.

Cách an toàn:

```c
strncpy(dst, src, sizeof dst - 1);
dst[sizeof dst - 1] = '\0';
```

Hoặc dùng `snprintf`:

```c
snprintf(dst, sizeof dst, "%s", src);
```

`snprintf` tự đảm bảo null-terminate, portable, dễ đọc, được khuyến nghị trong CERT C Coding Standard.
</details>

<details>
<summary>Q3. Vì sao race condition khó phát hiện hơn buffer overflow?</summary>

Race condition phụ thuộc vào **interleaving** của các thread, một chiều phụ thuộc mà testing thông thường không kiểm soát được. Một test case có thể chạy đúng hàng nghìn lần rồi mới fail trong một thread schedule đặc biệt (ví dụ OS chuyển thread đúng giữa hai instruction nhạy cảm). Trong khi đó, buffer overflow chỉ phụ thuộc input, một input cố định sẽ luôn cho cùng kết quả.

Đây là lý do Lecture 4 dành toàn bộ cho concurrency verification: cần các kỹ thuật riêng như **context-bounded analysis** (giới hạn số lần chuyển thread) và **partial-order reduction** (loại bớt các interleaving tương đương) để khám phá không gian schedule một cách có hệ thống.
</details>

---

**Tiếp theo**: [1.4 Web vulnerabilities (SQLi, XSS, XXE, DoS)](./04-web-vulnerabilities)
