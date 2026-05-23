---
id: ds-perspective
title: DS perspective - đối chiếu Software Security với ML/DS
sidebar_position: 4
description: "Tài liệu phụ trợ cho người có nền Data Science / Machine Learning. Mỗi concept Software Security có analogy trong DS/ML giúp hiểu nhanh hơn."
---

# DS perspective: đối chiếu Software Security ↔ ML/DS

> **Tóm tắt một dòng**: Nếu bạn đến từ Data Science hoặc Machine Learning, nhiều concept trong Software Security có **analogy gần** với những gì bạn đã quen. Bài này tổng hợp các analogy đó, giúp bạn map kiến thức mới vào framework cũ và học nhanh hơn.

## Tại sao bài này tồn tại?

Tài liệu Software Security mặc định người đọc quen với system programming (C, pointer, memory). DS scientist thường mạnh về Python, statistics, optimization, model training - không mạnh về memory model hay concurrency.

Tin tốt: **rất nhiều ý tưởng cốt lõi đã có tương đương** trong DS/ML world. Hiểu được analogy giúp bạn:

1. Học nhanh hơn vì có "anchor" đã quen.
2. Nhớ lâu hơn vì kết nối nhiều giác quan.
3. Giảng cho người khác (cả DS và non-DS) dễ hơn.

Bài này không thay thế bài giảng chính - đọc bài giảng chính trước, dùng bài này như reference.

## 1. SAT / SMT solver ↔ Constraint Satisfaction Problem

| Software Security | DS / ML |
|---|---|
| SAT solver | CSP solver trong scheduling (timetable, sudoku) |
| SMT solver | Specialized solver như `cvxpy` cho convex optimization |
| Boolean variable | Decision variable trong MILP |
| Clause | Constraint |
| Unit propagation | Constraint propagation (AC-3 trong CSP) |
| Backtracking | Branch-and-bound trong MILP |
| Theory (LIA, BV, FP) | Domain-specific solver (LP cho linear, NLP cho nonlinear) |
| Counterexample | Infeasible point in optimization |

**Insight chung**: cả SAT/SMT và CSP/MILP đều giải bài toán "tìm assignment thoả constraint". Khác biệt: SAT/SMT focus vào correctness (binary thoả/không), MILP focus vào optimal (objective function).

**Lợi thế DS**: bạn đã biết cách model bài toán dưới dạng constraint. Chỉ cần học syntax SMT-LIB là dùng được Z3/CVC5 ngay.

## 2. Abstract Interpretation ↔ Interval Analysis trong ML

| Software Security | DS / ML |
|---|---|
| Abstract domain (interval, polyhedra) | Confidence interval, prediction range |
| Sound over-approximation | Conservative bound (e.g. Bayesian credible interval) |
| Widening operator | Early stopping, regularization (force convergence) |
| Fixpoint iteration | Iterative training till convergence |
| Concretization | Get point estimate from posterior |

**Insight**: cả 2 đều "thay vì track giá trị chính xác (đắt), track range (rẻ)". Sound over-approximation giống Bayesian: thà bound rộng còn hơn miss.

ML interpretability tool **LIME, SHAP** cũng compute "bound for prediction sensitivity" - tương tự abstract interpretation trace bound for variable.

## 3. Bounded Model Checking ↔ Loop Unrolling trong RNN

| Software Security | DS / ML |
|---|---|
| Unwind loop tới depth k | Unroll RNN qua T timestep |
| SSA encoding | Computational graph của PyTorch/TensorFlow |
| Path constraint | Backward pass collecting gradient |
| SMT formula | Loss function của entire unrolled graph |
| Solver finds counterexample | Optimizer finds adversarial example |

**Insight**: BMC dịch chương trình thành **một công thức lớn**, giống cách TensorFlow build computational graph rồi compute. SMT solver search assignment thoả constraint = optimizer search input minimizing loss.

**Adversarial example** trong ML chính là **counterexample** trong BMC: input nhỏ làm output sai. Cùng triết lý "stress test với worst-case input".

## 4. Coverage Criteria ↔ Cross-Validation

| Software Security | DS / ML |
|---|---|
| Statement coverage | Fraction of data seen during training |
| Decision coverage (branch) | Stratified sampling: every class covered |
| MC/DC | Feature interaction testing (ANOVA) |
| Path coverage | Exponential combinatorial coverage |
| Coverage as quality metric | k-fold CV score |
| Uncovered branch | Underrepresented subgroup in training set |

**Insight**: coverage trong testing trả lời "tôi đã test bao nhiêu phần code?" giống "tôi đã thấy bao nhiêu phần data?" trong ML.

MC/DC đặc biệt giống **factorial design** trong DOE: với $n$ feature binary, cần $\geq n+1$ test để cover mọi pair interaction. ANOVA trong statistics dùng cùng ý tưởng.

## 5. Fuzzing ↔ Data Augmentation và Adversarial Training

| Software Security | DS / ML |
|---|---|
| Seed corpus | Training data |
| Mutation strategy | Data augmentation (flip, rotate, noise) |
| Coverage-guided fuzzing | Active learning: select most informative sample |
| AFL energy schedule | Curriculum learning: schedule difficulty |
| Crash | Misclassification |
| White-box (DSE) fuzzing | Adversarial attack với gradient (FGSM, PGD) |
| Hybrid AFL+DSE (Driller) | Hybrid genetic + gradient (CMA-ES warm-started) |

**Insight chính**: fuzzing là **search trong input space để tìm input gây fail**. ML adversarial attack identical.

- AFL ≈ genetic algorithm (mutation + selection by fitness=coverage).
- DSE ≈ gradient-based attack (use derivative information).
- Hybrid = best of both world.

**Lợi thế DS**: bạn đã biết về data augmentation, generative model, adversarial example. Fuzzing chỉ là "adversarial example tìm bug thay vì fool classifier".

## 6. Symbolic Execution ↔ Tracing Computational Graph

| Software Security | DS / ML |
|---|---|
| Symbolic variable | Tensor with `requires_grad=True` |
| Path constraint accumulation | Backward pass accumulating gradient |
| Z3 solve for input | Gradient descent for adversarial input |
| Fork at branch | Conditional in computational graph |
| Concolic execution | PGD attack: concrete + gradient |

**Insight**: PyTorch autograd **literally tracks symbolic dependency** giữa tensor. Khi bạn `loss.backward()`, framework solve "gradient of loss w.r.t. input parameters". Symbolic execution làm tương tự với boolean/integer constraint.

KLEE (symbolic exec tool) và PyTorch share abstraction "build graph of operation, solve for variable".

## 7. Race Condition ↔ Async Training Divergence

| Software Security | DS / ML |
|---|---|
| Data race | Hogwild! async SGD update collision |
| Memory model (TSO, weak) | Eventual consistency in distributed SGD |
| Happens-before relation | Causal dependency in async training |
| Partial-order reduction | Equivalence class trong distributed scheduling |
| Lock-free algorithm | Lock-free training (Hogwild!) |

**Insight**: async SGD (Hogwild!) **literally has data race** giữa worker updating same parameter. Theory paper chứng minh "với learning rate đủ nhỏ, race tolerable". Đây là tradeoff cùng kiểu race condition trong systems code.

DS/ML practitioner đã làm distributed training **đã có intuition** về race condition. Software Security chỉ formalize thêm.

## 8. Buffer Overflow ↔ Out-of-Distribution Input

| Software Security | DS / ML |
|---|---|
| Buffer overflow | OOD input (input outside training distribution) |
| Type confusion | Wrong input type (text into image model) |
| Format string attack | Prompt injection in LLM |
| ROP gadget chain | Adversarial patch composing primitive |
| ASLR | Random seed in dropout |
| Stack canary | Anomaly detector before downstream model |

**Insight**: cả 2 đều "input bất ngờ làm system behavior bất ngờ". Mitigation tương tự:
- Input validation = OOD detection.
- Sandbox = guardrail layer.
- DEP/NX = strict separation of "data" vs "code/instruction".

**LLM prompt injection** đặc biệt giống format string attack: cả 2 đều "data biến thành instruction" do parser không phân biệt rõ.

## 9. Formal Verification ↔ Model Validation Mathematically

| Software Security | DS / ML |
|---|---|
| Verify property of program | Verify property of model (fairness, monotonicity) |
| Soundness | No false negative (don't miss bug / unfair case) |
| Completeness | No false positive |
| Counterexample-guided abstraction refinement (CEGAR) | Active learning loop |
| Bounded model checking | Empirical robustness testing with bounded perturbation |
| Theorem proving (Coq, Lean) | Proof of generalization bound |

**Insight**: PAC learning, VC bound, Rademacher complexity là formal verification của ML model. Cộng đồng dùng từ khác ("learning theory") nhưng essence giống.

Modern field **certified robust ML** (Wong et al., interval bound propagation) thực sự dùng kỹ thuật abstract interpretation từ Software Security, áp dụng cho neural network.

## 10. Threat Model ↔ Failure Mode Analysis

| Software Security | DS / ML |
|---|---|
| STRIDE threat | Failure mode (FMEA in engineering) |
| Attack tree | Fault tree |
| Threat intel | Concept drift monitoring |
| Red team exercise | Adversarial testing |
| Defense in depth | Ensemble model (multiple defenses) |
| Zero trust | Skeptical pipeline (verify input at every stage) |

**Insight**: threat model = systematic enumeration of "what can go wrong". DS có "FMEA" (Failure Mode and Effects Analysis) và "Model card" làm điều tương tự cho ML system.

## 11. Cryptography ↔ Differential Privacy

| Software Security | DS / ML |
|---|---|
| Encryption | Obfuscation / homomorphic encryption |
| Key | Privacy budget $\epsilon$ |
| MAC for integrity | Hash for data versioning |
| Side-channel attack | Membership inference attack |
| Zero-knowledge proof | Federated learning aggregation |

**Insight**: differential privacy trong ML và cryptography trong Software Security share "**mathematical privacy guarantee**" instead of "ad-hoc obfuscation". $\epsilon$-DP cho ML giống "$2^{128}$ security" cho crypto.

## 12. Security Process ↔ MLOps

| Software Security | DS / ML |
|---|---|
| SDLC | ML lifecycle |
| Secure SDLC | MLOps with model monitoring |
| Vulnerability scan | Data quality check, drift detection |
| Patch management | Model retraining schedule |
| SBOM | Model registry, data lineage |
| Incident response | Model rollback procedure |
| Threat intelligence | Concept drift signal |

**Insight**: rất nhiều pattern từ DevSecOps map 1-1 sang MLOps. Hiểu một cái giúp design cái kia.

## Practical Implications cho DS Reader

Nếu bạn là DS scientist đọc tài liệu này:

### Bạn có lợi thế

1. **Bạn quen với constraint satisfaction**: SMT/SAT là natural.
2. **Bạn quen với input space exploration**: fuzzing intuitive.
3. **Bạn quen với gradient + symbolic computation**: KLEE/symbolic exec không quá lạ.
4. **Bạn quen với race trong async training**: data race trong systems code dễ grasp.

### Bạn có gap cần fill

1. **Memory model**: stack/heap/pointer arithmetic chưa quen. Dành thời gian cho [Phụ lục C basics](./appendix-c-basics).
2. **Bitwise operation**: integer overflow, bit-blasting cần intuition về 2's complement.
3. **OS / system call**: TOCTOU race cần biết về file system semantic.
4. **Network protocol**: TLS, OAuth, CORS không phải DS knowledge.

### Strategy học hiệu quả

1. **Đọc phần 1 (Lec 1-2) chậm**, làm bài tập [Exercise Set 1](../exercises/) để build C intuition.
2. **Phần 2-3 (Lec 3-4) đọc nhanh**: SAT/SMT/abstract interp bạn đã có anchor.
3. **Phần 4 (Lec 5) dùng analogy fuzzing-as-adversarial** để hiểu nhanh.
4. **Phần 5 (Lec 6) practical**, không cần background sâu, đọc bất cứ lúc nào.
5. **Phần 7 (Topics Bổ sung) → đặc biệt 7.5 Secure SDLC** vì có direct MLOps analogy.

## Reverse: software security → ML benefit gì?

Học Software Security thường giúp ML practitioner ở những điểm:

1. **Adversarial robustness mindset**: think like attacker, find edge case.
2. **Mathematical bound discipline**: don't trust empirical, prove guarantee.
3. **Threat modeling cho ML system**: privacy leakage, model extraction.
4. **Secure ML deployment**: API auth, input sanitization, model file integrity.
5. **MLOps best practice**: process integration, monitoring, incident response.

Software Security và ML đang **converge**: certified ML, formal verification cho NN, privacy-preserving ML, secure aggregation. Người vững cả 2 sẽ là leader trong field này 5-10 năm tới.

## Tóm tắt bảng đối chiếu nhanh

| Concept Software Security | Best analogy DS/ML |
|---|---|
| SAT/SMT | Constraint satisfaction, MILP |
| Abstract interpretation | Bayesian credible interval |
| BMC | RNN unrolling, computational graph |
| Symbolic execution | PyTorch autograd |
| Coverage | k-fold CV, factorial design |
| Fuzzing | Adversarial example, data augmentation |
| Race condition | Hogwild async SGD |
| Buffer overflow | OOD input, prompt injection |
| Formal verification | PAC bound, certified robust ML |
| Threat model | FMEA, model card |
| Cryptography | Differential privacy |
| Secure SDLC | MLOps |

Lưu bảng này. Khi đọc bài giảng và gặp concept lạ, check bảng để tìm anchor familiar.

## Tham khảo cross-disciplinary

Nếu bạn muốn đào sâu mối quan hệ:

- **Wong et al., "Provable defenses against adversarial examples via the convex outer adversarial polytope"** (ICML 2018): dùng abstract interpretation cho NN.
- **Recht & Roelofs et al., "Hogwild!: A Lock-Free Approach to Parallelizing Stochastic Gradient Descent"** (NIPS 2011): race condition trong ML training.
- **Dwork & Roth, "The Algorithmic Foundations of Differential Privacy"** (2014): mathematical privacy.
- **Mitchell et al., "Model Cards for Model Reporting"** (FAccT 2019): threat model cho ML.

Software Security có nhiều thứ học được từ ML, và ngược lại. Bài này hy vọng tạo bridge cho bạn.
