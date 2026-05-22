# Software Security Foundation

Tài liệu nền tảng về An toàn Phần mềm: Formal Methods, BMC, SMT và Fuzzing.

**Live site**: <https://tuandung222.github.io/Temp1/>

## Nội dung

Bộ tài liệu chia thành bốn cụm bài giảng:

| Cụm | Chủ đề | Trạng thái |
|---|---|---|
| 1 | Software Security là gì, vulnerabilities, intro formal verification | Hoàn thành |
| 2 | Static Analysis I (BMC + SMT chi tiết) | Đang biên soạn |
| 3 | Static Analysis II (Concurrency) | Đang biên soạn |
| 4 | Dynamic Analysis (Testing, Monitoring, Fuzzing) | Đang biên soạn |

## Phát triển local

Yêu cầu Node.js 20 trở lên.

```bash
npm install
npm start
```

Mở <http://localhost:3000/Temp1/> để xem.

## Build

```bash
npm run build
```

Output ở `./build`, có thể serve bằng bất kỳ static hosting nào.

## Deploy

Tự động qua GitHub Actions khi push lên `main`. Cấu hình ở `.github/workflows/deploy.yml`.

## License

- Nội dung văn bản: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Code snippet minh hoạ: MIT.
