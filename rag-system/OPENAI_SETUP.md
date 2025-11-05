# OpenAI API 配置指南

本指南说明如何在 RAG 系统中配置和使用 OpenAI API 来生成更好的回答。

## 前提条件

1. **OpenAI API Key**: 需要有效的 OpenAI API 密钥
2. **已安装依赖**: 确保已安装 `openai` 包（已在 `requirements.txt` 中）

## 配置步骤

### 方法 1: 使用环境变量（推荐）

#### macOS / Linux

```bash
# 在终端中设置环境变量
export OPENAI_API_KEY="your-api-key-here"

# 或者添加到 ~/.bashrc 或 ~/.zshrc 以永久保存
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

#### Windows

```cmd
# 在命令提示符中设置环境变量
set OPENAI_API_KEY=your-api-key-here

# 或者在 PowerShell 中
$env:OPENAI_API_KEY="your-api-key-here"
```

### 方法 2: 在代码中直接设置（不推荐用于生产环境）

修改 `rag_system.py` 中的初始化代码：

```python
# 在 RAGSystem.__init__ 方法中
self.llm_client = OpenAI(api_key="your-api-key-here")
```

⚠️ **注意**: 不推荐在生产环境中使用此方法，因为会暴露 API 密钥。

### 方法 3: 使用 .env 文件

1. 在项目根目录创建 `.env` 文件：

```bash
cd rag-system
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

2. 安装 `python-dotenv` 包（如果还没有安装）：

```bash
pip install python-dotenv
```

3. 在代码中加载环境变量：

```python
from dotenv import load_dotenv
load_dotenv()

# 然后使用
api_key = os.getenv("OPENAI_API_KEY")
```

## 验证配置

### 方法 1: 运行测试脚本

```python
from rag_system import RAGSystem
import os

# 检查 API 密钥是否设置
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ API Key found: {api_key[:10]}...")
else:
    print("❌ API Key not found. Please set OPENAI_API_KEY environment variable.")

# 初始化 RAG 系统
rag = RAGSystem(
    es_host="localhost",
    es_port=9200,
    es_user="elastic",
    es_password="w2b9I2dq",
    index_name="rag_documents"
)

# 检查 LLM 客户端是否初始化
if rag.llm_client:
    print("✅ OpenAI client initialized successfully!")
else:
    print("❌ OpenAI client not initialized. Check your API key.")
```

### 方法 2: 运行测试查询

```python
from rag_system import RAGSystem

rag = RAGSystem(
    es_host="localhost",
    es_port=9200,
    es_user="elastic",
    es_password="w2b9I2dq",
    index_name="rag_documents"
)

# 处理 PDF（如果还没有处理）
rag.process_and_index_pdf("example.pdf")

# 查询
result = rag.query("What is this document about?", top_k=5)

# 检查回答是否使用了 OpenAI
if result['answer'] and "OpenAI" not in result['answer']:
    print("✅ Using OpenAI API for answer generation!")
    print(f"\nAnswer:\n{result['answer']}")
else:
    print("⚠️ Using simple answer generation (OpenAI API not configured)")
```

## 使用示例

### 基本使用

```python
from rag_system import RAGSystem
import os

# 确保设置了 API 密钥
# export OPENAI_API_KEY="your-api-key-here"

# 初始化 RAG 系统
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
result = rag.query("What is the main topic?", top_k=5)

print(f"Question: {result['question']}")
print(f"\nAnswer:\n{result['answer']}")
```

### 自定义模型

如果需要使用不同的 OpenAI 模型，可以修改 `rag_system.py` 中的 `generate_answer` 方法：

```python
# 在 generate_answer 方法中
response = self.llm_client.chat.completions.create(
    model="gpt-4",  # 或 "gpt-4-turbo", "gpt-3.5-turbo" 等
    messages=[
        {"role": "system", "content": "你是一个基于文档回答问题的助手。"},
        {"role": "user", "content": prompt}
    ],
    max_tokens=max_tokens,
    temperature=0.7
)
```

## 支持的模型

- **gpt-4**: 最新、最强大的模型
- **gpt-4-turbo**: 更快的 GPT-4 版本
- **gpt-3.5-turbo**: 更经济的选择（默认）

## 成本估算

OpenAI API 按使用量计费：

- **gpt-3.5-turbo**: 
  - 输入: $0.50 / 1M tokens
  - 输出: $1.50 / 1M tokens

- **gpt-4**: 
  - 输入: $30.00 / 1M tokens
  - 输出: $60.00 / 1M tokens

**估算**: 每个查询大约消耗 500-1000 tokens，取决于检索到的文档数量和回答长度。

## 故障排除

### 问题 1: API Key 未找到

**错误信息**: 
```
⚠️ OpenAI client not available: ...
```

**解决方法**:
1. 检查环境变量是否正确设置：`echo $OPENAI_API_KEY`
2. 确保在运行 Python 脚本之前设置了环境变量
3. 检查 API 密钥格式是否正确（应该以 `sk-` 开头）

### 问题 2: API 调用失败

**错误信息**:
```
Error generating answer with OpenAI: ...
```

**可能原因**:
1. API 密钥无效或过期
2. 账户余额不足
3. 网络连接问题
4. API 速率限制

**解决方法**:
1. 验证 API 密钥：https://platform.openai.com/api-keys
2. 检查账户余额：https://platform.openai.com/account/billing
3. 检查网络连接
4. 等待一段时间后重试（如果遇到速率限制）

### 问题 3: 模型不可用

**错误信息**:
```
Model not found: gpt-4
```

**解决方法**:
1. 检查模型名称是否正确
2. 确认您的账户有权访问该模型（某些模型可能需要付费账户）
3. 使用 `gpt-3.5-turbo` 作为替代

## 最佳实践

1. **安全存储 API 密钥**: 使用环境变量，不要将密钥硬编码到代码中
2. **设置使用限制**: 在 OpenAI 账户中设置使用限制以避免意外费用
3. **监控使用量**: 定期检查 API 使用情况
4. **错误处理**: 确保代码有适当的错误处理，当 API 不可用时回退到简单回答
5. **缓存**: 对于重复查询，考虑缓存结果以减少 API 调用

## 与简单回答的对比

### 使用 OpenAI API
- ✅ 更自然、更流畅的回答
- ✅ 更好的上下文理解
- ✅ 可以处理复杂问题
- ❌ 需要 API 密钥
- ❌ 产生费用
- ❌ 需要网络连接

### 使用简单回答（默认）
- ✅ 无需 API 密钥
- ✅ 完全免费
- ✅ 无需网络连接（除了 Elasticsearch）
- ❌ 回答质量较低
- ❌ 只是简单的文本拼接

## 获取 OpenAI API Key

1. 访问 https://platform.openai.com/
2. 注册或登录账户
3. 导航到 API Keys 页面：https://platform.openai.com/api-keys
4. 点击 "Create new secret key"
5. 复制生成的密钥（只会显示一次）
6. 设置环境变量：`export OPENAI_API_KEY="sk-..."`

## 更多信息

- OpenAI API 文档: https://platform.openai.com/docs
- OpenAI Python SDK: https://github.com/openai/openai-python
- 定价信息: https://openai.com/pricing

