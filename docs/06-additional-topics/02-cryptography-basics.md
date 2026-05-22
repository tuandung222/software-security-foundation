---
id: 02-cryptography-basics
title: 7.2 Cryptography basics cho Software Security
sidebar_position: 2
description: "Hash, MAC, symmetric/asymmetric encryption, PKI, key derivation. Đủ để hiểu CIA và tránh dùng sai cryptography trong code."
---

# 7.2 Cryptography basics cho Software Security

> **Tóm tắt một dòng**: Cryptography là toán học của việc giấu và xác thực thông tin. Bài này không dạy bạn thiết kế thuật toán mới (chỉ chuyên gia mới làm), mà dạy bạn **dùng đúng** các primitive có sẵn (hash, MAC, encryption, signature, PKI) trong code. Sai một bước nhỏ trong cách dùng = phá vỡ toàn bộ.

## Vì sao bài này quan trọng?

Ở [bài 1.1](../01-introduction/01-overview), ta đã thấy ranh giới giữa Cryptography và Software Security: cryptography giả định code đúng, Software Security làm cho code đúng. Vậy tại sao một bài về cryptography lại nằm trong tài liệu Software Security?

Lý do: **dùng cryptography sai là một dạng implementation vulnerability**. Code "đúng compile" nhưng dùng MD5 cho password = bug security. Code dùng AES nhưng hardcode key trong source = bug. Vì thế, một Software Security engineer cần biết:

1. Mỗi primitive cryptography làm gì và **không làm** gì.
2. Cách dùng đúng từng primitive (mode, padding, IV, key size).
3. Khi nào dùng cái nào.
4. Các pitfall phổ biến.

Bài này cover phần 1-4 ở mức "đủ dùng", không sâu vào toán học.

## 1. Hash function

Hash function ánh xạ **input bất kỳ kích thước** thành **output cố định kích thước**, ví dụ SHA-256 luôn cho 256 bit.

Ba tính chất cốt lõi của hash an toàn:

1. **Preimage resistance**: cho output $h$, khó tìm input $x$ thoả $\text{hash}(x) = h$.
2. **Second preimage resistance**: cho $x_1$, khó tìm $x_2 \neq x_1$ với $\text{hash}(x_1) = \text{hash}(x_2)$.
3. **Collision resistance**: khó tìm hai input bất kỳ $x_1 \neq x_2$ có cùng hash.

### Các hash function phổ biến

| Hash | Output | Trạng thái | Dùng cho |
|---|---|---|---|
| MD5 | 128-bit | **Broken** (collision 2004) | Chỉ checksum non-security |
| SHA-1 | 160-bit | **Broken** (collision 2017 SHAttered) | Legacy, nên migrate |
| SHA-256 | 256-bit | An toàn | Mặc định mới |
| SHA-512 | 512-bit | An toàn | Khi cần độ rộng cao |
| SHA-3 (Keccak) | 256/512-bit | An toàn | Backup cho SHA-2 |
| BLAKE3 | 256-bit | An toàn, nhanh | Modern, parallel |

**Quy tắc 2024**: dùng SHA-256 hoặc BLAKE3. Tránh MD5, SHA-1 cho mọi security purpose.

### Sai lầm thường gặp 1: dùng hash cho password

```python
# SAI
import hashlib
password_hash = hashlib.sha256(password.encode()).hexdigest()
db.save(user_id, password_hash)
```

Tại sao sai? SHA-256 quá nhanh. GPU modern hash 10 tỷ lần/giây. Brute force 8-char password mất giây.

Đúng cách: dùng **password hashing function** chuyên biệt có work factor (chậm chủ ý).

```python
# ĐÚNG
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
db.save(user_id, password_hash)
```

`bcrypt`, `argon2`, `scrypt`, `PBKDF2` là 4 password hash chuẩn. Argon2 là winner của Password Hashing Competition 2015, được khuyến nghị cho thiết kế mới.

Trade-off:
- Rounds cao = chậm hơn brute force nhưng cũng chậm hơn login hợp pháp.
- Pick `rounds=12` cho bcrypt (~100ms/hash) là sweet spot 2024.

### Sai lầm thường gặp 2: hash không salt

```python
# SAI
hash = sha256(password)
```

Hai user cùng password = cùng hash. Attacker dump database, tìm hash chung = biết những user dùng cùng password. Rainbow table tấn công.

Đúng: thêm **salt** ngẫu nhiên cho mỗi user.

```python
# ĐÚNG (bcrypt làm tự động)
salt = bcrypt.gensalt()
hash = bcrypt.hashpw(password.encode(), salt)
# salt được embed trong hash output
```

`bcrypt` và `argon2` tự sinh salt và store cùng hash. Không cần làm thủ công.

## 2. Symmetric Encryption

Encryption ngược được = decryption. Symmetric: cùng key cho cả hai phép.

### Block cipher: AES

**AES (Advanced Encryption Standard)** là chuẩn industry. Key 128, 192, hoặc 256 bit. Block 128 bit.

AES tự nó chỉ encrypt 1 block 128-bit. Để encrypt message dài, cần **mode of operation**:

| Mode | An toàn? | Đặc điểm |
|---|:-:|---|
| ECB | Không | Mỗi block độc lập, lộ pattern |
| CBC | Có (với HMAC) | Cần IV ngẫu nhiên, không authenticated |
| CTR | Có (với HMAC) | Stream mode, parallelizable, cần unique nonce |
| **GCM** | **Có** | **Authenticated**, mode mặc định cho mới |

**Quy tắc 2024**: dùng **AES-GCM** hoặc **ChaCha20-Poly1305**. Cả hai đều là **AEAD** (Authenticated Encryption with Associated Data): tự handle confidentiality + integrity trong một call.

```python
# ĐÚNG: AES-GCM với cryptography library
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = AESGCM.generate_key(bit_length=256)
aesgcm = AESGCM(key)
nonce = os.urandom(12)   # 96-bit nonce
ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)
# Để decrypt:
plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
```

### Sai lầm: dùng ECB

```python
# SAI: AES-ECB
```

Hậu quả: cùng plaintext block → cùng ciphertext block. Pattern hiện ra.

Ví dụ kinh điển: encrypt một hình ảnh bằng AES-ECB, hình vẫn nhìn ra outline. Đây là "Penguin example" được dạy trong mọi crypto course.

**Quy tắc**: KHÔNG BAO GIỜ dùng ECB cho data có pattern.

### Sai lầm: tái dùng nonce/IV

GCM: nonce 96-bit. Mỗi message phải có nonce **unique** với cùng key.

Tái dùng nonce 1 lần với 2 message khác nhau = phá hoàn toàn confidentiality + integrity. XOR hai ciphertext = XOR hai plaintext, attacker lấy được plaintext.

**Quy tắc**: sinh nonce ngẫu nhiên cho mỗi message hoặc dùng counter có sync.

### Stream cipher: ChaCha20

ChaCha20 (Daniel J. Bernstein) là stream cipher modern, nhanh hơn AES trên CPU không có AES-NI (mobile, embedded). Kết hợp với Poly1305 MAC thành **ChaCha20-Poly1305**, AEAD tương đương AES-GCM.

Google sử dụng ChaCha20-Poly1305 cho TLS trên Android. Wireguard dùng làm primitive chính.

## 3. Asymmetric Encryption và Digital Signature

Asymmetric: 2 key khác nhau, **public key** và **private key**. Encrypt với public, decrypt với private (và ngược lại cho signature).

### RSA

Dựa trên độ khó integer factorization. Key size 2048-bit (minimum 2024) hoặc 3072/4096-bit cho long-term.

Phép cơ bản:
- `encrypt(public_key, plaintext)`: bất kỳ ai có public key đều encrypt được.
- `decrypt(private_key, ciphertext)`: chỉ owner private key decrypt được.
- `sign(private_key, message)`: tạo signature, owner private key.
- `verify(public_key, message, signature)`: ai có public key đều verify được.

```python
# ĐÚNG: RSA signature với padding chuẩn
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Sign
signature = private_key.sign(
    message,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256()
)

# Verify
public_key.verify(
    signature, message,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256()
)
```

Quan trọng: dùng **PSS padding**, không phải PKCS1v15 cũ (có attack).

### Elliptic Curve

Modern alternative cho RSA. Key nhỏ hơn nhiều cho cùng mức bảo mật:
- 256-bit ECC ≈ 3072-bit RSA.
- Tốc độ nhanh hơn, đặc biệt cho key generation.

**Curve phổ biến**:
- **P-256** (NIST): được hỗ trợ rộng nhất.
- **Curve25519** (Bernstein): dùng cho key exchange (X25519).
- **Ed25519**: dùng cho signature.

```python
from cryptography.hazmat.primitives.asymmetric import ed25519

private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

signature = private_key.sign(message)
public_key.verify(signature, message)
```

Ed25519 không có padding option (built-in chuẩn), API đơn giản hơn RSA nhiều.

### MAC vs Digital Signature

Quan trọng phân biệt:

| | MAC (HMAC) | Digital Signature |
|---|---|---|
| Key | Symmetric (shared) | Asymmetric (private/public) |
| Verify | Cùng key generate | Public key |
| Non-repudiation | Không | Có |
| Tốc độ | Nhanh | Chậm hơn (RSA), nhanh hơn (Ed25519) |
| Khi dùng | Internal API auth, session token | Document signing, cert, software update |

Đã giải thích chi tiết ở [bài 1.2](../01-introduction/02-cia-and-properties). Nhắc lại: MAC không cho Non-repudiation vì cả 2 bên đều có key.

## 4. Key Derivation Function (KDF)

Vấn đề: bạn có một "input key material" (IKM) như password, shared secret từ DH, hoặc master key. Muốn derive từ đó nhiều subkey cho các purpose khác nhau (encryption, MAC, IV).

**HKDF (HMAC-based KDF)** là standard:

```python
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

hkdf = HKDF(
    algorithm=hashes.SHA256(),
    length=32,          # output 32 byte
    salt=salt,
    info=b'application context, e.g. "encryption key v1"',
)
derived_key = hkdf.derive(input_key_material)
```

`info` field cho phép derive **nhiều key** từ cùng IKM với label khác nhau:
- `info="encrypt"` → encryption key.
- `info="mac"` → MAC key.
- `info="iv"` → IV.

Mỗi derived key độc lập, leak một cái không affect cái khác.

## 5. Public Key Infrastructure (PKI)

PKI quản lý certificate, là document signed bởi Certificate Authority (CA) chứng nhận public key thuộc về danh tính nào.

```
Root CA (self-signed, in trust store)
    ↓ signs
Intermediate CA
    ↓ signs
End-entity cert (your website)
```

**TLS handshake** verify cert chain:
1. Server gửi cert.
2. Client check signature từ Intermediate CA.
3. Client check Intermediate cert signature từ Root CA.
4. Client check Root CA trong trust store của OS/browser.

Nếu chain valid, public key trong end-entity cert được tin tưởng để encrypt session key.

### Sai lầm: tự ký cert, disable verify

```python
# SAI
requests.get("https://api.example.com", verify=False)
```

`verify=False` bypass cert check. MITM attack = ăn được mọi traffic. Bug rất phổ biến trong dev code lọt vào production.

**Quy tắc**: dùng cert thật (Let's Encrypt free, ACM trên AWS). Không bao giờ disable verify trong prod.

## 6. Side-channel Attack Awareness

Side-channel: lấy secret qua "kênh phụ" không qua main algorithm.

Loại phổ biến:

**Timing attack**: đo thời gian xử lý. Naive `string_compare` stop tại byte khác đầu tiên, attacker đo time để guess byte-by-byte.

```python
# SAI
if user_token == valid_token:
    grant_access()

# ĐÚNG: constant-time compare
import hmac
if hmac.compare_digest(user_token, valid_token):
    grant_access()
```

**Power analysis**: đo điện tiêu thụ trong khi crypto chạy. AES không constant-time để lộ key bit qua mức điện. Mitigation: AES-NI (CPU implementation) constant-time.

**Cache attack** (Spectre, Meltdown): đo cache hit/miss để leak data từ kernel/sandbox. Mitigation: kernel patch, microcode update.

Side-channel relevant cho **HSM, smart card, banking terminal, military equipment**. Đối với app thông thường, dùng implementation đã hardened (libsodium, cryptography library) đủ.

## 7. Tổng kết "dùng đúng" cryptography

| Mục đích | Recommendation 2024 |
|---|---|
| Password hashing | bcrypt rounds=12, hoặc argon2id |
| Symmetric encryption | AES-GCM 256-bit, hoặc ChaCha20-Poly1305 |
| Hash for integrity | SHA-256, BLAKE3 |
| MAC | HMAC-SHA256 |
| Signature | Ed25519 (modern), RSA-PSS 2048+ (compat) |
| Key exchange | X25519, ECDH P-256 |
| KDF | HKDF-SHA256 |
| TLS | TLS 1.3 only (or 1.2 minimum) |
| Random number | OS CSPRNG (`os.urandom`, `secrets.token_bytes`) |

**Quy tắc vàng**: dùng library cao cấp (libsodium, NaCl, cryptography), không "roll your own crypto". Library đã handle padding, mode, side-channel, key management.

## DS perspective

Cryptography có nhiều điểm tương đồng với ML:

- **Hash function ≈ feature hashing**: ánh xạ input variable size → fixed size. Hash trong ML dùng cho feature engineering (hashing trick).
- **Encryption ≈ obfuscation/encoding**: biến input thành dạng khó đọc. ML có concept tương tự với encoded representation (autoencoder).
- **Key derivation ≈ embedding**: từ input thấp chiều → vector cao chiều có structure. HKDF giống embedding layer.
- **Side-channel attack ≈ membership inference**: leak thông tin gián tiếp. ML có membership inference attack tương tự (xem model output đoán training data).

Khác biệt cốt lõi: crypto cần **đảm bảo mathematically** an toàn, ML chỉ cần **statistically** tốt.

## Mini-quiz

<details>
<summary>Q1. Vì sao dùng SHA-256 cho password là sai? Đề xuất giải pháp.</summary>

SHA-256 được thiết kế **nhanh** (xử lý gigabyte/giây). Tốt cho integrity check, file hash. Nhưng password hash cần **chậm** để chống brute force.

GPU modern hash SHA-256 ~10 tỷ lần/giây. Brute force 8-char password (62^8 ≈ 2 * 10^14 case) trong vài giờ.

Đúng: dùng **bcrypt, argon2, scrypt, PBKDF2** với work factor. bcrypt rounds=12 ≈ 100ms/hash. Brute force 8-char ≈ 700 năm.

```python
import bcrypt
hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```
</details>

<details>
<summary>Q2. Phân biệt AES-GCM và AES-CBC. Cái nào nên dùng cho code mới?</summary>

**AES-CBC**: chỉ encryption (confidentiality). Cần **HMAC riêng** cho integrity. Cần IV ngẫu nhiên. Padding (PKCS#7).

**AES-GCM**: AEAD - kết hợp encryption + authentication trong một mode. Không cần HMAC riêng. Cần unique nonce. Không padding.

**Code mới: dùng GCM**. Lý do:
- Một call thay vì hai (encrypt + HMAC).
- Khó dùng sai hơn (không quên HMAC).
- Performance tốt hơn (parallel).
- Standard cho TLS 1.3.

CBC vẫn an toàn nếu dùng đúng (HMAC, IV ngẫu nhiên), nhưng dễ dùng sai hơn.
</details>

<details>
<summary>Q3. Vì sao MAC không cho non-repudiation nhưng digital signature thì có?</summary>

MAC dùng **symmetric key** chia sẻ giữa A và B. Cả A và B có cùng khả năng tạo MAC hợp lệ. Khi tranh chấp: A có thể chối "không phải tôi gửi, B tự fake MAC".

Digital signature dùng **asymmetric key**: private key chỉ A có. Signature chỉ A tạo được. Khi tranh chấp: signature valid = A đã ký, A không thể chối.

Hệ quả thực tế:
- MAC: internal authentication (microservice talking to each other, đều thuộc 1 organization).
- Signature: cross-organization (sign contract, sign software update).
</details>

---

**Tiếp theo**: [7.3 OWASP Top 10 chi tiết](./03-owasp-top-10)
