# RAG 系统实现文档

## 作业完成情况

### ✅ 1. 在本地部署 Elasticsearch

**实现方式**: 
- 使用 Docker Compose 在本地部署 Elasticsearch
- 配置文件位于 `../elastic-start-local/` 目录
- 启动脚本: `../elastic-start-local/start.sh`

**验证方法**:
```bash
cd ../elastic-start-local
./start.sh
curl http://localhost:9200
```

**配置信息**:
- 主机: localhost
- 端口: 9200
- 用户名: elastic
- 密码: w2b9I2dq (从 `.env` 文件获取)

---

### ✅ 2. PDF 处理：提取文本

**实现方式**: 
- 使用多种方法提取 PDF 文本：
  - **PyMuPDF (fitz)**: 更好的文本提取
  - **pdfplumber**: 更好的布局保持
  - **PyPDF2**: 备用文本提取方法

**代码位置**: `rag_system.py` - `PDFProcessor.extract_text()`

**功能**:
- 支持多页 PDF 文本提取
- 自动选择最佳提取方法
- 保留页码信息

**使用示例**:
```python
processor = PDFProcessor()
text_chunks = processor.extract_text("example.pdf")
```

---

### ✅ 3. 内容切分：将内容拆分成可检索的单元

**实现方式**: 
- 使用 `RecursiveCharacterTextSplitter` 进行文本切分
- 支持自定义块大小和重叠大小
- 支持中文和英文分隔符

**代码位置**: `rag_system.py` - `TextSplitter` 类

**配置参数**:
- `chunk_size`: 默认 500 字符
- `chunk_overlap`: 默认 50 字符

**使用示例**:
```python
splitter = TextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text_chunks(text_chunks)
```

---

### ✅ 4. 向量化：为文本生成向量

**实现方式**: 
- 使用 `sentence-transformers` 生成文本向量
- 默认模型: `sentence-transformers/all-MiniLM-L6-v2` (384 维)
- 支持自定义模型

**代码位置**: `rag_system.py` - `Vectorizer` 类

**功能**:
- 批量生成向量
- 自动处理编码
- 支持自定义模型

**使用示例**:
```python
vectorizer = Vectorizer(model_name="sentence-transformers/all-MiniLM-L6-v2")
embeddings = vectorizer.encode(texts)
```

---

### ✅ 5. 索引：将内容与向量一起存储到 Elasticsearch

**实现方式**: 
- 使用 Elasticsearch 的 `dense_vector` 字段类型
- 使用余弦相似度（cosine similarity）进行相似度计算
- 批量索引，提高效率

**代码位置**: `rag_system.py` - `RAGSystem._create_index()` 和 `process_and_index_pdf()`

**索引映射**:
```json
{
  "mappings": {
    "properties": {
      "text": {"type": "text", "analyzer": "standard"},
      "text_vector": {
        "type": "dense_vector",
        "dims": 384,
        "index": true,
        "similarity": "cosine"
      },
      "page": {"type": "integer"},
      "source": {"type": "keyword"},
      "chunk_id": {"type": "integer"}
    }
  }
}
```

**使用示例**:
```python
rag = RAGSystem()
rag.process_and_index_pdf("example.pdf")
```

---

### ✅ 6. 检索：支持混合搜索（hybrid search）

**实现方式**: 
- 结合向量搜索和 BM25 搜索
- 向量搜索: 使用余弦相似度
- BM25 搜索: 传统的关键词搜索
- 混合两种搜索结果

**代码位置**: `rag_system.py` - `RAGSystem.hybrid_search()`

**搜索策略**:
1. 向量搜索: 使用 `cosineSimilarity` 计算相似度
2. BM25 搜索: 使用 `match` 查询
3. 混合: 使用 `bool` 查询结合两种搜索

**使用示例**:
```python
results = rag.hybrid_search("machine learning", top_k=20)
```

---

### ✅ 7. 重排序：应用 RRF 或 reranker model 做最终排序

**实现方式**: 
- 支持两种重排序方法：
  - **RRF (Reciprocal Rank Fusion)**: 默认方法，不需要额外模型
  - **Reranker Model**: 使用交叉编码器模型（如 `cross-encoder/ms-marco-MiniLM-L-6-v2`）

**代码位置**: `rag_system.py` - `Reranker` 类

**RRF 方法**:
- 计算方式: `RRF_score = 1 / (k + rank + 1)`
- 默认 k 值: 60
- 不需要额外模型，计算效率高

**Reranker Model 方法**:
- 使用交叉编码器模型
- 更准确的排序
- 需要更多计算资源

**使用示例**:
```python
# 使用 RRF
rag = RAGSystem(reranker_method="rrf")

# 使用 reranker model
rag = RAGSystem(
    reranker_method="reranker",
    reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2"
)
```

---

### ✅ 8. 回答：基于检索结果生成回答

**实现方式**: 
- 如果有 OpenAI API，使用 GPT 模型生成回答
- 如果没有 API，使用简单的基于检索结果的回答

**代码位置**: `rag_system.py` - `RAGSystem.generate_answer()`

**回答流程**:
1. 从检索结果中提取前 5 个最相关的文档
2. 构建上下文（包含来源和页码信息）
3. 使用 LLM 生成回答（如果有 API）
4. 或使用简单的基于检索结果的回答

**使用示例**:
```python
result = rag.query("What is this document about?", top_k=5)
print(result['answer'])
```

---

## 系统架构

```
RAG 系统
├── PDF 处理
│   ├── 文本提取 (PyMuPDF, pdfplumber, PyPDF2)
│   ├── 图片提取 (PyMuPDF)
│   └── 表格提取 (pdfplumber)
├── 内容切分
│   └── RecursiveCharacterTextSplitter
├── 向量化
│   └── SentenceTransformer
├── 索引
│   └── Elasticsearch (dense_vector)
├── 检索
│   ├── 向量搜索 (cosine similarity)
│   └── BM25 搜索
├── 重排序
│   ├── RRF (Reciprocal Rank Fusion)
│   └── Reranker Model
└── 回答生成
    ├── OpenAI API (可选)
    └── 简单回答生成
```

## 文件结构

```
AI-native/
├── rag_system.py              # RAG 系统主程序
├── rag_example.py             # 使用示例
├── requirements.txt           # Python 依赖
├── RAG_README.md             # 完整使用文档
├── RAG_QUICK_START.md        # 快速启动指南
├── RAG_IMPLEMENTATION.md     # 实现文档（本文件）
└── ../elastic-start-local/       # Elasticsearch 本地部署
    ├── docker-compose.yml
    ├── start.sh
    ├── stop.sh
    └── .env
```

## 技术栈

- **PDF 处理**: PyPDF2, pdfplumber, PyMuPDF
- **文本处理**: LangChain
- **向量化**: sentence-transformers
- **搜索引擎**: Elasticsearch 8.11+
- **重排序**: RRF, transformers (reranker models)
- **LLM**: OpenAI API (可选)

## 使用流程

1. **启动 Elasticsearch**
   ```bash
   cd ../elastic-start-local
   ./start.sh
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **初始化 RAG 系统**
   ```python
   from rag_system import RAGSystem
   
   rag = RAGSystem(
       es_host="localhost",
       es_port=9200,
       es_user="elastic",
       es_password="w2b9I2dq",  # 从 .env 文件获取
       index_name="rag_documents"
   )
   ```

4. **处理 PDF 文件**
   ```python
   rag.process_and_index_pdf("example.pdf")
   ```

5. **查询**
   ```python
   result = rag.query("What is this document about?", top_k=5)
   print(result['answer'])
   ```

## 测试验证

### 测试 PDF 处理
```python
from rag_system import PDFProcessor

processor = PDFProcessor()
result = processor.process_pdf("example.pdf")
print(f"文本块数: {len(result['text_chunks'])}")
print(f"图片数: {len(result['images'])}")
print(f"表格数: {len(result['tables'])}")
```

### 测试搜索
```python
rag = RAGSystem()
results = rag.search("machine learning", top_k=5)
for i, result in enumerate(results, 1):
    print(f"{i}. {result['_source']['text'][:200]}...")
```

### 测试完整流程
```python
rag = RAGSystem()
rag.process_and_index_pdf("example.pdf")
result = rag.query("What is the main topic?", top_k=5)
print(result['answer'])
```

## 性能优化建议

1. **批量处理**: 使用批量索引提高效率
2. **模型选择**: 根据需要选择合适的模型大小
3. **块大小**: 根据文档特性调整块大小
4. **缓存**: 缓存向量结果避免重复计算
5. **并行处理**: 使用多线程处理多个 PDF 文件

## 总结

✅ 所有作业要求均已实现：
1. ✅ 在本地部署 Elasticsearch
2. ✅ PDF 处理：提取文本、图片和表格
3. ✅ 内容切分：将内容拆分成可检索的单元
4. ✅ 向量化：为文本生成向量
5. ✅ 索引：将内容与向量一起存储到 Elasticsearch
6. ✅ 检索：支持混合搜索（hybrid search）
7. ✅ 重排序：应用 RRF 或 reranker model 做最终排序
8. ✅ 回答：基于检索结果生成回答

系统已完整实现，可以直接使用！

