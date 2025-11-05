# RAG 系统使用文档

这是一个完整的 RAG (Retrieval-Augmented Generation) 系统，能够处理任意 PDF 文件，包括提取和处理其中的文本、图片和表格。

## 功能特性

✅ **PDF 处理**: 提取文本、图片和表格
✅ **内容切分**: 将内容拆分成可检索的单元
✅ **向量化**: 为文本生成向量
✅ **索引**: 将内容与向量一起存储到 Elasticsearch
✅ **混合搜索**: 支持向量搜索和 BM25 搜索的混合搜索
✅ **重排序**: 支持 RRF (Reciprocal Rank Fusion) 或 reranker model 做最终排序
✅ **回答生成**: 基于检索结果生成回答

## 系统要求

- Python 3.8+
- Docker 和 Docker Compose（用于本地 Elasticsearch）
- 至少 8GB 可用磁盘空间（用于 Elasticsearch 和模型）

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 启动本地 Elasticsearch

```bash
cd ../elastic-start-local
./start.sh
```

这将启动 Elasticsearch 和 Kibana。默认配置：
- Elasticsearch: `http://localhost:9200`
- 用户名: `elastic`
- 密码: `changeme`（请根据实际情况修改）

### 3. 配置环境变量（可选）

如果需要使用 OpenAI API 生成回答，请设置：

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 使用方法

### 基本使用

```python
from rag_system import RAGSystem

# 初始化 RAG 系统
rag = RAGSystem(
    es_host="localhost",
    es_port=9200,
    es_user="elastic",
    es_password="changeme",  # 请根据实际情况修改
    index_name="rag_documents",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    reranker_method="rrf",
    chunk_size=500,
    chunk_overlap=50
)

# 处理 PDF 文件
rag.process_and_index_pdf("example.pdf")

# 查询
question = "What is this document about?"
result = rag.query(question, top_k=5)

print(f"问题: {result['question']}")
print(f"回答: {result['answer']}")
```

### 运行示例程序

```bash
python rag_example.py
```

### 命令行使用

```bash
python rag_system.py
```

## 功能详解

### 1. PDF 处理

系统支持多种 PDF 处理方式：
- **PyMuPDF (fitz)**: 更好的文本提取
- **pdfplumber**: 更好的布局保持和表格提取
- **PyPDF2**: 备用文本提取方法

**提取内容**:
- 文本：从 PDF 页面提取文本
- 图片：提取 PDF 中的图片并保存到 `extracted_images/` 目录
- 表格：提取表格并转换为 DataFrame 和文本格式

### 2. 内容切分

使用 `RecursiveCharacterTextSplitter` 将文本切分成可检索的单元：
- 默认块大小：500 字符
- 默认重叠：50 字符
- 支持中文和英文分隔符

### 3. 向量化

使用 `sentence-transformers` 生成文本向量：
- 默认模型：`all-MiniLM-L6-v2`（384 维）
- 支持自定义模型
- 自动处理批量编码

### 4. 索引到 Elasticsearch

将文档和向量索引到 Elasticsearch：
- 支持密集向量索引（dense vector）
- 使用余弦相似度（cosine similarity）
- 批量索引，提高效率

### 5. 混合搜索

支持两种搜索方式的混合：
- **向量搜索**: 使用余弦相似度搜索
- **BM25 搜索**: 传统的关键词搜索
- **混合**: 结合两种搜索结果，提高检索质量

### 6. 重排序

支持两种重排序方法：

#### RRF (Reciprocal Rank Fusion)
- 默认方法
- 不需要额外模型
- 计算效率高

#### Reranker Model
- 使用交叉编码器模型（如 `cross-encoder/ms-marco-MiniLM-L-6-v2`）
- 更准确的排序
- 需要更多计算资源

### 7. 回答生成

基于检索结果生成回答：
- 如果有 OpenAI API，使用 GPT 模型生成回答
- 如果没有 API，使用简单的基于检索结果的回答

## 配置参数

### RAGSystem 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `es_host` | str | "localhost" | Elasticsearch 主机 |
| `es_port` | int | 9200 | Elasticsearch 端口 |
| `es_user` | str | "elastic" | Elasticsearch 用户名 |
| `es_password` | str | "changeme" | Elasticsearch 密码 |
| `index_name` | str | "rag_documents" | 索引名称 |
| `embedding_model` | str | "sentence-transformers/all-MiniLM-L6-v2" | 嵌入模型 |
| `reranker_method` | str | "rrf" | 重排序方法 ("rrf" 或 "reranker") |
| `reranker_model` | str | None | Reranker 模型名称（可选） |
| `chunk_size` | int | 500 | 文本块大小 |
| `chunk_overlap` | int | 50 | 文本块重叠大小 |

### 方法参数

#### `process_and_index_pdf()`
- `pdf_path`: PDF 文件路径
- `extract_images`: 是否提取图片（默认：True）
- `extract_tables`: 是否提取表格（默认：True）

#### `query()`
- `question`: 查询问题
- `top_k`: 返回结果数量（默认：10）
- `generate_answer`: 是否生成回答（默认：True）

#### `search()`
- `query`: 搜索查询
- `top_k`: 返回结果数量（默认：10）
- `use_reranker`: 是否使用重排序（默认：True）

## 作业要求完成情况

✅ **在本地部署 Elasticsearch**: 使用 Docker Compose 在本地部署 Elasticsearch
✅ **PDF 处理：提取文本**: 支持多种方法提取 PDF 文本
✅ **内容切分**: 将内容拆分成可检索的单元
✅ **向量化**: 为文本生成向量
✅ **索引**: 将内容与向量一起存储到 Elasticsearch
✅ **检索：支持混合搜索**: 支持向量搜索和 BM25 搜索的混合搜索
✅ **重排序：应用 RRF 或 reranker model**: 支持 RRF 和 reranker model 两种方法
✅ **回答：基于检索结果生成回答**: 支持基于检索结果生成回答

## 使用示例

### 示例 1: 处理单个 PDF

```python
from rag_system import RAGSystem

rag = RAGSystem()
rag.process_and_index_pdf("document.pdf")
result = rag.query("What is the main topic?")
print(result['answer'])
```

### 示例 2: 处理多个 PDF

```python
rag = RAGSystem()

pdf_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
for pdf_path in pdf_files:
    rag.process_and_index_pdf(pdf_path)

result = rag.query("What are the common themes?")
print(result['answer'])
```

### 示例 3: 仅搜索，不生成回答

```python
rag = RAGSystem()
results = rag.search("machine learning", top_k=5)

for i, result in enumerate(results, 1):
    print(f"{i}. {result['_source']['text'][:200]}...")
```

### 示例 4: 使用 reranker model

```python
rag = RAGSystem(
    reranker_method="reranker",
    reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2"
)
rag.process_and_index_pdf("document.pdf")
result = rag.query("What is the conclusion?")
```

## 故障排除

### 1. Elasticsearch 连接失败

**问题**: `Cannot connect to Elasticsearch`

**解决**:
- 确保 Elasticsearch 正在运行：`cd ../elastic-start-local && ./start.sh`
- 检查端口是否正确：`curl http://localhost:9200`
- 检查用户名和密码是否正确

### 2. PDF 处理失败

**问题**: `PDF extraction failed`

**解决**:
- 确保 PDF 文件路径正确
- 检查 PDF 文件是否损坏
- 尝试使用其他 PDF 文件

### 3. 模型下载失败

**问题**: `Model download failed`

**解决**:
- 检查网络连接
- 使用镜像源（如果在中国）
- 手动下载模型并指定路径

### 4. 内存不足

**问题**: `Out of memory`

**解决**:
- 减小 `chunk_size`
- 减少批量处理的数量
- 使用更小的模型

## 性能优化

1. **批量处理**: 使用批量索引提高效率
2. **模型选择**: 根据需要选择合适的模型大小
3. **块大小**: 根据文档特性调整块大小
4. **缓存**: 缓存向量结果避免重复计算

## 技术栈

- **PDF 处理**: PyPDF2, pdfplumber, PyMuPDF
- **文本处理**: LangChain
- **向量化**: sentence-transformers
- **搜索引擎**: Elasticsearch
- **重排序**: RRF, transformers (reranker models)
- **LLM**: OpenAI API (可选)

## 许可证

本项目仅用于教育学习目的。

