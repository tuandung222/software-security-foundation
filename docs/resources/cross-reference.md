---
id: cross-reference
title: Cross-reference (bản đồ phụ thuộc)
sidebar_position: 5
description: "Bảng ánh xạ bài → bài liên quan, giúp bạn điều hướng theo nội dung thay vì theo tuần tự cụm."
---

# Cross-reference: bản đồ phụ thuộc giữa các bài

> **Tóm tắt một dòng**: Bảng này cho biết mỗi bài giảng **phụ thuộc** vào bài nào (prerequisite) và **được tham chiếu** bởi bài nào (downstream). Dùng để đọc theo nhu cầu thay vì tuần tự, hoặc để biết cần ôn lại bài nào trước khi đọc bài hiện tại.

## Cách dùng bảng

- **Cột Prerequisites**: bài này dựa trên concept của bài nào, nên đọc chúng trước.
- **Cột Used by**: bài này được tham chiếu trong bài nào, có thể đọc tiếp để thấy ứng dụng.
- **Cột Glossary terms**: thuật ngữ key được định nghĩa lần đầu hoặc nhấn mạnh trong bài.

Bài liệt kê theo thứ tự xuất hiện trong sidebar.

## Lecture 1-2: Foundation

| Bài | Prerequisites | Used by | Glossary terms |
|---|---|---|---|
| [1.1 Software Security là gì](../01-introduction/01-overview) | (none) | mọi bài sau | CIA, Software Security, Safety vs Security |
| [1.2 CIA và Security Properties](../01-introduction/02-cia-and-properties) | 1.1 | 1.4, 6.1-6.5, 7.2 | Confidentiality, Integrity, Availability, Authenticity, Non-repudiation, MAC, Digital Signature |
| [1.3 Vulnerabilities Catalog](../01-introduction/03-vulnerabilities-catalog) | 1.1 | 1.4, 5.5-5.8 | Buffer Overflow, Integer Overflow, Race Condition, TOCTOU, UAF, Format String |
| [1.4 Web Vulnerabilities](../01-introduction/04-web-vulnerabilities) | 1.2, 1.3 | 6.2, 7.3 | SQL Injection, XSS, CSRF, XXE, SSRF, ReDoS |
| [1.5 Formal Verification Intro](../01-introduction/05-formal-verification-intro) | 1.1 | 1.6, 3.1-3.7, 4.1-4.7 | Soundness, Completeness, Safety property, Liveness property, Model Checking, Theorem Proving, Abstract Interpretation |
| [1.6 BMC và SMT basics](../01-introduction/06-bmc-and-smt-basics) | 1.5 | 3.1-3.7, 4.1-4.7, 5.8 | BMC, SAT, SMT, SSA, Counterexample, Unwinding |

## Lecture 3: Static Analysis I (BMC + SMT)

| Bài | Prerequisites | Used by | Glossary terms |
|---|---|---|---|
| [3.1 Overview](../02-static-analysis-i/01-overview) | 1.5, 1.6 | 3.2-3.7 | (recap) |
| [3.2 V&V](../02-static-analysis-i/02-verification-vs-validation) | 1.5 | 5.1, 5.2 | Verification, Validation, V-model, SAST, DAST |
| [3.3 State Space Exploration](../02-static-analysis-i/03-state-space-exploration) | 1.6 | 3.4, 4.1, 4.4 | State Explosion, BFS/DFS, Symbolic Execution |
| [3.4 SAT và DPLL](../02-static-analysis-i/04-sat-and-dpll) | 1.6 | 3.5, 4.3, 5.8 | SAT, DPLL, CDCL, Unit Propagation, VSIDS, Backjumping |
| [3.5 SMT Theories](../02-static-analysis-i/05-smt-theories) | 3.4 | 3.6, 3.7, 4.3 | DPLL(T), EUF, LIA, LRA, Bit-Vector, Array, FP, Nelson-Oppen |
| [3.6 Encoding Numbers and Floats](../02-static-analysis-i/06-encoding-numbers-and-floats) | 3.5 | 3.7, 7.4 | BitVec, IEEE 754, NaN, bvslt vs bvult |
| [3.7 Encoding Pointers and Memory](../02-static-analysis-i/07-encoding-pointers-and-memory) | 3.6 | 4.2, 4.5, 7.4 | Memory Model (fixed/align/offset), array theory axiom, UAF detection |

## Lecture 4: Static Analysis II (Concurrency)

| Bài | Prerequisites | Used by | Glossary terms |
|---|---|---|---|
| [4.1 Overview](../03-static-analysis-ii/01-overview) | 1.6, 3.7 | 4.2-4.7 | (recap) |
| [4.2 Loop Unwinding and Safety](../03-static-analysis-ii/02-loop-unwinding-and-safety) | 3.7 | 4.3, 5.8 | Unwinding, Unwinding Assertion, k-induction, Safety Conditions |
| [4.3 Bit-blasting and Arrays](../03-static-analysis-ii/03-bit-blasting-and-arrays) | 3.5, 3.6, 4.2 | 4.4 | Bit-blasting, Array Axiom, Lambda-term, Eager vs Lazy |
| [4.4 Concurrency Verification](../03-static-analysis-ii/04-concurrency-verification) | 4.3 | 4.5-4.7 | Data Race, Atomicity, Deadlock, Memory Model (SC/TSO/Weak), Happens-before |
| [4.5 Context-bounded Analysis](../03-static-analysis-ii/05-context-bounded-analysis) | 4.4 | 4.6, 4.7 | CBA, Context Switch, Qadeer-Rehof Observation, Round-robin scheduler |
| [4.6 Lazy vs Schedule Recording](../03-static-analysis-ii/06-lazy-vs-schedule-recording) | 4.5 | 4.7 | Lazy Interleaving, Mazurkiewicz Trace, Vector Clock, DPOR |
| [4.7 Sequentialization (KISS, LR)](../03-static-analysis-ii/07-sequentialization-kiss-lr) | 4.5, 4.6 | (terminal) | KISS Sequentialization, LR Scheme, Round-robin abstraction |

## Lecture 5: Dynamic Analysis (Testing + Fuzzing)

| Bài | Prerequisites | Used by | Glossary terms |
|---|---|---|---|
| [5.1 Overview](../04-dynamic-analysis/01-overview) | 3.2 | 5.2-5.8 | (recap) |
| [5.2 Security Testing](../04-dynamic-analysis/02-security-testing) | 3.2 | 5.3, 6.x | Security Testing, Oracle, Vuln Scanning, Pen Testing |
| [5.3 Coverage Criteria](../04-dynamic-analysis/03-coverage-criteria) | 5.2 | 5.5-5.8 | Statement, Branch, Condition, MC/DC, Path coverage |
| [5.4 Monitoring với LTL và Büchi](../04-dynamic-analysis/04-monitoring-ltl-buchi) | 1.5 | (terminal) | LTL, Büchi Automaton, Online/Offline Monitoring, Bounded Liveness |
| [5.5 Fuzzing Basics](../04-dynamic-analysis/05-fuzzing-basics) | 5.3 | 5.6-5.8 | Fuzzing, Random Testing, Seed Corpus, Crash Triage |
| [5.6 Black-box (AFL, grammar, mutation)](../04-dynamic-analysis/06-blackbox-grammar-mutation) | 5.5 | 5.7, 7.4 | AFL, Coverage-guided Fuzzing, Forkserver, Energy Schedule, Grammar-based |
| [5.7 White-box Fuzzing (DSE)](../04-dynamic-analysis/07-whitebox-fuzzing-symbolic) | 3.3, 5.6 | 5.8 | DSE, Symbolic Execution, SAGE, KLEE, Driller (Hybrid) |
| [5.8 BMC for Test Generation](../04-dynamic-analysis/08-bmc-for-test-generation) | 1.6, 5.3, 5.7 | (terminal) | BMC Test Gen, Coverage Goal, CEGAR |

## Lecture 6: Case Study

| Bài | Prerequisites | Used by | Glossary terms |
|---|---|---|---|
| [6.1 Overview](../05-case-study/01-overview) | 1.1-1.5 | 6.2-6.5, 7.5 | STRIDE, DREAD, CVSS, Attack Tree |
| [6.2 Web/SaaS](../05-case-study/02-web-saas) | 1.4, 6.1 | 7.3 | OWASP Top 10, OAuth 2.0, OIDC, MFA, Session Mgmt |
| [6.3 Fintech](../05-case-study/03-fintech) | 1.2, 6.1 | 7.2 | PCI-DSS, KYC, AML, HSM, Key Hierarchy (Master/KEK/DEK) |
| [6.4 IoT](../05-case-study/04-iot) | 1.3, 6.1 | 7.4 | Secure Boot, OTA Update, Memory-safe Embedded, Side-channel |
| [6.5 Enterprise Cloud](../05-case-study/05-enterprise-cloud) | 6.1 | 7.5 | Zero Trust, Microsegmentation, mTLS, Identity Federation (SAML/OIDC), Ransomware 3-2-1 |

## Lecture 7: Topics Bổ sung

| Bài | Prerequisites | Used by | Glossary terms |
|---|---|---|---|
| [7.1 Overview](../06-additional-topics/01-overview) | (none, optional) | 7.2-7.5 | (recap) |
| [7.2 Cryptography Basics](../06-additional-topics/02-cryptography-basics) | 1.2 | 7.3, 7.5 | Hash, bcrypt/argon2, AES-GCM, ChaCha20-Poly1305, RSA, Ed25519, PKI, HKDF |
| [7.3 OWASP Top 10 (2021)](../06-additional-topics/03-owasp-top-10) | 1.4, 6.2, 7.2 | (terminal) | A01-A10, IDOR, SSRF Capital One, IMDSv2 |
| [7.4 CBMC Tutorial](../06-additional-topics/04-cbmc-tutorial) | 1.6, 3.7, 4.4 | (terminal) | CBMC, `--unwind`, `--bounds-check`, `__CPROVER_assume`, `goto-instrument`, ESBMC |
| [7.5 Secure SDLC + SDL + SAMM](../06-additional-topics/05-secure-sdlc) | 6.1 | (terminal) | SDL (12 practice), SAMM (5 BF / 15 practice), DevSecOps, Shift Left, Security Champion |

## Bảng đối chiếu thuật ngữ → bài định nghĩa

Khi đọc gặp thuật ngữ không hiểu, tra ở đây để biết bài nào giới thiệu lần đầu:

| Thuật ngữ | Bài định nghĩa | Glossary entry |
|---|---|---|
| CIA Triad | 1.2 | [Glossary C](./glossary#c) |
| Buffer Overflow | 1.3 | [Glossary B](./glossary#b) |
| SQL Injection | 1.4 | [Glossary S](./glossary#s) |
| XSS / CSRF | 1.4 | [Glossary X](./glossary#x), [C](./glossary#c) |
| Soundness / Completeness | 1.5 | [Glossary S](./glossary#s), [C](./glossary#c) |
| Safety vs Liveness | 1.5 | [Glossary S](./glossary#s), [L](./glossary#l) |
| BMC | 1.6 | [Glossary B](./glossary#b) |
| SAT / SMT | 1.6, 3.4, 3.5 | [Glossary S](./glossary#s) |
| SSA | 1.6 | [Glossary S](./glossary#s) |
| DPLL / CDCL | 3.4 | [Glossary D](./glossary#d), [C](./glossary#c) |
| Nelson-Oppen | 3.5 | [Glossary N](./glossary#n) |
| BitVec / IEEE 754 | 3.6 | [Glossary B](./glossary#b), [I](./glossary#i) |
| k-induction | 4.2 | [Glossary K](./glossary#k) |
| Memory Model (TSO/SC/Weak) | 4.4 | [Glossary T](./glossary#t) |
| CBA | 4.5 | [Glossary C](./glossary#c) |
| DPOR | 4.6 | [Glossary D](./glossary#d) |
| MC/DC | 5.3 | [Glossary M](./glossary#m) |
| LTL / Büchi | 5.4 | [Glossary L](./glossary#l), [B](./glossary#b) |
| AFL | 5.6 | [Glossary A](./glossary#a) |
| DSE / Symbolic Execution | 5.7 | [Glossary D](./glossary#d), [S](./glossary#s) |
| STRIDE | 6.1 | [Glossary S](./glossary#s) |
| OWASP Top 10 | 6.2, 7.3 | [Glossary O](./glossary#o) |
| PCI-DSS | 6.3 | [Glossary P](./glossary#p) |
| Secure Boot / OTA | 6.4 | [Glossary S](./glossary#s), [O](./glossary#o) |
| Zero Trust | 6.5 | [Glossary Z](./glossary#z) |
| bcrypt / argon2 | 7.2 | [Glossary B](./glossary#b) |
| AES-GCM | 7.2 | [Glossary A](./glossary#a) |
| RSA / Ed25519 | 7.2 | [Glossary R](./glossary#r), [E](./glossary#e) |
| HKDF | 7.2 | [Glossary H](./glossary#h) |
| IDOR | 7.3 | [Glossary I](./glossary#i) |
| SSRF | 7.3 | [Glossary S](./glossary#s) |
| CBMC tool | 7.4 | [Glossary C](./glossary#c) |
| SAMM (OWASP) | 7.5 | [Glossary S](./glossary#s) |
| SDL (Microsoft) | 7.5 | [Glossary M](./glossary#m) |
| DevSecOps | 7.5 | [Glossary D](./glossary#d) |

## Đề xuất đường đọc

### Đường đọc 1: tuần tự (default)

Lec 1-2 → 3 → 4 → 5 → 6 → 7. Đầy đủ, ~30-40 giờ đọc + thực hành.

### Đường đọc 2: focus formal verification

1.1, 1.5, 1.6 → 3.1-3.7 → 4.1-4.7 → 5.8, 7.4. Bỏ qua web vuln, case study.

### Đường đọc 3: focus practitioner web/cloud security

1.1, 1.2, 1.4 → 6.1, 6.2 → 7.2, 7.3, 7.5. Bỏ qua chi tiết BMC/SMT.

### Đường đọc 4: focus DS scientist crossover

[DS Perspective appendix](./ds-perspective) → 1.1, 1.5, 1.6 → 3.4 (SAT), 3.5 (SMT) → 5.5, 5.7 (fuzzing as adversarial) → 7.5 (SDLC as MLOps). Tận dụng analogy ML.

### Đường đọc 5: focus IoT/embedded

1.1, 1.3 → 3.6 (BitVec), 3.7 (memory) → 4.4 (concurrency) → 6.4 (IoT) → 7.4 (CBMC tutorial). Bỏ qua web, fintech.

### Đường đọc 6: focus fintech compliance

1.1, 1.2 → 6.1, 6.3 → 7.2 (Crypto basics), 7.5 (Secure SDLC). Bỏ qua BMC kỹ thuật.

## Mục lục liên kết ngoài

| Resource | Mô tả |
|---|---|
| [PDF Downloads](./pdfs) | 6 PDF gộp cho 6 cụm + slide gốc |
| [Glossary 200+ thuật ngữ](./glossary) | Tra cứu Anh-Việt |
| [Exam Checklist](./exam-checklist) | Self-test 90+ điểm kiến thức |
| [Appendix C basics](./appendix-c-basics) | Pointer, stack, heap, UB cho người chưa quen C |
| [DS Perspective](./ds-perspective) | Bảng đối chiếu với ML/DS |
| [Exercise Set 2](../exercises/exercise-set-2) | 7 bài thực hành code C |

Bookmark trang này để điều hướng nhanh.
