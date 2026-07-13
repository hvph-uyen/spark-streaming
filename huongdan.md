# Hướng dẫn làm Lab 04 - Streaming

Tài liệu này hướng dẫn cách thực hiện bài Lab 04 theo đúng yêu cầu đề, đồng thời cụ thể hóa trên chủ đề nhóm đã chọn là [`huggingface/peft`](https://github.com/huggingface/peft).

## 1. Mục tiêu chung của bài

Lab yêu cầu nhóm xây dựng một pipeline xử lý mã nguồn Python theo luồng gần thời gian thực, gồm các phần chính:

1. Chọn một repository Python công khai được chỉ định trên Moodle.
2. Quét các file `.py` trong repository và ghi nhận số lượng file.
3. Viết Parser Service xử lý từng file một, trích xuất CPG gồm:
   - AST nodes
   - CFG edges
   - DFG edges
   - Call edges
4. Đẩy các sự kiện này vào Kafka theo từng topic riêng.
5. Đưa graph topology vào Neo4j qua Neo4j Kafka Connector Sink.
6. Đưa metadata mã nguồn vào MongoDB bằng Spark Structured Streaming.
7. Chứng minh cơ chế replay idempotent bằng cách sửa một file Python rồi xử lý lại.
8. Ghi toàn bộ kết quả vào Jupyter Book và publish lên GitHub Pages.

Với chủ đề `huggingface/peft`, nhóm có lợi thế vì đây là một thư viện Python lớn, có cấu trúc rõ ràng:

- `src/peft/`: phần lõi của thư viện.
- `src/peft/tuners/`: nhiều biến thể PEFT như LoRA, AdaLoRA, IA3, VeRA, v.v.
- `src/peft/utils/`: các hàm tiện ích, merge, save/load, quantization.
- `examples/`: các script và notebook minh họa.
- `tests/`: bộ kiểm thử.
- `docs/`: tài liệu dự án.

Phần nên ưu tiên khi làm lab là `src/peft/`, vì đây là nơi có code thật của thư viện và có nhiều cấu trúc Python để parser xử lý.

## 2. Cách làm theo từng task

### Task 1. Clone repository và đếm file Python

Mục tiêu của task này là chứng minh nhóm đã clone đúng repo được chọn và biết rõ phạm vi mã nguồn sẽ phân tích.

#### Cách làm

1. Clone repository bằng git shallow clone để giảm dung lượng:

```bash
git clone --depth 1 https://github.com/huggingface/peft.git
cd peft
```

2. Liệt kê toàn bộ file Python trong cây thư mục:

```bash
rg --files -g "*.py"
```

3. Nếu muốn lọc bớt file kiểm thử, file setup, hoặc file sinh tự động thì có thể dùng:

```bash
rg --files -g "*.py" | rg -v "(^tests/|setup\.py$|^build/|__pycache__|generated)"
```

4. Ghi lại:
   - Tổng số file `.py` tìm được.
   - Số file sau khi lọc nếu nhóm quyết định loại `tests/`, `setup.py`, file generated.
   - Danh sách một vài thư mục chính để chứng minh hiểu cấu trúc repo.

#### Với PEFT, nên mô tả thêm

- `src/peft/` là lõi thư viện.
- `src/peft/tuners/` chứa các module adapter/PEFT khác nhau.
- `examples/` là nơi có nhiều script và notebook để minh họa.
- `tests/` thường không bắt buộc đưa vào phân tích chính, nhưng vẫn có thể đếm nếu nhóm muốn phân tích đầy đủ.

#### Kết quả cần đưa vào Jupyter Book

- Ảnh chụp terminal hoặc notebook hiển thị lệnh clone và số lượng file.
- Bảng thống kê file Python theo thư mục.
- Một đoạn mô tả ngắn vì sao nhóm chọn phạm vi phân tích như vậy.

---

### Task 2. Viết Parser Service incremental cho CPG

Đây là phần quan trọng nhất của bài. Nhóm cần xử lý từng file Python một, không đọc toàn bộ repository một lượt.

#### Gợi ý cách triển khai

Vì repo `peft` là Python thuần, nhóm có thể chọn một trong ba hướng:

- `ast` của Python chuẩn: dễ triển khai, ổn định, phù hợp lab.
- `tree-sitter`: mạnh hơn nếu muốn phân tích chi tiết hơn.
- Joern: nếu nhóm đã quen và có môi trường phù hợp.

Khuyến nghị thực tế cho bài lab là dùng `ast` để:

- parse từng file riêng lẻ,
- trích xuất class/function/import/call/assign,
- sinh event rõ ràng, dễ debug.

#### Cách chia CPG trong bài

Với mỗi file `*.py`, nhóm nên tạo các loại thực thể sau:

- AST nodes:
  - `Module`
  - `ClassDef`
  - `FunctionDef`
  - `AsyncFunctionDef`
  - `Import`
  - `ImportFrom`
  - `Assign`
  - `Call`
  - `Return`
  - `If`, `For`, `While`, `Try`, `With`
- CFG edges:
  - luồng điều khiển giữa các statement chính
- DFG edges:
  - luồng dữ liệu giữa biến được gán và nơi được dùng lại
- Call edges:
  - từ nơi gọi hàm đến định nghĩa hàm hoặc tên hàm được gọi

Với `peft`, nhóm sẽ gặp nhiều pattern thực tế như:

- class cấu hình adapter,
- hàm helper trong `utils`,
- method của các tuner như `layer.py`, `model.py`, `config.py`,
- import chéo giữa các module.

#### Cách làm incremental

Parser Service nên đọc từng file như một job độc lập:

1. Nhận `repo_path` và `file_path`.
2. Mở đúng file đó.
3. Parse AST.
4. Trích xuất node và edge.
5. Gửi từng nhóm sự kiện sang Kafka.
6. Giải phóng bộ nhớ rồi chuyển sang file tiếp theo.

Điểm cần nhớ: không giữ toàn bộ graph của repo trong RAM.

#### Cách đặt ID ổn định

Đây là mấu chốt để replay không sinh duplicate.

Nên tạo ID ổn định cho node/edge theo công thức có tính tái lập, ví dụ:

- Node ID:
  - `sha1(repo_name + file_path + node_type + qualified_name + normalized_source)`
- Edge ID:
  - `sha1(edge_type + source_node_id + target_node_id)`
- Metadata ID:
  - `sha1(repo_name + file_path + commit_sha)`

Không nên chỉ dùng số dòng vì khi file thay đổi, line number sẽ lệch và ID sẽ đổi hàng loạt.

#### Các event nên phát ra

Mỗi event nên là JSON có các trường tối thiểu:

```json
{
  "schema_version": 1,
  "event_time": "2026-07-11T12:00:00Z",
  "repo": "huggingface/peft",
  "commit_sha": "abc123",
  "file_path": "src/peft/utils/save_and_load.py",
  "element_id": "sha1...",
  "element_type": "FunctionDef",
  "payload": {}
}
```

#### Kết quả cần đưa vào Jupyter Book

- Mô tả kiến trúc Parser Service.
- Notebook cell hiển thị:
  - số node trích xuất,
  - số edge trích xuất,
  - vài sample event JSON,
  - một vài file đã xử lý.
- Giải thích vì sao chọn `ast` hoặc `tree-sitter`.

---

### Task 3. Thiết kế Kafka topics

Đề yêu cầu tách topic rõ ràng cho từng loại dữ liệu. Với bài này, nên thiết kế tối thiểu 4 topic:

1. `peft.cpg.nodes`
2. `peft.cpg.edges`
3. `peft.source.metadata`
4. `peft.parser.errors`

#### Ý nghĩa từng topic

- `peft.cpg.nodes`: chứa AST nodes và các node logic khác.
- `peft.cpg.edges`: chứa CFG/DFG/call edges.
- `peft.source.metadata`: chứa metadata cấp file như số dòng, số class, số function, hash nội dung, thời gian xử lý.
- `peft.parser.errors`: chứa lỗi parse hoặc file đặc biệt không xử lý được.

#### Schema cho mỗi message

Mỗi message nên có:

- `schema_version`
- `event_time`
- `repo`
- `commit_sha`
- `file_path`
- `event_type`
- `element_id`
- `payload`

#### Gợi ý key Kafka

Nên dùng key theo:

- `file_path` cho metadata,
- `element_id` cho node,
- `source_node_id` hoặc `edge_id` cho edge.

Làm vậy sẽ giúp giữ thứ tự tương đối tốt cho từng file và dễ debug.

#### Kết quả cần đưa vào Jupyter Book

- Bảng mô tả topic.
- Ảnh chụp Kafka topic list hoặc console producer.
- Mẫu message thực tế của từng topic.

---

### Task 4. Đưa graph topology vào Neo4j

Task này yêu cầu graph topology được ghi vào Neo4j trực tiếp từ Kafka, không qua Spark trung gian.

#### Cách làm khuyến nghị

1. Dùng Neo4j Kafka Connector Sink để đọc topic node và edge.
2. Tạo constraint/index cho ID ổn định.
3. Dùng `MERGE` thay cho `CREATE` để tránh duplicate.

#### Gợi ý mô hình Neo4j

- Node label:
  - `:File`
  - `:Module`
  - `:Class`
  - `:Function`
  - `:Call`
  - `:Statement`
- Edge type:
  - `:CONTAINS`
  - `:CFG_NEXT`
  - `:DFG_NEXT`
  - `:CALLS`

#### Điều quan trọng

- Node/edge phải được định danh bằng ID ổn định.
- Khi replay cùng nội dung, Neo4j chỉ cập nhật bản ghi đã có, không tạo bản sao.

#### Ví dụ logic ghi dữ liệu

```cypher
MERGE (n:Function {id: $element_id})
SET n.name = $name,
    n.file_path = $file_path,
    n.repo = $repo,
    n.updated_at = datetime()
```

#### Kết quả cần đưa vào Jupyter Book

- Ảnh chụp Neo4j Browser.
- Cypher query dùng để kiểm tra số node, số quan hệ.
- Bằng chứng `MERGE` hoạt động đúng khi replay.

---

### Task 5. Đưa metadata vào MongoDB bằng Spark Structured Streaming

Task này xử lý metadata của file, không phải toàn bộ graph topology.

#### Dữ liệu nên lưu vào MongoDB

Mỗi document có thể gồm:

- `repo`
- `file_path`
- `commit_sha`
- `schema_version`
- `num_ast_nodes`
- `num_cfg_edges`
- `num_dfg_edges`
- `num_call_edges`
- `num_classes`
- `num_functions`
- `num_imports`
- `content_hash`
- `processed_at`

#### Cách triển khai Spark

1. Spark Structured Streaming consume từ Kafka topic `peft.source.metadata`.
2. Parse JSON.
3. Ghi vào MongoDB bằng MongoDB Spark Connector.
4. Bật checkpoint để job resume được khi restart.

#### Checkpoint

Nên lưu checkpoint vào một thư mục riêng, ví dụ:

```text
checkpoints/peft_metadata_stream/
```

Checkpoint là yêu cầu bắt buộc để chứng minh pipeline có thể chạy lại mà không xử lý trùng offsets.

#### Kết quả cần đưa vào Jupyter Book

- Ảnh chụp MongoDB Compass hoặc giao diện MongoDB.
- Output query cho thấy document đã được update.
- Mô tả checkpoint location và lý do chọn.

---

### Task 6. Replay idempotent trên một file đã sửa

Đây là phần chứng minh hệ thống hoạt động thực sự như một pipeline streaming có khả năng replay.

#### Cách làm

1. Chọn một file Python nhỏ trong repo `peft`.
2. Sửa một thay đổi có tác động thật đến AST, ví dụ:
   - thêm một helper function nhỏ,
   - thêm một parameter,
   - thêm một import,
   - chỉnh logic trong một function ngắn.
3. Chạy lại Parser Service chỉ cho file đó.
4. Đẩy lại event vào Kafka.
5. Kiểm tra Neo4j và MongoDB.

#### Điều cần chứng minh

- Neo4j không sinh duplicate node/edge cho phần không đổi.
- MongoDB cập nhật đúng document metadata của file sửa đổi.
- Spark checkpoint bỏ qua offsets cũ của file không đổi.

#### Gợi ý chọn file trong PEFT

Nên chọn file:

- nhỏ,
- ít phụ thuộc,
- dễ kiểm tra output,
- không gây hỏng repository khi sửa.

Ví dụ hợp lý là một file trong:

- `src/peft/utils/`
- `src/peft/tuners/<một tuner bất kỳ>/`
- hoặc một script trong `examples/`

#### Kết quả cần đưa vào Jupyter Book

- Trước và sau khi sửa file.
- So sánh node count, edge count, metadata document.
- Giải thích vì sao replay không tạo duplicate.

---

## 3. Cấu trúc Jupyter Book nên làm

Vì đề yêu cầu nộp đúng một URL của Jupyter Book, nên nhóm nên chia nội dung thành các chương tương ứng với từng task.

### Gợi ý cấu trúc

1. `intro.md`
   - Giới thiệu đề bài
   - Giới thiệu repo `huggingface/peft`
   - Mục tiêu của nhóm

2. `task1_clone_and_discovery.md`
   - Clone repo
   - Đếm file Python
   - Mô tả cấu trúc thư mục

3. `task2_parser_service.md`
   - Kiến trúc parser
   - Cách trích xuất AST/CFG/DFG/call edges
   - Ví dụ event JSON

4. `task3_kafka_design.md`
   - Thiết kế topic
   - Schema message
   - Ảnh chụp Kafka

5. `task4_neo4j_ingestion.md`
   - Neo4j sink
   - Cypher MERGE
   - Screenshot và query kiểm tra

6. `task5_mongodb_streaming.md`
   - Spark Structured Streaming
   - Checkpoint
   - Screenshot MongoDB

7. `task6_replay_verification.md`
   - Chỉnh một file
   - Chạy lại parser
   - So sánh kết quả trước/sau

8. `architecture.md`
   - Sơ đồ tổng thể từ repo Python -> Parser -> Kafka -> Neo4j/MongoDB

9. `conclusion.md`
   - Những gì làm được
   - Vấn đề gặp phải
   - Bài học rút ra

### Mỗi chương nên có

- Mô tả ý tưởng.
- Các bước thực hiện.
- Notebook cells đã chạy thật.
- Kết quả đầu ra thực tế.
- Hình ảnh chụp màn hình.
- Một đoạn reflection ngắn.

---

## 4. Bố cục thư mục source code nên có trong repo nộp bài

Nhóm nên sắp xếp repo nộp bài theo kiểu dễ đọc và dễ chấm:

```text
project/
  notebooks/
  src/
    parser_service/
    kafka_producer/
    streaming_jobs/
  configs/
  diagrams/
  screenshots/
  logs/
  jupyter_book/
```

### Gợi ý nội dung từng thư mục

- `src/parser_service/`: code parser incremental.
- `src/kafka_producer/`: code đẩy event vào Kafka.
- `src/streaming_jobs/`: Spark job đọc metadata.
- `configs/`: cấu hình topic, MongoDB, Neo4j, checkpoint.
- `diagrams/`: sơ đồ kiến trúc.
- `screenshots/`: ảnh minh họa Kafka, Neo4j, MongoDB.
- `logs/`: log chạy thực tế.
- `jupyter_book/`: nội dung publish lên GitHub Pages.

---

## 5. Checklist trước khi nộp

Trước khi nộp, nhóm nên tự kiểm tra các điểm sau:

1. Có đúng một URL GitHub Pages cho Jupyter Book.
2. Jupyter Book có đủ chương theo từng task.
3. Có command và output thật, không phải chỉ mô tả lý thuyết.
4. Có ảnh chụp Neo4j và MongoDB.
5. Có sơ đồ kiến trúc tổng thể.
6. Có log replay sau khi sửa một file Python.
7. Có mô tả rõ vì sao chọn `huggingface/peft`.
8. Có giải thích cách giữ ID ổn định để tránh duplicate.
9. Có checkpoint cho Spark Structured Streaming.
10. Có reflection cuối mỗi chapter.

---

## 6. Gợi ý ngắn cho cách viết báo cáo

Khi viết trong Jupyter Book, nhóm nên ưu tiên cách trình bày sau:

- Nói rõ mục tiêu của từng bước.
- Sau đó mới đưa lệnh và kết quả.
- Với mỗi ảnh chụp màn hình, ghi chú nó chứng minh điều gì.
- Nếu có lỗi, đừng che đi, hãy mô tả cách xử lý.
- Với `peft`, nên nhấn mạnh rằng đây là thư viện nhiều module nhỏ, rất phù hợp để demo incremental parsing và replay idempotent.

---

## 7. Tóm tắt ý chính cho chủ đề `huggingface/peft`

Nếu nhóm bám theo repo này, bài làm nên nhấn mạnh các điểm:

- PEFT là thư viện tối ưu fine-tuning cho mô hình lớn.
- Mã nguồn Python có cấu trúc rõ ràng, nhiều module và nhiều biến thể tuner.
- Rất phù hợp để minh họa parse incremental từng file.
- Có đủ ngữ cảnh để tạo AST nodes, call edges, metadata, và replay verification.

Nếu cần, nhóm có thể lấy phần lõi ở `src/peft/` làm phạm vi chính, còn `examples/` và `tests/` chỉ dùng để minh họa hoặc mở rộng.
