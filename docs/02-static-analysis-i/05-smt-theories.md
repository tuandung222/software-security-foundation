---
id: 05-smt-theories
title: 3.5 SMT theories
sidebar_position: 5
description: SMT mở rộng SAT bằng các theory chuyên biệt. Lazy SMT vs eager SMT, các theory phổ biến (LIA, LRA, BV, A, FP, UF), Nelson-Oppen combination để ghép nhiều theory.
---

# 3.5 SMT theories: Khi SAT không đủ

> **Tóm tắt một dòng**: SMT solver mở rộng SAT bằng các **theory chuyên biệt** cho từng kiểu dữ liệu (số nguyên, bitvector, mảng, hàm). Kiến trúc DPLL(T) phối hợp SAT solver với "decision procedure" cho mỗi theory. Cho phép verifier diễn đạt và giải bài toán phức tạp hơn nhiều so với SAT thuần.

## Vì sao SAT chưa đủ?

Ở bài 3.4, ta thấy SAT giải bài toán "công thức boolean có thoả không?". Đó là một engine cực mạnh, nhưng có một hạn chế lớn: **chỉ làm việc với biến boolean**. Khi muốn diễn tả các ràng buộc phong phú hơn của chương trình, ta phải dịch về boolean, và bản dịch có thể rất dài.

Hãy thử ví dụ đơn giản. Bạn muốn check một property: "với $x, y \in \{0, 1, \ldots, 100\}$, tồn tại nào làm $x + y > 150$ không?". Để encode dưới SAT thuần, ta phải:

1. Biểu diễn $x$ bằng 7 bit boolean (vì $100 < 128 = 2^7$): $x_0, x_1, \ldots, x_6$.
2. Tương tự cho $y$.
3. Implement phép cộng $x + y$ bằng các cổng AND, OR, XOR (full adder), tạo ra ~30 biến boolean phụ.
4. So sánh kết quả với 150, dùng so sánh bitvector (thêm ~20 biến phụ).
5. Cuối cùng có công thức boolean ~60 biến, vài chục clause.

Vất vả! Hơn nữa, mọi lần thay đổi nhỏ (đổi 100 thành 1000) đều phải encode lại. Đây là cách tiếp cận **eager SMT** mà ta sẽ nói chi tiết bên dưới.

Cách thông minh hơn: cho phép ta viết trực tiếp `x + y > 150` với $x, y$ là số nguyên, và để solver tự xử lý phần arithmetic. Đó chính là **SMT solver**.

SMT = **S**atisfiability **M**odulo **T**heories. "Modulo" có nghĩa "với điều kiện kèm theo": SMT kiểm tra satisfiability của công thức **modulo** các theory được tích hợp.

## Các theory phổ biến

Mỗi theory cung cấp ngôn ngữ riêng để diễn đạt một loại constraint. Đây là các theory quan trọng nhất trong verification:

### Theory of Equality and Uninterpreted Functions (EUF, UF)

Theory đơn giản nhất. Cho phép viết:
- `(= a b)`: a bằng b.
- `(f a)`: hàm `f` áp dụng vào `a` (nhưng không biết `f` là gì).

Tính chất quan trọng: nếu `(= a b)`, thì `(= (f a) (f b))` đúng (functional consistency). 

Ví dụ ràng buộc EUF:

```scheme
(declare-sort U)
(declare-fun f (U) U)
(declare-const a U)
(declare-const b U)
(assert (= (f a) b))
(assert (= a (f b)))
(assert (not (= a b)))
```

Solver phải kiểm tra có nghiệm không. Phân tích: từ `(= (f a) b)` và `(= a (f b))`, áp `f` cả hai vế của phương trình thứ hai: `(= (f a) (f (f b)))`. Kết hợp với phương trình đầu: `(= b (f (f b)))`. Kết hợp lần nữa: từ `(= (f a) b)` có `(= (f (f b)) (f b))` (áp `f` vào hai vế `(= a (f b))`). Vậy `b = (f b)`. Tương tự dẫn tới $a = b$, mâu thuẫn với `(not (= a b))`. UNSAT.

EUF dùng cho verification của compiler optimization, abstract function call.

### Linear Integer Arithmetic (LIA) và Linear Real Arithmetic (LRA)

Theory cho số nguyên (LIA) hoặc số thực (LRA), với các phép `+, -, ≤, <, =` và nhân với hằng số.

Ví dụ:

```scheme
(declare-const x Int)
(declare-const y Int)
(assert (>= x 0))
(assert (>= y 0))
(assert (= (+ x y) 100))
(assert (< (- x y) 10))
(check-sat)
```

Tìm $x, y \geq 0$ thoả $x + y = 100$ và $x - y < 10$. Solver dùng thuật toán **Simplex** (giống Linear Programming) để giải.

LIA decidable nhưng tốn kém hơn LRA (do constraint nguyên). LRA decidable polynomial time với simplex.

:::warning[Linear vs Non-linear]
"Linear" rất quan trọng. `(= z (* 2 x))` là linear (nhân với hằng số 2). `(= z (* x y))` là **non-linear** (nhân hai biến). Non-linear integer arithmetic (NIA) là **undecidable** (Matiyasevich, 1970). Tool SMT có thể "thử" giải NIA nhưng không guarantee.
:::

### Bitvector Theory (BV)

Theory cho số bit-precise, mimic semantics của C/C++/Java. Đại diện số bằng dãy bit có độ dài cố định.

Ví dụ:

```scheme
(declare-const x (_ BitVec 32))
(declare-const y (_ BitVec 32))
(assert (= y (bvmul x x)))
(assert (bvslt y #x00000000))   ; y < 0 trong signed
(check-sat)
```

Hỏi: có $x$ nào làm $x \cdot x$ wrap thành số âm? Solver trả `sat` với $x = 46341$ (hoặc tương đương) cho $x^2 = 2147488281$, wrap về số âm 32-bit.

BV thực hiện qua **bit-blasting**: dịch mọi phép BV thành mạch boolean, gọi SAT solver giải. Đây là lý do BV thường chậm hơn LIA nhưng chính xác hơn cho semantics C. Chi tiết bit-blasting ở [bài 4.3](../03-static-analysis-ii/03-bit-blasting-and-arrays).

### Array Theory (A)

Theory cho mảng kích thước bất kỳ với hai phép cơ bản:

- `(select arr i)`: đọc phần tử thứ `i`.
- `(store arr i v)`: tạo mảng mới giống `arr` nhưng phần tử `i` thành `v`.

Tiên đề (axiom) quan trọng:

$$\text{select}(\text{store}(a, i, v), j) = \begin{cases} v & \text{nếu } i = j \\ \text{select}(a, j) & \text{nếu } i \neq j \end{cases}$$

Đây là axiom **read-over-write**: đọc một index ngay sau khi ghi vào index đó cho ra giá trị vừa ghi; đọc index khác cho ra giá trị cũ.

Array theory dùng để model **memory** trong chương trình C. Mọi `*p`, `a[i]` đều dịch thành `(select)`. Mọi `*p = v`, `a[i] = v` dịch thành `(store)`. Chi tiết encoding ở [bài 3.7](./07-encoding-pointers-and-memory).

### Floating-Point Theory (FP)

Theory cho số dấu phẩy động theo chuẩn IEEE 754. Hỗ trợ chính xác `float`, `double`, `quad` với mọi rounding mode, special value (NaN, ±Inf, denormalized).

```scheme
(declare-const x (_ FloatingPoint 8 24))   ; float 32-bit
(declare-const y (_ FloatingPoint 8 24))
(assert (= y (fp.add roundNearestTiesToEven x x)))
(assert (fp.isNaN y))
(check-sat)
```

Hỏi: có float $x$ nào làm $x + x$ là NaN? Solver trả `sat` nếu $x = $ NaN (vì NaN + NaN = NaN).

FP theory rất chậm vì semantics phức tạp. Nhưng cần thiết cho verify code làm phép tính thực, ví dụ engine vật lý, ML inference. Chi tiết ở [bài 3.6](./06-encoding-numbers-and-floats).

### String Theory (S)

Theory cho chuỗi ký tự, hỗ trợ `(str.contains)`, `(str.length)`, `(str.replace)`, regex matching.

Dùng để verify code xử lý chuỗi: parser, sanitizer, regex matcher. Tool: Z3-str, CVC5.

## Kiến trúc DPLL(T): cốt lõi SMT solver hiện đại

Câu hỏi: SMT solver kết hợp SAT solver với các theory như thế nào?

Có hai cách tiếp cận chính: **Eager SMT** và **Lazy SMT**. Hiện tại Lazy SMT (cụ thể là kiến trúc **DPLL(T)**) là chiếm ưu thế.

### Eager SMT

Dịch toàn bộ công thức SMT thành công thức SAT trước, rồi gọi SAT solver một lần.

Ví dụ công thức `(< x 5) AND (> x 3)` với $x \in \mathbb{Z}$:
- Eager: encode `x` thành bit vector 8-bit (`x_0, ..., x_7`), encode `(< x 5)` thành mạch so sánh bit, encode `(> x 3)` tương tự, gọi SAT giải.
- Pros: chỉ cần một SAT solver, đơn giản.
- Cons: bit-blasting làm công thức cực lớn (cubic hoặc tệ hơn). Bay thông tin cấu trúc của theory.

Tool: Z3 mặc định dùng eager cho BV. Boolector hoàn toàn eager.

### Lazy SMT với DPLL(T)

Tách công thức boolean (do SAT solver xử lý) khỏi phần theory (do **theory solver** xử lý). Phối hợp qua một giao diện chuẩn.

Hoạt động:

1. **Abstraction**: thay mỗi atom theory bằng một biến boolean. Ví dụ `(< x 5)` được abstract thành biến `p1`. `(> x 3)` thành `p2`. Công thức gốc `(< x 5) AND (> x 3)` thành công thức boolean `p1 AND p2`.

2. **SAT solver**: giải công thức boolean. Nếu UNSAT, output UNSAT. Nếu SAT với model $\{p_1 = 1, p_2 = 1\}$, gửi cho theory solver.

3. **Theory check**: theory solver kiểm tra "có giá trị $x$ làm $p_1$ true ($x < 5$) và $p_2$ true ($x > 3$) không?". Có ($x = 4$). Output SAT.

4. **Theory conflict**: nếu theory solver nói "không có giá trị $x$ nào thoả", nó trả về **theory lemma** (một clause boolean ràng buộc các literal theory phải mâu thuẫn). Thêm lemma vào SAT, lặp lại.

Lazy SMT giống như SAT + plug-in cho từng theory. Mỗi theory chỉ cần implement một **decision procedure** trả lời "tập literal này có thoả được không?".

### DPLL(T): incremental version

DPLL(T) là Lazy SMT thực hiện theo cách **incremental**, gọi theory solver mỗi khi SAT solver gán thêm một literal, không đợi đến cuối. Như vậy theory conflict được phát hiện sớm, học conflict clause hiệu quả hơn.

Đây là kiến trúc của Z3, CVC5, Yices, MathSAT, hầu hết SMT solver thương mại và open source.

## Nelson-Oppen: ghép nhiều theory

Câu hỏi tiếp: nếu công thức dùng cả LIA và Array, làm thế nào? Ví dụ:

```scheme
(declare-const arr (Array Int Int))
(declare-const i Int)
(assert (= (select arr i) (+ i 1)))
(assert (= i 5))
(check-sat)
```

Phần `(= (select arr i) (+ i 1))` cần cả Array theory và LIA: `select` thuộc Array, `+` thuộc LIA.

**Nelson-Oppen combination procedure** (1979) là thuật toán ghép decision procedure của nhiều theory để có decision procedure tổng. Yêu cầu:

1. Mỗi theory phải có decision procedure riêng.
2. Các theory phải **disjoint** về signature (không chia sẻ symbol).
3. Theory phải **stably infinite** (có vô hạn model).

Thuật toán:

1. **Purify**: tách công thức thành các sub-formula, mỗi cái thuần một theory. Dùng biến intermediate để chia sẻ giá trị giữa các sub-formula.
2. **Equality propagation**: nếu một theory suy ra `x = y`, lan toả equality này sang các theory khác. Mỗi theory phải có khả năng phát hiện và "broadcast" equality.
3. **Conflict propagation**: nếu một theory phát hiện UNSAT, output UNSAT toàn cục.

Nelson-Oppen có tính chất "sound and complete" cho các theory thoả điều kiện. Đây là kỹ thuật cốt lõi đằng sau khả năng combo theory của Z3 và CVC5.

## Ví dụ chạy DPLL(T) từng bước

Cho công thức SMT:

```scheme
(declare-const x Int)
(declare-const y Int)
(assert (or (< x 0) (< y 0)))
(assert (> (+ x y) 5))
(assert (< x 3))
(assert (< y 4))
```

Hỏi: có $x, y$ thoả tất cả không?

**Bước 1**: Abstract atom theory thành biến boolean:
- $p_1$ ↔ `(< x 0)`
- $p_2$ ↔ `(< y 0)`
- $p_3$ ↔ `(> (+ x y) 5)`
- $p_4$ ↔ `(< x 3)`
- $p_5$ ↔ `(< y 4)`

Công thức boolean: $(p_1 \lor p_2) \land p_3 \land p_4 \land p_5$.

**Bước 2**: SAT solver. Unit propagation cho $p_3, p_4, p_5$ thành true. Branching trên $p_1, p_2$. Thử $p_1 = 1, p_2 = 0$.

Model boolean: $\{p_1 = 1, p_2 = 0, p_3 = 1, p_4 = 1, p_5 = 1\}$.

**Bước 3**: Theory check. Gửi cho LIA solver:
- $p_1 = 1$: $x < 0$.
- $p_2 = 0$: $\neg(y < 0)$, tức $y \geq 0$.
- $p_3 = 1$: $x + y > 5$.
- $p_4 = 1$: $x < 3$.
- $p_5 = 1$: $y < 4$.

Có $x < 0, y \geq 0, x + y > 5, y < 4$. Từ $y < 4$ và $x + y > 5$: $x > 1$. Mâu thuẫn với $x < 0$.

LIA conflict: tập $\{p_1, \neg p_2, p_3, p_5\}$ mâu thuẫn. Theory lemma: $\neg p_1 \lor p_2 \lor \neg p_3 \lor \neg p_5$. Thêm vào SAT.

**Bước 4**: SAT solver tiếp tục với lemma mới. Buộc $p_1 = 0$ hoặc $p_2 = 1$. Thử $p_1 = 0, p_2 = 1$.

Theory check: $x \geq 0, y < 0, x + y > 5, x < 3, y < 4$. Từ $x < 3$ và $x + y > 5$: $y > 2$. Mâu thuẫn $y < 0$.

LIA conflict tương tự. Thêm lemma, SAT propagate, không có cách nào thoả cả $(p_1 \lor p_2)$ kèm các ràng buộc.

**Output**: UNSAT.

## So sánh các SMT solver

| Solver | Thế mạnh | Tốt cho |
|---|---|---|
| **Z3** (Microsoft) | All-around mạnh, API tốt, license MIT | Verification, hardware, software |
| **CVC5** (Stanford) | Strings, datatypes, separation logic | Web security, smart contract |
| **Yices** (SRI) | Rất nhanh cho QF_BV, LIA | Hardware verification |
| **MathSAT** (FBK) | Interpolation cho IC3 | Model checking, IC3 |
| **Boolector** (now Bitwuzla) | Pure BV, eager | Bitvector heavy |

Trong BMC, CBMC dùng MiniSat (SAT), ESBMC dùng Z3 hoặc CVC5 (SMT).

## Tóm tắt

- **SMT** mở rộng SAT bằng các **theory** cho data type chuyên biệt.
- **Theory phổ biến**: EUF, LIA, LRA, BV, Array, FP, String.
- **DPLL(T)** là kiến trúc Lazy SMT chiếm ưu thế: SAT solver phối hợp với theory solver theo incremental fashion.
- **Nelson-Oppen** ghép nhiều theory disjoint thành decision procedure tổng.
- BMC thường dùng SMT logic **QF_AUFBV** (Quantifier-Free Array UF Bitvector) cho C.

## Mini-quiz

<details>
<summary>Q1. Vì sao gọi là "Modulo Theories"?</summary>

"Modulo" trong toán nghĩa là "với điều kiện kèm theo". SMT kiểm tra satisfiability **với điều kiện** các theory đã được tích hợp đang hoạt động.

Ví dụ một công thức `(< x 5) AND (> x 10)` là UNSAT modulo LIA (theory số nguyên), vì LIA biết không có số nguyên nào vừa < 5 vừa > 10. Nhưng nếu coi `<` và `>` chỉ là predicate boolean không có nghĩa, công thức trên SAT (gán cả hai true).

Nói cách khác, SMT solver kiểm tra "có model nào thoả công thức **và** thoả mọi tiên đề của các theory tích hợp không?".
</details>

<details>
<summary>Q2. Phân biệt Eager SMT và Lazy SMT (DPLL(T)). Cái nào phổ biến hơn?</summary>

**Eager SMT**: dịch toàn bộ công thức SMT thành SAT formula trước (bit-blasting hoặc cách tương đương), rồi gọi SAT solver một lần. Đơn giản nhưng formula nổ về kích thước.

**Lazy SMT (DPLL(T))**: tách boolean (SAT solver) khỏi theory (theory solver). SAT giải phần boolean, theory solver kiểm tra theory constraint. Khi theory conflict, theory trả lemma về SAT.

DPLL(T) phổ biến hơn vì:
- Không cần bit-blast tất cả (formula nhỏ hơn).
- Có thể tận dụng decision procedure mạnh cho từng theory (Simplex cho LIA, congruence closure cho EUF).
- Dễ extend với theory mới: chỉ cần implement decision procedure.

Eager vẫn dùng cho pure BV (Bitwuzla), khi theory không có decision procedure efficient.
</details>

<details>
<summary>Q3. Nelson-Oppen yêu cầu các theory phải "disjoint signature". Vì sao?</summary>

"Disjoint signature" nghĩa là hai theory không dùng chung symbol. Ví dụ LIA dùng `+, -, <` cho số nguyên, Array dùng `select, store` cho mảng. Không overlap.

Vì sao cần? Vì Nelson-Oppen hoạt động bằng cách **purify** công thức: chia thành sub-formula thuần một theory. Nếu hai theory dùng chung symbol (ví dụ cả LIA và LRA đều dùng `+`), thì khi gặp `(+ x y)` không biết là `+` của LIA hay LRA.

Trong thực tế, các theory được thiết kế disjoint từ đầu. Khi cần kết hợp số nguyên với real, dùng theory mixed Int-Real có sẵn (LIRA) thay vì ghép LIA + LRA bằng Nelson-Oppen.
</details>

:::tip[DS perspective]
SMT theory giống **specialized solver** trong optimization: LIA ≈ Integer Programming solver, LRA ≈ Linear Programming, NRA ≈ nonlinear (NLP), FP ≈ floating-point arithmetic. Nelson-Oppen combination tương tự **column generation** hay **Benders decomposition** - chia bài toán lớn thành sub-problem theo domain rồi exchange info. Nếu bạn từng dùng `scipy.optimize` chọn method khác nhau cho linear vs nonlinear, bạn đã hiểu trực giác về SMT theory selection.
:::

---

**Tiếp theo**: [3.6 Encoding numbers và floats](./06-encoding-numbers-and-floats)
