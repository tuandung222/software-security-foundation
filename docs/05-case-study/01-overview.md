---
id: 01-overview
title: 6.1 Tổng quan Case Study
sidebar_position: 1
description: "Framework chung để tiếp cận tư vấn security cho một dự án: threat modeling, STRIDE, attack tree, security requirement, defense in depth."
---

# Lecture 6 (Case Study): Tư vấn giải pháp Security

> **Tóm tắt một dòng**: Cụm này khác bốn cụm trước về tinh thần: thay vì đi sâu vào một kỹ thuật, ta áp dụng tổng hợp mọi kỹ thuật đã học để **tư vấn** cho một dự án thực tế. Mỗi scenario có format: bối cảnh công ty, các vấn đề security cần quan tâm, recommendation cụ thể kèm trade-off.

## Vì sao cần cụm Case Study?

Bốn cụm trước (Lec 1-5) dạy kỹ thuật: CIA, vulnerabilities, BMC, SMT, fuzzing. Đó là **what** và **how**: cái gì là bug, làm sao tìm, làm sao chứng minh.

Cụm này dạy **when** và **why**: trong một dự án cụ thể, ưu tiên gì, đầu tư vào đâu, đánh đổi như thế nào. Đây là kỹ năng của **security architect** hoặc **CISO**, không phải chỉ developer.

Khi bạn được giao một dự án mới, không có quy trình một-size-fit-all. Web app cần khác fintech cần khác IoT. Bài này giúp bạn:

1. Có một **framework chung** để tiếp cận mọi dự án.
2. Biết **các loại requirement** thường xuất hiện trong từng domain.
3. Biết **trade-off** giữa security với cost, performance, time-to-market.

## Framework: 5 bước tiếp cận

Một quy trình chuẩn industry để tư vấn security:

### Bước 1: Hiểu bối cảnh (Context)

Câu hỏi cần trả lời:

- Công ty làm gì? Sản phẩm chính là gì?
- Ai là user? Họ access từ đâu (mobile, desktop, IoT device)?
- Dữ liệu xử lý là loại nào (PII, payment, health, intellectual property)?
- Đối thủ và threat actor là ai (cybercrime, nation-state, competitor)?
- Budget và timeline có giới hạn gì?

Không có context, recommendation chỉ là generic. Ví dụ "dùng HTTPS" áp dụng mọi nơi, không phải tư vấn.

### Bước 2: Threat Modeling

Threat modeling là quy trình formal để liệt kê threat. Có nhiều framework, phổ biến nhất là **STRIDE** của Microsoft:

| Threat | Đe doạ | Vi phạm CIA |
|---|---|---|
| **S**poofing | Giả mạo danh tính | Authenticity |
| **T**ampering | Sửa data trái phép | Integrity |
| **R**epudiation | Chối bỏ đã làm gì | Non-repudiation |
| **I**nformation Disclosure | Rò rỉ thông tin | Confidentiality |
| **D**enial of Service | Làm dịch vụ down | Availability |
| **E**levation of Privilege | Leo thang quyền | Authorization |

Cho mỗi component của hệ thống (web server, database, API gateway), enumerate STRIDE threats. Output: bảng threat liệt kê các attack vector tiềm năng.

### Bước 3: Risk Assessment

Không phải threat nào cũng nguy hiểm như nhau. Risk = **Likelihood × Impact**:

| Likelihood | Impact | Risk |
|---|---|---|
| High (mỗi tuần) | Critical (mất 100% data) | Catastrophic |
| Medium (mỗi tháng) | High (mất 10% data) | High |
| Low (mỗi năm) | Medium (mất 1% data) | Medium |
| Very low (mỗi 10 năm) | Low | Low |

Sort threats theo risk, prioritize. Treat critical/high trước, low chấp nhận hoặc accept.

Tool industry: **DREAD** (Damage, Reproducibility, Exploitability, Affected users, Discoverability), **CVSS** (Common Vulnerability Scoring System).

### Bước 4: Mitigation và Defense in Depth

Cho mỗi high-risk threat, define **mitigation**:

- **Preventive**: ngăn không cho threat xảy ra (vd: input validation chống injection).
- **Detective**: phát hiện khi threat xảy ra (vd: SIEM, IDS).
- **Corrective**: phục hồi sau khi threat xảy ra (vd: backup, incident response).
- **Deterrent**: làm threat ít khả thi (vd: log toàn diện cho audit).

**Defense in depth**: không dựa vào một lớp bảo vệ. Combine nhiều layer. Ví dụ chống SQL injection:

- Layer 1: parameterized query (preventive, mạnh nhất).
- Layer 2: web application firewall (preventive, secondary).
- Layer 3: least privilege database account (mitigate impact nếu SQLi thành công).
- Layer 4: monitoring database query lạ (detective).
- Layer 5: audit log + backup (corrective).

Nếu attacker bypass layer 1 (ví dụ bug trong ORM), layer 2-5 vẫn chặn được.

### Bước 5: Trade-off và Roadmap

Security có cost. Mọi mitigation đều có:

- **Tiền**: tool license, infrastructure, headcount.
- **Performance**: encryption thêm latency, validation thêm CPU.
- **Usability**: 2FA tốn thời gian user, password complex khó nhớ.
- **Time-to-market**: review + audit chậm release.

Tư vấn tốt cân nhắc trade-off, không "max security everywhere". Roadmap chia mitigation thành phases:

- **Phase 1 (must-have)**: ngăn các bug critical (SQLi, auth bypass).
- **Phase 2 (should-have)**: defense in depth (WAF, monitoring).
- **Phase 3 (nice-to-have)**: advanced (BMC verification, formal proof).

## Áp dụng vào 4 scenario

Cụm này có 4 bài tương ứng 4 domain:

| Scenario | Đặc điểm | Bài học chính |
|---|---|---|
| [Web/SaaS Startup](./02-web-saas) | Move fast, MVP, scale fast | OWASP Top 10, auth, secrets management |
| [Fintech/Banking](./03-fintech) | High regulation, money | PCI-DSS, key management, transaction integrity |
| [IoT/Embedded](./04-iot) | Constrained resource, physical access | Memory safety, secure boot, OTA, side-channel |
| [Doanh nghiệp số hoá](./05-enterprise-cloud) | Legacy + cloud, federation | Identity, network segmentation, BYOD, ransomware |

Mỗi bài follow cấu trúc:
1. Bối cảnh và stakeholder.
2. Threat model (STRIDE applied).
3. Risk assessment.
4. Recommendation phase-by-phase.
5. Common pitfalls.

## Một số nguyên tắc chung xuyên suốt

Trước khi đi vào từng scenario, đây là các nguyên tắc áp dụng cho mọi domain:

### Principle 1: Least Privilege

Mỗi component chỉ có quyền tối thiểu cần thiết. Ví dụ:
- Database account của app chỉ có SELECT/INSERT/UPDATE trên các bảng app dùng, không phải mọi bảng.
- Container chạy với non-root user.
- AWS IAM role chỉ có S3:GetObject trên bucket cụ thể, không phải * trên *.

Khi attacker compromise một component, blast radius bị hạn chế bởi privilege của component đó.

### Principle 2: Zero Trust

Không tin tưởng dựa vào network location. "Inside corporate network" không có nghĩa "an toàn". Verify mọi request, mọi connection.

Implementation: mutual TLS, service mesh (Istio), policy-based access (OPA).

### Principle 3: Secure by Default

Mặc định setting là an toàn nhất. User phải explicit opt-in để giảm security.

Ví dụ: AWS S3 bucket mặc định private. User phải explicit set public. Trước 2018, mặc định là public, gây hàng nghìn data leak.

### Principle 4: Defense in Depth

Không dựa vào một lớp. Multiple layers, mỗi layer có thể fail.

### Principle 5: Fail Securely

Khi component fail, mặc định behavior là deny, không allow.

Ví dụ: nếu authorization service down, không cho phép action thay vì allow everything.

### Principle 6: Privacy by Design

Không lưu dữ liệu không cần. Encrypt at rest và in transit. Implement data deletion theo GDPR/CCPA request.

### Principle 7: Monitoring và Incident Response

Mọi component log đủ để truy ngược khi sự cố. Có playbook khi bug được phát hiện. Test playbook định kỳ.

## Ngoài STRIDE: các framework khác

STRIDE là phổ biến nhất nhưng không phải duy nhất. Một số framework khác:

**PASTA** (Process for Attack Simulation and Threat Analysis): 7 stage, sâu hơn STRIDE.

**ATT&CK** (MITRE): catalog attack tactic và technique. Không phải framework threat modeling thuần, mà là **kho** để map mọi attack đã quan sát thực tế. Dùng cho threat intelligence.

**Attack Tree**: vẽ cây với root là goal attacker (ví dụ "đánh cắp customer data"), child là cách đạt goal (SQL injection, social engineering, insider). Trực quan, hay dùng trong workshop.

**OCTAVE**: focus organizational risk (people, process, technology). Phù hợp enterprise có nhiều stakeholder.

Trong tài liệu này dùng STRIDE làm primary framework. Bạn có thể combine với attack tree cho complex threat.

## Tóm tắt

- Cụm Case Study về **tư vấn** dự án thực, không phải kỹ thuật cụ thể.
- **5 bước**: Context, Threat Model (STRIDE), Risk Assessment, Mitigation (defense in depth), Trade-off + Roadmap.
- **7 nguyên tắc chung**: Least Privilege, Zero Trust, Secure by Default, Defense in Depth, Fail Securely, Privacy by Design, Monitoring + IR.
- Framework khác: PASTA, ATT&CK, Attack Tree, OCTAVE.

## Mini-quiz

<details>
<summary>Q1. Phân biệt threat modeling và risk assessment.</summary>

**Threat modeling**: liệt kê **mọi threat tiềm năng** mà attacker có thể thử. Không phán xét likelihood/impact. Output: comprehensive list.

**Risk assessment**: với mỗi threat, đánh giá **likelihood** (xác suất xảy ra) và **impact** (hậu quả). Risk = Likelihood × Impact. Output: prioritized list.

Threat modeling cho ta "biết những gì có thể xảy ra". Risk assessment cho ta "biết phải lo cái nào trước".

Ví dụ: threat "nation-state attack với 0-day exploit" có impact catastrophic nhưng likelihood low cho startup nhỏ. Risk medium-low. Trong khi đó "SQL injection vào form login" likelihood high (script kiddie), impact high (data leak). Risk critical.

Threat modeling là input cho risk assessment. Cả hai phải làm.
</details>

<details>
<summary>Q2. Cho ví dụ "defense in depth" trong context chống XSS.</summary>

Defense in depth cho XSS:

- **Layer 1**: Output encoding theo context (HTML, attribute, JS, URL). Mạnh nhất.
- **Layer 2**: Content-Security-Policy header: cấm inline script, eval, restrict origin. Block attack ngay cả khi layer 1 fail.
- **Layer 3**: HttpOnly + Secure + SameSite cookie. XSS không lấy được session cookie.
- **Layer 4**: Trusted Types API (modern browser): chỉ cho phép gán DOM từ "trusted" source. Block toàn bộ class DOM-based XSS.
- **Layer 5**: WAF (Web Application Firewall) chặn payload nghi ngờ ở edge.
- **Layer 6**: Monitoring và alert khi thấy `<script>` trong log request lạ.

Nếu attacker bypass output encoding (layer 1), CSP chặn. Nếu CSP có exception cho legitimate inline script, HttpOnly cookie bảo vệ session. Mỗi layer "cover" lỗ hổng của layer khác.

Triết lý: không lớp nào perfect. Combine multiple đảm bảo overall security.
</details>

<details>
<summary>Q3. Tại sao "Secure by Default" lại quan trọng hơn "Documentation tốt"?</summary>

User không đọc documentation. Đặc biệt:
- Developer rush deadline.
- Junior không biết cần đọc gì.
- Sysadmin không expert security.

Setting mặc định ảnh hưởng **99%** user. Một mặc định không an toàn = 99% deployment không an toàn.

Ví dụ điển hình:
- **MongoDB pre-3.0**: mặc định bind 0.0.0.0 (mọi network), không có auth. Hàng chục nghìn database leak online vì admin không biết phải secure.
- **AWS S3 pre-2018**: mặc định ACL "public-read" cho nhiều operation. Hàng nghìn data leak. AWS phải đổi default + warning banner.

Documentation hữu ích nhưng không thay thế được mặc định an toàn. Best practice: mặc định mọi thứ deny/private, user explicit opt-in cho permission/exposure.

Trong Web framework: Django mặc định `DEBUG=False` cho production, CSRF protection enabled, XSS template escaping enabled. Không cần config thêm để "secure by default".
</details>

---

**Tiếp theo**: [6.2 Case Study: Web/SaaS Startup](./02-web-saas)
