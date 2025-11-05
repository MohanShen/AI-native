# 项目结构说明

## 整理后的项目结构

```
AI-native/
├── README.md                    # 根目录说明文档
├── .gitignore                   # Git 忽略文件
│
├── amazon-scraper/              # Amazon 产品评论爬虫项目
│   ├── README.md               # 项目文档
│   ├── requirements.txt        # 项目依赖
│   ├── amazon_scraper.py       # 主程序
│   ├── example_usage.py        # 使用示例
│   ├── HOMEWORK_VERIFICATION.md # 作业验证
│   ├── QUICK_START.md          # 快速开始指南
│   ├── amazon_cookies.pkl      # Cookies 文件
│   ├── amazon_reviews.csv      # 评论数据（CSV）
│   ├── amazon_reviews.json     # 评论数据（JSON）
│   └── search_page_debug.png   # 调试截图
│
├── rag-system/                 # RAG 系统项目
│   ├── requirements.txt        # 项目依赖
│   ├── rag_system.py           # 主程序
│   ├── rag_example.py          # 使用示例
│   ├── test_rag.py             # 测试脚本
│   ├── RAG_README.md           # 完整文档
│   ├── RAG_QUICK_START.md      # 快速开始指南
│   ├── RAG_IMPLEMENTATION.md   # 实现文档
│   ├── RAG_TEST_RESULTS.md     # 测试结果
│   ├── example.pdf             # 示例 PDF 文件
│   └── extracted_images/      # 提取的图片
│
├── elastic-start-local/         # Elasticsearch 本地部署（共享）
│   ├── docker-compose.yml      # Docker Compose 配置
│   ├── start.sh                # 启动脚本
│   ├── stop.sh                 # 停止脚本
│   ├── uninstall.sh            # 卸载脚本
│   ├── .env                    # 环境配置
│   └── config/                 # 配置文件
│       └── telemetry.yml
│
└── venv/                       # Python 虚拟环境（可选）
```

## 项目说明

### 1. Amazon Scraper（亚马逊爬虫）

**位置**: `amazon-scraper/`

**功能**: 抓取亚马逊产品评论

**依赖**: 
- selenium>=4.15.0

**使用**:
```bash
cd amazon-scraper
pip install -r requirements.txt
python amazon_scraper.py
```

### 2. RAG System（RAG 系统）

**位置**: `rag-system/`

**功能**: 处理 PDF 文档的 RAG 系统

**依赖**: 
- PyPDF2, pdfplumber, pymupdf
- langchain, sentence-transformers
- elasticsearch, transformers, torch
- 等等（见 requirements.txt）

**使用**:
```bash
# 1. 启动 Elasticsearch
cd ../elastic-start-local
./start.sh

# 2. 安装依赖
cd ../rag-system
pip install -r requirements.txt

# 3. 运行示例
python rag_example.py
```

### 3. Elasticsearch Local（共享资源）

**位置**: `elastic-start-local/`

**用途**: 为 RAG 系统提供 Elasticsearch 本地部署

**使用**:
```bash
cd elastic-start-local
./start.sh    # 启动
./stop.sh     # 停止
```

## 整理说明

✅ 已将项目文件按功能分类到不同文件夹
✅ 每个项目都有独立的 `requirements.txt`
✅ 更新了所有文档中的路径引用
✅ 创建了根目录的 README.md 说明整体结构

## 注意事项

1. **路径引用**: 
   - 从 `rag-system/` 目录访问 `elastic-start-local/` 时，使用 `../elastic-start-local/`
   - 所有文档中的路径引用已更新

2. **依赖管理**: 
   - 每个项目都有独立的 `requirements.txt`
   - 建议为每个项目创建独立的虚拟环境

3. **共享资源**: 
   - `elastic-start-local/` 位于根目录，两个项目都可以使用
   - `venv/` 位于根目录，可以共享或为每个项目创建独立的虚拟环境

