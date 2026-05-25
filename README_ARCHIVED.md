# Software Security Foundation

> Tài liệu mở (Tiếng Việt) về nền tảng An toàn Phần mềm: Formal Methods, BMC, SMT, Concurrency, Dynamic Analysis, Fuzzing và phân tích code C/C++.

[![Docusaurus](https://img.shields.io/badge/Built%20with-Docusaurus%203.10-3578E5?logo=docusaurus)](https://docusaurus.io)
[![Deploy](https://img.shields.io/badge/Deploy-GitHub%20Pages-222?logo=github)](https://tuandung222.github.io/software-security-foundation/)
[![Content License](https://img.shields.io/badge/Content-CC%20BY%204.0-lightgrey?logo=creativecommons)](https://creativecommons.org/licenses/by/4.0/)
[![Code License](https://img.shields.io/badge/Code-MIT-blue.svg)](#license)

**Live site**: <https://tuandung222.github.io/software-security-foundation/>

---

## Mục lục

- [Giới thiệu](#giới-thiệu)
- [Nội dung khoá học](#nội-dung-khoá-học)
- [Cấu trúc repo](#cấu-trúc-repo)
- [Quick start](#quick-start)
- [Build PDF](#build-pdf)
- [Scripts tiện ích](#scripts-tiện-ích)
- [Deploy](#deploy)
- [Đóng góp](#đóng-góp)
- [License](#license)

---

## Giới thiệu

Repo này là một bộ tài liệu giảng dạy Tiếng Việt về **Software Security** ở mức nền tảng đại học. Mục tiêu: giúp người học hiểu vì sao phần mềm dễ bị tấn công, các kỹ thuật phát hiện lỗi tự động (Bounded Model Checking, SMT, Fuzzing, Dynamic Symbolic Execution), và cách áp dụng vào pipeline phát triển thực tế.

Tài liệu được viết theo phong cách "lecturer": dẫn dắt trực giác trước, hình thức hoá sau, kèm ví dụ C/C++ chạy được và sơ đồ Mermaid minh hoạ. Trình bày bằng Docusaurus 3, hỗ trợ KaTeX cho công thức toán, render Mermaid, và xuất PDF gộp theo phần.

## Nội dung khoá học

Tám phần bài giảng phủ toàn bộ pipeline phát hiện lỗi phần mềm, từ định nghĩa cơ bản tới phân tích code ở mức production.

| Phần | Chủ đề | Trọng tâm |
|---|---|---|
| **1. Giới thiệu** | Software Security, CIA triad, vulnerabilities catalog, web vulns | Build vocabulary, threat model |
| **2. Formal Verification** | Intro formal methods, BMC + SMT basics | Cầu nối lý thuyết → thực hành |
| **3. Static Analysis I** | V&V, state space, SAT/DPLL, SMT theories, encoding numbers + memory | Cốt lõi BMC engine |
| **4. Static Analysis II** | Loop unwinding, bit-blasting, concurrency verification, context-bounded analysis, KISS/LR | Mở rộng cho code thực |
| **5. Dynamic Analysis** | Security testing, coverage, LTL/Büchi monitoring, fuzzing (black/grey/white), DSE | Bổ sung kỹ thuật runtime |
| **6. Case Study** | Web SaaS, Fintech, IoT, Enterprise cloud | Tư vấn dự án thực |
| **7. Topics Bổ sung** | Cryptography basics, OWASP Top 10, CBMC tutorial, Secure SDLC | Mở rộng kiến thức |
| **8. Code Analysis** | 39 patterns C/C++ + CWE mapping + tool perspective | Skill quan trọng nhất khi đi làm |

Tài nguyên tra cứu:

- **Glossary**: thuật ngữ tiếng Việt - Anh.
- **Cross-reference**: bản đồ phụ thuộc giữa các bài + lộ trình đọc theo focus area.
- **Data Science perspective**: liên hệ Software Security với ML/Data Science.
- **Course Summary**: tóm tắt toàn khoá theo phong cách lecturer.
- **Exercises**: 2 set bài tập có lời giải chi tiết.

## Cấu trúc repo

```
.
├── docs/                       # Markdown nguồn (theo phần)
│   ├── intro.md
│   ├── 01-introduction/        # Phần 1 + 2
│   ├── 02-static-analysis-i/   # Phần 3
│   ├── 03-static-analysis-ii/  # Phần 4
│   ├── 04-dynamic-analysis/    # Phần 5
│   ├── 05-case-study/          # Phần 6
│   ├── 06-additional-topics/   # Phần 7
│   ├── 07-code-analysis/       # Phần 8
│   ├── exercises/              # Bài tập có lời giải
│   └── resources/              # Glossary, cross-ref, PDF index
│
├── src/                        # Component + page + CSS
├── static/                     # Asset tĩnh (img, PDF served)
│   └── pdfs/lectures/          # 8 PDF gộp, deploy cùng site
│
├── pdfs/                       # PDF hiển thị trực tiếp trên GitHub
│   ├── *-full.pdf              # 8 PDF gộp (mirror static/)
│   └── archive/                # Tham chiếu nội bộ, không serve public
│
├── scripts/                    # Tooling Python
│   ├── build_lecture_pdfs.py   # Markdown → PDF (pandoc + xelatex)
│   ├── _review_pdfs.py         # Scan PDF: tofu, raw markdown, layout issue
│   ├── _verify_pdf_render.py   # Verify currency render + diacritics
│   ├── _scan_dollar.py         # Source: unescaped $ trong prose
│   ├── verify_content.py       # All-in-one (anonymity, link, syntax)
│   └── _assets/pdf-header.tex  # Fancyhdr + running header cho PDF
│
├── docusaurus.config.ts        # Site config
├── sidebars.ts                 # Cấu trúc sidebar
└── .github/workflows/deploy.yml # GitHub Pages CI
```

## Quick start

Yêu cầu: **Node.js ≥ 20** (LTS hiện tại).

```bash
git clone https://github.com/tuandung222/software-security-foundation
cd software-security-foundation
npm install
npm start
```

Mở <http://localhost:3000/software-security-foundation/> để xem dev site (hot reload).

```bash
# Build production tĩnh
npm run build

# Serve thử local trước khi deploy
npm run serve
```

## Build PDF

Yêu cầu: `pandoc` + `xelatex` (MacTeX trên macOS, TeX Live trên Linux), `python3`, và `mmdc` (Mermaid CLI) để render sơ đồ.

```bash
# Render 8 PDF gộp + course summary
python3 scripts/build_lecture_pdfs.py

# PDF xuất ra static/pdfs/lectures/
# Copy sang pdfs/ để hiển thị trực tiếp trên GitHub
cp static/pdfs/lectures/*.pdf pdfs/
```

Mỗi PDF có:

- Mục lục (TOC) tự động, depth 3.
- Running header (tên section hiện tại) ở top mỗi trang.
- Footer "Trang X / Y" ở center.
- Mermaid render thành PNG nhúng, scale 94-98% bề rộng trang.
- Font Monaco (full Vietnamese diacritics), Helvetica body.

## Scripts tiện ích

Toàn bộ ở `scripts/`:

```bash
# Scan markdown source: $ chưa escape (gây lỗi KaTeX)
python3 scripts/_scan_dollar.py

# Scan PDF đầu ra: tofu, raw markup lộ, image overflow
python3 scripts/_review_pdfs.py

# Verify PDF: currency render đúng, không tofu chars
python3 scripts/_verify_pdf_render.py

# All-in-one source check (anonymity, link, mermaid, C/Py syntax)
python3 scripts/verify_content.py
```

## Deploy

Tự động deploy lên GitHub Pages qua `.github/workflows/deploy.yml` khi push lên `main`. Site live tại <https://tuandung222.github.io/software-security-foundation/>.

Manual deploy (nếu cần):

```bash
GIT_USER=tuandung222 npm run deploy
```

## Đóng góp

PR và issue đều welcome. Trước khi gửi PR, vui lòng:

1. Chạy `python3 scripts/verify_content.py` (link, anonymity, mermaid syntax).
2. Chạy `python3 scripts/_scan_dollar.py` (escape `$` currency).
3. Nếu sửa lecture → rebuild PDF: `python3 scripts/build_lecture_pdfs.py`.
4. Giữ phong cách lecturer: dẫn dắt trực giác trước, hình thức hoá sau, ví dụ thực.
5. Tránh em-dash `—`; dùng dấu phẩy, ngoặc, hoặc dấu hai chấm.

## License

| Loại | License |
|---|---|
| Văn bản tài liệu (`docs/`) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Code snippet minh hoạ + scripts tooling | [MIT](https://opensource.org/licenses/MIT) |

Bạn tự do dùng, sửa, chia sẻ với điều kiện ghi nguồn.
