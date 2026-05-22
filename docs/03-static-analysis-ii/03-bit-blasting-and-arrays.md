---
id: 03-bit-blasting-and-arrays
title: 4.3 Bit-blasting và arrays
sidebar_position: 3
description: Cách SMT solver dịch bitvector formula sang SAT (bit-blasting), và cách handle array theory hiệu quả qua lambda-term hoặc theory of arrays với extensions.
---

# 4.3 Bit-blasting và arrays: từ theory về SAT

> **Tóm tắt một dòng**: Bit-blasting là quá trình dịch một bitvector formula thành một SAT formula tương đương. Đây là "phép biến đổi cuối" mà mọi SMT solver dùng bitvector phải làm. Tương tự, array theory được xử lý qua lambda-term hoặc các kỹ thuật axiom-instantiation. Hiểu hai cách này giúp ta biết vì sao một số query nhanh và một số chậm.

## Tại sao cần bit-blasting?

Ở [bài 3.5](../02-static-analysis-i/05-smt-theories), ta thấy SMT solver phối hợp SAT engine với các theory solver chuyên biệt. Câu hỏi tự nhiên: theory solver cho bitvector hoạt động ra sao? Có phải nó implement riêng phép cộng, nhân, AND, OR, hay nó cũng dùng SAT?

Câu trả lời: hầu hết là dùng SAT, qua **bit-blasting**. Lý do là việc giải bitvector formula trực tiếp (không qua SAT) khó hơn nhiều so với giải SAT formula tương đương. Ngược lại, SAT solver đã tối ưu hoá đến mức rất tốt, nên dịch về SAT rồi giải lại nhanh hơn implement riêng.

Bit-blasting là phép biến đổi: cho bitvector formula trên $n$ biến BV, mỗi biến $w$-bit, sinh ra SAT formula trên $n \cdot w$ biến boolean (mỗi bit của mỗi BV variable thành một biến boolean).

## Bit-blasting các phép cơ bản

### Bitwise AND, OR, XOR, NOT

Đây là dễ nhất. Bitvector $x = (x_{w-1}, \ldots, x_0)$ và $y = (y_{w-1}, \ldots, y_0)$. Phép bitwise độc lập trên từng bit:

- $x \, \& \, y = (x_{w-1} \land y_{w-1}, \ldots, x_0 \land y_0)$
- $x \, | \, y = (x_{w-1} \lor y_{w-1}, \ldots, x_0 \lor y_0)$
- $x \, \oplus \, y = (x_{w-1} \oplus y_{w-1}, \ldots, x_0 \oplus y_0)$
- $\neg x = (\neg x_{w-1}, \ldots, \neg x_0)$

Mỗi phép thành $w$ phép boolean, đơn giản.

### Equality

$x = y$ tương đương mọi bit bằng nhau:

$$x = y \quad \Leftrightarrow \quad (x_{w-1} = y_{w-1}) \land (x_{w-2} = y_{w-2}) \land \ldots \land (x_0 = y_0)$$

Mỗi `x_i = y_i` là `not (x_i xor y_i)`.

### Phép cộng (Full adder)

Cộng hai BV $x + y$ giống cộng hai số thập phân bằng tay: cộng từng cột, có nhớ (carry). Thuật toán **ripple-carry adder**:

```
carry_0 = 0
for i in 0..w-1:
    sum_i = x_i XOR y_i XOR carry_i
    carry_{i+1} = (x_i AND y_i) OR (carry_i AND (x_i XOR y_i))
```

Encode thành SAT: mỗi `sum_i` và `carry_i` là biến boolean. Các equation trên là clause SAT.

Ripple-carry tạo $O(w)$ depth (bit cuối phải đợi carry từ bit đầu). Có **carry-lookahead adder** giảm xuống $O(\log w)$ depth nhưng nhiều clause hơn. Hầu hết SMT solver dùng ripple-carry vì SAT solver tốt hơn nhiều với clause "đơn giản nhưng nhiều" so với "ít nhưng phức tạp".

### Phép trừ

$x - y = x + (-y) = x + (\neg y + 1)$ (two's complement). Encode đơn giản qua cộng.

### Phép nhân

$x \cdot y$ phức tạp hơn. Một cách phổ biến: **shift-and-add** mimic phép nhân tay:

$$x \cdot y = \sum_{i=0}^{w-1} y_i \cdot (x << i)$$

trong đó $x << i$ là shift trái $i$ bit. Mỗi term $y_i \cdot (x << i)$ là conditional addition.

Encode bằng $w$ phép cộng, mỗi phép cộng $w$ bit. Tổng cộng $O(w^2)$ gate. Khá đắt với $w = 32$ hoặc 64.

Có thuật toán **Booth multiplication** và **Wallace tree** giảm hằng số, nhưng vẫn $O(w^2)$.

### Phép chia

$x / y$ là phép đắt nhất. Một cách: **long division** mimic chia tay:

```
remainder = 0
for i in w-1 downto 0:
    remainder = (remainder << 1) | x_i
    if remainder >= y:
        quotient_i = 1
        remainder = remainder - y
    else:
        quotient_i = 0
```

Encode: $w$ iteration, mỗi iter có 1 phép so sánh và 1 phép trừ conditional. Tổng $O(w^2)$ với hằng số cao.

### So sánh không dấu (`bvult`)

$x <_u y$ kiểm tra từ bit cao xuống thấp:

```
result = false
for i in w-1 downto 0:
    if x_i < y_i:   // x_i = 0, y_i = 1
        result = true
        break
    if x_i > y_i:   // x_i = 1, y_i = 0
        result = false
        break
// else x_i == y_i, tiếp tục
```

Encode thành recursive boolean expression.

### So sánh có dấu (`bvslt`)

Phức tạp hơn vì MSB là dấu. Cách đơn giản:

$$x <_s y \quad \Leftrightarrow \quad (x_{w-1} = 1 \land y_{w-1} = 0) \lor (x_{w-1} = y_{w-1} \land x <_u y)$$

Tức: $x$ âm và $y$ không âm, hoặc cùng dấu và unsigned $<$.

## Kích thước formula sau bit-blasting

Bảng tóm tắt (cho $w$-bit BV):

| Phép | Số biến boolean | Số clause |
|---|---|---|
| AND, OR, XOR, NOT | $w$ | $O(w)$ |
| Equality | $w$ | $O(w)$ |
| Cộng | $O(w)$ | $O(w)$ |
| Nhân | $O(w^2)$ | $O(w^2)$ |
| Chia | $O(w^2)$ | $O(w^2)$ |
| So sánh không dấu | $O(w)$ | $O(w)$ |

Với $w = 32$, phép nhân tạo ~1000 biến và clause. Phép chia ~3000-5000. Một formula có vài chục phép nhân, vài chục bitvector variable đã có hàng triệu clause. SAT solver hiện đại vẫn xử lý được trong giây hoặc phút.

:::warning[Nhân là phép đắt nhất]
Khi BMC formula chứa nhiều phép nhân (ví dụ verify code crypto, hash function), tốc độ giảm mạnh. Một số tool có heuristic không bit-blast nhân, mà dùng abstraction (treat như uninterpreted function), check post-hoc với mô hình cụ thể.
:::

## Eager vs lazy SMT cho bitvector

Hai cách tiếp cận đã giới thiệu ở bài 3.5, áp dụng cụ thể cho BV:

**Eager**: bit-blast toàn bộ BV formula thành SAT, gọi SAT solver một lần. Đơn giản, tốt cho công thức nhỏ. Tool: Boolector (cũ), Bitwuzla.

**Lazy DPLL(T)**: trừu tượng BV atom thành boolean, SAT giải, gọi BV theory solver check theory consistency. BV theory solver có thể dùng bit-blasting trên subset cần thiết. Tool: Z3, CVC5.

Lazy thường hiệu quả hơn cho công thức lớn vì:
- Không bit-blast mọi thứ ngay.
- Khai thác cấu trúc SAT (hầu hết các quyết định không liên quan BV).

Tuy nhiên với công thức "đầy BV" như crypto verification, eager thắng vì lazy phải bit-blast hết cuối cùng.

## Array theory: từ axiom tới algorithm

Như đã giới thiệu ở [bài 3.7](../02-static-analysis-i/07-encoding-pointers-and-memory), array theory có axiom cơ bản:

$$\text{select}(\text{store}(a, i, v), j) = \begin{cases} v & \text{nếu } i = j \\ \text{select}(a, j) & \text{nếu } i \neq j \end{cases}$$

Câu hỏi: làm thế nào tự động hoá việc áp dụng axiom này khi solver gặp một công thức có nhiều store/select?

### Cách 1: Axiom instantiation

Mỗi cặp `(store(a, i, v), select(_, j))` xuất hiện trong formula sinh ra 2 axiom instance:
- Nếu `i = j`, then result = v.
- Nếu `i != j`, then result = select(a, j).

Số instance là $O(n \cdot m)$ với $n$ store và $m$ select trong formula. Với formula thực tế (verify chương trình C với memory), $n$ và $m$ có thể vài nghìn. Số axiom instance vài triệu.

Cách này đúng nhưng có thể chậm.

### Cách 2: Lambda-term

Một cách thanh lịch: encode array trực tiếp như function. `store(a, i, v)` thành lambda:

$$\lambda k. \text{ite}(k = i, v, a(k))$$

trong đó $a(k)$ là `select(a, k)`. Lambda biểu diễn "function trả về $v$ tại $i$, trả về `a(k)` ở chỗ khác".

`select(store(a, i, v), j)` simplify thành `ite(j = i, v, a(j))` tự động qua beta-reduction.

Lambda-term encoding giảm số axiom phải instantiate. Z3 và CVC5 đều dùng lambda extension cho array theory.

### Cách 3: Extensionality

Một extension của array theory: $a = b$ khi mọi index cho cùng giá trị:

$$a = b \quad \Leftrightarrow \quad \forall k. \text{ select}(a, k) = \text{select}(b, k)$$

Có quantifier (`forall`), nên array theory với extensionality không quantifier-free thuần. Solver phải dùng quantifier-elimination hoặc skolemization.

Trong verification thực tế, extensionality ít cần thiết, các tool BMC thường tắt nó để giữ formula quantifier-free.

## Mảng đa chiều và mảng struct

C có `int arr[10][10]` (2D array) và `struct S arr[10]` (array of struct). Encode thế nào?

**2D array**: encode như array of array hoặc flatten thành 1D với index `i * 10 + j`.

**Array of struct**: encode như memory array, với mỗi struct chiếm `sizeof(struct S)` byte liền nhau. Access `arr[i].field` thành `select(memory, &arr[i] + offset_of(field))`.

Cả hai approach đều tractable nhưng formula lớn hơn 1D array nhiều. Tool BMC có optimization để gộp các phép truy cập liền kề.

## Tóm tắt

- **Bit-blasting** dịch bitvector formula sang SAT formula tương đương.
- Phép đắt nhất là nhân ($O(w^2)$) và chia ($O(w^2)$).
- **Eager** bit-blast tất cả ngay, **Lazy DPLL(T)** chỉ bit-blast khi cần.
- **Array theory** dùng axiom instantiation, lambda-term, hoặc extensionality để tự động hoá.
- Tool BMC ưu tiên lambda-term (nhanh hơn axiom thuần) và tắt extensionality (giữ QF).

## Mini-quiz

<details>
<summary>Q1. Vì sao SMT solver dùng SAT solver thay vì implement riêng cho bitvector?</summary>

Hai lý do chính:

1. **SAT solver đã được tối ưu cực kỳ trong 30 năm**. Hàng nghìn researcher đã refine CDCL, restart strategy, decision heuristic, clause learning. Implement riêng cho BV khó match được mức độ tinh vi này.

2. **Bitvector formula có cấu trúc rất phù hợp với SAT**. Sau bit-blasting, ta được SAT formula với clauses rất ngắn (mỗi clause ít literal), nhiều symmetry, nhiều unit propagation. Đây là input lý tưởng cho CDCL.

Một số tool (Boolector cũ) implement BV theory hoàn chỉnh, tốc độ tương đương Z3/CVC5 cho BV pure. Nhưng kiến trúc dùng SAT làm engine cốt lõi vẫn được ưa chuộng hơn vì module hơn.
</details>

<details>
<summary>Q2. Vì sao nhân và chia đắt hơn cộng/trừ rất nhiều?</summary>

Cộng và trừ là **linear** trong số bit: $w$-bit cộng cần $w$ full adder, tổng $O(w)$ gate.

Nhân là **bậc hai**: thuật toán shift-and-add cần $w$ partial product, mỗi partial product là một $w$-bit (sau khi gộp). Tổng cộng $O(w^2)$ gate. Với $w = 32$, đã là 1024 gate; với $w = 64$, là 4096 gate.

Chia càng đắt: long division là vòng lặp với so sánh và trừ conditional, cùng $O(w^2)$ nhưng hằng số cao hơn nhân.

Trong thực tế, nếu code verify có nhiều phép nhân (crypto, ML), tool BMC chậm đáng kể. Optimization: nếu một biến chỉ nhân với hằng số, có thể dùng shift + add thay vì general multiplier.
</details>

<details>
<summary>Q3. Lambda-term cho array theory giúp gì so với axiom instantiation?</summary>

Axiom instantiation: với mỗi cặp `(store, select)`, tạo các axiom instance. Số instance $O(n \cdot m)$ và phải áp dụng riêng lẻ trong SAT/theory loop.

Lambda-term: encode `store(a, i, v)` thành `λk. ite(k=i, v, a(k))`. Khi gặp `select(store(a, i, v), j)`, beta-reduce thành `ite(j=i, v, select(a, j))` **trong một bước**, không cần axiom instance.

Lambda-term tự nhiên cho lập trình hàm và có support trong SMT-LIB 2.6. Z3 và CVC5 dùng lambda khi gặp array nested (`store(store(...))`), giúp giảm formula size đáng kể.

Đánh đổi: solver cần hỗ trợ lambda calculus (extension không phải mọi solver có).
</details>

---

**Tiếp theo**: [4.4 Concurrency verification](./04-concurrency-verification)
