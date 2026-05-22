---
id: 04-concurrency-verification
title: 4.4 Concurrency verification
sidebar_position: 4
description: Vì sao verify chương trình đa luồng khó hơn nhiều so với sequential, các loại bug concurrency (data race, atomicity violation, deadlock), và memory model.
---

# 4.4 Concurrency verification

> **Tóm tắt một dòng**: Concurrency verification phải xử lý không chỉ mọi input mà còn mọi cách OS có thể chuyển thread. Số schedule khả dĩ bùng nổ tổ hợp. Bài này giới thiệu các lớp bug concurrency, vai trò của memory model trong verification, và lý do tại sao kỹ thuật chuyên biệt (Context-Bounded Analysis, Sequentialization) là cần thiết.

## Một bug "không thể tin được"

Hãy bắt đầu với một ví dụ rất nhỏ minh hoạ độ khó của concurrency:

```c
int counter = 0;

void* increment(void *arg) {
    for (int i = 0; i < 1000000; i++) {
        counter++;
    }
    return NULL;
}

int main() {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, increment, NULL);
    pthread_create(&t2, NULL, increment, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("%d\n", counter);
    return 0;
}
```

Câu hỏi: chương trình in ra gì? Trực giác: $2 \times 10^6$. Thực tế: khi tôi chạy trên máy, kết quả thường là một số trong khoảng $[10^6, 2 \times 10^6]$, hiếm khi đạt đúng $2 \times 10^6$.

Tại sao? Vì `counter++` không phải atomic. Compiler dịch thành 3 instruction:

```
load counter -> reg
add reg, 1
store reg -> counter
```

Khi thread 1 và thread 2 chạy song song, có thể xảy ra:

```
Thread 1: load counter -> reg1   (reg1 = 100)
Thread 2: load counter -> reg2   (reg2 = 100)
Thread 1: add reg1, 1            (reg1 = 101)
Thread 1: store reg1 -> counter  (counter = 101)
Thread 2: add reg2, 1            (reg2 = 101)
Thread 2: store reg2 -> counter  (counter = 101)
```

Hai thread cùng làm 2 increment, nhưng `counter` chỉ tăng 1. Đây là **data race**, lớp bug concurrency phổ biến nhất.

Điều đáng sợ: bug này **phụ thuộc timing**. Trên một số máy, một số OS, một số tải, có thể chương trình chạy đúng hàng nghìn lần rồi mới fail một lần. Testing thông thường rất khó tìm.

## Các lớp bug concurrency

### Data race

Hai thread truy cập cùng một biến chia sẻ, ít nhất một là **write**, không có sync (mutex, atomic). Hậu quả: kết quả không xác định.

Ngoài counter, data race xuất hiện trong:

```c
// flag-based signaling
bool ready = false;
int data = 0;

void* producer(void *arg) {
    data = compute();
    ready = true;   // data race với consumer
}

void* consumer(void *arg) {
    while (!ready);   // data race
    use(data);
}
```

Bug: compiler hoặc CPU có thể **reorder** `data = compute()` và `ready = true`. Consumer thấy `ready = true` nhưng `data` chưa được ghi. Use giá trị cũ của `data`.

Để fix: dùng `_Atomic bool ready` (C11) hoặc `std::atomic<bool>` (C++).

### Atomicity violation

Sequence các thao tác đáng nhẽ phải atomic nhưng không được bảo vệ. Ví dụ:

```c
if (account_balance >= amount) {       // check
    account_balance -= amount;          // use
}
```

Giữa check và use, thread khác có thể rút tiền, làm `account_balance` không còn đủ. Đây là TOCTOU classic (đã gặp trong [bài 1.3](../01-introduction/03-vulnerabilities-catalog)), nhưng giờ trong context đa luồng.

Để fix: lock toàn bộ sequence.

```c
pthread_mutex_lock(&mutex);
if (account_balance >= amount) {
    account_balance -= amount;
}
pthread_mutex_unlock(&mutex);
```

### Deadlock

Hai thread chờ nhau giải phóng resource, không tiến lên được.

```c
// Thread 1
lock(A);
lock(B);
// work
unlock(B);
unlock(A);

// Thread 2
lock(B);
lock(A);
// work
unlock(A);
unlock(B);
```

Nếu Thread 1 đã lock A và Thread 2 đã lock B, cả hai chờ nhau mãi.

Để tránh: **lock ordering** (mọi thread lock theo cùng một thứ tự).

### Livelock

Hai thread liên tục yield cho nhau, không ai làm việc thực sự.

```c
// Thread 1
while (true) {
    if (try_lock(mutex)) { work(); break; }
    sleep(small_random);   // yield
}

// Thread 2 tương tự
```

Nếu cả hai cùng "lịch sự" yield, có thể không ai vào critical section. Hiếm gặp trong thực tế nhưng có thật.

### Order violation

Hai event đáng nhẽ phải xảy ra theo thứ tự nhất định, nhưng race condition cho phép thứ tự sai.

```c
// Init thread
config = load_config();
worker_start();

// Worker thread
use(config);   // có thể chạy trước config = load_config()?
```

Nếu `worker_start()` chỉ trigger worker (không block), worker có thể bắt đầu trước khi `config` được load. Order violation.

## Memory model: vì sao reordering có thể xảy ra?

Bạn có thể hỏi: tại sao compiler/CPU lại reorder instruction? Đáng nhẽ phải chạy đúng thứ tự như viết chứ?

Câu trả lời nằm ở **memory model**: một specification của ngôn ngữ/CPU nói "với chương trình đa luồng, kết quả được phép như thế nào?". Memory model balance giữa performance (cho phép tối ưu hoá) và predictability (đảm bảo correctness).

### Sequential Consistency (SC)

Memory model đơn giản nhất, đề xuất bởi Leslie Lamport (1979):

> Mọi execution tương đương với việc các instruction được trộn thành **một thứ tự tổng** theo cách giữ nguyên thứ tự nội bộ của mỗi thread.

SC là "intuitive": kết quả như khi bạn tay viết schedule và chạy step-by-step.

Tuy nhiên SC quá nghiêm ngặt, làm CPU/compiler không thể tối ưu nhiều. Hầu hết phần cứng và ngôn ngữ thực tế **không** SC.

### Total Store Order (TSO)

Memory model của x86. Mỗi CPU có một **store buffer**: store không immediate flush ra memory chính, mà vào buffer trước. Hậu quả: store của một thread có thể "trễ" so với khi nó "logically" xảy ra.

Phép quan trọng trên TSO: **store-load reordering** được phép, nhưng các reordering khác không. CPU x86 cung cấp `MFENCE` instruction để force flush store buffer.

### Weak memory models

ARM, POWER có memory model "yếu" hơn TSO: gần như mọi reordering đều được phép (store-store, load-store, load-load). Compiler phải chèn memory barrier (`DMB` trên ARM) ở chỗ cần.

### Java Memory Model (JMM) và C11/C++11

Ngôn ngữ cao hơn (Java, C/C++ kể từ 2011) định nghĩa memory model riêng, độc lập phần cứng. Code dùng `_Atomic` hoặc `std::atomic` với memory order specification (`memory_order_acquire`, `_release`, `_seq_cst`).

## Verify concurrency: thách thức cơ bản

Để verify chương trình đa luồng, BMC tool phải khám phá:

1. **Mọi input** (đã có với sequential).
2. **Mọi schedule** (thread nào chạy lúc nào, được phép reorder gì).
3. **Mọi memory model behavior** (tuỳ phần cứng/ngôn ngữ).

Số combination bùng nổ rất nhanh. Đây là vấn đề trung tâm mà các bài 4.5, 4.6, 4.7 sẽ giải quyết.

### Encoding ngây thơ: enumerate schedule

Với $k$ thread, mỗi thread $n$ instruction, số schedule là $\frac{(kn)!}{(n!)^k}$.

Bảng:

| $k$ | $n$ | Số schedule |
|---|---|---|
| 2 | 5 | 252 |
| 2 | 10 | 184,756 |
| 2 | 20 | $\approx 10^{11}$ |
| 3 | 10 | $\approx 10^{14}$ |
| 4 | 10 | $\approx 10^{19}$ |

Enumerate hết là bất khả với $n$ lớn. Cần kỹ thuật.

### Hai họ giải pháp

**Giảm số schedule khám phá**:
- Partial-order reduction: nếu hai instruction giao hoán, chỉ khám phá 1 thứ tự.
- Context-bounded analysis: giới hạn số context switch.

**Mã hoá thông minh**:
- Sequentialization: dịch multi-thread thành single-thread.
- Lazy interleaving: chỉ fork khi thực sự cần.

Bài 4.5 và 4.6 đi sâu vào các kỹ thuật này.

## Atomicity và lock-set analysis

Một kỹ thuật cũ nhưng hiệu quả để detect data race: **lock-set analysis**.

Ý tưởng: với mỗi biến shared $x$, track tập các lock đang được giữ khi access $x$. Nếu hai thread access cùng $x$ mà lock-set giao nhau bằng rỗng, có data race.

```c
pthread_mutex_t m;

void* t1() {
    lock(m);
    x = 5;       // lock_set(x) ∋ m
    unlock(m);
}

void* t2() {
    x = 10;      // lock_set(x) = ∅ (không lock)
}
```

`t1` access $x$ với lock-set $\{m\}$, `t2` với $\emptyset$. Giao $= \emptyset$. Báo race.

Tool **Eraser** (DEC, 1997) là implementation kinh điển. Lock-set analysis nhanh nhưng **không sound**: có thể báo false positive nếu code dùng custom sync (atomic, lock-free).

Modern: **ThreadSanitizer** (TSan) trong gcc/clang dùng combination of happens-before và lock-set, sound hơn nhưng vẫn dynamic.

## Tóm tắt

- Bug concurrency: **data race, atomicity violation, deadlock, livelock, order violation**.
- **Memory model** spec hành vi reordering: SC (lý tưởng), TSO (x86), weak (ARM/POWER), JMM (Java), C11 (C/C++).
- Verify multi-threaded gặp **state explosion mạnh**: số schedule mũ trong số instruction.
- Hai họ giải pháp: giảm schedule khám phá (POR, CBA) và mã hoá thông minh (sequentialization, lazy).
- **Lock-set analysis** (Eraser, TSan) là kỹ thuật cổ điển để detect data race, có cả static lẫn dynamic version.

## Mini-quiz

<details>
<summary>Q1. Phân biệt data race và atomicity violation. Code dưới đây là loại nào?</summary>

```c
if (queue.size() > 0) {
    auto x = queue.pop();
}
```

(Giả sử queue được protected bằng mutex riêng cho mỗi method.)

**Data race**: hai thread truy cập biến chia sẻ, không sync.
**Atomicity violation**: sequence các thao tác đáng nhẽ phải atomic nhưng bị thread khác chen vào.

Code trên là **atomicity violation**, không phải data race. Mỗi method `size()` và `pop()` riêng lẻ thread-safe (có lock), nhưng **sequence** `check rồi pop` không atomic. Giữa `size() > 0` và `pop()`, thread khác có thể pop hết queue. `pop()` ở thread hiện tại fail (hoặc undefined behavior tuỳ thư viện).

Fix: dùng `try_pop()` trả về `optional`, không cần check trước.
</details>

<details>
<summary>Q2. Vì sao sequential consistency "intuitive" nhưng ít memory model thực tế thoả?</summary>

SC đảm bảo execution như "trộn instruction thành thứ tự tổng". Đây là cách lập trình viên hay nghĩ, nên gọi là intuitive.

Tuy nhiên SC cấm nhiều reordering mà compiler/CPU muốn làm để tối ưu:
- Compiler không thể reorder lệnh đọc/ghi để giảm cache miss.
- CPU không thể dùng store buffer (gây store-load reordering).
- CPU không thể out-of-order execution effectively.

Mất các tối ưu này làm performance giảm 20-50%. Không phần cứng/ngôn ngữ mainstream nào sẵn sàng trả giá đó. Vì thế họ chọn memory model yếu hơn (TSO, weak, JMM) và yêu cầu programmer thêm memory barrier khi cần SC.
</details>

<details>
<summary>Q3. Số schedule khả dĩ của 4 thread, mỗi thread 20 instruction là gì? Tại sao explicit enumeration không scale?</summary>

Số schedule = $\frac{(4 \times 20)!}{(20!)^4} = \frac{80!}{(20!)^4}$.

Tính: $80! \approx 7.16 \times 10^{118}$. $(20!)^4 \approx (2.43 \times 10^{18})^4 \approx 3.49 \times 10^{73}$.

Kết quả: $\approx 2.05 \times 10^{45}$.

So sánh: số nguyên tử trong toàn bộ Trái Đất $\approx 10^{50}$. Một fraction nhỏ, nhưng vẫn quá lớn để liệt kê.

Vì thế phải dùng **context-bounded analysis** (giới hạn context switch xuống 2-5 thay vì 80) và **partial-order reduction** (gộp các schedule tương đương) để giảm xuống còn vài triệu schedule, lúc đó BMC tractable.
</details>

---

**Tiếp theo**: [4.5 Context-bounded analysis](./05-context-bounded-analysis)
