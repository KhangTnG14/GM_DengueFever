Thành Viên:

- Nguyễn Vũ Hà - 23705991
- Nguyễn Huỳnh Nhật Tân - 23650801
- Trương Thanh Phụng - 23644201
- Khuất Quốc Khánh - 23711381
- Nguyễn Tấn Khang - 23722301

Chạy file environment.yml

- conda env create -f environment.yml
- conda activate dengue-graph

Cách chạy Day 1 (A):

- python src/data/generate_dengue_data.py

Cách chạy Day 1 (B):

- Chạy câu lệnh cày environment.yml và kích hoạt môi trường
- python src/data/filter_hcm_geo.py
- python src/data/merge_filter_HCM.py
- python src/graph/build_adjacency.py
- python src/graph/build_traffic.py

Cách chạy Day 2 (B):

- Chỉ cần chạy file notebook: 03_centrality_analysis.ipynb
  Cách chạy Day 3 (B):

- Chỉ cần chạy file notebook: 06_sir_epidemic_model.ipynb
