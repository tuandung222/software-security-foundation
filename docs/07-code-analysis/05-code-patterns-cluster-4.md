---
id: 05-code-patterns-cluster-4
title: 8.5 Code patterns Cụm 4 (Lec 5 - Testing & Fuzzing)
sidebar_position: 5
description: "Phân tích code dùng làm coverage demo, fuzz target, white-box symbolic execution example. Bao gồm cách viết fuzz harness an toàn và CBMC test gen."
---

# 8.5 Code patterns Cụm 4 (Lec 5 - Testing và Fuzzing)

> **Tóm tắt một dòng**: Code Lec 5 chia 3 nhóm: (1) program nhỏ minh hoạ coverage criteria (statement, branch, MC/DC), (2) fuzz target trông như production function nhưng có bug subtle, (3) symbolic execution example. Bài này đọc lại từng nhóm, comment chi tiết, và viết fuzz harness chuẩn.

## Sample 1: Coverage demo program

**Nguồn**: Lec 5, mục Coverage Criteria (statement coverage).

**Code**:

```c
#include "lib.h"

int max_or_default(int a, int b, int def) {
    int result;
    if (a > b) {
        result = a;
    } else if (b > a) {
        result = b;
    } else {
        result = def;
    }
    return result;
}
```

**Đọc nhanh**: trả về max của a và b, hoặc default nếu equal.

**Phân tích coverage**:

**Statement coverage 100%**: cần test cover mọi statement.
- Test 1: `a=5, b=3, def=0` → vào nhánh `a > b`, result = 5. Cover line `result = a`.
- Test 2: `a=3, b=5, def=0` → nhánh `b > a`, result = 5. Cover line `result = b`.
- Test 3: `a=5, b=5, def=99` → nhánh else, result = 99. Cover line `result = def`.

**3 test** cover hết statement.

**Branch coverage 100%**: cần cover mọi branch true/false.
- `a > b` true: test 1. False: test 2 và 3.
- `b > a` true: test 2. False: test 3.

3 test trên cover hết branch.

**Bug subtle** (có thể không bị detect bởi 3 test trên):

- **Bug 1**: nếu `a == INT_MIN, b == INT_MAX`: `a > b` false, `b > a` true, return INT_MAX. OK.
- **Bug 2**: nếu `a == INT_MAX, b == INT_MIN`: `a > b` true, return INT_MAX. OK.

Function này thực ra **đúng**. Đây là test case "happy path".

**Test edge case bằng CBMC**:

```c
#include <assert.h>
#include <limits.h>

int max_or_default(int a, int b, int def);

int main(void) {
    int a = nondet_int();
    int b = nondet_int();
    int def = nondet_int();
    
    int result = max_or_default(a, b, def);
    
    // Property: result is max(a, b) hoặc def nếu equal
    if (a > b) assert(result == a);
    else if (b > a) assert(result == b);
    else assert(result == def);
    return 0;
}
```

```bash
cbmc harness.c lib.c
```

Nếu function đúng, CBMC chứng minh assertion hold cho **mọi input 32-bit**.

**Bài học**: 100% coverage **không đảm bảo bug-free**. Nhưng < 100% coverage = có code không test, chắc chắn có rủi ro. Coverage là **necessary but not sufficient**.

## Sample 2: Code có MC/DC challenge

**Nguồn**: Lec 5, mục MC/DC coverage.

**Code**:

```c
int check_access(int is_admin, int is_owner, int file_public) {
    if ((is_admin || is_owner) && !file_public) {
        return 1;  // access granted
    }
    return 0;
}
```

Wait - logic này sai? Let me re-read.

Actually let me reverse it - it makes more sense:

```c
int check_access(int is_admin, int is_owner, int file_public) {
    if ((is_admin || is_owner) || file_public) {
        return 1;  // access granted
    }
    return 0;
}
```

**Phân tích MC/DC**:

Decision: `(A || B) || C` với A=is_admin, B=is_owner, C=file_public.

MC/DC yêu cầu: mỗi condition độc lập ảnh hưởng outcome.

Bảng truth:
| Test | A | B | C | (A\|\|B) | Result |
|---|---|---|---|---|---|
| T1 | 0 | 0 | 0 | 0 | 0 |
| T2 | 1 | 0 | 0 | 1 | 1 |
| T3 | 0 | 1 | 0 | 1 | 1 |
| T4 | 0 | 0 | 1 | 0 | 1 |
| T5 | 1 | 1 | 0 | 1 | 1 |
| T6 | 1 | 0 | 1 | 1 | 1 |
| T7 | 0 | 1 | 1 | 1 | 1 |
| T8 | 1 | 1 | 1 | 1 | 1 |

Cần show mỗi condition độc lập:

- **A độc lập**: B và C giữ, A đổi outcome. So sánh T1 (A=0, out=0) với T2 (A=1, out=1). B=0, C=0. **OK**.
- **B độc lập**: A và C giữ, B đổi outcome. T1 (B=0, out=0) vs T3 (B=1, out=1). A=0, C=0. **OK**.
- **C độc lập**: A và B giữ, C đổi outcome. T1 (C=0, out=0) vs T4 (C=1, out=1). A=0, B=0. **OK**.

**Test set MC/DC: T1, T2, T3, T4**. 4 test cho 3 condition. Đúng $n+1$.

**Bug subtle**:

Code này có **logic bug**: "OR với file_public" = bất kỳ ai cũng truy cập file public, bất kể admin hay owner. Có thể đúng intent, nhưng nếu intent là "AND not file_public" (private file, chỉ admin/owner) thì sai.

**Fix nếu intent là "private"**:

```c
int check_access(int is_admin, int is_owner, int file_public) {
    if ((is_admin || is_owner) && !file_public) {
        return 1;
    }
    return 0;
}
```

MC/DC test set cho version này **khác hoàn toàn**. Phân tích lại MC/DC là bài tập cho người đọc.

**Bài học**: MC/DC catch logic interaction. Boolean expression phức tạp cần MC/DC + manual review intent.

## Sample 3: Fuzz target naïve

**Nguồn**: Lec 5, mục Fuzzing Basics.

**Code (fuzz target)**:

```c
#include <stdint.h>
#include <stddef.h>

extern int parse_packet(const uint8_t *data, size_t size);

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size > 0) {
        parse_packet(data, size);   // (1) just call, no oracle
    }
    return 0;
}
```

**Đọc nhanh**: fuzz harness chuẩn libFuzzer, gọi `parse_packet` với input random.

**Vấn đề (không phải bug, mà thiếu)**:

1. **Không có oracle**: fuzzer chỉ detect crash, không detect "wrong output". Nếu parser trả về sai data nhưng không crash, fuzzer miss.
2. **Không validate state**: sau parse, không check internal invariant.

**Enhancement**:

```c
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 2) return 0;
    
    PacketState state;
    int result = parse_packet(data, size, &state);
    
    if (result == 0) {  // parse succeeded
        // Property 1: parsed size <= input size
        assert(state.parsed_bytes <= size);
        
        // Property 2: round-trip
        uint8_t buf[1024];
        size_t serialized = serialize_packet(&state, buf, sizeof(buf));
        assert(serialized <= sizeof(buf));
        
        PacketState state2;
        int reparse = parse_packet(buf, serialized, &state2);
        assert(reparse == 0);
        assert(packet_state_equal(&state, &state2));
    }
    return 0;
}
```

**Differential fuzzing**: 2 implementation so sánh:

```c
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    PacketState s1, s2;
    int r1 = parse_packet_v1(data, size, &s1);
    int r2 = parse_packet_v2(data, size, &s2);
    
    // Property: both parser agree on success/fail
    assert((r1 == 0) == (r2 == 0));
    if (r1 == 0 && r2 == 0) {
        assert(packet_state_equal(&s1, &s2));
    }
    return 0;
}
```

Differential fuzz tìm divergence giữa implementations. Hữu ích khi có reference (e.g. fast C version vs slow Python version).

**Bài học**: fuzz target tốt = (1) drive code path, (2) có property check, (3) idempotent.

## Sample 4: Symbolic execution example

**Nguồn**: Lec 5, mục White-box Fuzzing.

**Code (target cho DSE)**:

```c
int check_input(int x, int y) {
    if (x > 100) {
        if (y < 50) {
            if (x + y > 200) {
                assert(0);   // (1) BUG path
            }
        }
    }
    return 0;
}
```

**Đọc nhanh**: 3 nested if, tới được `assert(0)` chỉ nếu thoả 3 điều kiện.

**Tính khả thi của path random**:

- `x > 100`: với x random 32-bit, P(x > 100) ≈ 50% (chỉ cần signed, half values).
- `y < 50`: P(y < 50) ≈ 50%.
- `x + y > 200`: phụ thuộc x, y.

P(reach assert with random) ≈ 12-25%. Random fuzz có thể trigger.

Nhưng nếu thay condition thành **magic constant**:

```c
if (x == 0xDEADBEEF) {
    if (y == 0xCAFEBABE) {
        assert(0);
    }
}
```

P(random hit) = $2^{-64}$. Random fuzz không bao giờ trigger (cần $\sim 5 \times 10^{17}$ year).

**DSE approach**:

DSE track symbolic constraint:
- Path 1: `x == 0xDEADBEEF and y == 0xCAFEBABE`.
- Solve với Z3: instantly trả về `x = 0xDEADBEEF, y = 0xCAFEBABE`.

DSE tìm input chính xác trong giây.

**Verify với CBMC** (BMC for test gen):

```bash
cbmc check.c --cover decision
```

Hoặc explicit:

```c
int main(void) {
    int x = nondet_int();
    int y = nondet_int();
    check_input(x, y);
    return 0;
}
```

```bash
cbmc check.c --trace
```

CBMC trả về counterexample: `x = 0xDEADBEEF, y = 0xCAFEBABE`.

**Bài học**: DSE/BMC **mạnh hơn random fuzzing** cho path có magic constant hoặc complex constraint. Combine = best (Driller pattern, đã thấy bài 5.7).

## Sample 5: BMC for test generation

**Nguồn**: Lec 5, mục BMC for Test Gen.

**Code (target function)**:

```c
int classify(int x) {
    if (x < 0) return -1;
    if (x == 0) return 0;
    if (x < 10) return 1;
    if (x < 100) return 2;
    return 3;
}
```

**Goal**: sinh test set cover mọi return path.

**Harness**:

```c
#include <assert.h>

int classify(int x);

void cover_path_neg(void) {
    int x = nondet_int();
    assert(classify(x) != -1);   // assert FAIL → counterexample là test cho path -1
}

void cover_path_zero(void) {
    int x = nondet_int();
    assert(classify(x) != 0);
}

void cover_path_small(void) {
    int x = nondet_int();
    assert(classify(x) != 1);
}

void cover_path_medium(void) {
    int x = nondet_int();
    assert(classify(x) != 2);
}

void cover_path_large(void) {
    int x = nondet_int();
    assert(classify(x) != 3);
}

int main(void) {
    cover_path_neg();
    return 0;
}
```

Chạy CBMC mỗi `cover_path_X` riêng:

```bash
cbmc classify.c --function cover_path_neg --trace
```

Output: counterexample `x = -5` (e.g.). Đây là test case.

Tự động hoá: script generate harness cho mỗi path, chạy CBMC, collect counterexample → test suite.

**Tool có sẵn**: `cbmc --cover line` sinh test cho mỗi line, `--cover branch` cho mỗi branch.

```bash
cbmc classify.c --cover branch
```

CBMC liệt kê branch chưa cover và sinh input cover được.

**Bài học**: BMC for test gen = "**negate goal, ask for counterexample**". Đảo property thành assertion sai, BMC sinh input đạt path.

## Sample 6: Fuzz harness cho parser

**Nguồn**: Lec 5, ví dụ fuzz parser binary format.

**Code (target)**:

```c
#include <stdint.h>
#include <string.h>

typedef struct {
    uint16_t magic;
    uint32_t version;
    uint32_t payload_len;
    uint8_t payload[];
} Packet;

int parse_packet(const uint8_t *data, size_t size, Packet *out) {
    if (size < 10) return -1;  // header size = 10
    
    out->magic = (data[0] << 8) | data[1];
    if (out->magic != 0xCAFE) return -1;
    
    memcpy(&out->version, data + 2, 4);
    memcpy(&out->payload_len, data + 6, 4);
    
    // (1) BUG: integer overflow check missing
    if (size < 10 + out->payload_len) return -1;
    
    // (2) BUG: payload too big for output buffer
    memcpy(out->payload, data + 10, out->payload_len);
    return 0;
}
```

**Bug**:

1. **Bug (Critical)**: `out->payload_len` is uint32_t. Attacker set `payload_len = 0xFFFFFFFE`. `10 + 0xFFFFFFFE` overflow uint32 → 8 (very small). Check passes!
2. **Bug (Critical)**: assuming `out->payload` có đủ chỗ chứa `payload_len` byte. Nếu `out` là `Packet packet` (stack alloc nhỏ), overflow stack.

**Fix**:

```c
int parse_packet(const uint8_t *data, size_t size, Packet *out, size_t out_max_payload) {
    if (size < 10) return -1;
    
    out->magic = (data[0] << 8) | data[1];
    if (out->magic != 0xCAFE) return -1;
    
    memcpy(&out->version, data + 2, 4);
    memcpy(&out->payload_len, data + 6, 4);
    
    // Check 1: payload_len trong giới hạn caller cho phép
    if (out->payload_len > out_max_payload) return -1;
    
    // Check 2: input đủ data cho payload_len declared
    // Dùng so sánh không overflow (size - 10 thay vì 10 + payload_len)
    if (size < 10 || size - 10 < out->payload_len) return -1;
    
    memcpy(out->payload, data + 10, out->payload_len);
    return 0;
}
```

Quy tắc: với check `a + b > c`, viết lại thành `a > c - b` (nếu `c >= b`) để tránh overflow.

**Fuzz harness**:

```c
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size > 100000) return 0;  // limit input size để fuzzer fast
    
    Packet *out = malloc(sizeof(Packet) + 1024);  // 1024 byte payload max
    if (!out) return 0;
    
    parse_packet(data, size, out, 1024);
    
    free(out);
    return 0;
}
```

Chạy:

```bash
clang -fsanitize=address,fuzzer parse.c fuzz.c -o fuzz
./fuzz -max_len=200
```

ASan + libFuzzer: ASan detect memory bug, fuzzer drive input.

**Verify với CBMC** (chứng minh không bug với fix):

```c
#include <assert.h>
#include <stdlib.h>

int main(void) {
    size_t size = nondet_size_t();
    __CPROVER_assume(size <= 10000);  // bound for tractability
    
    uint8_t *data = malloc(size);
    if (!data) return 0;
    // Fill data với nondet
    for (size_t i = 0; i < size; i++) data[i] = nondet_uint8();
    
    Packet *out = malloc(sizeof(Packet) + 1024);
    if (out) {
        parse_packet(data, size, out, 1024);
        // Property: no memory corruption (automatic via --pointer-check)
    }
    
    free(data);
    free(out);
    return 0;
}
```

```bash
cbmc parse_harness.c --pointer-check --bounds-check --memory-leak-check
```

**Bài học**: parser binary format là **#1 attack surface**. Mỗi field length cần overflow-safe check. Format pattern: `size_t consumed`, tăng dần, compare với `size_remaining`.

## Tóm tắt Cụm 4

| Sample | Topic | Tool |
|---|---|---|
| 1 Coverage demo | Statement/branch coverage | gcov, llvm-cov |
| 2 MC/DC | Boolean coverage | gcov MC/DC mode |
| 3 Fuzz target naïve | Property-based | libFuzzer + ASan |
| 4 Symbolic exec | DSE for magic constant | CBMC, KLEE |
| 5 BMC test gen | Auto test generation | CBMC --cover |
| 6 Parser fuzz | Integer overflow check | libFuzzer + ASan + CBMC |

6 sample = blueprint cho testing modern: coverage + property + fuzz + formal.

## Pattern fuzz harness tốt

Sau khi đọc, blueprint cho **fuzz harness chất lượng**:

1. **Limit input size**: `if (size > MAX) return 0;` để fuzzer fast.
2. **Multiple input formats**: parse data từ input theo schema, không treat as opaque blob.
3. **Property check**: sau gọi target, assert invariant (size bound, round-trip).
4. **Memory cleanup**: alloc trong harness phải free để fuzzer detect leak.
5. **Differential**: nếu có ref impl, compare output.
6. **Seed corpus**: cung cấp 10-100 valid input để fuzzer warm start.
7. **Dictionary**: với grammar-based format (HTTP, SQL), cung cấp keyword dictionary.

Harness tốt = bug found tăng 10x với cùng CPU time.

## Combine BMC + Fuzz

Workflow modern:

1. **BMC** trên hot function → tìm bug functional với formal guarantee (bounded).
2. **Fuzz** trên parser/codec → tìm bug runtime với volume input.
3. **BMC sinh seed corpus** cho fuzz (sample 5).
4. **Fuzz crash → minimize, reproduce, file** → fix.
5. **Regression**: thêm crash input vào test suite, run mỗi CI.

Combination = highest signal-to-noise. Pure formal có scope limit; pure fuzz không guarantee.

---

**Tiếp theo**: [8.6 Exercise code analysis](./06-exercise-analysis)
