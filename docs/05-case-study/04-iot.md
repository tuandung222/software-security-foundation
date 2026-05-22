---
id: 04-iot
title: 6.4 Case Study - IoT/Embedded
sidebar_position: 4
description: "Tư vấn security cho thiết bị IoT/embedded: memory safety, secure boot, OTA update, side-channel, physical access. Khác biệt với web vì resource constrained và physical."
---

# 6.4 Case Study: IoT / Embedded

## Bối cảnh

**Công ty C** sản xuất camera an ninh thông minh cho gia đình. Camera có WiFi, microphone, motion sensor, kết nối cloud để stream video, nhận command từ mobile app.

Thông số:
- Hardware: ARM Cortex-M4, 256KB RAM, 1MB flash, không có OS (bare metal C).
- 500K camera đã bán, đang phát triển model mới.
- Trước đó có **CVE** bị disclose: hardcoded admin password, attacker zombie camera vào botnet.
- Đang gặp PR crisis, customer hỏi "có an toàn không".

**Đến gặp bạn** để tư vấn: "Chúng tôi cần làm gì để model mới an toàn từ đầu, và làm sao patch model cũ?"

## Bước 1: Hiểu Context

IoT khác web/mobile ở nhiều điểm quan trọng:

- **Resource constrained**: ít RAM, CPU yếu. Không thể chạy heavy security check.
- **Physical access**: attacker có thể mua thiết bị, mổ xẻ, đọc flash. Không "trust the hardware".
- **Long lifecycle**: thiết bị dùng 5-10 năm. Cần patch lâu dài.
- **Hard to update**: khác web (push một deploy), IoT cần OTA mechanism reliable.
- **Network heterogeneous**: WiFi, BLE, LoRa, Zigbee. Mỗi protocol có security riêng.

Recommend: **security from design**, không retrofit. Model cũ phải có **kill switch** (force update) nếu critical vuln.

## Bước 2: Threat Model cho IoT camera

| Attacker | Goal | Vector |
|---|---|---|
| Script kiddie | Botnet (Mirai-like) | Default password, exposed Telnet |
| Privacy invader | Spy on family | Steal video stream, eavesdrop |
| Burglar | Disable camera trước khi đột nhập | Jam WiFi, DoS camera |
| Nation-state | Surveillance | Implant backdoor in supply chain |

STRIDE applied:

| Threat | Risk |
|---|---|
| Spoofing camera (giả device ID, push fake video) | High |
| Tampering firmware | Critical |
| Repudiation (attack mà không log) | Medium |
| Info Disclosure (stream leak) | Critical |
| DoS (làm camera unresponsive) | High |
| Elevation (root via debug port) | Critical |

## Bước 3: Recommendation theo lớp

### 3.1 Memory Safety

ARM Cortex-M4 bare metal C: không có ASLR, không có DEP. Buffer overflow → arbitrary code execution dễ.

**Khuyến nghị**:

**Switch ngôn ngữ nếu có thể**: Rust biên dịch sang Cortex-M, memory safe by language. ESP32 đã có Rust toolchain.

**Nếu phải dùng C**:
- Bật mọi compiler warning, treat as error.
- Dùng MISRA-C subset (safety-critical C standard).
- Static analyzer: PVS-Studio, Coverity, ESBMC.
- Stack canary nếu CPU support (nhiều MCU không có).
- Tránh `strcpy`, `sprintf`, `gets`. Dùng safe alternative.

**Library**: dùng tested library (Embedded TLS, mbedTLS) thay vì self-roll crypto.

### 3.2 Secure Boot

**Vấn đề**: attacker có physical access, có thể flash firmware giả. Boot từ firmware compromised, mọi security check trong firmware bypass.

**Secure boot solution**:

```
Boot ROM (hardware, immutable)
    ↓ verify signature of
Stage 1 bootloader
    ↓ verify signature of
Stage 2 bootloader (optional)
    ↓ verify signature of
Application firmware
    ↓ run
```

Mỗi stage verify next stage bằng signature (RSA hoặc ECDSA). Root of trust nằm trong Boot ROM (mạch điện, không thể flash lại).

**Tool**: ARM TrustZone, ESP32 Secure Boot, nRF52 với MCUboot.

**Trade-off**: cost design (cần CPU support), key management (private key signing không được leak), latency tăng (verify thêm boot time).

### 3.3 OTA Update

Critical vì IoT field deployed, không thể recall hàng triệu device.

**OTA requirement**:

1. **Signed firmware**: download xong verify signature trước khi apply.
2. **Atomic update**: nếu mất điện giữa chừng, vẫn boot được (A/B partition).
3. **Rollback**: nếu firmware mới crash 3 lần, auto rollback.
4. **Mandatory update**: critical CVE → force update, không cho user reject.
5. **Bandwidth-aware**: download tăng dần theo time, không peak.

Architecture điển hình:

```
Cloud: firmware repo + signing service
   ↓ HTTPS
Device: download firmware → verify signature → write to inactive partition
   ↓ reboot
Device: boot inactive partition → run → if healthy, commit; else, rollback
```

**Tool**: AWS IoT Device Management, Mender, MCUboot.

### 3.4 Authentication và Authorization

**Pitfall điển hình IoT**: hardcoded admin password (CVE đã bị attack).

**Solution**:

- **Unique device credential per unit**: mỗi camera có private key riêng, gen tại factory.
- **TLS mutual auth**: device và cloud authenticate lẫn nhau bằng certificate.
- **No default password**: lần đầu setup, user phải set password.
- **Account lockout**: 5 failed auth, lock 30 phút.

**Token rotation**: mobile app authenticate với cloud, lấy token để control camera. Token rotate hàng giờ, revoke khi user logout.

### 3.5 Network Security

**Disable unused protocol**: không có lý do để camera mở Telnet, FTP, UPnP. Disable hết.

**WiFi credential storage**: encrypt với device-unique key, không plain text trong flash.

**Encrypted communication**:
- Camera → Cloud: TLS 1.3.
- Camera → Mobile app (local network): DTLS hoặc end-to-end encryption.

**Network segmentation guide**: hướng dẫn user đặt IoT trên VLAN riêng, không cùng VLAN với laptop work.

### 3.6 Side-Channel Resistance

Side-channel attack: attacker đo physical signal (timing, power, EM) để extract secret.

**Ví dụ**: attacker đo time AES decryption. Time phụ thuộc key byte. Sau hàng nghìn measurement, extract key.

**Mitigation**:
- Dùng AES implementation **constant-time** (intel AES-NI, ARM crypto extension).
- Dùng masking: thêm random vào computation để hide signal.
- Physical: enclosure hard to open, tamper-evident.

Cho consumer IoT, side-channel thường low priority (chi phí attack cao, không scale). Nhưng cho thiết bị banking, military, side-channel quan trọng.

### 3.7 Privacy

Camera xử lý video, audio: rất nhạy cảm.

**Best practice**:

- **Local processing**: motion detection, face recognition chạy on-device, không send everything cloud.
- **End-to-end encryption**: video encrypt từ camera, chỉ user mobile app decrypt. Cloud không xem được.
- **Data minimization**: chỉ lưu metadata cần thiết, không lưu video không user explicit.
- **Transparent privacy policy**: rõ ràng "chúng tôi không truy cập video của bạn".
- **GDPR / privacy law compliance**: user có quyền delete data, export data.

## Bước 4: Patch model cũ

Đối với 500K camera đã bán có CVE:

### Step 1: Disclosure
- Public security advisory chi tiết CVE, scope ảnh hưởng.
- Coordinate với CERT (CISA, VNCERT) nếu critical.

### Step 2: Patch development
- Fix code, sign firmware.
- Test extensive ở dev lab + bê ta.

### Step 3: OTA push
- Push update tới mọi device.
- Force update sau 30 ngày nếu user không apply.
- Monitor success rate.

### Step 4: Devices không update được
- Một số device không lên mạng > 30 ngày: không nhận được patch.
- Có thể disable một số tính năng remote control nếu firmware quá cũ.
- Worst case: recall thiết bị (đắt nhưng cần thiết cho critical vuln).

### Step 5: Process improvement
- Why hardcoded password slipped? → audit code review process.
- Implement Static Analyzer cho mọi commit.
- Mandatory security training cho developer.

## Bước 5: Common Pitfalls

### Pitfall 1: Hardcoded credential

Vẫn xảy ra! Developer hard-code cho debug, quên remove. Test với grep + signature scanner trong CI.

### Pitfall 2: Backdoor "support"

Backdoor cho support team troubleshoot. Backdoor leak → attacker dùng.

Solution: không có backdoor. Support cần access → user explicit consent + temporary credential.

### Pitfall 3: Đặt private key trong flash

Private key cho signing là tài sản quý. Nếu attacker đọc flash, lấy được key, có thể sign firmware giả.

Solution: private key trong **secure element** (Microchip ATECC608A, NXP A71CH). Hardware-protected, key never exits.

### Pitfall 4: Update mechanism không tested

OTA update viết, không test edge case (mất điện, network drop giữa chừng). Khi push thật, brick hàng nghìn device.

Solution: chaos engineering. Simulate fail mid-update. A/B partition + rollback.

### Pitfall 5: Telemetry leak privacy

Telemetry để debug: location, device ID, behavior. Leak qua cloud breach.

Solution: anonymize, aggregate. Document rõ telemetry collect cái gì.

## Tóm tắt

- IoT có constraint riêng: resource, physical, lifecycle.
- **Memory safety**: ưu tiên Rust hoặc C với heavy linting.
- **Secure Boot**: chain of trust từ Boot ROM.
- **OTA**: signed, atomic, rollback, mandatory critical.
- **Unique credential per device**: không hardcoded.
- **Network**: disable unused protocol, segment VLAN.
- **Privacy**: local processing, E2E encryption, data minimization.

## Bài học chính

IoT security khó nhất ở **physical access** và **lifecycle**. Web app có thể patch trong giờ; IoT mất tuần/tháng và một số device không bao giờ patch được.

Vì thế: **design for security from start**, plan OTA mechanism từ ngày 1, expect attacker có physical access từ ngày 1. Retrofit security cực kỳ đắt và không hiệu quả.

---

**Tiếp theo**: [6.5 Case Study: Doanh nghiệp số hoá](./05-enterprise-cloud)
