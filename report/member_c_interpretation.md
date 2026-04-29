# Diễn giải kết quả phân tích - Thành viên C

## 1) Đánh giá chất lượng clustering

- Louvain (Modularity Q tốt nhất): **0.3218**
- Spectral (Silhouette tốt nhất): **-0.0099**
- Nhận xét: Louvain phù hợp hơn trên đồ thị hiện tại; Spectral có silhouette âm, cho thấy cụm chưa tách biệt rõ.

## 2) Validation thực tế qua đồng pha bùng phát (time-series correlation)

- Louvain: `within = 0.7625`, `across = 0.7578`, `lift = 0.0047`
- Spectral: `within = 0.7469`, `across = 0.7702`, `lift = -0.0233`
- Diễn giải: `lift > 0` nghĩa là các quận trong cùng community có xu hướng bùng phát đồng pha hơn so với khác community. Louvain nhất quán hơn trong bộ dữ liệu này.

## 3) Centrality vs thực tế ca bệnh

- Spearman(betweenness, tổng ca): **-0.2721**
- Quận top betweenness: **Quận 1**
- Quận top tổng ca: **Thủ Đức**
- Diễn giải: Vai trò cầu nối trong mạng (betweenness cao) có thể không trùng với quận có số ca cao nhất do còn phụ thuộc dân số, điều kiện môi trường và hành vi tiếp xúc.

## 4) Ý nghĩa thực tế

- Có thể ưu tiên can thiệp vào các nút trung gian quan trọng để giảm tốc độ lan truyền giữa nhiều cụm.
- Có thể lập kế hoạch theo community thay vì theo từng quận đơn lẻ.

## 5) Hạn chế

- Chuỗi dữ liệu 2022-2024 còn ngắn cho kết luận dài hạn.
- Trọng số cạnh đồ thị chưa phản ánh đầy đủ biến động di chuyển theo thời gian.
- Correlation không khẳng định nhân quả.

## 6) Đề xuất cải tiến

- Bổ sung mobility theo tuần/ngày, biến khí hậu, biến dân cư.
- Thử dynamic community detection / temporal graph models.
- Đánh giá rolling-window và chỉ số cảnh báo sớm lead-lag.
