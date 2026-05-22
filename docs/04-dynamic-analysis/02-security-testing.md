---
id: 02-security-testing
title: 5.2 Security testing
sidebar_position: 2
description: "Vì sao security testing khó hơn functional testing, test suite vs test oracle, các khái niệm pen test, vulnerability scan, security regression."
---

# 5.2 Security testing: tại sao khó hơn nhiều?

> **Tóm tắt một dòng**: Functional testing check chương trình **làm đúng cái cần làm** (positive). Security testing check chương trình **không làm cái không nên làm** (negative). Sự khác biệt này, dù tinh tế, dẫn tới những khó khăn fundamental: test oracle không rõ ràng, attack surface rộng, expert kiến thức cần thiết.

## Một bài tập: test đăng nhập

Hãy bắt đầu với một ví dụ. Bạn được giao test feature login. Username và password đúng cho user, sai thì reject.

Functional testing tự nhiên:
1. Đăng nhập với credential đúng → kỳ vọng pass, user vào dashboard.
2. Đăng nhập với password sai → kỳ vọng reject, hiện message lỗi.
3. Đăng nhập với username không tồn tại → reject.
4. Đăng nhập với field rỗng → reject.

Đây là 4 test case cover happy path và một số sad path. Trong functional testing, đây có thể đã đủ.

Nhưng từ lăng kính security, còn thiếu rất nhiều:

5. Đăng nhập với username `admin' --` (SQL injection) → kỳ vọng reject, không bypass.
6. Đăng nhập với password có 1 triệu ký tự → kỳ vọng reject hoặc handle gracefully, không crash.
7. Đăng nhập 1000 lần liên tiếp với password sai → kỳ vọng rate limit kick in.
8. Đăng nhập với username có Unicode normalization tricky (`admin` vs `аdmin` với cyrillic 'а') → kỳ vọng reject hoặc consistent behavior.
9. Đăng nhập rồi check session cookie có `HttpOnly`, `Secure`, `SameSite` không.
10. Đăng nhập trên HTTPS, thử redirect sang HTTP → kỳ vọng không leak session.
11. Đăng nhập trên một browser, dùng cùng session trên browser khác → kỳ vọng có session tracking.
12. ... còn rất nhiều ...

Functional có 4 test, security có 20+. Đây là khoảng cách của hai loại testing.

## Functional vs Security testing

| Tiêu chí | Functional | Security |
|---|---|---|
| Câu hỏi | "Có làm đúng spec không?" | "Có làm sai không (kể cả không trong spec)?" |
| Test case | Hữu hạn rõ ràng (positive + sad path) | "Vô hạn" (mọi attack vector) |
| Oracle | "Output đúng spec" | "Không vi phạm security property" |
| Tester | Developer, QA | Security engineer, pen tester |
| Tool | Selenium, JUnit | Burp Suite, ZAP, fuzzer |

### Test oracle: vấn đề cốt lõi

**Test oracle** là "câu trả lời đúng" mà test so sánh với. Trong functional, oracle thường rõ: spec nói output là gì, test compare.

Trong security, oracle mơ hồ. "Không có bug security" là gì? Không có buffer overflow? Không có SQLi? Không có race? Không có timing attack? Liệt kê hết là bất khả.

Trong thực tế, security testing dùng các oracle gián tiếp:
- **Crash**: nếu chương trình crash với input nào, đó là bug (có thể security).
- **Sanitizer alert**: ASan, MSan, UBSan, TSan báo memory bug.
- **Specific attack succeed**: pen tester thử SQL injection, nếu thành công thì có bug.
- **Diff oracle**: chạy 2 version (cũ và mới), nếu output khác có thể regress.
- **Differential testing**: chạy 2 implementation tương đương (OpenSSL vs BoringSSL), khác output có thể bug.

## Khái niệm Test Suite

**Test Suite** là tập các test case cùng test cho một mục đích. Trong security:

- **Regression suite**: test các bug đã sửa, đảm bảo không tái phát.
- **Fuzzing corpus**: tập input mẫu dùng làm seed cho fuzzer.
- **Vulnerability scanner check**: rules của tool như Nessus, OpenVAS.
- **Pen test playbook**: các attack chuẩn được tester thử theo thứ tự.

### Coverage của Test Suite

Quality của test suite đo bằng coverage. Bài 5.3 đi sâu vào các criterion (statement, branch, MC/DC). Ở đây ta nói tổng quan:

- Coverage cao **không đảm bảo** không có bug, chỉ đảm bảo "code đã được chạm".
- Coverage thấp **đảm bảo** có chỗ chưa test, có thể có bug.
- Mục tiêu: 80%+ branch coverage là good practice.

## Các loại Security Testing

### Vulnerability Scanning

Tool tự động scan hệ thống/code tìm các pattern lỗ hổng đã biết. Ví dụ:
- **Web scanner**: Nessus, OpenVAS, Burp Suite scanner, OWASP ZAP. Scan URL, gửi payload SQLi/XSS, ghi nhận response.
- **Source code scanner (SAST)**: SonarQube, Veracode, Checkmarx. Phân tích source code tìm pattern lỗi.
- **Dependency scanner**: Snyk, Dependabot. Check version thư viện có CVE không.
- **Container scanner**: Trivy, Clair. Check image Docker có vulnerable package không.

Ưu: nhanh, scale. Nhược: chỉ tìm bug đã biết, miss bug mới.

### Penetration Testing (Pen Test)

Manual hoặc semi-automated. Tester đóng vai attacker, thử mọi cách tấn công có thể. Quy trình điển hình:

1. **Reconnaissance**: thu thập thông tin target (subdomain, port mở, công nghệ dùng).
2. **Threat modeling**: liệt kê các attack vector tiềm năng.
3. **Exploitation**: thử exploit, document những gì thành công.
4. **Post-exploitation**: nếu vào được, leo thang quyền, lateral movement.
5. **Reporting**: viết báo cáo cho dev fix.

Pen test đắt nhưng tìm bug sâu hơn scanner.

### Security Regression Testing

Khi sửa một bug security, viết test cụ thể tái tạo bug. Bug fix làm test pass. Mọi PR sau chạy test này; nếu fail, regression đã xảy ra.

Best practice modern: mọi CVE filed đều phải có regression test trong codebase.

### Fuzzing (chi tiết ở bài 5.5-5.7)

Tự động sinh input, mục tiêu tìm crash. Có thể kết hợp với coverage để hiệu quả hơn.

### Property-based Testing

Generalization của fuzzing: định nghĩa property, framework tự sinh input ngẫu nhiên, check property holds. Tool: QuickCheck (Haskell), Hypothesis (Python), proptest (Rust).

Khác fuzzing: PBT có structured input (sinh theo type), check semantic property (không chỉ crash).

## Khi nào dùng loại nào?

Không có "best" technique, mọi technique đều có vai trò:

| Tình huống | Technique phù hợp |
|---|---|
| Pre-release scan rộng | Vulnerability scanner |
| Code mới merge | SAST + dependency scan |
| Critical release (banking, healthcare) | Pen test |
| Bug đã sửa | Regression test |
| Parser, network protocol | Fuzzing |
| Algorithm correctness | Property-based testing |
| Production monitoring | Runtime monitor (bài 5.4) |

Defense in depth: dùng nhiều technique, mỗi technique bắt một lớp bug.

## Khó khăn lớn nhất: thinking like attacker

Cuối cùng, security testing đòi hỏi một **mindset đặc biệt**: nghĩ như attacker. Tester phải tưởng tượng "nếu tôi là kẻ tấn công, tôi sẽ thử gì?". Đây là kỹ năng cần rèn luyện qua nhiều năm và kiến thức về:

- Các attack pattern phổ biến (OWASP Top 10, CWE Top 25).
- Cách hệ thống thường được bypass.
- Trick về encoding, parsing, race timing.
- Awareness về threat actor (script kiddie vs APT).

Không có tool nào thay thế được mindset này. Đó là lý do pen tester giỏi rất đắt.

## Tóm tắt

- Security testing **khó hơn** functional vì test oracle mơ hồ, attack surface rộng.
- **Oracle gián tiếp**: crash, sanitizer alert, specific attack, diff, differential.
- **Test loại**: vulnerability scanner, pen test, security regression, fuzzing, property-based.
- **Defense in depth**: kết hợp nhiều technique.
- **Mindset attacker** không thay thế được bằng tool.

## Mini-quiz

<details>
<summary>Q1. Vì sao test oracle khó định nghĩa cho security?</summary>

Functional có spec rõ: "input X → output Y". Oracle là Y, test compare.

Security yêu cầu chương trình "không vi phạm security property". Property có thể là:
- Không có buffer overflow.
- Không có SQLi.
- Không leak data.
- Không bypass auth.
- ... vô số ...

Liệt kê hết và check từng cái cho từng input là bất khả. Vì thế dùng oracle gián tiếp:
- Crash là dấu hiệu bug (có thể security).
- Sanitizer alert là bug được tool detect.
- Specific attack succeed là confirmed bug.

Không có oracle "đúng tuyệt đối" cho security testing, chỉ có heuristic bắt được phần lớn bug.
</details>

<details>
<summary>Q2. Phân biệt vulnerability scanning và pen testing.</summary>

**Vulnerability scanning**:
- Tự động bằng tool (Nessus, OpenVAS).
- Tìm pattern bug đã biết (CVE, CWE Top 25).
- Nhanh, scale.
- Miss bug mới hoặc bug logic phức tạp.

**Penetration testing**:
- Manual hoặc semi-auto bởi expert.
- Tìm bug bằng creative attack, có thể là bug mới.
- Đắt (tester \$200-500/giờ, project nhiều ngày).
- Tìm bug sâu, đặc biệt là chain attack (bug A leverage bug B).

Best practice: scan trước (cheap, rộng), pen test sau (đắt, sâu) cho critical asset.
</details>

<details>
<summary>Q3. Property-based testing khác fuzzing thế nào?</summary>

**Fuzzing**: input random/mutated, mục tiêu crash. Không có structured property cụ thể. Oracle là "crash hay hang".

**Property-based testing (PBT)**: định nghĩa property formal (ví dụ "reverse(reverse(list)) == list" hoặc "encrypt then decrypt = identity"). Framework sinh input ngẫu nhiên theo type, check property.

Khác biệt chính:
- PBT có structured input (theo type system của ngôn ngữ).
- PBT check semantic property (không chỉ crash).
- PBT cần programmer viết property (cost effort upfront).
- Fuzzing không cần property (chỉ cần input và executable).

Trong thực tế: PBT cho code có spec rõ (algorithm, parser format). Fuzzing cho code thiếu spec hoặc cần test wide.

Modern tool kết hợp cả hai: AFL có thể chạy với assertion (property), Hypothesis (PBT) có coverage-guided mode.
</details>

---

**Tiếp theo**: [5.3 Coverage criteria](./03-coverage-criteria)
