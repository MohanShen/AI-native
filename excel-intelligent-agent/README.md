# Excel智能分析助手

一个基于自然语言处理和OpenAI API的Excel数据分析智能体系统，能够理解用户的中文或英文查询，自动生成Python分析代码并执行，同时支持实时语音输入。

## 功能特性

### 核心功能

1. **文件预处理**
   - 自动将复杂Excel表格重塑为标准的二维表
   - 支持多sheet Excel文件，自动选择数据最多的sheet
   - 智能清理空行空列，规范化列名

2. **自然语言解析**
   - 使用OpenAI GPT模型理解用户查询意图
   - 支持中文和英文查询
   - 自动提取分析意图（求和、分组、趋势分析、排序、筛选等）
   - 智能匹配目标文件和列

3. **代码生成与执行**
   - 根据用户意图自动生成Python分析代码
   - 支持多种分析类型：
     - 求和（Sum）
     - 分组聚合（Group）
     - 趋势分析（Trend）
     - 排序（Sort）
     - 筛选（Filter）
     - 相关性分析（Correlation）
     - 可视化（Visualization）
     - 统计分析（Statistics）
   - 实时执行代码并展示结果

4. **数据追溯**
   - 自动追踪使用的数据列
   - 清晰展示分析过程中使用的所有列名
   - 提供完整的分析元数据

5. **实时语音输入**
   - WebSocket实时通信
   - 支持浏览器原生语音识别API
   - 实时显示处理状态和结果

## 系统架构

```
excel-intelligent-agent/
├── app.py                 # Flask主应用，整合所有模块
├── excel_preprocessor.py  # Excel文件预处理模块
├── nlp_parser.py          # 自然语言解析模块
├── code_generator.py      # Python代码生成模块
├── code_executor.py       # 代码执行模块
├── templates/
│   └── index.html         # 前端界面
├── knowledge_base/        # Excel文件存储目录
├── requirements.txt       # Python依赖
└── README.md             # 项目文档
```

## 安装与配置

### 1. 环境要求

- Python 3.8+
- OpenAI API密钥

### 2. 安装依赖

```bash
cd excel-intelligent-agent
pip install -r requirements.txt
```

### 3. 配置OpenAI API密钥

在启动应用后，通过Web界面输入您的OpenAI API密钥，或设置环境变量：

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 使用方法

### 1. 启动应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

### 2. 准备Excel文件

将需要分析的Excel文件放入 `knowledge_base` 目录，或通过Web界面上传。

### 3. 使用界面

1. **初始化**
   - 在"OpenAI API密钥"输入框中输入您的API密钥
   - 点击"初始化"按钮

2. **上传文件**
   - 点击上传区域或拖拽Excel文件
   - 支持 `.xlsx` 和 `.xls` 格式

3. **输入查询**
   - **文本输入**：在文本框中输入自然语言查询
     - 例如："帮我分析各地区销售趋势"
     - 例如："计算每个月的销售额总和"
     - 例如："按地区分组统计销售数据"
   
   - **语音输入**：点击麦克风按钮开始录音
     - 支持中文语音识别
     - 识别结果自动填入查询框

4. **查看结果**
   - 分析意图：显示系统理解的分析类型和目标
   - 生成的代码：展示自动生成的Python代码
   - 执行结果：显示代码执行后的输出
   - 使用的数据列：列出分析过程中使用的所有列

## 使用示例

### 示例1：销售趋势分析

**查询**："帮我分析各地区销售趋势"

**系统行为**：
1. 识别意图：趋势分析
2. 选择包含"地区"和"销售"相关列的文件
3. 生成趋势分析代码
4. 执行并展示结果

### 示例2：分组统计

**查询**："按地区分组统计销售额"

**系统行为**：
1. 识别意图：分组聚合
2. 选择"地区"作为分组列，"销售额"作为聚合列
3. 生成分组统计代码
4. 展示分组结果

### 示例3：排序分析

**查询**："找出销售额最高的20个产品"

**系统行为**：
1. 识别意图：排序
2. 按"销售额"列降序排序
3. 取前20条记录
4. 展示排序结果

## API接口

### REST API

- `POST /api/initialize` - 初始化API密钥
- `POST /api/query` - 发送查询请求
- `POST /api/upload` - 上传Excel文件
- `GET /api/files` - 获取文件列表

### WebSocket事件

- `voice_query` - 发送语音查询
- `processing` - 处理中状态
- `intent_parsed` - 意图解析完成
- `code_generated` - 代码生成完成
- `execution_complete` - 执行完成
- `error` - 错误信息

## 技术栈

- **后端**：
  - Flask - Web框架
  - Flask-SocketIO - WebSocket支持
  - OpenAI API - 自然语言理解
  - Pandas - 数据处理
  - NumPy - 数值计算
  - Matplotlib - 数据可视化

- **前端**：
  - HTML5/CSS3 - 界面
  - JavaScript - 交互逻辑
  - WebSocket API - 实时通信
  - Web Speech API - 语音识别

## 注意事项

1. **API密钥安全**：请妥善保管您的OpenAI API密钥，不要提交到版本控制系统
2. **文件大小**：建议Excel文件大小不超过50MB
3. **浏览器兼容**：语音识别功能需要支持Web Speech API的现代浏览器（Chrome、Edge等）
4. **代码执行安全**：系统会执行生成的Python代码，请确保文件来源可信

## 故障排除

### 问题1：无法连接WebSocket

- 检查防火墙设置
- 确保端口5000未被占用
- 检查浏览器控制台错误信息

### 问题2：语音识别不工作

- 确保使用支持Web Speech API的浏览器
- 检查浏览器权限设置（允许麦克风访问）
- 尝试使用HTTPS连接（某些浏览器要求）

### 问题3：代码执行失败

- 检查Excel文件格式是否正确
- 确认数据列名是否存在
- 查看错误信息中的具体提示

## 开发计划

- [ ] 支持更多分析类型
- [ ] 添加图表可视化展示
- [ ] 支持导出分析结果
- [ ] 添加分析历史记录
- [ ] 支持多文件联合分析
- [ ] 优化代码生成质量

## 许可证

MIT License

## 作者

Excel智能分析助手开发团队

## 贡献

欢迎提交Issue和Pull Request！

