---
id: 04-monitoring-ltl-buchi
title: 5.4 Monitoring với LTL và Büchi automata
sidebar_position: 4
description: "Runtime monitoring để theo dõi property tại runtime. LTL (Linear Temporal Logic) làm ngôn ngữ spec, Büchi automaton làm runtime engine, ứng dụng thực tế trong production."
---

# 5.4 Runtime monitoring với LTL và Büchi automata

> **Tóm tắt một dòng**: Runtime monitoring là kỹ thuật theo dõi chương trình **khi nó chạy**, check property tại từng event. Property thường là temporal (liên quan thứ tự thời gian), diễn đạt bằng **LTL**. Implementation: chuyển LTL sang **Büchi automaton**, chạy automaton song song với chương trình, alert nếu vào state "vi phạm".

## Tại sao cần monitoring khi đã có testing?

Testing chạy chương trình với input cụ thể trong môi trường test. Monitoring chạy chương trình trong **môi trường thực** (production, staging), với input thực, observed.

Khác biệt:

| Tiêu chí | Testing | Monitoring |
|---|---|---|
| Môi trường | Test, isolated | Production, real |
| Input | Cụ thể, chuẩn bị trước | Real-time, không control |
| Mục tiêu | Tìm bug trước khi release | Phát hiện sự cố trong production |
| Action khi fail | Block release | Alert ops, có thể self-heal |

Trong DevOps modern, monitoring là **lớp cuối** của defense in depth. Sau khi test pass, monitor production để bắt bug edge case mà test miss.

Property monitoring trong code thường có dạng temporal:

- "Mọi request đều có response trong 5 giây."
- "Sau khi user login, mọi action đều có authentication."
- "Khi malloc fail, không có dereference của pointer đó."
- "Mọi connection cuối cùng đều được close."

Diễn đạt các property này cần một **ngôn ngữ thời gian**, đó là LTL.

## Linear Temporal Logic (LTL)

LTL là logic với các **temporal operator** ngoài boolean thông thường:

| Operator | Đọc | Nghĩa |
|---|---|---|
| $G \phi$ | Globally $\phi$ | $\phi$ đúng tại mọi thời điểm |
| $F \phi$ | Finally $\phi$ | $\phi$ đúng tại một thời điểm trong tương lai |
| $X \phi$ | Next $\phi$ | $\phi$ đúng tại thời điểm kế tiếp |
| $\phi U \psi$ | $\phi$ Until $\psi$ | $\phi$ đúng cho tới khi $\psi$ đúng |

Kết hợp boolean ($\land, \lor, \neg$) và temporal, ta diễn đạt được hầu hết property thực tế.

### Ví dụ LTL formula

**"Safety: không bao giờ chia cho 0"**:
$$G \neg (\text{div\_op} \land \text{denominator} = 0)$$

**"Liveness: mọi request rồi sẽ có response"**:
$$G (\text{request} \implies F \text{response})$$

**"Sau lock phải có unlock trước khi lock lại"**:
$$G (\text{lock} \implies X (\neg \text{lock} U \text{unlock}))$$

**"Sau khi malloc, không free trước khi dùng"** (xấp xỉ):
$$G (\text{malloc}(p) \implies (\text{not free}(p)) U \text{use}(p))$$

LTL là powerful: diễn đạt được hầu hết safety và liveness property mà ta gặp trong practice.

## Büchi automaton: machine cho LTL

Để implement runtime monitor, ta cần "biến" LTL formula thành thứ có thể chạy. Cách phổ biến: dịch sang **Büchi automaton (BA)**.

### Định nghĩa

Büchi automaton là finite-state automaton trên infinite word. Cấu trúc:

- $Q$: tập state.
- $\Sigma$: alphabet (tập event).
- $\delta: Q \times \Sigma \to 2^Q$: transition.
- $q_0 \in Q$: initial state.
- $F \subseteq Q$: accepting state.

Khác automaton thông thường: BA accept **infinite word** $w = a_1 a_2 a_3 \ldots$ nếu có run vô hạn đi qua một state trong $F$ **vô hạn lần**.

Định lý: với mỗi LTL formula $\phi$, tồn tại Büchi automaton $\mathcal{A}_\phi$ accept đúng các infinite word thoả $\phi$.

### Ví dụ BA

LTL: $G p$ ("$p$ luôn đúng").

BA tương ứng có 1 state, là accepting, transition tự loop với event $p$. Nếu gặp $\neg p$, transit sang state non-accepting (sink). Word vô hạn chỉ accept nếu mọi event là $p$.

```
        p
       ┌──┐
       v  │
    →(q0)─┘    q0 accepting
       │ ¬p
       v
      (q1)     q1 non-accepting (sink)
       │
       └─┐
         │ any
         v
       (q1)
```

LTL: $F p$ ("rồi $p$ sẽ đúng").

BA có 2 state: q0 (chưa gặp p), q1 (đã gặp p). q1 accepting. Transition: q0 với $\neg p$ → q0; q0 với $p$ → q1; q1 → q1.

Word infinite cần accept khi cuối cùng gặp $p$ rồi stay tại q1 mãi (đi qua q1 vô hạn lần).

## Dùng BA cho runtime monitoring

Algorithm:

```
def monitor(events_stream, ba):
    state = ba.initial_state
    for event in events_stream:
        state = ba.transition(state, event)
        if state == sink_state:
            alert("Property violated")
            break
```

Mỗi event từ chương trình (function call, variable update, network message), monitor transit BA. Nếu vào sink state (bad), alert.

Đây là **online monitoring**: process event real-time, không cần lưu toàn bộ trace.

### Implementation trên Java với AspectJ

```java
@Aspect
public class MutexMonitor {
    private State currentState = State.UNLOCKED;
    
    @Before("execution(* lock(..))")
    public void onLock() {
        if (currentState == State.LOCKED) {
            // Vi phạm: đã lock, lại lock nữa (double lock)
            throw new RuntimeException("Property violation: double lock");
        }
        currentState = State.LOCKED;
    }
    
    @Before("execution(* unlock(..))")
    public void onUnlock() {
        if (currentState == State.UNLOCKED) {
            throw new RuntimeException("Property violation: unlock without lock");
        }
        currentState = State.UNLOCKED;
    }
}
```

Đây là BA đơn giản với 2 state (LOCKED, UNLOCKED), implement bằng aspect. Tự động chạy trước mỗi `lock()` và `unlock()` trong codebase.

## Online vs Offline monitoring

**Online monitor**: chạy đồng thời với chương trình. Alert real-time. Phù hợp production. Overhead vài %.

**Offline monitor**: log mọi event ra file, chạy monitor trên file sau khi chương trình kết thúc. Phù hợp post-mortem analysis. Không có overhead runtime nhưng cần I/O lớn.

Một số tool support cả hai: log everything in production, replay với BA monitor khi cần.

## Soundness của monitoring

**Vấn đề**: BA có chỉ chứng minh được safety property (counterexample hữu hạn). Liveness property cần infinite trace, monitor không thể "đợi mãi".

Giải pháp:
- **Bounded liveness**: thay $F \phi$ bằng "$\phi$ xảy ra trong $k$ event tới". Hữu hạn, monitor được.
- **Robust liveness**: định nghĩa "vi phạm liveness" là "đã $k$ event mà $\phi$ chưa xảy ra".

Hầu hết production monitor dùng bounded liveness ($k$ là timeout).

## Generating Büchi automaton từ LTL

Manual: cho LTL nhỏ, vẽ BA tay. Đã thấy ví dụ $G p$, $F p$.

Automated: tool **LTL2BA**, **Spot**. Input là LTL formula, output là Büchi automaton.

Algorithm gốc: **Vardi-Wolper construction**. Build BA exponential trong size LTL formula. Modern optimization (alternating automata, generalized BA) giảm size đáng kể.

Trong thực tế, code monitoring thường có LTL formula nhỏ (1-2 operator), BA chỉ vài state, dễ implement tay.

## Tool monitoring trong industry

**AspectJ** (Java): aspect-oriented programming, dễ inject monitor.

**DTrace** (Solaris, macOS, FreeBSD): probe-based, kernel + userland.

**eBPF** (Linux modern): runtime kernel program, monitor mọi syscall, network event. Cực kỳ powerful.

**Splunk**: enterprise log monitoring, có thể implement BA qua query.

**Prometheus + Grafana**: metric-based monitor, alert qua threshold.

**Datadog APM**: trace-based, application performance monitoring với security extension.

## Ứng dụng security

Runtime monitor cho security:

**Anomaly detection**: monitor mọi syscall, alert nếu có syscall lạ (process tạo network connection bất thường).

**File integrity monitoring (FIM)**: monitor `/etc/passwd`, `/etc/shadow`. Alert nếu sửa.

**Authentication monitoring**: count fail login, alert nếu vượt threshold (brute force).

**Privilege escalation detection**: monitor execve của setuid binary, alert nếu user gọi không đúng context.

**Network anomaly**: monitor traffic pattern, alert outbound to suspicious IP.

Combine với SIEM (Security Information and Event Management) như Splunk, ELK, để có visibility toàn bộ infrastructure.

## Tóm tắt

- **Monitoring** check property tại runtime, bổ sung testing/verification.
- **LTL** diễn đạt temporal property (safety và liveness).
- **Büchi automaton** là machine để implement LTL monitor, chạy song song với chương trình.
- **Online** monitor real-time, **offline** monitor log replay.
- Tools: AspectJ, DTrace, eBPF, Splunk, Prometheus.
- Ứng dụng security: anomaly detection, FIM, authentication monitoring.

## Mini-quiz

<details>
<summary>Q1. Phân biệt safety và liveness trong context monitoring.</summary>

**Safety** ("điều xấu không xảy ra"): counterexample hữu hạn. Khi vi phạm xảy ra, monitor phát hiện ngay tại event đó. Ví dụ: "không double lock" - khi gặp lock lần 2 mà đã lock, alert ngay.

**Liveness** ("điều tốt sẽ xảy ra"): counterexample vô hạn. Monitor không thể "đợi mãi" để chứng minh liveness violation. Cần **bounded liveness**: timeout sau $k$ event.

Ví dụ: "request rồi sẽ có response" - không thể đợi vô hạn. Bounded: "request có response trong 5 giây". Alert nếu sau 5 giây không response.

Hầu hết production monitor dùng bounded liveness vì soundly chạy được.
</details>

<details>
<summary>Q2. Tại sao Büchi automaton accept infinite word thay vì finite word?</summary>

LTL property thường liên quan execution **vô hạn** (chương trình chạy forever, như daemon, server). Property $G p$ ("luôn $p$") cần xem toàn bộ infinite trace.

Finite-word automaton (DFA, NFA) không đủ: chỉ accept/reject finite word.

Büchi giải quyết: accept infinite word nếu có run đi qua accepting state **vô hạn lần**. Vì state hữu hạn nhưng word vô hạn, run phải lặp lại state. Lặp trên accepting → accept.

Trong monitoring, ta chỉ process prefix hữu hạn của infinite trace (chương trình chưa kết thúc). BA phát hiện vi phạm khi vào sink state (bad state không escape được), không cần đợi infinity.
</details>

<details>
<summary>Q3. eBPF có gì đặc biệt cho monitoring so với DTrace?</summary>

**DTrace** (1990s, Solaris): probe-based, có ngôn ngữ D để write monitor script. Portable cho macOS, FreeBSD. Linux có port nhưng chưa được adopt rộng.

**eBPF** (2014, Linux): tương tự về concept (probe + script), nhưng:
- **Native trên Linux**: không cần kernel patch, ship sẵn.
- **JIT compile**: script eBPF được compile thành native code, chạy in kernel space, rất nhanh.
- **Safe**: verifier check script không crash kernel trước khi load.
- **Versatile**: probe syscall, network, file system, even userland (uprobes).

Modern security tool dùng eBPF: Falco (Sysdig), Cilium (CNCF), Tetragon. Hầu hết observability stack hiện đại trên Linux đều base on eBPF.

Trade-off: eBPF require Linux 4.x+, không portable. DTrace portable hơn nhưng chậm hơn.
</details>

---

**Tiếp theo**: [5.5 Fuzzing basics](./05-fuzzing-basics)
