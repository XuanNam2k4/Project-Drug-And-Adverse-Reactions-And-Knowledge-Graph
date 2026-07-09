# 🎓 HƯỚNG DẪN CÀI ĐẶT ĐỒ ÁN TỐT NGHIỆP

**Trích xuất phản ứng có hại của thuốc từ diễn đàn y tế và xây dựng Knowledge Graph thuốc – tác dụng phụ**

---

## Mục lục

1. [Giới thiệu đề tài](#1-giới-thiệu-đề-tài)
2. [Pipeline xử lý](#2-pipeline-xử-lý)
3. [Cấu trúc thư mục](#3-cấu-trúc-thư-mục)
4. [Cài đặt môi trường](#4-cài-đặt-môi-trường)
5. [Cài đặt Python & thư viện](#5-cài-đặt-python--thư-viện)
6. [Kiểm tra cài đặt](#6-kiểm-tra-cài-đặt)
7. [Hướng dẫn chạy Knowledge Graph (KG) trên Protege](#7-hướng-dẫn-chạy-knowledge-graph-kg-trên-protege)
8. [Chạy giao diện Demo (Streamlit)](#8-chạy-giao-diện-demo-streamlit)
9. [Cài đặt môi trường cho mô hình BERT NER](#9-cài-đặt-môi-trường-cho-mô-hình-bert-ner)
10. [Huấn luyện lại mô hình BERT NER](#10-huấn-luyện-lại-mô-hình-bert-ner)
11. [Chạy các module NER, Relation Extraction & Knowledge Graph] (# 11. Chạy các module NER, Relation Extraction & Knowledge Graph)

---

## 1. Giới thiệu đề tài

**Tên đề tài**: *"Trích xuất phản ứng có hại của thuốc từ diễn đàn y tế và xây dựng Knowledge Graph về thuốc – tác dụng phụ"*

Đề tài thực hiện việc thu thập dữ liệu y tế từ các diễn đàn y tế, bài viết hoặc bình luận của người dùng. Nội dung chủ yếu là trải nghiệm khi dùng thuốc, xử lý ngôn ngữ (NLP) để tìm ra các thông tin quan trọng trong câu: thuốc nào được nhắc đến, tác dụng phụ nào xuất hiện, xác định mối quan hệ giữa chúng và biểu diễn lại dữ liệu dưới dạng đồ thị quan hệ.

---

## 2. Pipeline xử lý

```
┌──────────────────────────────────────────────────────────┐
│           Pipeline trích xuất ADE & xây dựng KG          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  📥 Dữ liệu đầu vào                                      │
│    ├── CADEC Corpus                                      │
│    └── Thongke_Dulieu_CADEC.csv                          │
│                                                          │
│  📝 Tiền xử lý dữ liệu                                   │
│    ├── Văn bản bài đăng thô                              │
│    ├── Tiền xử lý dữ liệu                                │
│    └── cadec_tienxuly.csv                                │
│                                                          │
│  🔍 Nhận diện thực thể và trích xuất thông tin NLP                             │
│    ├── Named Entity Recognition (NER)                    │
│    │   └── baseline_ketqua.csv                           │
│    └── Relation Extraction                               │
│        └── relation_extraction.py                        │
│                                                          │
│  🧩 Chuẩn hoá & Ontology                                 │
│    └── Chuẩn hoá thực thể / Ontology                     │
│                                                          │
│  🕸️ Xây dựng Knowledge Graph                             │
│    ├── RDF Triples: Drug causes ADE                      │
│    ├── Tạo KG: tao_KG.py                                 │
│    └── drug_ade_kg.ttl                                   │
│                                                          │
│  ⚡ Truy vấn KG                                          │
│    └── SPARQL query                                      │
│                                                          │
│  📊 Đánh giá hệ thống                                    │
│    ├── Đánh giá mô hình NER, Relation Extraction         │
│    └── Đánh giá định tính                                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Cấu trúc thư mục

```
DoanTN/
│
├── HuongdanReadme.md                        # Hướng dẫn toàn bộ bài đồ án
│
├── Về thống kê dữ liệu
│   ├── thongke.py                     # Thực hiện thống kê dữ liệu
│   └── Thongke_Dulieu_CADEC.csv       # File CSV lưu trữ dữ liệu CADEC
│
├── Về xử lý NLP
│   ├── tienxuly_cadec.py              # Xử lý tiền dữ liệu văn bản thô
│   └── cadec_tienxuly.csv             # Kết quả tiền xử lý
│
├── Về nhận dạng NER (baseline dictionary matching)
│   ├── baseline.py                    # Code xử lý nhận dạng NER
│   ├── ner_evaluation_per_file.csv    # Kết quả đánh giá trên từng file NER
│   └── baseline_ketqua.csv           # Đánh giá NER (Entity, TP, FP, FN, Precision, Recall, F1)
│
├── Về trích xuất quan hệ RE (Relation Extraction)
│   ├── relation_extraction.py         # Code xử lý trích xuất tạo cặp Drug-ADE
│   ├── relation_evaluation.py         # Code đánh giá trích xuất
│   ├── drug_ade_relations.csv         # Kết quả tạo cặp Drug-ADE
│   ├── relation_evaluation_per_file.csv # Đánh giá trích xuất từng file
│   ├── danh_gia_dinh_tinh(ban đầu).csv   # đánh giá định tính file cũ
│   └── danh_gia_dinh_tinh.csv         # Đánh giá định tính phân tích lỗi
│
├── Về Knowledge Graph
│   ├── tao_KG.py                      # Xây dựng KG chính (Drug-ADE + mở rộng ngữ cảnh)
│   └── KG2.py                         # Xây dựng KG ban đầu (chỉ Drug và ADE)
│
├── Về Ontology
│   ├── drug_ade_kg.ttl                # Ontology hiện tại (chỉnh kèm mở rộng)
│   └── dug_ade_kg2.ttl                # Ontology ban đầu (giữ lại để so sánh)
│
├── Về dữ liệu
│   └── data/
│       └── cadec/                     # Dữ liệu gốc CADEC (cần tải từ nguồn)
│           ├── meddra/                # Ánh xạ/chú thích theo chuẩn MedDRA
│           ├── original/              # Dữ liệu gốc chưa xử lý (.ann)
│           ├── sct/                   # Chú thích theo chuẩn SNOMED CT
│           ├── text/                  # Văn bản thô từ bài đăng (.txt)
│           ├── CADEC.v1.zip           # Bộ dữ liệu CADEC v1
│           └── CADEC.v2.zip           # Bộ dữ liệu CADEC v2
│
├── Về BERT
│   ├── drug_ade_relations.csv         # Bảng chuẩn hoá từ điển ngoài ADE
│   ├── drug_normalization.csv         # Bảng chuẩn hoá từ điển ngoài Drug
│   ├── BERT.ipynb                     # Xử lý BERT
│   ├── bert_ner_results.csv           # Kết quả đánh giá BERT
│   └── phan_tich_loi/                 # Phân tích lỗi
│       ├── bieu_do_phan_tich_loi_luan_van.png    # Biểu đồ phân tích lỗi
│       ├── chi_tiet_phan_tich_loi.csv            # Chi tiết phân tích lỗi
│       ├── luat_loc_qua_manh_fn.csv              # Lỗi luật lọc quá mạnh
│       ├── ner_bo_sot_thuat_ngu.csv              # Lỗi bỏ sót thuật ngữ
│       ├── nhieu_thuoc_trong_cau.csv             # Lỗi nhiều thuốc trong câu
│       ├── phu_dinh_error.csv                    # Lỗi phủ định
│       ├── tach_cau_loi.csv                      # Lỗi tách câu
│       └── vi_du_5_loi_moi_nhom.csv              # Minh hoạ mỗi nhóm 5 ví dụ
│
├── model của BERT lưu lại/
│   └── ner_env/                       # Môi trường ảo Python
│       ├── Include/
│       ├── Lib/
│       │   └── site-packages/
│       ├── etc/
│       │   └── jupyter/
│       │       └── jupyter_server_config.d/
│       └── pyvenv.cfg
│
├── ner_model/                         # Model đã huấn luyện
│   ├── checkpoint-375/
│   │   ├── config.json
│   │   ├── model.safetensors
│   │   ├── optimizer.pt
│   │   ├── rng_state.pth
│   │   ├── scheduler.pt
│   │   ├── tokenizer.json
│   │   ├── tokenizer_config.json
│   │   ├── trainer_state.json
│   │   └── training_args.bin
│   ├── checkpoint-500/
│   │   ├── config.json
│   │   ├── model.safetensors
│   │   ├── optimizer.pt
│   │   ├── rng_state.pth
│   │   ├── scheduler.pt
│   │   ├── tokenizer.json
│   │   ├── tokenizer_config.json
│   │   ├── trainer_state.json
│   │   └── training_args.bin
│   └── checkpoint-750/
│       ├── config.json
│       ├── model.safetensors
│       ├── optimizer.pt
│       ├── rng_state.pth
│       ├── scheduler.pt
│       ├── tokenizer.json
│       ├── tokenizer_config.json
│       ├── trainer_state.json
│       └── training_args.bin
│
├── metadata/
│   ├── collection_import_sha256sum.txt
│   ├── CSIRO Data Licence.html
│   ├── dublincore-000010948v003.xml
│   └── readme-help.md
│
├── ui/                                # Giao diện Streamlit
│   ├── ungdung.py                     # Chạy: streamlit run ungdung.py
│   └── (Các tab trên ứng dụng)
│       ├── Tab 1: Tra cứu thuốc và phản ứng có hại thường gặp
│       ├── Tab 2: Nhập tên thuốc và lọc theo giới tính, độ tuổi, bệnh nền
│       └── Tab 3: Hỏi đáp đơn giản
│
├── Ảnh vẽ Draw.io/
│   ├── anh1.png
│   ├── anh2.png
│   ├── anh3.png
│   ├── anh4.png
│   ├── anh5.png
│   └── anh6.png
│
├── Báo cáo ĐATN_HuynhXuanNam_64131375_....docx
├── gold_standard.csv                   # Đánh giá tập chuẩn
├── main.py                             # Kiểm tra thử dữ liệu CADEC
├── check.py                            # Kiểm tra môi trường thư viện
├── bieudokg.py                         # Biểu đồ vẽ KG
├── bieudoNER.py                        # Biểu đồ NER
├── BERT(2).ipynb                       # BERT cũ
├── CADEC-QEzDvqEq-.zip                 # dữ liệu gốc CADEC chưa giải nén còn trên zip
├── bieudotichhop.py                    # Biểu đồ tích hợp
├── "File Readme hướng dẫn cài đặt.docx" # File hướng dẫn cài đặt bằng Word
└── "File chính Word chứa các câu truy vấn.docx" # File câu truy vấn
```

---

## 4. Cài đặt môi trường

### 4.1. Cài đặt Visual Studio Code

Visual Studio Code là môi trường phát triển được sử dụng để chỉnh sửa và chạy mã nguồn của dự án.

#### Bước 1: Tải Visual Studio Code

Truy cập trang chính thức: [https://code.visualstudio.com/](https://code.visualstudio.com/)

#### Bước 2: Cài đặt

- Tải phiên bản phù hợp với hệ điều hành (Windows, macOS hoặc Linux).
- Chạy tệp cài đặt vừa tải về.
- Thực hiện theo các hướng dẫn trên màn hình để hoàn tất.

#### Bước 3: Kiểm tra

Sau khi cài đặt thành công, mở Visual Studio Code để kiểm tra và đảm bảo chương trình hoạt động bình thường.

### 4.2. Cài đặt Jupyter Lab

Jupyter Lab được sử dụng để mở và chạy các tệp Notebook (`.ipynb`) trong dự án.

#### Cài đặt

Mở **Command Prompt (CMD)** hoặc **Terminal** và chạy lệnh:

```bash
pip install jupyterlab
```

#### Kiểm tra cài đặt

Sau khi cài đặt hoàn tất, chạy:

```bash
jupyter lab
```

Nếu cài đặt thành công, giao diện Jupyter Lab sẽ tự động mở trên trình duyệt.

### 4.3. Mở thư mục dự án

Trước khi khởi động Jupyter Lab, cần chuyển đến thư mục chứa dự án.

Ví dụ dự án được lưu trong ổ đĩa **D**:

```bash
D:
cd DoanTN
```

Trong đó:
- `D:` : chuyển sang ổ đĩa D.
- `DoanTN` : thư mục chứa mã nguồn của đồ án.

### 4.4. Khởi động Jupyter Lab

Tại thư mục dự án, chạy:

```bash
jupyter lab
```

Jupyter Lab sẽ được mở trên trình duyệt mặc định.

### 4.5. Chạy Notebook

1. Trong giao diện Jupyter Lab, mở tệp **BERT.ipynb**.
2. Chọn **Run → Run All Cells** hoặc nhấn nút **Run** trên thanh công cụ.
3. Chờ Notebook thực thi toàn bộ các ô lệnh.
4. Kết quả sẽ được hiển thị bên dưới từng ô lệnh.

Người dùng có thể:
- Xem mã nguồn của mô hình BERT.
- Thực thi lại quá trình huấn luyện hoặc dự đoán.
- Kiểm tra kết quả đầu ra của mô hình.
- Theo dõi các chỉ số đánh giá và thống kê được hiển thị trong Notebook.

#### Tóm tắt lệnh

```bash
pip install jupyterlab

D:
cd DoanTN

jupyter lab
```

---

## 5. Cài đặt Python & thư viện

### 5.1. Yêu cầu phiên bản

> **⚠️ Yêu cầu: Python 3.10**
>
> Không dùng Python 3.12 hoặc 3.13 vì một số package (như `sentence-transformers`, `rdflib`) có thể chưa tương thích. Python 3.11 cũng hoạt động, nhưng **3.10 được khuyến nghị** để đảm bảo ổn định nhất.
Đối với project hiện tại đang thực hiện cài Python 3.11.0 với môi trường env.
### 5.2. Cài đặt Python trên Windows

**Cách 1 — Download từ python.org** (khuyến nghị):

1. Truy cập [https://www.python.org/downloads/release/python-31011/](https://www.python.org/downloads/release/python-31011/)
2. Tải `Windows installer (64-bit)` — file: `python-3.10.11-amd64.exe`
3. Khi cài đặt: ✅ **NHỚ tick "Add Python to PATH"**
4. Click **Install Now**

Sau khi cài, kiểm tra:

```cmd
python --version
```

Kết quả: `Python 3.10.x`

⏱ Thời gian: 5–15 phút (tuỳ tốc độ mạng và cấu hình máy).

### 5.3. Cài đặt model spaCy (bổ sung)

```cmd
python -m spacy download en_core_web_sm
```

### 5.4. Kiểm tra các package quan trọng

Chạy lệnh sau để kiểm tra các thư viện cần thiết cho dự án:

```cmd
python -c "import pandas; import numpy; import matplotlib; import plotly; import rdflib; import streamlit; import altair; import pyarrow; import requests; import jsonpickle; print('✅ All required packages loaded successfully')"
```

Nếu xuất hiện thông báo:

```
✅ All required packages loaded successfully
```

thì các thư viện đã được cài đặt thành công.

### 5.5. Các package chính được sử dụng

| Package      | Version |
|--------------|---------|
| altair       | 6.1.0   |
| GitPython    | 3.1.50  |
| ipython      | 9.14.0  |
| jsonpickle   | 4.1.2   |
| matplotlib   | 3.10.9  |
| numpy        | 2.4.4   |
| pandas       | 3.0.2   |
| plotly       | 6.7.0   |
| pyarrow      | 24.0.0  |
| rdflib       | 7.6.0   |
| requests     | 2.33.1  |
| streamlit    | 1.57.0  |

Để xem toàn bộ các package đã cài đặt trong môi trường hiện tại:

```cmd
pip list
```

---

## 6. Kiểm tra cài đặt

### Kiểm tra môi trường

```cmd
python -c "
import sys;
import pandas;
import numpy;
import rdflib;
import streamlit;
import networkx;
import plotly;

print(f'Python: {sys.version}')
print(f'Pandas: {pandas.__version__}')
print(f'NumPy: {numpy.__version__}')
print(f'Streamlit: {streamlit.__version__}')
print(f'NetworkX: {networkx.__version__}')
print(f'Plotly: {plotly.__version__}')
print(f'RDFLib: {rdflib.__version__}')
print('✅ Environment ready!')
"
```

---

## 7. Hướng dẫn chạy Knowledge Graph (KG) trên Protege

### 7.1. Cài đặt thư viện cần thiết

Để chạy được hệ thống tạo **Knowledge Graph (KG)**, cần cài đặt các thư viện sau:

```bash
pip install pandas
pip install rdflib
pip install numpy
pip install lxml
```

### 7.2. Mở file `.ttl` trên Protégé

Để chạy file `.ttl`, ta thực hiện:

1. Truy cập trang chủ [Protégé](https://protege.stanford.edu/) để tải phần mềm về.
2. Mở ứng dụng Protégé.
3. Vào **File → Open**, chọn file `drug_ade_kg.ttl` và nhấn **Open**.
4. Ta có thể xem cấu trúc của KG và thực hiện truy vấn SPARQL.

### 7.3. Tạo KG từ code

```bash
python tao_KG.py
```

---

## 8. Chạy giao diện Demo (Streamlit)

### 8.1. Yêu cầu trước khi chạy

Đảm bảo các tệp sau nằm trong cùng thư mục dự án:

- `ungdung.py`
- `drug_ade_kg.ttl`

Và các thư viện Python cần thiết:

- streamlit
- rdflib
- pandas
- plotly

Cài đặt thư viện:

```bash
pip install streamlit rdflib pandas plotly
```

### 8.2. Lệnh chạy

Trong VSCode, mở terminal và gõ:

```bash
streamlit run ungdung.py
```

### 8.3. URL truy cập

Sau khi chạy, Terminal sẽ hiển thị:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Mở trình duyệt và truy cập: **http://localhost:8501**

> 💡 Cổng mặc định là 8501.

### 8.4. Giao diện trong UI


| Trang | Mô tả | Cách sử dụng |
|-------|-------|--------------|
| **🏠 Chức năng:** | Chuyển đổi dịch tự động Tiếng Việt và Tiếng Anh |
| **🏠 Trang chủ** | Tổng quan hệ thống | Mở app là thấy ngay |
| **💊 Tra cứu thuốc** | Tra cứu thông tin thuốc và các phản ứng có hại liên quan trong KG | Nhập tên thuốc → Click "Tìm kiếm" |
---

## 9. Cài đặt môi trường cho mô hình BERT NER

Ngoài các thư viện đã cài đặt cho ứng dụng Knowledge Graph, cần cài đặt thêm các thư viện phục vụ cho việc huấn luyện và đánh giá mô hình BERT NER trên Jupyter Lab.

### 9.1. Cài đặt các thư viện cần thiết

```bash
pip install transformers torch scikit-learn seqeval numpy pandas
```

Hoặc cài đặt lần lượt:

```bash
pip install transformers
pip install torch
pip install scikit-learn
pip install seqeval
pip install numpy
pip install pandas
```

---

## 10. Huấn luyện lại mô hình BERT NER

> **⚠️ Lưu ý:**
> - Thời gian huấn luyện phụ thuộc vào cấu hình phần cứng của máy tính.
>   - Máy cấu hình mạnh: khoảng **15–60 phút**.
>   - Máy cấu hình trung bình hoặc cũ: có thể mất **3–4 giờ** hoặc lâu hơn.
> - Trong quá trình huấn luyện, không nên tắt Jupyter Lab hoặc tắt máy tính.

### 10.1. Chạy lại các cell huấn luyện

Thực hiện chạy lần lượt các cell trong notebook có sử dụng các thư viện sau:

```python
from transformers import BertTokenizerFast
from sklearn.model_selection import train_test_split
from transformers import BertForTokenClassification

from seqeval.metrics import (
    classification_report,
    precision_score,
    recall_score,
    f1_score
)

from seqeval.metrics.sequence_labeling import get_entities
```

Các cell này thực hiện:
- Tiền xử lý dữ liệu.
- Chia tập huấn luyện và tập kiểm thử.
- Tokenization bằng BERT Tokenizer.
- Huấn luyện mô hình BERT NER.
- Lưu mô hình vào thư mục `./ner_model`.

### 10.2. Tải lại mô hình đã lưu

Sau khi huấn luyện hoàn tất, tải lại mô hình:

```python
from transformers import AutoModelForTokenClassification
from transformers import AutoTokenizer

model = AutoModelForTokenClassification.from_pretrained("./ner_model")
tokenizer = AutoTokenizer.from_pretrained("./ner_model")
```

### 10.3. Đánh giá mô hình

Chạy lệnh:

```python
trainer.evaluate()
```

Nếu quá trình tải mô hình thành công, màn hình sẽ hiển thị thông báo tương tự:

```
Loading weights: 100%|█████████████████████████| 199/199 [00:00<00:00, 1998.22it/s]
Loading weights: 100%|█████████████████████████| 199/199 [00:00<00:00, 3774.26it/s]
```

### 10.4. Kiểm tra kết quả

Sau khi đánh giá hoàn tất, hệ thống sẽ sinh ra tệp kết quả:

```
bert_ner_results.csv
```

Tệp này chứa các thông tin:
- Văn bản đầu vào.
- Nhãn thực tế (Ground Truth).
- Nhãn dự đoán của mô hình.
- Kết quả nhận diện thực thể thuốc (Drug).
- Kết quả nhận diện phản ứng có hại (ADE).

Tệp kết quả được sử dụng để:
- Đánh giá hiệu năng mô hình.
- So sánh nhãn dự đoán với nhãn thực tế.
- Phục vụ cho việc báo cáo và phân tích kết quả nghiên cứu.

---

> **© Đồ án tốt nghiệp** — Trích xuất phản ứng có hại của thuốc từ diễn đàn y tế và xây dựng Knowledge Graph thuốc – tác dụng phụ

---

## 11. Chạy các module NER, Relation Extraction & Knowledge Graph

> **⚠️ Lưu ý trước khi chạy:**
> - Các lệnh được thực thi trong **terminal của VSCode** tại thư mục gốc dự án.
> - Nếu muốn chạy ra kết quả mới, cần **xoá các file CSV cũ** đã có trong đồ án trước đó.

### 11.1. Tiền xử lý dữ liệu

```bash
python tienxuly_cadec.py
```

### 11.2. Nhận dạng thực thể (NER)

```bash
python baseline.py
```

Sau khi chạy, các kết quả và file đánh giá CSV sẽ được sinh ra tự động.

### 11.3. Trích xuất quan hệ (Relation Extraction)

Chạy trích xuất quan hệ:

```bash
python relation_extraction.py
```

Sau đó chạy đánh giá:

```bash
python relation_evaluation.py
```

### 11.4. Xây dựng Knowledge Graph

```bash
python tao_KG.py
```

Sau khi chạy, các kết quả và file đánh giá CSV sẽ được sinh ra tự động.
