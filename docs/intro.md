---
id: intro
title: Giới thiệu
sidebar_position: 1
slug: /intro
description: Tổng quan về bộ tài liệu Software Security Foundation và cách sử dụng.
---

# Software Security Foundation

Chào mừng bạn đến với bộ tài liệu **Software Security Foundation**. Mục tiêu của trang web này là cung cấp một bức tranh **đầy đủ, mạch lạc và có chiều sâu** về An toàn Phần mềm cho những người đã có nền tảng lập trình hệ thống cơ bản (biết C/C++, hiểu cách hoạt động của stack, heap và biết viết một chương trình đa luồng đơn giản).

Bạn không cần kiến thức trước về logic toán hay verification. Tài liệu sẽ dẫn bạn đi từ những câu hỏi rất tự nhiên (ví dụ: *"vì sao một bug nhỏ như Heartbleed lại làm rò rỉ private key?"*) tới những công cụ chính quy như SMT solver hay bounded model checker. Mỗi khái niệm đều được dựng lên từ trực giác trước, rồi mới hình thức hoá sau, theo đúng cách một người mới học nên tiếp cận.

## Tại sao chủ đề này quan trọng?

Nếu bạn đã từng viết code, có lẽ bạn đã quen với việc dùng `strcpy`, để con trỏ "tự lo", và tin rằng "compiler sẽ bắt lỗi". Thực tế, hầu hết các sự cố an ninh mạng lớn trong 30 năm qua không xuất phát từ giải thuật mã hoá yếu, mà từ những **bug rất nhỏ trong mã nguồn**: thiếu một check bounds, ép kiểu sai, hai thread chen vào nhau. Một dòng `memcpy` trong OpenSSL đã để lộ private key của một phần lớn Internet (Heartbleed, 2014). Một biến không khởi tạo trong Apple iMessage đã cho phép remote code execution (FORCEDENTRY, 2021). Một regex viết hơi sai làm Cloudflare sập 27 phút và kéo theo nửa Internet (2019).

Vấn đề chung của các vụ trên không phải là kỹ năng coder kém, mà là **không gian lỗi quá lớn để mắt người có thể duyệt hết**. Đây chính là lý do Software Security tồn tại như một ngành học: cung cấp các **công cụ tự động** và **phương pháp có hệ thống** để tìm hoặc loại trừ các lớp lỗi nhất định trước khi code chạy ngoài thực tế.

## Bạn sẽ học được gì?

Tài liệu chia thành bốn phần bài giảng nối tiếp nhau. Mỗi phần trả lời một câu hỏi lớn:

**Phần 1 (Lecture 1-2): Software Security là gì và lỗ hổng đến từ đâu?** Bạn sẽ hiểu khái niệm CIA Triad, phân biệt nó với Cryptography, đi qua các lớp lỗ hổng kinh điển (buffer overflow, integer overflow, race condition, SQL injection, XSS, XXE), và lần đầu gặp ý tưởng dùng logic toán để **chứng minh** một chương trình không có một lớp lỗi nào đó.

**Phần 2 (Lecture 3): Làm thế nào kiểm tra một chương trình tuần tự bằng máy?** Đây là phần đi sâu vào *Bounded Model Checking* và *SMT solver*. Bạn sẽ thấy cách một chương trình C được dịch thành công thức logic, và làm thế nào một solver như Z3 quyết định công thức đó có thể thoả hay không. Phần encoding số nguyên, số dấu phẩy động và con trỏ sẽ giải thích vì sao tool như CBMC, ESBMC bắt được những bug mà mắt người gần như không thể thấy.

**Phần 3 (Lecture 4): Làm thế nào kiểm tra một chương trình đa luồng?** Khi nhiều thread chạy song song, không gian state nổ tung. Bạn sẽ học các kỹ thuật giảm không gian này (*context-bounded analysis*, *lazy exploration*, *schedule recording*) và cách dịch chương trình đa luồng về chương trình tuần tự để dùng lại tools của Phần 2 (*sequentialization*).

**Phần 4 (Lecture 5): Khi không chứng minh được, làm thế nào tìm bug bằng cách chạy?** Đây là phần *dynamic analysis*: coverage criteria, runtime monitoring với LTL/Büchi automata, và đặc biệt là *fuzzing* (mutation-based với AFL, grammar-based, whitebox với dynamic symbolic execution). Cuối cùng bạn sẽ thấy hai họ kỹ thuật ở Phần 2 và Phần 4 **gặp nhau** khi BMC được dùng để **sinh test case** thay vì để chứng minh.

## Triết lý xuyên suốt

Một câu nói rất hay của Edsger Dijkstra từ 1972:

> *"Program testing can be used to show the presence of bugs, but never to show their absence."*

Câu này tóm gọn lý do tại sao chúng ta cần verification chứ không chỉ testing. Testing tìm thấy bug thì khẳng định "có bug ở đây", nhưng không tìm thấy bug **không** có nghĩa là "không có bug". Một hàm cộng hai số nguyên 32-bit có $2^{64}$ cặp đầu vào, test hết một cặp mỗi nano giây cũng mất gần 600 năm. Vì thế, tài liệu này dành nhiều tâm sức cho hai câu hỏi cốt lõi:

1. **Làm thế nào để CHỨNG MINH một chương trình không có một lớp lỗi nào đó?** (Lecture 3-4)
2. **Khi chưa chứng minh được, làm thế nào để TÌM PHẢN VÍ DỤ một cách có hệ thống?** (Lecture 5)

Hai họ kỹ thuật trả lời hai câu hỏi này không tách rời nhau. Một bounded model checker khi gặp counterexample thực ra đã trả lời cả hai cùng lúc: nó vừa chứng minh "an toàn trong bound $k$", vừa cho counterexample khi bug nằm trong bound đó. Bạn sẽ thấy sự thống nhất này dần dần khi đi qua từng phần.

## Cách đọc tài liệu

Sidebar bên trái sắp xếp các bài theo thứ tự logic. Bạn nên đọc tuần tự vì mỗi phần xây dựng trên phần trước. Nếu cần tra cứu nhanh một thuật ngữ, hãy dùng thanh tìm kiếm phía trên hoặc trang [Glossary](./resources/glossary).

Mỗi bài đều có cùng cấu trúc để bạn dễ định hướng:

- **Tóm tắt một dòng** ở đầu trang giúp bạn biết bài này nói về cái gì trong 10 giây.
- **Phần dẫn dắt** từ một câu hỏi hoặc ví dụ thực tế, sau đó mới đi tới định nghĩa hình thức.
- **Ví dụ minh hoạ** có giải thích chi tiết từng dòng code. Hầu hết ví dụ viết bằng C vì C để lộ rõ nhất các cơ chế memory và là input chính của BMC tool.
- **Phần thảo luận sâu** giải thích vì sao cách giải an toàn là cách an toàn, và những cách "có vẻ an toàn" sai ở đâu.
- **Mini-quiz** ở cuối mỗi bài để bạn tự kiểm tra hiểu biết. Đáp án nằm trong thẻ `<details>` để bạn tự suy nghĩ trước khi xem.

Khi gặp thuật ngữ tiếng Anh in nghiêng trong ngoặc, ví dụ *bounded model checking*, đó là từ khoá bạn dùng để tra cứu paper, sách giáo trình hoặc tài liệu tiếng Anh khác.

## Tài nguyên kèm theo

Trang [Tài nguyên](./resources/pdfs) lưu các file PDF tham chiếu để bạn xem hình ảnh slide, sơ đồ trực quan. Trang [Bài tập](./exercises/) cung cấp một bộ bài tập thực hành kèm lời giải chi tiết, giúp bạn áp dụng những gì đã học vào phân tích code thực tế.

## Bản quyền

Toàn bộ nội dung văn bản phát hành theo giấy phép [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Các đoạn code minh hoạ phát hành theo giấy phép MIT. Bạn được tự do sao chép, sửa đổi và sử dụng cho mục đích học tập, giảng dạy hay thương mại miễn là ghi nguồn.

Chúc bạn đọc tài liệu vui và thấy An toàn Phần mềm thú vị như tác giả thấy nó.
