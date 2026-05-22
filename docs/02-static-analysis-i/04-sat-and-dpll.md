---
id: 04-sat-and-dpll
title: 3.4 SAT và DPLL
sidebar_position: 4
description: Bài toán SAT, CNF, thuật toán DPLL với unit propagation và pure literal, conflict-driven clause learning, vì sao SAT solver hiện đại nhanh tới mức ngoài sức tưởng tượng.
---

# 3.4 SAT và thuật toán DPLL

> **Tóm tắt một dòng**: SAT (Satisfiability) là bài toán "có tồn tại gán giá trị cho các biến boolean làm công thức đúng không?". Mặc dù NP-complete về lý thuyết, các SAT solver hiện đại dùng thuật toán DPLL kết hợp Conflict-Driven Clause Learning (CDCL) đã giải được công thức có hàng triệu biến trong vài giây. Đây là engine cốt lõi mà BMC và SMT đều dựa vào.

## Vì sao SAT quan trọng đến vậy?

Khi nói "SMT solver", ta hay nghĩ tới một "hộp đen" giải mọi loại constraint. Thực ra hộp đen đó có một engine nhỏ hơn bên trong gọi là **SAT solver**, và mọi theory phức tạp (số nguyên, mảng, bitvector) cuối cùng đều được dịch về SAT để giải. Hiểu SAT là hiểu nền móng của BMC, SMT, và do đó cả Lecture 3 lẫn 4.

Có một câu chuyện thú vị về tầm quan trọng của SAT trong vài thập kỷ qua. Năm 1971, Stephen Cook chứng minh SAT là **NP-complete đầu tiên**, mở ra cả lĩnh vực complexity theory. Trong nhiều năm, người ta coi SAT là bài toán "khó", không thực dụng. Đến những năm 1990, nhờ một số đột phá thuật toán (đặc biệt là CDCL), SAT solver bắt đầu giải được những instance "không tưởng": công thức với hàng triệu biến, hàng chục triệu clause, trong vài phút trên laptop thông thường. Hiện tượng này gọi là **"SAT revolution"**.

Nhờ SAT revolution, một loạt ứng dụng trở nên khả thi: hardware verification, software verification (BMC), planning, scheduling, cryptanalysis (tìm collision trong hash), thậm chí giải Sudoku và Mario level generation. Tài liệu mà bạn đang đọc tồn tại được phần lớn nhờ vào SAT solver hiệu quả.

Trong bài này, ta sẽ đi qua:

1. Định nghĩa hình thức SAT và Conjunctive Normal Form (CNF).
2. Thuật toán DPLL gốc với unit propagation và pure literal.
3. Conflict-Driven Clause Learning (CDCL), cốt lõi của SAT solver hiện đại.
4. Vì sao CDCL nhanh đến vậy trong thực tế dù lý thuyết NP-complete.

## Bài toán SAT chính thức

Cho một công thức boolean $\phi$ trên các biến $x_1, x_2, \ldots, x_n$, **SAT** hỏi: có gán giá trị $\{0, 1\}^n$ cho các biến làm $\phi$ true không?

Nếu có, ta nói $\phi$ là **satisfiable** (SAT). SAT solver trả về gán cụ thể (gọi là **model**).

Nếu không, ta nói $\phi$ là **unsatisfiable** (UNSAT). SAT solver chứng minh không có model nào.

Ví dụ:
- $\phi_1 = x \land \neg x$: UNSAT (mâu thuẫn nội tại).
- $\phi_2 = x \lor y$: SAT, model $\{x = 1, y = 0\}$ (hoặc nhiều model khác).
- $\phi_3 = (x \lor y) \land (\neg x \lor y) \land (x \lor \neg y) \land (\neg x \lor \neg y)$: UNSAT (cả 4 case bị loại trừ).

### Conjunctive Normal Form (CNF)

SAT solver thường yêu cầu input dưới dạng chuẩn gọi là **CNF**: công thức là **AND của các OR của các literal**, với literal là biến hoặc phủ định biến.

$$\phi = \bigwedge_{i=1}^{m} C_i, \quad C_i = \bigvee_{j} \ell_{i,j}$$

Mỗi $C_i$ gọi là một **clause**. Mỗi $\ell_{i,j}$ là literal (như $x_3$ hoặc $\neg x_5$).

Ví dụ CNF:

$$\phi = (x_1 \lor \neg x_2 \lor x_3) \land (\neg x_1 \lor x_4) \land (x_2 \lor \neg x_4)$$

Vì sao CNF? Vì nó có cấu trúc đều đặn, dễ implement thuật toán. Mọi công thức boolean đều có thể chuyển sang CNF bằng quy trình **Tseitin transformation** (nhanh, kích thước tăng tuyến tính).

:::tip[Phép loại suy CNF]
Hãy hình dung CNF như một danh sách yêu cầu. Mỗi clause là một yêu cầu mà ít nhất một literal trong đó phải đúng. Cả công thức đúng khi mọi yêu cầu được thoả.

Ví dụ "Tôi muốn một laptop có (Mac OR Linux) AND (≥ 16 GB RAM) AND (≥ 512 GB SSD)" là CNF với 3 clause. Một laptop chỉ "OK" khi thoả cả 3 clause.
:::

## Thuật toán DPLL: nền tảng

**DPLL** (Davis-Putnam-Logemann-Loveland, 1962) là thuật toán đầu tiên giải SAT một cách có hệ thống. Ý tưởng cơ bản: thử gán giá trị cho từng biến một, nếu mâu thuẫn thì quay lui (backtrack).

Pseudocode tổng quát:

```
function DPLL(φ, assignment):
    φ = unit_propagate(φ, assignment)
    φ = pure_literal_eliminate(φ, assignment)
    if φ chứa empty clause:
        return UNSAT
    if mọi clause đều satisfied:
        return SAT, assignment
    x = choose_variable(φ)
    return DPLL(φ ∧ x, assignment ∪ {x = 1}) 
        or DPLL(φ ∧ ¬x, assignment ∪ {x = 0})
```

Bốn ý tưởng then chốt:

### 1. Unit propagation

**Unit clause** là clause chỉ còn 1 literal chưa được gán. Ví dụ sau khi gán $x_1 = 0$, clause $(x_1 \lor x_2)$ trở thành $(x_2)$, vì $x_1 = 0$ không thoả được nên clause buộc $x_2 = 1$ mới đúng.

Unit propagation: khi gặp unit clause, **ép** giá trị literal đó. Nếu literal là $x$, gán $x = 1$. Nếu là $\neg x$, gán $x = 0$. Sau đó áp dụng lại trên các clause khác (có thể tạo thêm unit clause mới, "lan toả").

Unit propagation là **lý do chính** SAT solver hiệu quả. Nó thường xử lý 80-90% các biến mà không cần đoán mò.

### Ví dụ unit propagation

Cho công thức:

$$\phi = (x_1 \lor x_2) \land (\neg x_1 \lor x_3) \land (\neg x_3 \lor x_4) \land (\neg x_4)$$

Thực hiện unit propagation:

- Clause $(\neg x_4)$ là unit, ép $x_4 = 0$.
- Áp vào $(\neg x_3 \lor x_4)$: $x_4 = 0$ không thoả, clause còn $(\neg x_3)$, là unit, ép $x_3 = 0$.
- Áp vào $(\neg x_1 \lor x_3)$: $x_3 = 0$ không thoả, clause còn $(\neg x_1)$, ép $x_1 = 0$.
- Áp vào $(x_1 \lor x_2)$: $x_1 = 0$ không thoả, clause còn $(x_2)$, ép $x_2 = 1$.

Kết quả: $\{x_1 = 0, x_2 = 1, x_3 = 0, x_4 = 0\}$. **Không cần đoán bất kỳ biến nào.** Toàn bộ 4 biến được suy ra từ unit propagation.

### 2. Pure literal elimination

**Pure literal** là literal chỉ xuất hiện ở một dạng (positive hoặc negative) trong toàn bộ công thức.

Ví dụ $\phi = (x_1 \lor x_2) \land (x_1 \lor \neg x_3) \land (\neg x_2 \lor x_3)$:
- $x_1$ xuất hiện 2 lần, đều positive → $x_1$ là pure positive literal.

Khi gán $x_1 = 1$, cả 2 clause chứa $x_1$ được thoả, ta loại bỏ chúng. Công thức nhỏ đi, dễ giải hơn.

Pure literal elimination ít hiệu quả hơn unit propagation và bị bỏ qua trong nhiều SAT solver hiện đại để tối ưu code path. Nhưng nó là một ý tưởng có giá trị về mặt giáo trình.

### 3. Branching (đoán mò)

Khi unit propagation và pure literal eliminate hết, nếu vẫn còn biến chưa gán và công thức chưa có empty clause, ta phải **đoán**. Chọn một biến $x$ chưa gán, thử $x = 1$ trước. Nếu fail (dẫn tới UNSAT trong subtree), thử $x = 0$.

Chiến lược chọn biến (gọi là **decision heuristic**) ảnh hưởng rất lớn tới hiệu năng. Các heuristic phổ biến:
- **VSIDS** (Variable State Independent Decaying Sum): biến nào xuất hiện trong nhiều conflict gần đây được ưu tiên.
- **Jeroslow-Wang**: ưu tiên biến trong clause ngắn.
- **MOMS** (Maximum Occurrences in Minimum Sized clauses): tương tự Jeroslow-Wang.

Trong SAT solver hiện đại, VSIDS chiếm ưu thế.

### 4. Backtracking

Khi đoán $x = 1$ dẫn tới UNSAT, quay lui (chronological backtracking), undo gán, thử $x = 0$.

DPLL gốc dùng chronological backtracking (luôn quay lui về biến gần nhất). CDCL (phần sau) dùng **non-chronological backtracking** thông minh hơn.

## Ví dụ chạy DPLL từng bước

Cho công thức:

$$\phi = (x_1 \lor x_2) \land (\neg x_1 \lor x_2 \lor x_3) \land (\neg x_2 \lor \neg x_3) \land (\neg x_1 \lor \neg x_2)$$

DPLL chạy như sau:

**Bước 1**: không có unit clause, không có pure literal (mỗi biến xuất hiện cả positive và negative).

**Bước 2**: branching trên $x_1$, thử $x_1 = 1$.

Áp vào công thức:
- $(x_1 \lor x_2)$: thoả, bỏ.
- $(\neg x_1 \lor x_2 \lor x_3)$: $\neg x_1 = 0$, còn $(x_2 \lor x_3)$.
- $(\neg x_2 \lor \neg x_3)$: chưa thay đổi.
- $(\neg x_1 \lor \neg x_2)$: $\neg x_1 = 0$, còn $(\neg x_2)$, là unit.

**Bước 3**: unit propagation $\neg x_2 \Rightarrow x_2 = 0$.

Áp tiếp:
- $(x_2 \lor x_3)$: $x_2 = 0$, còn $(x_3)$, là unit.
- $(\neg x_2 \lor \neg x_3)$: $\neg x_2 = 1$, thoả, bỏ.

**Bước 4**: unit propagation $x_3 \Rightarrow x_3 = 1$.

Mọi clause đã thoả. SAT với $\{x_1 = 1, x_2 = 0, x_3 = 1\}$.

Nếu thử $x_1 = 0$ ở bước 2 thay vì $x_1 = 1$:
- $(x_1 \lor x_2)$: $x_1 = 0$, còn $(x_2)$, unit, ép $x_2 = 1$.
- $(\neg x_2 \lor \neg x_3)$: $x_2 = 1$, $\neg x_2 = 0$, còn $(\neg x_3)$, ép $x_3 = 0$.
- $(\neg x_1 \lor x_2 \lor x_3)$: thoả qua $\neg x_1 = 1$, bỏ.
- $(\neg x_1 \lor \neg x_2)$: thoả qua $\neg x_1 = 1$, bỏ.

Cũng SAT với $\{x_1 = 0, x_2 = 1, x_3 = 0\}$. Một công thức có thể có nhiều model.

## Conflict-Driven Clause Learning (CDCL)

DPLL gốc dùng chronological backtracking: khi gặp conflict, quay lui một bước, đảo giá trị, thử tiếp. Vấn đề: nếu conflict gốc nằm ở quyết định cách 50 biến trước, DPLL phải mò đi mò lại 50 lớp.

**CDCL** (1996, Marques-Silva và Sakallah) cải tiến bằng cách: khi gặp conflict, **phân tích** nguyên nhân, **học** một clause mới (gọi là **conflict clause**), và **quay lui xa hơn** tới đúng tầng quyết định gây ra conflict.

Bốn ý tưởng then chốt của CDCL:

### Ý tưởng 1: Implication graph

Khi unit propagation chạy, ta vẽ một đồ thị có hướng: nút là literal đã gán, cạnh đi từ literal "nguyên nhân" tới literal "kết quả" (qua unit clause).

Ví dụ: nếu gán $x_1 = 1$, $x_2 = 0$, và clause $(\neg x_1 \lor x_2 \lor x_3)$ trở thành unit $(x_3)$, ép $x_3 = 1$, thì ta vẽ:

```
x_1=1 ─┐
       ├──> x_3=1
x_2=0 ─┘
```

Đồ thị này tích lũy mọi gán ép từ unit propagation. Khi conflict xảy ra (một clause trở thành empty), ta có thể truy ngược tìm gốc.

### Ý tưởng 2: Conflict analysis

Khi gặp empty clause, ta **truy ngược** implication graph để tìm tập các decision (gán mò) nào trực tiếp gây ra conflict. Tập này gọi là **conflict set**.

Phủ định conflict set tạo ra **conflict clause** (clause học được). Clause này thêm vào công thức, đảm bảo trong tương lai không bao giờ rơi vào cùng combination này nữa.

Ví dụ: nếu conflict do đồng thời $x_1 = 1, x_2 = 0, x_5 = 1$, conflict clause là $\neg x_1 \lor x_2 \lor \neg x_5$. Lần sau, bất kỳ đường nào đi tới $\{x_1 = 1, x_2 = 0, x_5 = 1\}$ đều bị clause này chặn ngay từ unit propagation.

### Ý tưởng 3: Non-chronological backjumping

Sau khi học conflict clause, không quay lui 1 bước, mà quay lui tới **tầng quyết định cao nhất trong conflict set**. Ví dụ nếu conflict set có quyết định ở các tầng $\{1, 3, 5\}$, ta nhảy về tầng 3 (cao thứ hai), undo mọi gán sau đó, rồi tiếp tục với clause mới.

Backjumping có thể nhảy qua nhiều tầng cùng lúc, tiết kiệm rất nhiều công sức so với chronological backtracking.

### Ý tưởng 4: Clause forgetting và restart

Càng học nhiều clause, bộ nhớ càng đầy và unit propagation càng chậm. Định kỳ, SAT solver **xóa bớt** các clause học được ít hữu ích (theo metric "clause activity").

**Restart**: định kỳ xoá toàn bộ decision (nhưng giữ lại clauses học được), bắt đầu lại từ tầng 0. Lý do: heuristic chọn biến có thể đã rẽ sai từ đầu; restart cho cơ hội chọn lại với "kinh nghiệm" tích lũy trong các clause học được.

## Vì sao CDCL nhanh đến vậy trong thực tế?

Lý thuyết: SAT là NP-complete. Worst case của CDCL vẫn là $O(2^n)$. Vậy tại sao thực tế nó giải được công thức triệu biến trong giây?

Câu trả lời nằm ở hai sự thật:

**Sự thật 1**: Hầu hết công thức SAT thực tế **không phải worst case**. Công thức từ hardware verification, software verification, planning đều có **cấu trúc** (biến và clause không độc lập, có liên kết logic). CDCL khai thác cấu trúc qua learning.

**Sự thật 2**: Mỗi conflict clause học được **cắt** một phần lớn không gian tìm kiếm. Sau hàng triệu conflict, không gian còn lại chỉ là một fraction rất nhỏ của $2^n$.

Một analogy hữu ích: tìm kim trong đống cỏ. Brute force là sờ từng cọng. CDCL là: mỗi lần sờ trúng "phần không có kim", ghi nhớ và không bao giờ sờ vào phần đó nữa. Sau một triệu lần ghi nhớ, vùng phải tìm thu hẹp rất nhiều.

:::tip[Vì sao SAT competition quan trọng?]
Mỗi năm, cộng đồng tổ chức **SAT Competition**: các solver thi giải cùng tập benchmark. Solver thắng cuộc thường được integrate vào BMC tool (CBMC, ESBMC) trong năm sau. Hiện tại (2024), các solver hàng đầu gồm Kissat, CaDiCaL, MapleSAT.

Nhờ cạnh tranh này, hiệu năng SAT solver tăng đều đặn ~2x mỗi vài năm trong 20 năm qua. Một benchmark "khó" của 2004 giờ giải được trong vài mili giây.
:::

## Mở rộng: SAT enabling cho các ngành khác

SAT solver mạnh mở ra ứng dụng cho rất nhiều lĩnh vực ngoài verification:

- **Hardware design**: equivalence checking giữa 2 thiết kế mạch.
- **Planning**: lập lịch tác vụ với nhiều ràng buộc.
- **Cryptanalysis**: tìm collision trong hash function, break stream cipher.
- **Bioinformatics**: phân tích pathway phản ứng hoá học.
- **Optimization**: kết hợp với MaxSAT cho bài toán tối ưu hoá có ràng buộc.

Có một cộng đồng nghiên cứu sôi động xung quanh SAT, với hội nghị thường niên SAT Conference, journal JSAT, và open dataset SATLIB.

## Tóm tắt

- **SAT** là bài toán quyết định xem công thức boolean có thoả được không. NP-complete về lý thuyết.
- **CNF** là dạng chuẩn AND của OR, đầu vào tiêu chuẩn cho SAT solver.
- **DPLL** dùng unit propagation, pure literal, branching, backtracking.
- **CDCL** mở rộng DPLL với conflict analysis, learning, backjumping, restart.
- Hiệu năng thực tế của CDCL **vượt xa worst-case lý thuyết** nhờ khai thác cấu trúc và học conflict.
- SAT solver là engine cốt lõi cho mọi BMC tool (CBMC, ESBMC, SeaHorn) và SMT solver (Z3, CVC5, Yices).

## Mini-quiz

<details>
<summary>Q1. Áp dụng unit propagation cho công thức $(\neg x_1) \land (x_1 \lor x_2) \land (\neg x_2 \lor x_3)$. Kết quả?</summary>

- Clause $(\neg x_1)$ là unit, ép $x_1 = 0$.
- Áp vào $(x_1 \lor x_2)$: $x_1 = 0$ không thoả, còn $(x_2)$, ép $x_2 = 1$.
- Áp vào $(\neg x_2 \lor x_3)$: $x_2 = 1, \neg x_2 = 0$ không thoả, còn $(x_3)$, ép $x_3 = 1$.

Kết quả: $\{x_1 = 0, x_2 = 1, x_3 = 1\}$. SAT, mọi clause thoả.
</details>

<details>
<summary>Q2. Pure literal là gì? Tại sao gán giá trị "thuận chiều" của pure literal luôn an toàn?</summary>

Pure literal là literal chỉ xuất hiện ở **một dạng** (positive hoặc negative) trong toàn bộ công thức. Ví dụ nếu $x_1$ chỉ xuất hiện positive ($x_1$, không bao giờ $\neg x_1$), thì $x_1$ là pure positive.

Gán $x_1 = 1$ cho pure positive luôn an toàn vì:
- Mọi clause chứa $x_1$ trở thành satisfied (bỏ được).
- Không clause nào chứa $\neg x_1$ nên không thể tạo ra empty clause từ phép gán này.

Tức là gán pure literal không bao giờ làm công thức từ SAT thành UNSAT. Đây là một "safe move" thuần tuý.
</details>

<details>
<summary>Q3. Vì sao CDCL được gọi là "non-chronological backtracking"?</summary>

DPLL gốc dùng chronological backtracking: khi gặp conflict ở tầng decision $k$, quay lui về tầng $k-1$, đảo giá trị, thử lại.

CDCL phân tích conflict và xác định **tầng decision cao nhất trong conflict set** (gọi là tầng $j$, có thể $j << k-1$). CDCL nhảy thẳng về tầng $j$, bỏ qua nhiều tầng trung gian. Đây là backjumping non-chronological, hay nhanh hơn chronological rất nhiều khi conflict gốc nằm ở quyết định xa.

Ví dụ: conflict ở tầng 100, conflict set chỉ có decision ở tầng 5 và 80. Chronological: backtrack 100 → 99 → 98 → ... mỗi lần lại bị mâu thuẫn. Non-chronological: nhảy thẳng từ 100 về 80, cùng với clause học được đảm bảo không lặp lại conflict.
</details>

:::tip[DS perspective]
SAT là **Constraint Satisfaction Problem** (CSP) ở dạng thuần boolean, tương đương việc giải Sudoku hay scheduling. DPLL chính là **backtracking search** quen thuộc, CDCL nâng lên thành **branch-and-bound** giống MILP solver. **Unit propagation** ≈ **constraint propagation (AC-3)** trong CSP. **VSIDS heuristic** ≈ **variable importance** trong feature selection. Nếu bạn quen `cvxpy` hay `pulp`, SMT solver là cùng triết lý: model bài toán dưới dạng constraint, để solver lo phần combinatorial.
:::

---

**Tiếp theo**: [3.5 SMT theories](./05-smt-theories)
