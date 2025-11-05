# OpenAI API 快速设置指南

## 快速开始

### 1. 获取 OpenAI API Key

访问 https://platform.openai.com/api-keys 并创建新的 API 密钥。

### 2. 设置环境变量

**macOS / Linux:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

**永久设置（macOS / Linux）:**
```bash
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. 验证配置

```bash
cd rag-system
source ../venv/bin/activate
python test_openai.py
```

### 4. 使用

```python
from rag_system import RAGSystem

# 初始化 RAG 系统（会自动检测 OPENAI_API_KEY）
rag = RAGSystem(
    es_host="localhost",
    es_port=9200,
    es_user="elastic",
    es_password="w2b9I2dq",
    index_name="rag_documents"
)

# 处理 PDF
rag.process_and_index_pdf("example.pdf")

# 查询（会自动使用 OpenAI API 如果配置了）
result = rag.query("What is this document about?", top_k=5)
print(result['answer'])
```

## 需要什么？

1. **OpenAI API Key** - 从 https://platform.openai.com/api-keys 获取
2. **环境变量** - 设置 `OPENAI_API_KEY` 环境变量
3. **已安装依赖** - `openai` 包已在 `requirements.txt` 中

## 详细文档

查看 `OPENAI_SETUP.md` 获取完整配置指南和故障排除。

