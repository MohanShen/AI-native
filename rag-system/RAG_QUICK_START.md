# RAG 系统快速启动指南

## 快速开始

### 1. 启动 Elasticsearch

```bash
cd ../elastic-start-local
./start.sh
```

等待 Elasticsearch 启动完成（通常需要 1-2 分钟）。

### 2. 检查 Elasticsearch 是否运行

```bash
curl http://localhost:9200
```

或者访问 Kibana: http://localhost:5601

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 4. 运行示例

```bash
python rag_example.py
```

或者直接使用：

```python
from rag_system import RAGSystem

# 初始化 RAG 系统
rag = RAGSystem(
    es_host="localhost",
    es_port=9200,
    es_user="elastic",
    es_password="w2b9I2dq",  # 从 ../elastic-start-local/.env 中获取
    index_name="rag_documents"
)

# 处理 PDF 文件
rag.process_and_index_pdf("your_document.pdf")

# 查询
result = rag.query("What is this document about?")
print(result['answer'])
```

## Elasticsearch 配置

根据 `../elastic-start-local/.env` 文件，默认配置为：
- **主机**: localhost
- **端口**: 9200
- **用户名**: elastic
- **密码**: w2b9I2dq (从 .env 文件中获取)

如果您的配置不同，请修改 `RAGSystem` 初始化参数。

## 停止 Elasticsearch

```bash
cd ../elastic-start-local
./stop.sh
```

## 常见问题

### Q: Elasticsearch 连接失败
**A**: 确保 Elasticsearch 正在运行：
```bash
cd ../elastic-start-local
./start.sh
```

### Q: 密码错误
**A**: 检查 `../elastic-start-local/.env` 文件中的 `ES_LOCAL_PASSWORD` 值。

### Q: 端口被占用
**A**: 检查 `../elastic-start-local/.env` 文件中的 `ES_LOCAL_PORT` 值，或修改端口。

### Q: 模型下载失败
**A**: 检查网络连接，或使用镜像源（如果在中国）。

## 完整使用示例

```python
from rag_system import RAGSystem

# 1. 初始化 RAG 系统
rag = RAGSystem(
    es_host="localhost",
    es_port=9200,
    es_user="elastic",
    es_password="w2b9I2dq",
    index_name="rag_documents",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    reranker_method="rrf",
    chunk_size=500,
    chunk_overlap=50
)

# 2. 处理 PDF 文件
pdf_path = "example.pdf"
rag.process_and_index_pdf(pdf_path)

# 3. 查询
question = "What is this document about?"
result = rag.query(question, top_k=5)

print(f"问题: {result['question']}")
print(f"\n回答:\n{result['answer']}")
print(f"\n找到 {result['num_results']} 个相关文档")

# 4. 查看索引统计
stats = rag.get_index_stats()
print(f"\n索引统计:")
print(f"  文档数量: {stats['document_count']}")
print(f"  索引大小: {stats['size'] / 1024 / 1024:.2f} MB")
```

## 下一步

- 查看完整文档: [RAG_README.md](RAG_README.md)
- 运行示例程序: `python rag_example.py`
- 查看系统实现: `rag_system.py`

