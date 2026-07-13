# Cách chạy project `group4`

Tài liệu này là hướng dẫn chạy từ đầu đến cuối trên Windows PowerShell. Cách dưới đây ưu tiên lệnh nào cũng chạy được, kể cả khi `group4-lab4` chưa được tạo ra trong PATH.

## 1. Mở terminal đúng thư mục

Vào thư mục project:

```powershell
cd "D:\Đại Học\Học kì 6\Bigdata\lab4\group4"
```

## 2. Tạo môi trường ảo

Nếu chưa có `.venv` thì tạo mới:

```powershell
python -m venv .venv
```

Kích hoạt môi trường:

```powershell
.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn script, chạy:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

Sau đó kích hoạt lại:

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Nâng cấp bộ cài

Lệnh này rất quan trọng để `pyproject.toml` và editable install hoạt động ổn định:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

## 4. Cài project vào venv

Chạy:

```powershell
python -m pip install -e .[all]
```

Nếu bạn chỉ muốn cài phần tối thiểu để chạy parser và test cơ bản:

```powershell
python -m pip install -e .[dev]
```

Sau bước này, nếu mọi thứ ổn, lệnh `group4-lab4` sẽ xuất hiện.

## 5. Kiểm tra cài đặt

Chạy test:

```powershell
pytest -q
```

Nếu test pass thì môi trường cơ bản đã ổn.

## 6. Clone repo PEFT để phân tích

Đây là repo đầu vào của bài lab. Nếu chưa có, clone về một thư mục cố định:

```powershell
git clone --depth 1 https://github.com/huggingface/peft.git D:\repos\peft
```

## 7. Chạy discovery

### Cách 1: dùng lệnh ngắn

Nếu `group4-lab4` đã xuất hiện:

```powershell
group4-lab4 discover --repo "D:\repos\peft"
```

### Cách 2: chắc chắn chạy được dù chưa có console script

Nếu PowerShell báo không nhận `group4-lab4`, dùng trực tiếp Python module:

```powershell
$env:PYTHONPATH="src"
python -m group4_lab.cli discover --repo "D:\repos\peft"
```

Lệnh này sẽ trả về:

- `total_files`
- thống kê theo thư mục
- vài file mẫu

## 8. Parse một file mẫu

Chạy:

```powershell
python -m group4_lab.cli parse-file --file samples\example_module.py
```

Nếu muốn ghi kết quả ra file:

```powershell
python -m group4_lab.cli parse-file --file samples\example_module.py --output output\sample-events.jsonl
```

## 9. Parse toàn bộ repo PEFT

Chạy:

```powershell
python -m group4_lab.cli parse-repo --repo "D:\repos\peft" --output output\peft-events.jsonl
```

Nếu muốn in trực tiếp ra console thì bỏ `--output`:

```powershell
python -m group4_lab.cli parse-repo --repo "D:\repos\peft"
```

## 10. Chạy replay để kiểm tra idempotent

So sánh cùng một file trước và sau:

```powershell
python -m group4_lab.cli replay-file --before-file samples\example_module.py --after-file samples\example_module.py
```

Nếu bạn có file cũ và file mới đã sửa:

```powershell
python -m group4_lab.cli replay-file --before-file "D:\path\before.py" --after-file "D:\path\after.py"
```

Kết quả sẽ có:

- `before_events`
- `after_events`
- `added_events`
- `removed_events`
- `stable_event_ids`

## 11. Sinh config cho Kafka, Neo4j, MongoDB, Spark

```powershell
python -m group4_lab.cli emit-configs --output configs\generated
```

Lệnh này tạo các file cấu hình cần thiết trong `configs\generated`.

## 12. Chạy Spark job metadata

Nếu bạn đã có Kafka và MongoDB chạy rồi, có thể chạy job:

```powershell
python jobs\mongo_streaming_job.py
```

Job này đọc topic `peft.source.metadata` và ghi metadata sang MongoDB.

## 13. Tạo lại Jupyter Book

```powershell
python -m group4_lab.cli build-book --output docs\book
```

Sau đó nội dung report nằm trong `docs/book`.

## 14. Các lệnh tắt trong Makefile

Nếu máy có `make`, bạn có thể chạy:

```powershell
make test
make discover
make parse-sample
make replay-sample
make emit-configs
make book-skeleton
```

## 15. Trình tự chạy để lấy kết quả cho bài

1. Tạo venv và cài project.
2. Chạy `pytest -q`.
3. Clone `huggingface/peft` về `D:\repos\peft`.
4. Chạy `discover`.
5. Chạy `parse-repo`.
6. Chạy `emit-configs`.
7. Khởi động Kafka, Neo4j, MongoDB nếu cần demo pipeline.
8. Chạy `replay-file`.
9. Chạy `build-book`.
10. Chụp output, screenshot và đưa vào báo cáo.

## 16. Nếu bị lỗi

### Không nhận `group4-lab4`

Chạy:

```powershell
$env:PYTHONPATH="src"
python -m group4_lab.cli discover --repo "D:\repos\peft"
```

### Không import được `group4_lab`

Thường là do chưa cài project vào venv. Hãy chạy lại:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[all]
```

### PowerShell chặn script activate

Chạy:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

Rồi kích hoạt lại `.venv`.

