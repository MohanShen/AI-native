"""
代码生成模块 - 使用LLM生成Python数据分析代码
"""
import logging
import os
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class CodeGenerator:
    """使用OpenAI生成Python代码进行Excel数据分析"""
    
    def __init__(self, openai_client=None):
        """
        初始化代码生成器
        
        Args:
            openai_client: OpenAI客户端（可选，如果为None则使用规则生成）
        """
        self.openai_client = openai_client
        self.used_columns = []
    
    def generate_code(self, intent: Dict, file_path: str, df: pd.DataFrame) -> str:
        """
        生成Python代码
        
        Args:
            intent: 解析后的意图字典
            file_path: Excel文件路径
            df: 预处理后的DataFrame
            
        Returns:
            生成的Python代码字符串
        """
        if self.openai_client:
            # 使用LLM生成代码
            return self._generate_code_with_llm(intent, file_path, df)
        else:
            # 回退到规则生成（保持向后兼容）
            logger.warning("OpenAI客户端未设置，使用规则生成代码")
            return self._generate_code_with_rules(intent, file_path, df)
    
    def _generate_code_with_llm(self, intent: Dict, file_path: str, df: pd.DataFrame) -> str:
        """使用LLM生成代码"""
        try:
            # 构建schema信息
            schema = self._build_schema(df, file_path)
            
            # 构建提示词
            prompt = self._build_prompt(intent, file_path, schema)
            
            # 调用OpenAI API
            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            code = response.choices[0].message.content.strip()
            code = self._format_code_response(code)
            
            # 从生成的代码中提取使用的列名（简单启发式方法）
            self._extract_used_columns_from_code(code, df)
            
            return code
            
        except Exception as e:
            logger.error(f"LLM代码生成失败: {e}", exc_info=True)
            logger.info("回退到规则生成")
            return self._generate_code_with_rules(intent, file_path, df)
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return '''You are an expert Python data analyst specializing in pandas. Generate clean, executable Python code for Excel data analysis.

**CRITICAL: File Path Usage**
- The variable `file_path` is ALREADY DEFINED in the execution context
- ALWAYS use `file_path` variable to read Excel files: `df = pd.read_excel(file_path, ...)`
- NEVER hardcode file paths in your generated code
- The file path shown in the prompt is for reference only - use the variable

**Excel Data Processing Rules**

1. Basic Code Structure Requirements:
   1.1 Necessary imports and settings:
   ```python
   import pandas as pd
   import numpy as np
   import warnings
   warnings.simplefilter(action='ignore', category=Warning)
   pd.set_option('display.max_columns', None)
   pd.set_option('display.max_rows', None)
   pd.set_option('display.width', None)
   pd.set_option('display.max_colwidth', None)
   ```
   1.2 Output format requirements:
   - Output only code, no additional explanations
   - Do not include Markdown code block markers (```python or ```)
   - Output pure Python code as plain text
   - All results must be printed to console using "print"
   - Create a result dictionary with 'type', 'answer', and 'data' fields

2. Data Query and Processing Requirements:
   2.1 Multi-row data processing:
   - Before generating code, determine if user wants data in a "range" or "specific value" based on Excel structure
   - When sorting results, explicitly specify `ascending=False` (descending) or `True` (ascending), avoid default sorting
   
   2.2 Key field processing:
   - Time fields must be converted using `pd.to_datetime(..., errors='coerce').dt.normalize()` and extract year/month/day components for comparison
   - For identifier fields, use `.astype(str)` for string conversion to avoid format issues (leading zeros, scientific notation, precision truncation)
   - Numeric fields must be converted using `pd.to_numeric(..., errors='coerce')` to avoid string comparison
   - For numerical calculations (sum, comparison, aggregation, sorting), use "pd.to_numeric(data, errors='coerce')" to convert to numeric type before calculation, ignoring unconvertible values
   
   2.3 String matching and filtering (CRITICAL for Chinese and mixed-language data):
   - When filtering by identifier values (e.g., "18号", "motor 18", "第18号"), use flexible matching:
     * First convert the identifier column to string: `df['column'].astype(str)`
     * Strip whitespace: `.str.strip()`
     * Use flexible matching patterns:
       - For exact match: `df[df['column'].astype(str).str.strip() == 'value']`
       - For partial match: `df[df['column'].astype(str).str.strip().str.contains('value', na=False, regex=False)]`
     * When the question mentions a number (e.g., "18号", "第18号"), extract just the numeric part and match flexibly
   - Always check column existence before filtering: `if 'column_name' in df.columns:`
   - Handle column names with spaces or special characters exactly as they appear in the schema
   - When column names have multiple spaces, preserve them exactly
   
   2.4 Data cleaning and processing:
   - Keep special characters in column names (underscores, multiple spaces) unchanged
   - Normalize whitespace in data values but preserve column name structure
   
   2.5 Output specifications:
   - Format and print line by line for batch output
   - For queries asking "how much" or "what is the total", calculate the sum/aggregation
   - When filtering and then calculating (e.g., "苹果的销售额是多少"), first filter, then sum the numeric column

3. Code Robustness Requirements:
   3.1 Exception handling:
   - Code must include exception handling, wrap file operations and data processing logic in try-except
   - Catch common exceptions like FileNotFoundError, KeyError and provide friendly messages
   - When printing exceptions, include specific error information: print(f"Error details: {str(e)}")
   
   3.2 Data validation:
   - Check df.empty immediately after reading data to avoid operating on empty DataFrame
   - For key filter fields, first confirm existence with `if 'column_name' in df.columns:`
   - If a filter returns empty results, print a helpful message showing what was searched and what columns/values are available
   - If file has multiple sheets, generate code for each qualifying sheet
   
   3.3 Column name matching:
   - Use exact column names as provided in the schema (preserve spaces, special characters)
   - When filtering, always verify the column exists before using it
   - If a column name in the question doesn't match exactly, try to find the closest match or list available columns

4. Naming Conventions:
   4.1 Variable and function naming:
   - Avoid using symbols like # in function or variable names
   - Avoid using Chinese characters in function or variable names
   - Use meaningful English variable names like filtered_df, result_data, etc.

5. Problem Decomposition Principles:
   5.1 Analyze user needs:
   - First parse key dimensions of user's question
   - Convert natural language descriptions to corresponding pandas operation chains
   - For questions like "苹果的销售额是多少" (what is the sales amount of apples), you should:
     * Filter rows where product name contains "苹果"
     * Then sum the sales amount column
     * Return the total as the answer
   
   5.2 Defensive programming:
   - Assume raw data may have missing values, type confusion, or special characters

6. Result Dictionary Format:
   - Always create a result dictionary at the end with this structure:
   ```python
   result = {
       'type': 'filter_sum' or 'filter' or 'sum' or 'group' etc.,
       'answer': 'The answer to the question',
       'data': filtered_df.to_dict('records') if applicable,
       # Additional fields based on operation type
   }
   ```
   - For filter+sum operations, include: 'filter_column', 'filter_value', 'sum_column', 'total_sales'
   - Print the result dictionary at the end

7. Chart Generation:
   - If user's question indicates need for a chart, use "import plotly.graph_objects as go" to generate an interactive local HTML page
   - Use go.Figure with mode parameter value "lines+markers+text"
   - fig.update_layout must include title (centered), xaxis_title, yaxis_title
   - Sort X-axis data from small to large before plotting
   - ALWAYS print the filename after saving: print(f"Chart saved to: {filename}") or print("Chart saved to: filename.html")
   - Example: fig.write_html('chart.html'); print("Chart saved to: chart.html")
'''
    
    def _build_schema(self, df: pd.DataFrame, file_path: str) -> Dict:
        """从DataFrame构建schema信息"""
        schema = {
            'file_name': os.path.basename(file_path),
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'headers': list(df.columns),
            'column_types': {}
        }
        
        # 获取列类型信息
        for col in df.columns:
            dtype = df[col].dtype
            readable_type = self._get_readable_type(dtype)
            sample_values = df[col].dropna().head(3).tolist()
            
            schema['column_types'][col] = {
                'dtype': str(dtype),
                'readable_type': readable_type,
                'sample_values': sample_values
            }
        
        # 获取前5行和后5行数据
        if len(df) > 0:
            schema['first_5_rows'] = df.head(5).to_dict('records')
            schema['last_5_rows'] = df.tail(5).to_dict('records')
        else:
            schema['first_5_rows'] = []
            schema['last_5_rows'] = []
        
        return schema
    
    def _get_readable_type(self, dtype) -> str:
        """获取可读的数据类型"""
        if pd.api.types.is_integer_dtype(dtype):
            return 'integer'
        elif pd.api.types.is_float_dtype(dtype):
            return 'float'
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return 'datetime'
        elif pd.api.types.is_bool_dtype(dtype):
            return 'boolean'
        else:
            return 'string'
    
    def _build_prompt(self, intent: Dict, file_path: str, schema: Dict) -> str:
        """构建提示词"""
        question = intent.get('original_query', intent.get('operation', '数据分析'))
        intent_type = intent.get('intent', 'general_analysis')
        target_columns = intent.get('target_columns', [])
        keywords = intent.get('keywords', [])
        
        schema_lines = []
        schema_lines.append(f"File: {schema.get('file_name', 'unknown')}")
        schema_lines.append(f"Total rows: {schema.get('total_rows', 0)}, Total columns: {schema.get('total_columns', 0)}")
        schema_lines.append("")
        schema_lines.append("Columns with data types:")
        for header in schema.get('headers', []):
            col_type = schema.get('column_types', {}).get(header, {})
            readable_type = col_type.get('readable_type', 'unknown')
            schema_lines.append(f"  - {header} ({readable_type})")
        
        if schema.get('first_5_rows'):
            schema_lines.append("")
            schema_lines.append("First 5 rows (sample data):")
            for i, row in enumerate(schema['first_5_rows'], 1):
                row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                schema_lines.append(f"  Row {i}: {row_str}")
        
        if schema.get('last_5_rows'):
            schema_lines.append("")
            schema_lines.append("Last 5 rows (sample data):")
            for i, row in enumerate(schema['last_5_rows'], 1):
                row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                schema_lines.append(f"  Row {i}: {row_str}")
        
        schema_text = "\n".join(schema_lines)
        
        prompt = f'''User question: {question}

Target Excel file: {file_path}
File name: {os.path.basename(file_path)}

Analysis intent: {intent_type}
Target columns: {target_columns}
Keywords: {keywords}

Table Schema (from reconstructed table):
{schema_text}

Please generate Python code to:
1. Read the Excel file using the variable `file_path` (already defined in the execution context)
2. Perform the analysis requested in the question
3. Print the results
4. Create a result dictionary with the answer

Important:
- ALWAYS use the variable `file_path` to read the Excel file: `df = pd.read_excel(file_path, ...)`
- Do NOT hardcode the file path - use the `file_path` variable that is already available
- The file path shown above ({file_path}) is for reference only - use the variable in your code
- The table has been reconstructed and cleaned - use the column names EXACTLY as shown in the schema (preserve spaces, special characters)
- Handle the columns: {target_columns if target_columns else 'all columns'}
- Pay attention to data types: {', '.join([f"{col}: {schema.get('column_types', {}).get(col, {}).get('readable_type', 'unknown')}" for col in schema.get('headers', [])[:10]])}
- For filtering by identifier values (especially Chinese text with numbers like "18号", "第18号"):
  * Convert identifier columns to string: `.astype(str)`
  * Strip whitespace: `.str.strip()`
  * Use flexible matching (try full match first, then partial match)
  * If no results found, print available values from that column for debugging
- Always verify column existence before filtering: `if 'column_name' in df.columns:`
- Include proper error handling with helpful messages
- Print all results clearly
- For questions asking "how much" or "what is the total/sum" (e.g., "苹果的销售额是多少"), you should:
  * First filter the data based on the condition (e.g., product name contains "苹果")
  * Then calculate the sum of the numeric column (e.g., sales amount)
  * Return the total as the answer in the result dictionary
- If charts are needed, generate interactive HTML files using plotly and save them to the current working directory
- IMPORTANT: After saving a chart with fig.write_html(), always print the filename: print(f"Chart saved to: filename.html")
- IMPORTANT: Always create a result dictionary at the end with 'type', 'answer', and 'data' fields'''
        
        return prompt
    
    def _format_code_response(self, code: str) -> str:
        """清理和格式化生成的代码"""
        code = code.strip()
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        return code.strip()
    
    def _extract_used_columns_from_code(self, code: str, df: pd.DataFrame) -> None:
        """从生成的代码中提取使用的列名（简单启发式方法）"""
        used_cols = []
        available_cols = list(df.columns)
        
        # 查找代码中出现的列名
        for col in available_cols:
            # 检查列名是否在代码中出现（作为字符串字面量）
            if f"'{col}'" in code or f'"{col}"' in code or f"df['{col}']" in code or f'df["{col}"]' in code:
                used_cols.append(col)
        
        self.used_columns = used_cols
    
    def get_used_columns(self) -> List[str]:
        """获取使用的列名"""
        return self.used_columns
    
    def _generate_code_with_rules(self, intent: Dict, file_path: str, df: pd.DataFrame) -> str:
        """使用规则生成代码（向后兼容的简单实现）"""
        # 这是一个简化的规则生成器，仅作为后备方案
        intent_type = intent.get('intent', 'statistics')
        target_columns = intent.get('target_columns', [])
        keywords = intent.get('keywords', [])
        
        # 简单的规则生成逻辑
        code = f"""# 数据分析
import pandas as pd
import numpy as np

# 读取数据
df = pd.read_excel(file_path)

# 基本统计
print("数据形状:", df.shape)
print("\\n列名:", list(df.columns))
print("\\n前5行数据:")
print(df.head())

# 创建结果字典
result = {{
    'type': '{intent_type}',
    'answer': '数据分析完成',
    'data': df.head(10).to_dict('records')
}}
"""
        return code
