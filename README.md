# AI Native Projects

This repository contains multiple AI-native projects.

## Project Structure

```
AI-native/
├── amazon-scraper/          # Amazon 产品评论爬虫项目
│   ├── amazon_scraper.py
│   ├── example_usage.py
│   ├── requirements.txt
│   ├── README.md
│   └── ...
│
├── rag-system/              # RAG (Retrieval-Augmented Generation) 系统
│   ├── rag_system.py
│   ├── rag_example.py
│   ├── test_rag.py
│   ├── requirements.txt
│   ├── RAG_README.md
│   ├── RAG_QUICK_START.md
│   ├── RAG_IMPLEMENTATION.md
│   ├── RAG_TEST_RESULTS.md
│   └── ...
│
├── elastic-start-local/     # Elasticsearch 本地部署配置（共享）
│   ├── docker-compose.yml
│   ├── start.sh
│   ├── stop.sh
│   └── ...
│
└── README.md                # This file
```

## Projects

### 1. Amazon Scraper (亚马逊产品评论爬虫)

A web scraper for Amazon product reviews.

**Location**: `amazon-scraper/`

**Features**:
- Keyword search for products
- Star rating filtering
- Paginated review scraping
- Persistent login with cookies

**Quick Start**:
```bash
cd amazon-scraper
pip install -r requirements.txt
python amazon_scraper.py
```

**Documentation**: See `amazon-scraper/README.md`

---

### 2. RAG System (检索增强生成系统)

A complete RAG system for processing PDF documents with hybrid search and reranking.

**Location**: `rag-system/`

**Features**:
- PDF text, image, and table extraction
- Text chunking and vectorization
- Elasticsearch indexing
- Hybrid search (vector + BM25)
- RRF or reranker model reranking
- Answer generation based on retrieved results

**Quick Start**:
```bash
# 1. Start Elasticsearch
cd elastic-start-local
./start.sh

# 2. Install dependencies
cd ../rag-system
pip install -r requirements.txt

# 3. Run example
python rag_example.py
```

**Documentation**: 
- `rag-system/RAG_README.md` - Full documentation
- `rag-system/RAG_QUICK_START.md` - Quick start guide
- `rag-system/RAG_IMPLEMENTATION.md` - Implementation details

---

### 3. Elasticsearch Local Deployment

Shared Elasticsearch local deployment configuration for RAG system.

**Location**: `elastic-start-local/`

**Usage**:
```bash
cd elastic-start-local
./start.sh    # Start Elasticsearch and Kibana
./stop.sh     # Stop services
```

**Configuration**: See `.env` file in `elastic-start-local/` directory

---

## Requirements

### Python
- Python 3.8+ (recommended: 3.10+)

### Docker
- Docker and Docker Compose (for Elasticsearch local deployment)

### System Requirements
- At least 8GB disk space (for Elasticsearch and models)
- Chrome browser and ChromeDriver (for Amazon scraper)

## Installation

### For Amazon Scraper:
```bash
cd amazon-scraper
pip install -r requirements.txt
```

### For RAG System:
```bash
cd rag-system
pip install -r requirements.txt
```

## Notes

- Each project has its own `requirements.txt` file
- The `elastic-start-local/` directory is shared between projects
- Virtual environment (`venv/`) is at the root level and can be shared
- Each project has its own documentation in its respective directory

## License

This project is for educational purposes only.

