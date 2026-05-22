# PDF Files

Thư mục này chứa toàn bộ file PDF của tài liệu để bạn dễ download/copy. GitHub render được link trực tiếp tới file PDF.

## PDF gộp theo cụm (bản chính, đọc text)

Sinh tự động từ markdown source qua `pandoc + xelatex`. Có mục lục, font Helvetica, formatted A4, dễ in.

| File | Cụm | Kích thước |
|---|---|---|
| [`lecture-1-2-full.pdf`](./lecture-1-2-full.pdf) | Lecture 1-2: Giới thiệu Software Security | ~245 KB |
| [`lecture-3-full.pdf`](./lecture-3-full.pdf) | Lecture 3: Static Analysis I (BMC + SMT) | ~214 KB |
| [`lecture-4-full.pdf`](./lecture-4-full.pdf) | Lecture 4: Static Analysis II (Concurrency) | ~190 KB |
| [`lecture-5-full.pdf`](./lecture-5-full.pdf) | Lecture 5: Dynamic Analysis (Fuzzing) | ~199 KB |
| [`lecture-6-case-study-full.pdf`](./lecture-6-case-study-full.pdf) | Lecture 6: Case Study (Tư vấn dự án) | ~127 KB |
| [`lecture-7-additional-topics-full.pdf`](./lecture-7-additional-topics-full.pdf) | Lecture 7: Topics Bổ sung (Crypto, OWASP, CBMC, SDLC) | ~216 KB |

## PDF slide gốc (tham chiếu hình ảnh)

Slide gốc có hình ảnh, sơ đồ trực quan.

| File | Cụm | Kích thước |
|---|---|---|
| [`lecture-1-2.pdf`](./lecture-1-2.pdf) | Lecture 1-2 (slide) | 8.9 MB |
| [`lecture-3.pdf`](./lecture-3.pdf) | Lecture 3 (slide) | 9.1 MB |
| [`lecture-4.pdf`](./lecture-4.pdf) | Lecture 4 (slide) | 4.7 MB |
| [`lecture-5.pdf`](./lecture-5.pdf) | Lecture 5 (slide) | 3.7 MB |
| [`exercises-set-2.pdf`](./exercises-set-2.pdf) | Bài tập | 152 KB |

## Download tất cả

Bạn có thể `git clone` hoặc download zip từ trang chính:

```bash
git clone https://github.com/tuandung222/Temp1
cp Temp1/pdfs/*.pdf ~/Documents/SoftwareSecurity/
```

Hoặc download zip qua web: vào https://github.com/tuandung222/Temp1, click "Code" → "Download ZIP".

## Cách rebuild PDF từ source

Yêu cầu: `pandoc` + `xelatex` (TeX Live trên Linux, MacTeX trên macOS), Python 3.

```bash
python3 scripts/build_lecture_pdfs.py
```

Output ở `static/pdfs/lectures/`. Copy sang `pdfs/` để cập nhật thư mục này:

```bash
cp static/pdfs/lectures/*.pdf pdfs/
```
