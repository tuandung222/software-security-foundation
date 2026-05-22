---
id: 05-enterprise-cloud
title: 6.5 Case Study - Doanh nghiệp số hoá
sidebar_position: 5
description: "Tư vấn security cho doanh nghiệp truyền thống chuyển lên cloud: identity federation, network segmentation, BYOD, ransomware protection, legacy system."
---

# 6.5 Case Study: Doanh nghiệp số hoá (Enterprise Cloud Migration)

## Bối cảnh

**Công ty D** là tập đoàn sản xuất truyền thống (đồ gia dụng), 5000 nhân viên, đang trong quá trình "digital transformation":

- Trước: ERP on-prem (SAP), mọi nhân viên access qua VPN.
- Đang: chuyển ERP lên SaaS (Workday, Salesforce), Office 365, deploy app web nội bộ trên AWS.
- Đang: cho phép BYOD (Bring Your Own Device), nhân viên làm việc từ xa.
- Trước: chỉ có IT support, không security team riêng.
- Mới: tuyển CISO + 5 security engineer.

**Đến gặp bạn** để tư vấn (bạn là consultant cho CISO mới): "Chúng tôi cần roadmap security 12 tháng để hỗ trợ digital transformation an toàn."

## Bước 1: Hiểu Context

Enterprise migrate to cloud có challenge riêng:

- **Legacy system phức tạp**: ERP cũ chứa logic 20 năm, không thể rewrite. Phải integrate với cloud.
- **Identity sprawl**: nhân viên có account ở 50+ system. Khó manage.
- **Compliance overlay**: SOX (financial), GDPR (PII), industry-specific (FDA, NIST).
- **People process change**: nhân viên không quen tool mới. Training cost lớn.
- **Vendor lock-in concern**: dùng nhiều SaaS, khó migrate sau.
- **Ransomware target**: enterprise = wallet to attacker.

Recommend: **roadmap chia phase**, đo bằng business outcome chứ không phải tool count.

## Bước 2: Threat Landscape

Enterprise face threat khác startup:

| Threat | Mức độ | Loss potential |
|---|---|---|
| Ransomware | Critical | $$$$ (millions USD) |
| Insider data theft (M&A info, IP) | High | $$$ |
| Phishing → compromise admin | Critical | $$$$ |
| Cloud misconfiguration → data leak | High | $$$ |
| Third-party breach (vendor) | High | $$$ |
| Compliance fine | Medium | $$ |

Top attacker tactic:

1. **Phishing**: email spoof, target nhân viên có quyền cao.
2. **Credential stuffing**: dùng credential leak từ breach khác.
3. **Supply chain**: compromise vendor có access vào hệ thống.
4. **Insider**: nhân viên bất mãn hoặc bị mua chuộc.
5. **Ransomware**: encrypt data, đòi tiền chuộc.

## Bước 3: Roadmap 12 tháng

### Tháng 1-3: Foundation

**Identity và Access Management (IAM)**

Vấn đề lớn nhất ở enterprise migrate: identity ở mọi nơi. AD on-prem, Salesforce, Workday, AWS, ... Mỗi system account riêng.

**Solution**: **Identity Federation** với Single Sign-On (SSO).

```
Employee → Identity Provider (Azure AD / Okta) → 50+ SaaS / AWS
```

Một login cho mọi thứ. Khi nhân viên nghỉ việc, disable trong IdP, mọi system mất access.

**Implementation**:
- Choose IdP: Azure AD (nếu đã có Microsoft) hoặc Okta (multi-cloud friendly).
- Federate SAML / OIDC với mọi SaaS.
- Implement SCIM cho auto-provisioning.

**Multi-Factor Authentication (MFA)**:
- Bắt buộc cho mọi access.
- Push notification (Duo, Microsoft Authenticator) > SMS.
- FIDO2 hardware key cho admin (cao nhất).

**Privileged Access Management (PAM)**:
- Admin account dùng riêng (không phải daily account).
- Just-in-time access: request quyền admin khi cần, expire sau X giờ.
- Tool: CyberArk, BeyondTrust.

### Tháng 3-6: Network và Endpoint

**Zero Trust Network**:

Cũ: VPN cho mọi access. Sai vì:
- VPN compromise = full network access.
- Lateral movement easy.
- Không scale với BYOD.

Mới: **Zero Trust**. Mỗi request verify regardless network location.

Implementation:
- **Software-defined perimeter** (Zscaler, Cloudflare Access).
- **Microsegmentation**: app A không thấy app B unless explicitly allowed.
- **Service mesh** (Istio) cho microservice.

**Endpoint Detection and Response (EDR)**:

Cài agent trên mọi laptop, server. Agent monitor:
- Process execution suspicious.
- File access pattern.
- Network connection.
- Behavior anomaly.

Tool: CrowdStrike, SentinelOne, Microsoft Defender for Endpoint.

**Mobile Device Management (MDM)**:

BYOD = phone cá nhân, không control hoàn toàn.

Solution: MDM enforce policy:
- Encrypt device.
- Password 6 digit minimum.
- Remote wipe nếu mất.
- Containerize work data (Microsoft Intune, MobileIron).

### Tháng 6-9: Data Protection

**Data Loss Prevention (DLP)**:

Monitor data leaving company:
- Email với attachment có PII → block hoặc encrypt.
- Upload tới personal cloud (Dropbox cá nhân) → block.
- Print large data set → log + approval.

Tool: Microsoft Purview, Symantec DLP.

**Cloud Access Security Broker (CASB)**:

Visibility và control trên SaaS usage:
- Discover Shadow IT (employee dùng SaaS không qua IT).
- Enforce policy (only allowed SaaS).
- DLP for SaaS data.

Tool: Netskope, Zscaler, Microsoft Defender for Cloud Apps.

**Backup và Ransomware**:

Ransomware kéo critical attack vector cho enterprise.

Mitigation:
- **3-2-1 backup**: 3 copy, 2 medium khác, 1 offsite.
- **Immutable backup**: không thể delete trong 30 ngày (S3 Object Lock, Veeam Immutable).
- **Air-gapped backup**: 1 copy hoàn toàn offline.
- **Test restore**: monthly drill, không chỉ test backup work, test recovery time.
- **Endpoint protection** với behavioral detection (CrowdStrike, SentinelOne).
- **Email security** (phishing là ingress chính): Proofpoint, Mimecast.

### Tháng 9-12: Compliance và Governance

**Information Security Policy**:

Document policy formal cho:
- Acceptable Use.
- Data Classification (Public, Internal, Confidential, Restricted).
- Incident Response.
- Vendor Risk Management.
- BCP/DR (Business Continuity / Disaster Recovery).

**Security Awareness Training**:

Mandatory cho mọi nhân viên:
- Phishing simulation hàng tháng.
- Annual security training.
- Onboarding training cho new hire.

Tool: KnowBe4, Cofense.

**Vendor Risk Management**:

Mọi vendor có access vào data company phải:
- Pass security questionnaire.
- Có SOC 2 report (hoặc tương đương).
- Sign DPA (Data Processing Agreement).
- Review hàng năm.

Tool: OneTrust, ProcessUnity.

**Compliance Certifications**:

Tuỳ industry:
- **SOC 2 Type 2**: 6 tháng observation period, $50-100K cost.
- **ISO 27001**: international standard, $30-80K.
- **GDPR**: nếu có EU user, designate DPO.
- **HIPAA**: nếu xử lý health data.

## Bước 4: Common Pitfalls

### Pitfall 1: "Lift and shift" không secure

Move workload từ on-prem lên cloud nguyên xi. Security model on-prem không apply cho cloud:
- Firewall rule on-prem khác AWS Security Group.
- IAM concept on-prem khác cloud.

Solution: re-architect cho cloud-native security (security group, IAM role, KMS, ...).

### Pitfall 2: Quá nhiều tool, overlap

Mua mọi tool quảng cáo: SIEM, SOAR, XDR, CSPM, DLP, ... Team không dùng được hết. Lãng phí budget.

Solution: chọn 1 tool / category, integrate well. Less is more.

### Pitfall 3: Security as blocker, không enabler

Security team say "no" mọi thứ. Developer bypass, dùng shadow IT.

Solution: security partnership. Đề xuất alternative thay vì reject. "Bạn muốn dùng tool X, tốt cho UX, nhưng concern A, B. Hãy cùng giải quyết."

### Pitfall 4: Bỏ qua phishing training

Bỏ tiền vào tool nhưng không train nhân viên. 95% breach bắt đầu bằng phishing. Training cheap, ROI cao nhất.

### Pitfall 5: Không test incident response

Có IR playbook nhưng không drill. Khi real incident, panic, slow.

Solution: tabletop exercise mỗi quý. Simulate breach scenario, walk through response.

### Pitfall 6: Bỏ qua Insider Threat

Focus external attacker, quên insider. Disgruntled employee, departing employee. 30% breach involve insider.

Solution: User Behavior Analytics (UBA), monitoring privileged access, exit interview với data check.

## Bước 5: Metric để đo success

12 tháng sau, đo:

| Metric | Target |
|---|---|
| % employee with MFA | 100% |
| % critical asset có EDR | 100% |
| Phishing click rate | < 5% (after training) |
| Mean Time to Detect (MTTD) | < 1 hour |
| Mean Time to Respond (MTTR) | < 4 hours |
| % vendors with SOC 2 | 80%+ |
| Backup restore test success | 100% monthly |
| Open critical vulnerabilities > 30 days | 0 |

Không có "100% secure" KPI. Mục tiêu là **reduce risk** measurably.

## Tóm tắt

- Enterprise migrate cloud cần roadmap 12+ tháng.
- **Tháng 1-3**: Identity (SSO, MFA, PAM).
- **Tháng 3-6**: Network (Zero Trust) + Endpoint (EDR, MDM).
- **Tháng 6-9**: Data (DLP, CASB, Backup).
- **Tháng 9-12**: Governance (Policy, Training, Vendor risk, Compliance).
- Avoid: lift-and-shift, tool overlap, security as blocker, no IR drill, insider blind spot.

## Bài học chính

Enterprise security là về **process và people**, không chỉ technology. Nhân viên là target chính (phishing). Vendor là attack vector growing (supply chain). Insider luôn risk.

Tool quan trọng nhưng không đủ. CISO thành công là người **partner với business**, không "police". Security enable business chuyển đổi, không block.

---

**Kết thúc Cụm 5 (Case Study).** Bạn đã có 4 framework để tư vấn 4 domain phổ biến: Web/SaaS, Fintech, IoT, Enterprise. Combine với kỹ thuật đã học ở Lec 1-5, bạn đủ kiến thức để approach hầu hết security project trong industry.
