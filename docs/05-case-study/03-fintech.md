---
id: 03-fintech
title: 6.3 Case Study - Fintech/Banking
sidebar_position: 3
description: "Tư vấn security cho fintech: PCI-DSS compliance, key management, transaction integrity, anti-fraud, audit log. Khác biệt với SaaS thông thường."
---

# 6.3 Case Study: Fintech / Banking

## Bối cảnh

**Công ty B** là fintech startup phát triển ví điện tử cho thị trường Đông Nam Á. App cho phép user nạp tiền, chuyển tiền, thanh toán merchant, tiết kiệm.

Thông số:
- 30 developer, 5 security engineer (đã có).
- Stack: React Native mobile, Go backend, PostgreSQL + Redis, deploy on prem + AWS hybrid.
- 5 triệu user, \$200M transaction/month.
- License **Tổ chức cung ứng dịch vụ trung gian thanh toán** từ NHNN.
- Phải tuân thủ **PCI-DSS** (vì xử lý thẻ tín dụng/debit).

**Đến gặp bạn** để tư vấn: "Chúng tôi sắp launch tính năng buy-now-pay-later, scale lên 20 triệu user. Cần thiết kế security cho tính năng mới và đảm bảo compliance audit pass."

## Bước 1: Hiểu Context

Fintech khác SaaS thông thường ở mức độ:

- **Regulation cực kỳ nặng**: NHNN, PCI-DSS, AML/KYC, GDPR (nếu user EU), local data residency law.
- **Money là target**: attacker có **financial incentive** rõ ràng. Nation-state, organized crime đầu tư resource.
- **Reputation critical**: một sự cố lớn = mất license, mất user.
- **Audit liên tục**: external auditor (Big 4), internal audit, regulator inspection.

Recommend: **không có shortcut**. Mọi feature phải qua security review. Budget phải để cho red team.

## Bước 2: Threat Modeling

Bảng STRIDE cho component **payment processing**:

| STRIDE | Threat | Mức quan trọng |
|---|---|---|
| Spoofing | Attacker giả user, transfer tiền | Critical |
| Tampering | MITM sửa amount giữa client và server | Critical |
| Tampering | Database breach, sửa balance | Critical |
| Repudiation | User chối đã transfer | High (legal) |
| Info Disclosure | Card number leak | Critical (PCI fine) |
| DoS | Attack ngày Black Friday | High |
| Elevation | Insider abuse, transfer ra account riêng | Critical |

Thêm threat đặc thù fintech:

- **Account Takeover (ATO)**: attacker steal credential, take over account.
- **Money mule**: account hợp pháp dùng để launder money.
- **Fraud network**: synthetic identity, ring of fake account.
- **API abuse**: thuê dịch vụ với credit card giả.

## Bước 3: Recommendation cho từng khía cạnh

### 3.1 PCI-DSS Compliance

PCI-DSS là standard cho mọi entity xử lý payment card. 12 requirement chính:

| Req | Mô tả ngắn |
|---|---|
| 1 | Firewall và network segmentation |
| 2 | Không default password |
| 3 | Protect stored cardholder data (PAN encryption) |
| 4 | Encrypt transmission (TLS) |
| 5 | Anti-malware |
| 6 | Secure development (SDLC, vuln scan) |
| 7 | Access control by business need |
| 8 | Identify and authenticate access |
| 9 | Physical access control |
| 10 | Track and monitor access |
| 11 | Regularly test (pen test, vuln scan) |
| 12 | Information security policy |

Đặc biệt khó:

**Req 3 (Encrypt PAN)**:
- PAN (Primary Account Number) phải mask khi display (chỉ show 4 số cuối).
- PAN phải encrypt at rest với key được manage trong HSM (Hardware Security Module).
- KHÔNG được store CVV/CVC.

**Req 10 (Logging)**:
- Mọi access tới cardholder data phải log.
- Log retention 1 năm minimum, 3 tháng online.
- Log không thể bị sửa (write-once or signed).

**Recommendation**: dùng **PCI-DSS scope reduction**. Không store cardholder data trên server của bạn. Dùng **tokenization** từ payment processor (Stripe, Adyen, VNPAY). Token thay thế PAN, có scope hẹp hơn nhiều.

Scope reduction giảm complience cost từ hàng trăm K USD/năm xuống hàng chục K.

### 3.2 Key Management

Trong fintech, key management là chỗ rất dễ sai và rất đắt khi sai.

**Hierarchy of keys**:

```
Master Key (HSM, never leaves)
    ↓ derives
KEK (Key Encryption Key)
    ↓ encrypts
DEK (Data Encryption Key)
    ↓ encrypts
Actual data (cardholder data, PII)
```

**Best practice**:
- Master key trong HSM (Thales Luna, AWS KMS HSM-backed). Không bao giờ rời HSM.
- Rotate DEK mỗi năm, re-encrypt data.
- Rotate KEK mỗi 2-3 năm.
- Có procedure recovery nếu HSM hỏng (multiple HSM cluster, key shares M-of-N).

**Avoid**:
- Store key trong code, env var, config file.
- Dùng cùng key cho mọi service (compromise 1 = compromise all).
- Manual key handling (human typing key = mistake).

### 3.3 Transaction Integrity

Mỗi transaction phải bảo đảm:

**Atomicity**: A → B chuyển 100K. Hoặc cả A trừ + B cộng, hoặc không gì cả. Không có "A trừ nhưng B không nhận".

Implementation:
- Database transaction (PostgreSQL BEGIN ... COMMIT).
- Distributed transaction nếu A và B khác database (2PC, saga pattern).

**Idempotency**: client retry transaction. Server thực hiện đúng 1 lần.

Implementation:
- Client gửi `idempotency_key` UUID.
- Server check key trước khi process. Nếu đã process, return previous result.

**Signed audit log**:
- Mỗi transaction log với timestamp, amount, signed by HSM.
- Audit log không thể sửa (append-only DB hoặc blockchain).

### 3.4 Anti-Fraud

Fraud detection là một ngành riêng. Cơ bản:

**Rule-based**:
- Transaction > \$10K từ tài khoản mới → flag.
- 10 transaction trong 1 phút từ cùng IP → block.
- Transaction từ device chưa từng dùng → require 2FA.

**ML-based**:
- Train model với historical fraud data.
- Feature: amount, time, location, device fingerprint, behavior pattern.
- Score mỗi transaction, > threshold → manual review.

Tool: Sift, Forter, hoặc build in-house.

**Trade-off**: false positive (legitimate user bị block) làm hại UX. False negative (fraud không catch) tốn tiền. Tune threshold theo cost.

### 3.5 KYC và AML

**KYC (Know Your Customer)**: verify identity của user khi onboard.
- Upload CCCD/CMND, selfie với CCCD.
- Liveness check (không phải photo của photo).
- Cross-check với government database nếu có.

**AML (Anti-Money Laundering)**:
- Monitor pattern transaction nghi ngờ (structuring, layering).
- Report Suspicious Activity Report (SAR) tới regulator.
- Hold transaction nghi ngờ pending review.

Tool: ComplyAdvantage, Refinitiv World-Check.

### 3.6 Insider Threat

Insider có quyền access database, có thể:
- Trừ balance của user.
- Tạo account giả, transfer tiền.
- Export PII bán cho 3rd party.

Mitigation:

- **Least privilege**: developer không access production data. Read-only account cho debug.
- **4-eye principle**: action sensitive (refund > \$10K) cần 2 người approve.
- **Audit log everything**: mọi query database log với user ID, query text.
- **Behavior analytics**: nhân viên access data ngoài giờ làm hoặc volume bất thường → alert.

Insider threat khó vì attacker biết internal. Combine technical control (least privilege) + organizational (background check, separation of duties) + cultural (whistleblower policy).

## Bước 4: Common Pitfalls fintech

### Pitfall 1: Store CVV

CVV/CVC chỉ dùng để verify transaction tại điểm authorization. Sau đó **bắt buộc** xoá. Store CVV = vi phạm PCI-DSS, fine \$5K-100K/month.

### Pitfall 2: Round error trong tính lãi/phí

```python
fee = amount * 0.01
total = amount + fee
```

Với float, $100.001 * 0.01 = 1.0000099999999$. Tích luỹ qua hàng triệu transaction tạo discrepancy. Cuối năm balance off bằng tỷ VND.

Fix: dùng **decimal** type (Python `Decimal`, Go `big.Float`, PostgreSQL `NUMERIC`). Không dùng float cho money.

### Pitfall 3: Race condition trong balance update

```python
def transfer(from_id, to_id, amount):
    balance = db.query(from_id).balance
    if balance >= amount:
        db.update(from_id, balance - amount)
        db.update(to_id, db.query(to_id).balance + amount)
```

Race: 2 transfer cùng lúc từ cùng account, cả 2 đọc balance trước update. Cả 2 pass check. Balance âm.

Fix: dùng `SELECT FOR UPDATE` hoặc database constraint `CHECK (balance >= 0)`.

### Pitfall 4: Timing attack trong compare token

```python
if token == valid_token:  # WRONG, không constant-time
    grant_access()
```

Compare normal stop tại byte khác đầu tiên. Attacker đo response time để guess byte by byte token.

Fix: dùng `hmac.compare_digest()` hoặc `crypto.timingSafeEqual()` (Node.js).

### Pitfall 5: Webhook không verify signature

Payment processor (Stripe, VNPAY) gửi webhook khi transaction complete. App của bạn nhận, update balance.

Attacker phát hiện webhook endpoint, gửi fake webhook để credit balance miễn phí.

Fix: verify HMAC signature trong webhook header. Mỗi processor có document riêng.

## Tóm tắt

- Fintech regulation rất nặng: PCI-DSS, NHNN, AML/KYC.
- **Tokenization** giảm PCI scope, đáng đầu tư.
- **Key management** với HSM, không bao giờ hard-code key.
- **Transaction integrity**: atomicity + idempotency + audit log.
- **Anti-fraud**: rule + ML, balance false pos/neg.
- **Insider threat**: least privilege, 4-eye, audit.
- Avoid: store CVV, float arithmetic, race condition, timing attack, unverified webhook.

## Bài học chính

Fintech cần **defense in depth** ở mọi tầng vì stake cao. Không có "good enough". Mỗi feature phải qua security review formal. Đầu tư vào red team + bug bounty là không tuỳ chọn.

Compliance không phải checkbox. Nó là continuous: auditor sẽ check lại mỗi năm, regulator có thể inspect bất kỳ lúc nào.

---

**Tiếp theo**: [6.4 Case Study: IoT/Embedded](./04-iot)
