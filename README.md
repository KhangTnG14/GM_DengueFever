Ứng dụng Graph Mining Phân tích và Dự đoán Lan truyền Dịch bệnh Sốt xuất huyết tại TP.HCM

Dự án này tiếp cận bài toán phòng chống dịch bệnh sốt xuất huyết tại Thành phố Hồ Chí Minh theo một hướng mới: mô hình hóa toàn bộ thành phố thành một Đồ thị lan truyền. Thay vì phân tích dịch truyền thống, chúng tôi áp dụng các kỹ thuật Khai phá đồ thị (Graph Mining) để xác định các thông tin ẩn về ổ dịch cụm và các quận cầu nối. 

Ý nghĩa thực tế: Hỗ trợ ngành y tế xác định ưu tiên phun thuốc, phân bổ nhân lực và cảnh báo sớm các khu vực có nguy cơ bùng phát thay vì phản ứng bị động.  

Thành Viên:

- Nguyễn Vũ Hà - 23705991
- Nguyễn Huỳnh Nhật Tân - 23650801
- Trương Thanh Phụng - 23644201
- Khuất Quốc Khánh - 23711381
- Nguyễn Tấn Khang - 23722301

Chạy file environment.yml

- conda env create -f environment.yml
- pip install -r requirements.txt
- conda activate dengue-graph

Chuẩn bị & Tiền xử lý dữ liệu :

Tạo bộ dữ liệu:
- python src/data/generate_dengue_data.py

Lọc dữ liệu bản đồ (GeoJSON) TP.HCM:
- python src/data/filter_hcm_geo.py

Hợp nhất dữ liệu ca bệnh vào bản đồ:
- python src/data/merge_filter_HCM.py

Xây dựng ma trận kề (Adjacency Matrix):
- python src/graph/build_adjacency.py

Xây dựng trọng số lưu lượng giao thông:
- python src/graph/build_traffic.py

Thực hiện phân tích:

Giai đoạn 1: Khởi tạo Đồ thị
- notebooks/01_data_collection_eda.ipynb
Nội dung: Chạy toàn bộ các cell để xem phân tích Top 10 quận, biểu đồ mùa vụ và heatmap dịch bệnh.
Outputs: Các biểu đồ Bar chart, Heatmap về phân phối ca bệnh.

- notebooks/02_graph_construction.ipynb
Nội dung: Khởi tạo đối tượng đồ thị NetworkX. Đây là bước quan trọng nhất để gán trọng số cạnh (Edge Weights) từ dữ liệu địa lý và giao thông đã chuẩn bị.
Outputs: Mô hình Graph

Giai đoạn 2: Khai phá cấu trúc mạng lưới
- notebooks/03_centrality_analysis.ipynb
Nội dung: Tính toán Betweenness, PageRank. Tìm ra "nút thắt" giao thông lây nhiễm.
Outputs: Bảng điểm Centrality, Bar chart Top 10 quận quan trọng.

- notebooks/04_community_detection.ipynb
Nội dung: Chạy thuật toán Louvain để gom nhóm các quận thành các "vùng xanh/đỏ" (ổ dịch cụm).
Outputs: Phân cụm ổ dịch (Louvain/Spectral), file community_labels.csv.

Giai đoạn 3: Phân tích nâng cao & Mô phỏng

- notebooks/05_temporal_graph.ipynb
Nội dung: Xem biến động dịch bệnh theo trục thời gian (tuần/tháng).
Outputs: File HTML bản đồ dịch bệnh thay đổi theo thời gian

- 06_sir_epidemic_model.ipynb
Nội dung: Chạy mô phỏng SIR. Bạn có thể thay đổi seed_node (quận bắt đầu dịch) để xem tốc độ lây lan khác nhau.
Outputs: File HTML mô phỏng SIR, biểu đồ đường cong dịch bệnh

Xem kết quả Trực quan hóa
- Mở các file `.html` trong `outputs/maps/` và `outputs/graphs/` bằng trình duyệt web để xem bản đồ và đồ thị mạng tương tác.
