"""
代码生成模块
根据用户意图自动生成Python分析代码
"""
from typing import Dict, List
import pandas as pd


class CodeGenerator:
    """代码生成器"""
    
    def __init__(self):
        """初始化代码生成器"""
        self.used_columns = []  # 追踪使用的列
    
    def generate_code(self, intent: Dict, file_path: str, df: pd.DataFrame) -> str:
        """
        根据意图生成Python代码
        
        Args:
            intent: 解析后的意图字典
            file_path: Excel文件路径
            df: 数据DataFrame
            
        Returns:
            生成的Python代码字符串
        """
        intent_type = intent.get('intent', 'statistics')
        target_columns = intent.get('target_columns', [])
        operation = intent.get('operation', '数据分析')
        
        # 重置使用的列
        self.used_columns = []
        
        # 根据意图类型生成代码
        if intent_type == 'sum':
            code = self._generate_sum_code(df, target_columns)
        elif intent_type == 'group':
            code = self._generate_group_code(df, target_columns)
        elif intent_type == 'trend':
            code = self._generate_trend_code(df, target_columns)
        elif intent_type == 'sort':
            code = self._generate_sort_code(df, target_columns)
        elif intent_type == 'filter':
            code = self._generate_filter_code(df, target_columns)
        elif intent_type == 'correlation':
            code = self._generate_correlation_code(df, target_columns)
        elif intent_type == 'visualization':
            code = self._generate_visualization_code(df, target_columns)
        else:
            code = self._generate_statistics_code(df, target_columns)
        
        return code
    
    def _generate_sum_code(self, df: pd.DataFrame, columns: List[str]) -> str:
        """生成求和代码"""
        numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])] if columns else []
        if not numeric_cols:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()[:3]
        
        self.used_columns = numeric_cols
        
        cols_str = str(numeric_cols)
        file_path = df.attrs.get('file_path', 'data.xlsx')
        code = f"""# 求和分析
import pandas as pd
import numpy as np

# 读取数据
df = pd.read_excel(r'{file_path}')

# 对数值列求和
sum_result = df[{cols_str}].sum()

print("=" * 50)
print("求和结果:")
print("=" * 50)
print(sum_result)
print("\\n")

# 创建结果字典
result = {{
    'type': 'sum',
    'columns': {cols_str},
    'values': sum_result.to_dict(),
    'summary': f"总计: {{sum_result.sum():.2f}}"
}}
"""
        return code
    
    def _generate_group_code(self, df: pd.DataFrame, columns: List[str]) -> str:
        """生成分组代码"""
        # 尝试找到分组列和聚合列
        group_cols = []
        agg_cols = []
        
        for col in columns:
            if df[col].dtype == 'object' or df[col].nunique() < len(df) * 0.5:
                group_cols.append(col)
            else:
                agg_cols.append(col)
        
        if not group_cols:
            # 如果没有明确的分组列，使用第一个非数值列
            object_cols = df.select_dtypes(include=['object']).columns.tolist()
            group_cols = object_cols[:1] if object_cols else []
        
        if not agg_cols:
            # 使用数值列进行聚合
            agg_cols = df.select_dtypes(include=['number']).columns.tolist()[:3]
        
        self.used_columns = group_cols + agg_cols
        
        group_cols_str = str(group_cols)
        agg_cols_str = str(agg_cols)
        file_path = df.attrs.get('file_path', 'data.xlsx')
        code = f"""# 分组分析
import pandas as pd
import numpy as np

# 读取数据
df = pd.read_excel(r'{file_path}')

# 分组聚合
group_result = df.groupby({group_cols_str})[{agg_cols_str}].agg(['sum', 'mean', 'count']).round(2)

print("=" * 50)
print("分组分析结果:")
print("=" * 50)
print(group_result)
print("\\n")

# 创建结果字典
result = {{
    'type': 'group',
    'group_by': {group_cols_str},
    'aggregate': {agg_cols_str},
    'data': group_result.to_dict(),
    'summary': f"共{{len(group_result)}}个分组"
}}
"""
        return code
    
    def _generate_trend_code(self, df: pd.DataFrame, columns: List[str]) -> str:
        """生成趋势分析代码"""
        # 查找日期列
        date_cols = []
        value_cols = []
        
        for col in columns:
            if 'date' in col.lower() or '时间' in col or '日期' in col or 'time' in col.lower():
                date_cols.append(col)
            elif pd.api.types.is_numeric_dtype(df[col]):
                value_cols.append(col)
        
        # 如果没有找到日期列，尝试转换
        if not date_cols:
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        pd.to_datetime(df[col].iloc[0])
                        date_cols.append(col)
                        break
                    except:
                        pass
        
        if not value_cols:
            value_cols = df.select_dtypes(include=['number']).columns.tolist()[:2]
        
        self.used_columns = date_cols + value_cols
        
        value_cols_str = str(value_cols)
        date_col_str = f"'{date_cols[0]}'" if date_cols else None
        file_path = df.attrs.get('file_path', 'data.xlsx')
        date_process = f"df['{date_cols[0]}'] = pd.to_datetime(df['{date_cols[0]}'])" if date_cols else "# 未找到日期列"
        date_sort = f"df = df.sort_values(by='{date_cols[0]}')" if date_cols else ""
        
        code = f"""# 趋势分析
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 读取数据
df = pd.read_excel(r'{file_path}')

# 处理日期列
{date_process}

# 按日期排序
{date_sort}

# 计算趋势
trend_data = df[{value_cols_str}].copy()
if len(trend_data) > 0:
    trend_summary = trend_data.describe()
    
    print("=" * 50)
    print("趋势分析结果:")
    print("=" * 50)
    print(trend_summary)
    print("\\n")
    
    # 创建结果字典
    result = {{
        'type': 'trend',
        'date_column': {date_col_str},
        'value_columns': {value_cols_str},
        'summary': trend_summary.to_dict(),
        'data_points': len(df)
    }}
else:
    result = {{'type': 'trend', 'error': '数据不足'}}
"""
        return code
    
    def _generate_sort_code(self, df: pd.DataFrame, columns: List[str]) -> str:
        """生成排序代码"""
        sort_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])] if columns else []
        if not sort_cols:
            sort_cols = df.select_dtypes(include=['number']).columns.tolist()[:1]
        
        self.used_columns = sort_cols
        
        file_path = df.attrs.get('file_path', 'data.xlsx')
        code = f"""# 排序分析
import pandas as pd

# 读取数据
df = pd.read_excel(r'{file_path}')

# 按列排序（降序）
sorted_df = df.sort_values(by='{sort_cols[0]}', ascending=False).head(20)

print("=" * 50)
print("排序结果（Top 20）:")
print("=" * 50)
print(sorted_df)
print("\\n")

# 创建结果字典
result = {{
    'type': 'sort',
    'sort_by': '{sort_cols[0]}',
    'top_n': 20,
    'data': sorted_df.to_dict('records')
}}
"""
        return code
    
    def _generate_filter_code(self, df: pd.DataFrame, columns: List[str]) -> str:
        """生成筛选代码"""
        filter_cols = columns[:2] if columns else df.columns[:2].tolist()
        self.used_columns = filter_cols
        
        filter_cols_str = str(filter_cols)
        file_path = df.attrs.get('file_path', 'data.xlsx')
        code = f"""# 筛选分析
import pandas as pd

# 读取数据
df = pd.read_excel(r'{file_path}')

# 筛选数据（示例：筛选非空值）
filtered_df = df.dropna(subset={filter_cols_str})

print("=" * 50)
print("筛选结果:")
print("=" * 50)
print(f"原始数据: {{len(df)}} 行")
print(f"筛选后: {{len(filtered_df)}} 行")
print("\\n")
print(filtered_df.head(20))
print("\\n")

# 创建结果字典
result = {{
    'type': 'filter',
    'filter_columns': {filter_cols_str},
    'original_count': len(df),
    'filtered_count': len(filtered_df),
    'data': filtered_df.head(20).to_dict('records')
}}
"""
        return code
    
    def _generate_correlation_code(self, df: pd.DataFrame, columns: List[str]) -> str:
        """生成相关性分析代码"""
        numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])] if columns else []
        if not numeric_cols:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) < 2:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()[:5]
        
        self.used_columns = numeric_cols
        
        numeric_cols_str = str(numeric_cols)
        file_path = df.attrs.get('file_path', 'data.xlsx')
        code = f"""# 相关性分析
import pandas as pd
import numpy as np

# 读取数据
df = pd.read_excel(r'{file_path}')

# 计算相关性矩阵
corr_matrix = df[{numeric_cols_str}].corr()

print("=" * 50)
print("相关性分析结果:")
print("=" * 50)
print(corr_matrix)
print("\\n")

# 创建结果字典
result = {{
    'type': 'correlation',
    'columns': {numeric_cols_str},
    'correlation_matrix': corr_matrix.to_dict(),
    'summary': '相关性矩阵已计算'
}}
"""
        return code
    
    def _generate_visualization_code(self, df: pd.DataFrame, columns: List[str]) -> str:
        """生成可视化代码"""
        numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])] if columns else []
        if not numeric_cols:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()[:2]
        
        self.used_columns = numeric_cols
        
        numeric_cols_str = str(numeric_cols)
        num_plots = min(len(numeric_cols), 2)
        file_path = df.attrs.get('file_path', 'data.xlsx')
        code = f"""# 可视化分析
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 读取数据
df = pd.read_excel(r'{file_path}')

# 创建图表
fig, axes = plt.subplots(1, {num_plots}, figsize=(12, 5))
if {num_plots} == 1:
    axes = [axes]

for idx, col in enumerate({numeric_cols_str}[:2]):
    axes[idx].plot(df[col].values[:100])  # 只显示前100个数据点
    axes[idx].set_title(f'{{col}} 趋势图')
    axes[idx].set_xlabel('索引')
    axes[idx].set_ylabel(col)
    axes[idx].grid(True)

plt.tight_layout()
plt.savefig('visualization_result.png', dpi=150, bbox_inches='tight')
print("图表已保存为 visualization_result.png")

# 创建结果字典
result = {{
    'type': 'visualization',
    'columns': {numeric_cols_str},
    'chart_file': 'visualization_result.png',
    'summary': f'已生成{{len({numeric_cols_str})}}个图表'
}}
"""
        return code
    
    def _generate_statistics_code(self, df: pd.DataFrame, columns: List[str]) -> str:
        """生成统计摘要代码"""
        numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])] if columns else []
        if not numeric_cols:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        self.used_columns = numeric_cols if numeric_cols else columns[:5]
        
        used_cols_str = str(self.used_columns)
        file_path = df.attrs.get('file_path', 'data.xlsx')
        code = f"""# 统计分析
import pandas as pd
import numpy as np

# 读取数据
df = pd.read_excel(r'{file_path}')

# 基本统计信息
if len({used_cols_str}) > 0:
    stats = df[{used_cols_str}].describe()
    
    print("=" * 50)
    print("统计摘要:")
    print("=" * 50)
    print(stats)
    print("\\n")
    
    # 创建结果字典
    result = {{
        'type': 'statistics',
        'columns': {used_cols_str},
        'statistics': stats.to_dict(),
        'row_count': len(df)
    }}
else:
    result = {{'type': 'statistics', 'error': '没有可分析的数值列'}}
"""
        return code
    
    def get_used_columns(self) -> List[str]:
        """获取使用的列"""
        return self.used_columns

