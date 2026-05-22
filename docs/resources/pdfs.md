---
id: pdfs
title: PDF tham chiếu
sidebar_position: 1
description: Các file PDF kèm theo tài liệu để tra cứu hình ảnh và sơ đồ.
---

# PDF tham chiếu và tải về

Trang này cung cấp các file PDF của tài liệu để bạn tải về đọc offline hoặc in ra.

## PDF gộp theo cụm (bản chính)

Các file PDF dưới đây gộp toàn bộ nội dung của mỗi cụm bài giảng, có mục lục, sinh tự động từ markdown source. Phù hợp để in và đọc offline.

| Cụm | Nội dung | File | Kích thước |
|---|---|---|---|
| Lecture 1-2 | Giới thiệu Software Security, vulnerabilities, formal verification | [lecture-1-2-full.pdf](pathname:///pdfs/lectures/lecture-1-2-full.pdf) | ~245 KB |
| Lecture 3 | Static Analysis I (BMC + SMT chi tiết) | [lecture-3-full.pdf](pathname:///pdfs/lectures/lecture-3-full.pdf) | ~214 KB |
| Lecture 4 | Static Analysis II (Concurrency) | [lecture-4-full.pdf](pathname:///pdfs/lectures/lecture-4-full.pdf) | ~190 KB |
| Lecture 5 | Dynamic Analysis (Testing, Monitoring, Fuzzing) | [lecture-5-full.pdf](pathname:///pdfs/lectures/lecture-5-full.pdf) | ~199 KB |
| Lecture 6 | Case Study (Tư vấn dự án thực) | [lecture-6-case-study-full.pdf](pathname:///pdfs/lectures/lecture-6-case-study-full.pdf) | ~127 KB |
| Lecture 7 | Topics Bổ sung (Crypto, OWASP, CBMC, SDLC) | [lecture-7-additional-topics-full.pdf](pathname:///pdfs/lectures/lecture-7-additional-topics-full.pdf) | ~216 KB |

## Tham chiếu gốc

Các file PDF gốc đính kèm để xem hình ảnh slide, sơ đồ trực quan.

| Cụm | File | Kích thước |
|---|---|---|
| Lecture 1-2 (slide) | [lecture-1-2.pdf](pathname:///pdfs/lecture-1-2.pdf) | 8.9 MB |
| Lecture 3 (slide) | [lecture-3.pdf](pathname:///pdfs/lecture-3.pdf) | 9.1 MB |
| Lecture 4 (slide) | [lecture-4.pdf](pathname:///pdfs/lecture-4.pdf) | 4.7 MB |
| Lecture 5 (slide) | [lecture-5.pdf](pathname:///pdfs/lecture-5.pdf) | 3.7 MB |
| Bài tập (slide) | [exercises-set-2.pdf](pathname:///pdfs/exercises-set-2.pdf) | 152 KB |

## Cách build PDF từ source

Nếu bạn fork repo và muốn rebuild PDF từ markdown source:

```bash
# Yêu cầu: pandoc + xelatex (LaTeX), Python 3
python3 scripts/build_lecture_pdfs.py
```

Output ở `static/pdfs/lectures/`.
