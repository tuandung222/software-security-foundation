---
id: 04-code-patterns-cluster-3
title: 8.4 Code patterns Cụm 3 (Lec 4 - Concurrency)
sidebar_position: 4
description: "Phân tích các đoạn code pthread/C++ thread trong Lec 4: data race, atomicity, deadlock, memory model, lock-free patterns."
---

# 8.4 Code patterns Cụm 3 (Lec 4 - Concurrency)

> **Tóm tắt một dòng**: Code Lec 4 là các program đa luồng minh hoạ class lỗi concurrency: data race, atomicity violation, deadlock, memory model. Khó debug bằng test thông thường vì bug **non-deterministic**, nhưng CBMC `--pthread` khám phá interleaving exhaustively trong bound.

## Sample 1: Race trên shared variable

**Nguồn**: Lec 4, mục Concurrency Verification.

**Code (cleaned up)**:

```c
#include <pthread.h>
#include <assert.h>

int n = 0;

void* P(void *arg) {
    n++;
    return NULL;
}

int main(void) {
    pthread_t id1, id2;
    pthread_create(&id1, NULL, P, NULL);
    pthread_create(&id2, NULL, P, NULL);
    pthread_join(id1, NULL);
    pthread_join(id2, NULL);
    assert(n == 2);   // (1) BUG?
    return 0;
}
```

**Đọc nhanh**: 2 thread mỗi cái `n++` 1 lần. Expect `n == 2`.

**Bug**:

1. **Bug (High)**: `n++` không atomic. Race possible, `n` có thể = 1 (lost update).

**Cơ chế interleaving**:

`n++` = 3 instruction: `LOAD r, n`; `INC r`; `STORE n, r`.

Schedule "bad":
```
T1: LOAD r1 from n (r1 = 0)
T2: LOAD r2 from n (r2 = 0)
T1: INC r1 (r1 = 1)
T2: INC r2 (r2 = 1)
T1: STORE r1 to n (n = 1)
T2: STORE r2 to n (n = 1)
Final: n = 1, NOT 2
```

Schedule "good":
```
T1: LOAD, INC, STORE → n = 1
T2: LOAD, INC, STORE → n = 2
Final: n = 2
```

Probability của bad schedule trên modern CPU: phụ thuộc memory model, contention. Test 1 triệu lần có thể vẫn không hit.

**Verify với CBMC**:

```bash
cbmc race.c --pthread --unwind 5
```

CBMC khám phá mọi interleaving khả dĩ. Output:

```
[main.assertion.1] line 17 assertion n == 2: FAILURE

Schedule:
  T1: LOAD n=0
  T2: LOAD n=0  
  T1: INC, STORE n=1
  T2: INC, STORE n=1
  → n = 1
```

**Fix với atomic**:

```c
#include <stdatomic.h>

atomic_int n = 0;

void* P(void *arg) {
    atomic_fetch_add(&n, 1);
    return NULL;
}
```

**Fix với mutex**:

```c
pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
int n = 0;

void* P(void *arg) {
    pthread_mutex_lock(&lock);
    n++;
    pthread_mutex_unlock(&lock);
    return NULL;
}
```

**Bài học**: mọi shared variable phải hoặc atomic, hoặc protected by lock. Single instruction nguồn gốc thường không atomic.

## Sample 2: Atomicity violation

**Nguồn**: Lec 4, mục Atomicity Violation.

**Code**:

```c
#include <pthread.h>

int balance = 100;
pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

void withdraw(int amount) {
    pthread_mutex_lock(&lock);
    if (balance >= amount) {
        // (1) lock release before action
        pthread_mutex_unlock(&lock);
        // Tại đây thread khác có thể withdraw
        balance -= amount;   // (2) BUG: race
    } else {
        pthread_mutex_unlock(&lock);
    }
}
```

**Bug**:

1. **Bug (High)**: lock được giữ trong check nhưng release trước modify. Hai thread cùng pass check, cùng subtract → balance âm.

**Cơ chế**:

```
balance = 100
T1: lock, check (100 >= 60: true), unlock
T2: lock, check (100 >= 60: true), unlock
T1: balance -= 60 → balance = 40
T2: balance -= 60 → balance = -20  (NEGATIVE!)
```

**Fix**:

```c
void withdraw(int amount) {
    pthread_mutex_lock(&lock);
    if (balance >= amount) {
        balance -= amount;   // (3) inside critical section
    }
    pthread_mutex_unlock(&lock);
}
```

Quy tắc: **check và action phải trong cùng critical section**.

**Verify với CBMC**:

```bash
cbmc withdraw.c --pthread --unwind 3
```

CBMC tìm schedule khiến balance < 0.

**Bài học**: lock granularity quan trọng. Lock quá fine = bug atomicity. Lock quá coarse = giảm performance.

## Sample 3: Deadlock cổ điển

**Nguồn**: Lec 4, mục Deadlock.

**Code**:

```c
#include <pthread.h>

pthread_mutex_t lockA = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t lockB = PTHREAD_MUTEX_INITIALIZER;

void* T1(void *arg) {
    pthread_mutex_lock(&lockA);
    // ... work ...
    pthread_mutex_lock(&lockB);   // (1)
    // ... work ...
    pthread_mutex_unlock(&lockB);
    pthread_mutex_unlock(&lockA);
    return NULL;
}

void* T2(void *arg) {
    pthread_mutex_lock(&lockB);
    // ... work ...
    pthread_mutex_lock(&lockA);   // (2)
    // ... work ...
    pthread_mutex_unlock(&lockA);
    pthread_mutex_unlock(&lockB);
    return NULL;
}
```

**Bug**:

1. **Bug (Critical)**: T1 lock A trước, T2 lock B trước. Schedule:

```
T1: lock A   T2: lock B
T1: WAIT for B   T2: WAIT for A
DEADLOCK
```

**Cơ chế**: bốn điều kiện deadlock (Coffman 1971):
1. Mutual exclusion.
2. Hold and wait.
3. No preemption.
4. Circular wait.

Code trên thoả mọi điều kiện → deadlock guaranteed under right schedule.

**Fix (lock ordering)**:

```c
// Mọi thread acquire lock theo cùng thứ tự
void* T1(void *arg) {
    pthread_mutex_lock(&lockA);   // luôn A trước
    pthread_mutex_lock(&lockB);
    // ...
    pthread_mutex_unlock(&lockB);
    pthread_mutex_unlock(&lockA);
    return NULL;
}

void* T2(void *arg) {
    pthread_mutex_lock(&lockA);   // A trước B
    pthread_mutex_lock(&lockB);
    // ...
    pthread_mutex_unlock(&lockB);
    pthread_mutex_unlock(&lockA);
    return NULL;
}
```

**Verify với CBMC**:

```bash
cbmc deadlock.c --pthread --deadlock-check --unwind 5
```

CBMC bắt circular wait.

**Bài học**: lock ordering convention global. Define order once (e.g. by address), enforce ở code review. Tool `tsan` cũng detect deadlock runtime.

## Sample 4: Lost wakeup

**Nguồn**: Lec 4, mục condition variable.

**Code**:

```c
#include <pthread.h>

pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t cv = PTHREAD_COND_INITIALIZER;
int ready = 0;

void* consumer(void *arg) {
    pthread_mutex_lock(&lock);
    if (!ready) {                   // (1) BUG: should be while
        pthread_cond_wait(&cv, &lock);
    }
    // ... use shared data ...
    pthread_mutex_unlock(&lock);
    return NULL;
}

void* producer(void *arg) {
    pthread_mutex_lock(&lock);
    ready = 1;
    pthread_cond_signal(&cv);       // (2) hoặc broadcast
    pthread_mutex_unlock(&lock);
    return NULL;
}
```

**Bug**:

1. **Bug (Medium)**: `if (!ready)` thay vì `while (!ready)`. Spurious wakeup hoặc multiple consumer = bug.
2. **Bug phụ**: `pthread_cond_signal` chỉ wake 1 thread. Nhiều consumer waiting = lost wakeup.

**Cơ chế spurious wakeup**:

POSIX cho phép `pthread_cond_wait` return ngẫu nhiên (kernel optimization). Nếu code `if`, sau wake thread tiếp tục mà không recheck condition → bug.

**Fix chuẩn**:

```c
void* consumer(void *arg) {
    pthread_mutex_lock(&lock);
    while (!ready) {                // ĐÚNG: while, không if
        pthread_cond_wait(&cv, &lock);
    }
    // ... use shared data ...
    pthread_mutex_unlock(&lock);
    return NULL;
}
```

`pthread_cond_broadcast` nếu có nhiều consumer cần wake.

**Verify**:

CBMC `--pthread` model `pthread_cond_wait` chính xác với spurious wakeup.

**Bài học**: pattern "condition wait" luôn dùng `while`, không bao giờ `if`. Quy tắc 1 dòng nhưng nhiều người sai.

## Sample 5: Memory model (TSO surprise)

**Nguồn**: Lec 4, mục Memory Model.

**Code (Dekker's algorithm simplified)**:

```c
#include <pthread.h>
#include <assert.h>

int x = 0, y = 0;
int r1, r2;

void* T1(void *arg) {
    x = 1;
    r1 = y;   // read y
    return NULL;
}

void* T2(void *arg) {
    y = 1;
    r2 = x;   // read x
    return NULL;
}

int main(void) {
    pthread_t id1, id2;
    pthread_create(&id1, NULL, T1, NULL);
    pthread_create(&id2, NULL, T2, NULL);
    pthread_join(id1, NULL);
    pthread_join(id2, NULL);
    
    // Under Sequential Consistency: r1 == 1 || r2 == 1 always
    assert(r1 == 1 || r2 == 1);   // (1) BUG under TSO
    return 0;
}
```

**Đọc nhanh**: T1 write x then read y. T2 write y then read x. Property: ít nhất 1 read thấy "1".

**Bug under TSO (x86 memory model)**:

CPU có **store buffer**: write `x = 1` vào buffer, không immediately commit. Read `r1 = y` có thể happen trước commit. Tương tự T2.

Schedule possible under TSO (impossible under SC):

```
T1: write x=1 to store buffer (delayed)
T2: write y=1 to store buffer (delayed)
T1: read y from memory → r1 = 0 (chưa thấy y=1)
T2: read x from memory → r2 = 0 (chưa thấy x=1)
Later: store buffer flush
Final: r1 = 0, r2 = 0. Assertion FAIL!
```

**Cơ chế**: TSO cho phép **store-load reordering**. x86 dùng TSO (chính xác là x86-TSO). ARM/POWER yếu hơn, cho phép thêm reordering.

**Fix với memory fence**:

```c
#include <stdatomic.h>

void* T1(void *arg) {
    x = 1;
    atomic_thread_fence(memory_order_seq_cst);  // full fence
    r1 = y;
    return NULL;
}

void* T2(void *arg) {
    y = 1;
    atomic_thread_fence(memory_order_seq_cst);
    r2 = x;
    return NULL;
}
```

Fence force CPU flush store buffer trước read.

**Fix với atomic + seq_cst**:

```c
atomic_int x = 0, y = 0;

void* T1(void *arg) {
    atomic_store(&x, 1);
    r1 = atomic_load(&y);
    return NULL;
}
```

Default `atomic_store/load` dùng `memory_order_seq_cst`, đảm bảo SC.

**Verify với CBMC**:

```bash
cbmc dekker.c --pthread --mm tso --unwind 3
```

CBMC support multiple memory model. Default SC. `--mm tso` test under TSO.

**Bài học**: code lock-free đòi hỏi hiểu memory model. Tránh trừ khi cần performance cực cao. Dùng mutex hoặc seq_cst atomic cho 99% case.

## Sample 6: ABA problem trong lock-free

**Nguồn**: Lec 4, ABA pattern.

**Code (stack lock-free naïve)**:

```c
#include <stdatomic.h>

typedef struct Node {
    int data;
    struct Node *next;
} Node;

atomic_uintptr_t top;   // pointer to head

void push(Node *n) {
    Node *old_top;
    do {
        old_top = (Node*)atomic_load(&top);
        n->next = old_top;
    } while (!atomic_compare_exchange_weak(&top, (uintptr_t*)&old_top, (uintptr_t)n));
}

Node* pop(void) {
    Node *old_top, *new_top;
    do {
        old_top = (Node*)atomic_load(&top);
        if (old_top == NULL) return NULL;
        new_top = old_top->next;
        // (1) ABA window
    } while (!atomic_compare_exchange_weak(&top, (uintptr_t*)&old_top, (uintptr_t)new_top));
    return old_top;
}
```

**Bug**:

1. **Bug (High) - ABA**: giữa load `old_top` và CAS, một thread khác có thể `pop`, `free`, `push back same address`. CAS thấy "vẫn old_top" nhưng nội dung đã khác.

**Cơ chế ABA**:

```
Initial: stack = A → B → C
T1: pop, load top = A, next = B → about to CAS
T2: pop A (returns A)
T2: pop B (returns B)  
T2: push A' at SAME ADDRESS as A
T1: CAS succeeds (A == A by pointer), but next is now C, not B
Bug: B is leaked, list broken
```

**Fix 1 (hazard pointer)**: complex, dùng trong production lock-free.

**Fix 2 (tag pointer)**: dùng 2 phần (pointer + version counter):

```c
typedef struct {
    Node *ptr;
    uint64_t version;
} TaggedPtr;

atomic of TaggedPtr (need 128-bit atomic on x86_64).
```

Mỗi modify increment version. CAS compare cả ptr và version.

**Fix 3 (đơn giản nhất)**: dùng mutex, không lock-free.

**Verify**:

CBMC `--pthread` có thể model lock-free với bounded exploration, nhưng ABA cần model memory allocator chính xác.

**Bài học**: lock-free data structure cực kỳ khó đúng. ABA chỉ là một trong nhiều bug class. Nếu không có lý do performance critical, **dùng mutex**.

## Sample 7: Condition race trong initialization

**Nguồn**: Lec 4, double-checked locking.

**Code (double-checked locking)**:

```c
#include <pthread.h>

pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
Singleton *instance = NULL;

Singleton* get_instance(void) {
    if (instance == NULL) {                   // (1) check without lock
        pthread_mutex_lock(&lock);
        if (instance == NULL) {                // (2) double check
            instance = create_singleton();    // (3) BUG under weak mem
        }
        pthread_mutex_unlock(&lock);
    }
    return instance;
}
```

**Bug**:

1. **Bug (Medium-High) on weak memory**: `instance = create_singleton()` không atomic. Compiler có thể reorder:
   - First write pointer.
   - Then initialize object fields.

Reader thread thấy `instance != NULL` (qua check at (1)), return pointer, dereference fields chưa init → garbage hoặc crash.

**Cơ chế**:

```
T1: alloc memory at address X
T1: write instance = X  ← reader can see this
T1: initialize *X
T2: check instance, see X (not NULL)
T2: dereference X → fields chưa init
```

Trên x86 (TSO) thường OK vì store ordered. Trên ARM/POWER (weaker), bug rõ.

**Fix với atomic + release/acquire**:

```c
#include <stdatomic.h>

atomic_uintptr_t instance = ATOMIC_VAR_INIT(0);

Singleton* get_instance(void) {
    Singleton *p = (Singleton*)atomic_load_explicit(&instance, memory_order_acquire);
    if (p == NULL) {
        pthread_mutex_lock(&lock);
        p = (Singleton*)atomic_load_explicit(&instance, memory_order_acquire);
        if (p == NULL) {
            p = create_singleton();
            atomic_store_explicit(&instance, (uintptr_t)p, memory_order_release);
        }
        pthread_mutex_unlock(&lock);
    }
    return p;
}
```

`memory_order_release` (writer) + `memory_order_acquire` (reader) đảm bảo: nếu reader thấy pointer mới, mọi write trước nó đều visible.

**Fix tốt nhất**: dùng `pthread_once` hoặc C++ `std::call_once`.

```c
pthread_once_t init_done = PTHREAD_ONCE_INIT;

void init(void) {
    instance = create_singleton();
}

Singleton* get_instance(void) {
    pthread_once(&init_done, init);
    return instance;
}
```

Pattern này standard, đảm bảo init đúng 1 lần thread-safe.

**Bài học**: double-checked locking là pattern **infamous khó đúng**. Dùng `call_once` / `pthread_once` thay thế.

## Sample 8: False sharing performance bug

**Nguồn**: Lec 4 (extension), cache line.

**Code**:

```c
#include <pthread.h>

struct Counters {
    int a;
    int b;
};

struct Counters counters;

void* T1(void *arg) {
    for (int i = 0; i < 1000000; i++) {
        counters.a++;   // (1) atomic? hoặc dùng atomic_int
    }
    return NULL;
}

void* T2(void *arg) {
    for (int i = 0; i < 1000000; i++) {
        counters.b++;
    }
    return NULL;
}
```

**Bug**:

1. Functional bug: cả 2 đều race (sample 1). Giả sử fix bằng atomic.
2. **Performance bug (Medium): false sharing**. `a` và `b` nằm cùng cache line 64 byte. Mọi modify cache line invalidate cho thread khác → cache miss → slow.

**Cơ chế**:

CPU cache hoạt động ở granularity 64-byte line. `int a, int b` (8 byte) nằm cùng 1 line. T1 modify a → invalidate line cho T2. T2 modify b → invalidate line cho T1. Ping-pong cache, không có race functional nhưng performance giảm 10-100x.

**Fix với cache line padding**:

```c
#include <stdatomic.h>

struct Counters {
    alignas(64) atomic_int a;
    alignas(64) atomic_int b;
};
```

`alignas(64)` đảm bảo a và b ở khác cache line.

Hoặc dùng padding manual:

```c
struct Counters {
    atomic_int a;
    char pad1[60];   // pad to 64 bytes
    atomic_int b;
    char pad2[60];
};
```

**Verify**: false sharing không phải functional bug, BMC không detect. Dùng `perf c2c` (Linux) hoặc Intel VTune để measure cache miss.

**Bài học**: false sharing là performance bug subtle. Pattern: thread-private counter padding tránh sharing. Quan trọng cho high-throughput data path.

## Tóm tắt Cụm 3

| Sample | Bug | Tool detect |
|---|---|---|
| 1 Race n++ | Data race | CBMC --pthread, TSan |
| 2 Atomicity violation | Logic race | CBMC --pthread |
| 3 Deadlock | Lock ordering | CBMC --deadlock-check, TSan |
| 4 Lost wakeup | Cond var | CBMC --pthread |
| 5 TSO reordering | Memory model | CBMC --mm tso |
| 6 ABA lock-free | Memory reuse | Manual review (BMC limited) |
| 7 Double-check init | Memory model | CBMC --pthread + memory order |
| 8 False sharing | Performance | perf c2c, VTune |

8 sample này demo **toàn bộ class concurrency bug** trong thực tế.

## Pattern an toàn cho concurrency

Sau khi đọc, các quy tắc cốt lõi:

1. **Mọi shared variable: atomic hoặc protected by lock**. Không có "I'll just be careful".
2. **Lock ordering global**: tránh circular deadlock.
3. **Condition wait luôn dùng while**: chống spurious wakeup.
4. **Atomic mặc định seq_cst**: weaker order chỉ khi đo performance critical.
5. **Tránh lock-free trừ khi cần**: ABA, memory model, leak khó debug.
6. **pthread_once cho lazy init**: thay double-checked locking.
7. **Cache padding cho hot counter**: tránh false sharing.

7 quy tắc này chống 90% concurrency bug thực tế. Còn 10% còn lại là expert territory (kernel, allocator, JIT runtime).

---

**Tiếp theo**: [8.5 Code patterns Cụm 4 (testing và fuzzing)](./05-code-patterns-cluster-4)
