---
id: 04-cbmc-tutorial
title: 7.4 CBMC Tutorial step-by-step
sidebar_position: 4
description: "Cài đặt CBMC, chạy trên ví dụ C đơn giản, đọc output, các flag quan trọng, debug counterexample, so sánh với ESBMC."
---

# 7.4 CBMC Tutorial step-by-step

> **Tóm tắt một dòng**: Bài này hướng dẫn thực hành CBMC (C Bounded Model Checker), tool BMC phổ biến nhất cho C/C++. Sau khi đọc, bạn sẽ tự cài, chạy CBMC trên code của mình, hiểu output, và biết các flag quan trọng nhất cho từng loại check.

## Vì sao thực hành CBMC?

Lec 3-4 dạy concept của BMC + SMT. Concept hay nhưng không thay thế được trải nghiệm thực tế chạy tool. CBMC là tool open-source, mature (từ 2001), được dùng trong production tại Amazon (AWS verify driver, networking code), Diffblue (gốc của tool), Microsoft.

Bài này không phải tutorial chính thức (đã có trên cprover.org), mà là **path nhanh** cho người đã biết concept để bắt tay làm.

## Bước 1: Cài đặt CBMC

### macOS (Homebrew)

```bash
brew install cbmc
cbmc --version
# Expected: CBMC version X.Y.Z 64-bit ...
```

### Linux (Ubuntu/Debian)

```bash
# Option 1: package từ repo (có thể cũ)
sudo apt update && sudo apt install cbmc

# Option 2: tải binary mới nhất từ GitHub release
wget https://github.com/diffblue/cbmc/releases/download/cbmc-5.95.1/ubuntu-22.04-cbmc-5.95.1-Linux.deb
sudo dpkg -i ubuntu-22.04-cbmc-5.95.1-Linux.deb
```

### Build from source (mọi OS)

```bash
git clone https://github.com/diffblue/cbmc.git
cd cbmc
make -C src minisat2-download
make -C src
# Binary tại src/cbmc/cbmc
```

Build cần GCC/Clang + Make. ~10-15 phút.

### Verify cài đặt

```bash
cbmc --help | head -20
```

Nếu thấy list option, OK.

## Bước 2: Hello World

Tạo file `hello.c`:

```c
#include <assert.h>

int main() {
    int x = 5;
    int y = 10;
    int z = x + y;
    assert(z == 15);
    return 0;
}
```

Chạy:

```bash
cbmc hello.c
```

Output (rút gọn):

```
CBMC version 5.95.1 (cbmc-5.95.1) 64-bit x86_64 macos
Parsing hello.c
Converting
Type-checking hello
Generating GOTO Program
Adding CPROVER library (x86_64)
...
file hello.c line 7 function main: assertion z == 15  SUCCESS

** 0 of 1 failed (1 iterations)
VERIFICATION SUCCESSFUL
```

CBMC chứng minh assertion đúng. **Verification successful**.

## Bước 3: Tìm bug đầu tiên

Sửa `hello.c` thành:

```c
#include <assert.h>

int main() {
    int x = 5;
    int y = 10;
    int z = x + y;
    assert(z == 16);   // sai assertion
    return 0;
}
```

Chạy:

```bash
cbmc hello.c
```

Output:

```
file hello.c line 7 function main: assertion z == 16  FAILURE

** Results:
hello.c function main
[main.assertion.1] line 7 assertion z == 16: FAILURE

** 1 of 1 failed (2 iterations)
VERIFICATION FAILED
```

CBMC báo assertion sai. Để xem counterexample (input dẫn tới fail), thêm flag `--trace`:

```bash
cbmc hello.c --trace
```

Trace cho thấy state từng step, giá trị mỗi biến.

## Bước 4: Verify với input không xác định

Code dùng `nondet_int()` để CBMC verify cho **mọi input**:

```c
#include <assert.h>

int nondet_int();   // declare without body, CBMC treats as "any int"

int main() {
    int x = nondet_int();
    if (x > 0) {
        int y = x + 1;
        assert(y > x);   // tin rằng cộng số dương cho kết quả lớn hơn
    }
    return 0;
}
```

```bash
cbmc overflow.c --trace
```

Output:

```
[main.assertion.1] line 8 assertion y > x: FAILURE

State 12 file overflow.c line 4 function main thread 0
----------------------------------------------------
  x=2147483647 (INT_MAX)

State 14 file overflow.c line 6 function main thread 0
----------------------------------------------------
  y=-2147483648 (INT_MIN, after overflow)
```

CBMC tìm được counterexample: `x = INT_MAX`. Khi `x + 1`, integer overflow wrap về `INT_MIN`. Assertion `y > x` thành `INT_MIN > INT_MAX` = false.

Đây là loại bug khó test bằng tay (ai nghĩ tới test với INT_MAX?), nhưng CBMC tìm trong giây.

## Bước 5: Các flag check tự động

CBMC có nhiều check built-in cho các lớp bug phổ biến:

```bash
cbmc program.c \
    --bounds-check \           # array out-of-bounds
    --pointer-check \          # null pointer dereference
    --div-by-zero-check \      # division by zero
    --signed-overflow-check \  # signed integer overflow
    --unsigned-overflow-check \ # unsigned overflow
    --pointer-overflow-check \ # pointer arithmetic overflow
    --memory-leak-check \      # memory leak
    --memory-cleanup-check \   # forgotten free
    --conversion-check \       # narrowing conversion bug
    --float-overflow-check \   # float overflow
    --nan-check                # NaN trong float
```

Hoặc bật tất cả: `--all-checks`.

### Ví dụ: detect buffer overflow

```c
#include <string.h>

int main() {
    char buf[10];
    char *src = "this is way too long";
    strcpy(buf, src);   // overflow!
    return 0;
}
```

```bash
cbmc bo.c --bounds-check --pointer-check
```

Output:

```
[main.array_bounds.1] line 6 dereference failure: ... 
  array `buf' upper bound: FAILURE
```

CBMC bắt được overflow của `strcpy`.

### Ví dụ: detect use after free

```c
#include <stdlib.h>

int main() {
    int *p = malloc(sizeof(int));
    *p = 5;
    free(p);
    *p = 10;   // UAF
    return 0;
}
```

```bash
cbmc uaf.c --pointer-check
```

```
[main.pointer_dereference.1] line 7 dereference failure:
  pointer NULL or freed: FAILURE
```

## Bước 6: Verify function với loop

CBMC unwind loop tới depth `--unwind`:

```c
#include <assert.h>

int sum(int n) {
    int s = 0;
    for (int i = 0; i < n; i++) s += i;
    return s;
}

int main() {
    int n = nondet_int();
    if (n >= 0 && n <= 5) {
        int result = sum(n);
        assert(result == n * (n - 1) / 2);
    }
    return 0;
}
```

```bash
cbmc loop.c --unwind 10
```

Nếu unwind đủ (>=5), assertion verify thành công.

Nếu unwind không đủ:

```bash
cbmc loop.c --unwind 3
```

Output:

```
** Unwinding loop main.0 iteration 3 file loop.c line 5 function sum
  unwinding assertion: FAILURE
```

CBMC báo "unwinding assertion failed": loop có thể chạy quá `--unwind 3`. Solution: tăng unwind, hoặc dùng `__CPROVER_assume(n <= 3)` để giới hạn input.

## Bước 7: Verify pthread (concurrency)

```c
#include <pthread.h>
#include <assert.h>

int x = 0;

void* thread_a(void *arg) {
    x = 1;
    return NULL;
}

void* thread_b(void *arg) {
    x = 2;
    return NULL;
}

int main() {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, thread_a, NULL);
    pthread_create(&t2, NULL, thread_b, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    assert(x == 1 || x == 2);
    return 0;
}
```

```bash
cbmc thread.c --pthread
```

CBMC khám phá mọi interleaving khả dĩ của 2 thread. Assertion `x == 1 || x == 2` pass vì cả 2 thread chỉ ghi 2 giá trị đó.

Đổi assertion thành `assert(x == 1)`:

```
[main.assertion.1] line 16 assertion x == 1: FAILURE

Counterexample shows: t2 chạy sau t1, x = 2 ở cuối.
```

## Bước 8: __CPROVER_assume - giới hạn input

Khi bạn biết một property của input không trivial, tell CBMC bằng `__CPROVER_assume`:

```c
#include <assert.h>

int main() {
    int x = nondet_int();
    __CPROVER_assume(x > 0 && x < 100);   // ràng buộc x
    int y = x * 2;
    assert(y > 0);   // pass vì x > 0
    return 0;
}
```

CBMC không khám phá x < 0 hay x >= 100. Nhanh hơn nhiều, và assertion `y > 0` trivially pass.

Dùng `__CPROVER_assume` để model precondition của hàm, hoặc input bị filter trước bởi tầng khác.

## Bước 9: Goto-instrument cho instrumentation nâng cao

CBMC có tool đi kèm `goto-instrument` để instrument program trước khi verify:

```bash
# Step 1: compile to GOTO program
goto-cc -o program.gb program.c

# Step 2: instrument để check race
goto-instrument program.gb program-race.gb --race-check

# Step 3: verify
cbmc program-race.gb
```

`--race-check` thêm check data race ở mọi shared access.

Các instrumentation khác:
- `--mm sc/tso/pso`: model memory weak (TSO/PSO).
- `--cover line/branch/mcdc`: instrument cho test gen.
- `--stack-depth N`: check stack overflow.

## Bước 10: Output formats

CBMC có nhiều output format:

```bash
cbmc program.c --xml-ui              # XML output
cbmc program.c --json-ui             # JSON output (machine-readable)
cbmc program.c --trace               # human-readable trace
cbmc program.c --show-properties     # list properties without running
cbmc program.c --show-goto-functions # show internal IR
```

JSON output dùng cho CI integration:

```bash
cbmc program.c --json-ui > result.json
jq '.[] | select(.result == "FAILURE")' result.json
```

## So sánh CBMC vs ESBMC

| Tiêu chí | CBMC | ESBMC |
|---|---|---|
| Maintainer | Diffblue + community | Academic community (multi-institution) |
| Backend SAT/SMT | MiniSat (default), CaDiCaL, Z3 | Z3, Boolector, CVC4, Yices |
| Concurrency | --pthread, basic | mature, multiple memory model |
| Float | --floatbv | mature FP support |
| Tốc độ | Trung bình | Trung bình tới nhanh |
| Use case | General-purpose | Concurrency-heavy, float-heavy |

Cả 2 đều free, open source. Bắt đầu với CBMC, switch sang ESBMC nếu cần concurrency support tốt hơn.

## Troubleshooting common errors

### "include file not found"

```bash
cbmc program.c -I /usr/include -I /usr/local/include
```

CBMC cần preprocessor headers như compiler.

### "Function X not found"

CBMC default không link với external library. Nếu code dùng `printf`, `malloc`, CBMC stub. Nếu dùng custom library:

```bash
cbmc program.c --function-pointer-checks library.c
```

### "Out of memory"

SMT formula quá lớn. Giảm `--unwind`, hoặc dùng `__CPROVER_assume` để giảm input space.

### "Loop unwinding insufficient"

Tăng `--unwind`. Hoặc dùng `--unwindset name:K` chỉ cho loop cụ thể.

### "Timeout"

Default timeout không giới hạn. Set với `--object-bits 8` (giảm số object track) hoặc switch SMT backend:

```bash
cbmc program.c --smt2 --z3
```

## Workflow trong CI

`Makefile` mẫu:

```makefile
.PHONY: verify
verify:
	@for src in src/*.c; do \
	    echo "Verifying $$src..."; \
	    cbmc $$src \
	        --unwind 20 \
	        --bounds-check --pointer-check \
	        --signed-overflow-check \
	        --pointer-overflow-check \
	        --memory-leak-check; \
	done

.PHONY: verify-fast
verify-fast:
	cbmc src/critical_function.c \
	    --unwind 5 --bounds-check --pointer-check
```

`.github/workflows/verify.yml`:

```yaml
name: CBMC Verify
on: [push, pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install CBMC
        run: sudo apt install cbmc
      - name: Run CBMC
        run: make verify
```

Mỗi PR chạy CBMC tự động. Block merge nếu fail.

## Bài tập thực hành

Tải repo này về và thử CBMC trên các bài tập [Exercise Set 2](../exercises/exercise-set-2):

```bash
git clone https://github.com/tuandung222/software-security-foundation
cd software-security-foundation/exercises
# Copy code C từ bài tập vào file
cbmc bai1.c --bounds-check --pointer-check
```

Xem CBMC bắt được bug nào, miss bug nào, vì sao.

## Tóm tắt

- CBMC: install qua brew/apt, version 5.95+.
- Run đơn giản: `cbmc program.c`.
- Counterexample: `--trace`.
- Built-in checks: `--bounds-check --pointer-check --signed-overflow-check ...`.
- Loop: `--unwind N`.
- Concurrency: `--pthread`.
- Limit input: `__CPROVER_assume(...)`.
- CI integration: `--json-ui` output.

CBMC là một trong những công cụ formal verification practical nhất hiện nay. Nắm vững nó là kỹ năng quý cho mọi software engineer làm việc với C/C++ critical code.

## Tham khảo

- [CBMC official docs](https://www.cprover.org/cbmc/)
- [CBMC tutorial trên GitHub](https://github.com/diffblue/cbmc/blob/develop/doc/cprover-manual/index.md)
- [ESBMC tutorial](http://esbmc.org/) (alternative)

---

**Tiếp theo**: [7.5 Secure SDLC + Microsoft SDL + OWASP SAMM](./05-secure-sdlc)
