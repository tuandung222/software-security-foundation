---
id: 02-web-saas
title: 6.2 Case Study - Web/SaaS Startup
sidebar_position: 2
description: "Tư vấn security cho startup web/SaaS, từ MVP launch tới scale up. OWASP Top 10, auth, secrets management, cloud security, roadmap chia phase."
---

# 6.2 Case Study: Web/SaaS Startup

## Bối cảnh

**Công ty A** là startup phát triển sản phẩm SaaS cho thị trường B2B. Sản phẩm hiện tại là một web app cho phép user tải file Excel, app phân tích và sinh report.

Thông số:
- 5 developer, 1 DevOps, không có security engineer.
- Stack: React frontend, Node.js backend, PostgreSQL, deployed trên AWS.
- 200 customer doanh nghiệp đang trả phí, tổng revenue $50K/month.
- Đang trong vòng gọi vốn Series A.
- Customer yêu cầu báo cáo security cho audit của họ.

**Đến gặp bạn** để tư vấn: "Chúng tôi cần làm gì để security tốt, qua được customer audit, và sẵn sàng scale lên 10x customer trong 6 tháng?"

## Bước 1: Hiểu Context

Đây là startup ở giai đoạn early-mid. Đặc điểm:

- **Time to market quan trọng**: không có budget cho security perfectionism.
- **Customer enterprise đòi hỏi**: SOC 2 audit, ISO 27001 ở chân trời.
- **Team nhỏ, không có dedicated security**: cần tool đơn giản, tự động.
- **Cloud-native**: AWS cung cấp nhiều primitive security sẵn.
- **Data sensitive**: file Excel của customer có thể chứa PII, financial data.

Recommend: focus vào **"good enough" security cho 90% threat**, không chạy theo bug edge case rare.

## Bước 2: Threat Modeling với STRIDE

Liệt kê component chính:

1. **React frontend** (CloudFront + S3).
2. **API backend** (Node.js trên ECS).
3. **Database** (RDS PostgreSQL).
4. **File storage** (S3 bucket).
5. **Auth service** (Cognito hoặc Auth0).

Cho mỗi component, áp dụng STRIDE. Đây là output rút gọn cho **API backend**:

| STRIDE | Threat cụ thể | Likelihood | Impact |
|---|---|---|---|
| Spoofing | Attacker gọi API với token giả | Medium | High |
| Tampering | SQL injection sửa data | High | Critical |
| Repudiation | User chối đã upload file XYZ | Low | Medium |
| Info Disclosure | API trả về data của user khác (IDOR) | High | High |
| DoS | Flood request, quá tải API | Medium | High |
| Elevation | User normal upgrade thành admin qua bug | Low | Critical |

Top threats theo risk: SQLi, IDOR, DoS, spoofing token.

## Bước 3: Risk-prioritized Recommendation

### Phase 1 (Must-have, làm trong 1 tháng): Cover OWASP Top 10

OWASP Top 10 là list lỗ hổng web phổ biến nhất, update mỗi 3-4 năm. Phiên bản 2021:

1. **A01 Broken Access Control** (IDOR, auth bypass).
2. **A02 Cryptographic Failures** (weak crypto, store password plain).
3. **A03 Injection** (SQLi, XSS, command injection).
4. **A04 Insecure Design** (thiếu rate limit, abuse logic).
5. **A05 Security Misconfiguration** (default password, debug mode in prod).
6. **A06 Vulnerable Components** (lib có CVE).
7. **A07 Auth Failures** (weak password, session fixation).
8. **A08 Data Integrity Failures** (no signature on update).
9. **A09 Logging Failures** (no audit log).
10. **A10 SSRF** (server-side request forgery).

Cover từng cái:

**A01 Access Control**:
- Mọi API endpoint check authorization explicit (không "if user logged in, allow").
- Object-level check: `if (resource.owner_id != current_user.id) return 403`.
- Test với 2 user account, đảm bảo user A không thấy data user B.

**A02 Cryptographic**:
- Password hash với bcrypt/argon2 (không MD5/SHA-1 thuần).
- TLS 1.2+ everywhere, HSTS header.
- Database encryption at rest (RDS encryption).

**A03 Injection**:
- ORM với parameterized query (Prisma, TypeORM).
- React auto-escape JSX (không dùng dangerouslySetInnerHTML).
- Input validation library (Joi, Zod) ở mọi endpoint.

**A04 Insecure Design**:
- Rate limit (express-rate-limit) ở endpoint nhạy cảm (login, password reset).
- Business logic review: "có thể abuse được không?" (vd: trial expire bypass, coupon stack).

**A05 Misconfiguration**:
- AWS Security Hub bật, follow recommendation.
- S3 bucket không public, encryption at rest.
- Container không chạy root.

**A06 Vulnerable Components**:
- Dependabot bật trên GitHub, auto-PR khi có CVE.
- `npm audit` trong CI, fail build nếu critical CVE.

**A07 Auth Failures**:
- Dùng Auth0/Cognito thay vì self-built auth.
- Password policy: min 8 chars, kết hợp letter + number, no common password.
- Session timeout 30 phút idle, 24h absolute.

**A08 Data Integrity**:
- HTTPS everywhere (đã có với CloudFront).
- File upload: verify content-type, không tin tưởng extension.

**A09 Logging**:
- CloudWatch log mọi authentication event, authorization deny, admin action.
- Retention 1 năm minimum.

**A10 SSRF**:
- Backend không gọi URL từ user input. Nếu cần, whitelist domain.

**Effort estimate**: 1 dev-month. Tool license: Auth0 ~$200/month, Dependabot free, AWS Security Hub ~$5/account/month.

### Phase 2 (Should-have, làm trong 3 tháng): Defense in depth

**WAF (Web Application Firewall)**:
- AWS WAF với managed rule (Core Rule Set, SQL Injection Rule, XSS Rule).
- Block payload SQLi/XSS biết trước, giảm load lên app.
- $5-10/month + rule cost.

**Secrets Management**:
- Không hard-code secret trong code/env file.
- AWS Secrets Manager hoặc HashiCorp Vault.
- Rotate database password tự động hàng quý.

**Container Image Scanning**:
- ECR có built-in scan (Trivy under the hood).
- Block deploy nếu high/critical CVE.

**SAST trong CI**:
- SonarQube hoặc Snyk Code.
- Catch lỗ hổng tại commit time, không phải production.

**Monitoring và Alerting**:
- CloudWatch alarm cho 5xx spike, login failure spike, slow query.
- PagerDuty/Opsgenie cho on-call.

**Effort estimate**: 1 dev-month. Tool cost: $100-300/month.

### Phase 3 (Nice-to-have, làm trong 6 tháng): Audit-ready

**SOC 2 Type 1 preparation**:
- Document policy (access control, incident response, data retention).
- Hire auditor (3-6 tháng process, $20-50K).

**Penetration Test**:
- Hire 3rd party pen tester (HackerOne, Cobalt).
- 2 weeks engagement, $15-30K.
- Fix findings critical/high, document.

**Bug Bounty Program**:
- Public program trên HackerOne (sau khi pen test xong).
- Pay $500-5000 per bug tuỳ severity.
- Incentivize community tìm bug 24/7.

**Effort estimate**: nhiều dev-month + budget $50K+.

## Bước 4: Common Pitfalls

Các sai lầm phổ biến của startup ở giai đoạn này:

### Pitfall 1: Self-build authentication

Đừng tự viết auth. Dùng Auth0, Cognito, Firebase Auth, Clerk. Tự viết = bug. Auth library handle:
- Password hashing đúng cách.
- Session management.
- Multi-factor auth.
- OAuth integration.
- Password reset flow.

Startup tự viết auth thường thiếu rate limit, OTP brute force protection, session fixation, ... Sửa bug auth là việc dài hơi.

### Pitfall 2: Bỏ qua dependency CVE

`npm install` xong, dependency graph có hàng nghìn package. Mỗi tháng có CVE mới. Không scan định kỳ = thời điểm nào đó sẽ deploy code có CVE biết trước.

Bật Dependabot. PR auto. Merge sớm.

### Pitfall 3: Secret trong code/.env commit

Easy mistake: tạo file `.env.example` với placeholder, dev copy thành `.env` và quên `.gitignore`. Push lên GitHub. Secret leak.

Solution: secret scanner trong pre-commit hook (TruffleHog, git-secrets). Và rotation policy: nếu nghi ngờ leak, rotate ngay.

### Pitfall 4: Tin tưởng client-side validation

Frontend validate `if (price >= 0) submit()`. Attacker bypass: dùng curl, gửi negative price. Backend không check. Negative price stored, free product.

**Rule**: backend luôn validate, không tin client. Frontend validation là UX, không phải security.

### Pitfall 5: Log nhạy cảm

`console.log(JSON.stringify(req.body))` log toàn body request, bao gồm password, credit card. Log file leak = breach.

**Rule**: structured logging với mask sensitive field. Tool: pino, winston với redaction.

### Pitfall 6: Không có incident response plan

Khi breach xảy ra, panic. Không biết:
- Ai notify ai (CTO, customer, regulator)?
- Steps để contain breach.
- Communication template cho customer.
- Legal obligation (GDPR notification trong 72h).

Solution: viết incident response playbook trước. Drill mỗi quý.

## Tóm tắt

- Phase 1 (1 tháng, ~$200-500/month): cover OWASP Top 10.
- Phase 2 (3 tháng): defense in depth (WAF, secrets, scanning, monitoring).
- Phase 3 (6 tháng+): audit-ready (SOC 2, pen test, bug bounty).
- Tránh self-build auth, ignore CVE, secret leak, trust client.

## Bài học chính

Web/SaaS startup cần balance "ship fast" và "secure". Tool managed (Auth0, AWS WAF, Snyk) giảm rất nhiều effort. Roadmap chia phase, mỗi phase deliver value visible.

Khi customer enterprise audit, có document và evidence sẵn (logs, policy, pen test report) là chìa khoá pass.

---

**Tiếp theo**: [6.3 Case Study: Fintech/Banking](./03-fintech)
