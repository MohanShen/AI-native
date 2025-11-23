"""
Excel文件预处理模块
将复杂Excel表格重塑为二维表
"""
import pandas as pd
import os
from typing import Dict, List, Tuple, Optional
import json


class ExcelPreprocessor:
    """Excel文件预处理器"""
    
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        """
        初始化预处理器
        
        Args:
            knowledge_base_path: 知识库路径，包含Excel文件
        """
        self.knowledge_base_path = knowledge_base_path
        self.processed_files: Dict[str, pd.DataFrame] = {}
        self.file_metadata: Dict[str, Dict] = {}
        
        # 确保知识库目录存在
        os.makedirs(knowledge_base_path, exist_ok=True)
    
    def load_excel_file(self, file_path: str) -> pd.DataFrame:
        """
        加载Excel文件并重塑为二维表
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            处理后的DataFrame
        """
        try:
            # 尝试读取所有sheet
            excel_file = pd.ExcelFile(file_path)
            sheets = excel_file.sheet_names
            
            # 如果只有一个sheet，直接读取
            if len(sheets) == 1:
                df = pd.read_excel(file_path, sheet_name=sheets[0])
            else:
                # 多个sheet时，尝试找到数据最多的sheet
                max_rows = 0
                best_sheet = sheets[0]
                for sheet in sheets:
                    temp_df = pd.read_excel(file_path, sheet_name=sheet)
                    if len(temp_df) > max_rows:
                        max_rows = len(temp_df)
                        best_sheet = sheet
                df = pd.read_excel(file_path, sheet_name=best_sheet)
            
            # 重塑为二维表：清理空行空列，重置索引
            df = self._reshape_to_2d(df)
            
            # 存储处理后的数据
            file_name = os.path.basename(file_path)
            self.processed_files[file_name] = df
            
            # 存储元数据
            self.file_metadata[file_name] = {
                'path': file_path,
                'columns': list(df.columns),
                'shape': df.shape,
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            return df
            
        except Exception as e:
            raise Exception(f"加载Excel文件失败: {str(e)}")
    
    def _reshape_to_2d(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将DataFrame重塑为标准的二维表
        
        Args:
            df: 原始DataFrame
            
        Returns:
            重塑后的DataFrame
        """
        # 删除完全为空的行和列
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        # 如果第一行看起来像列名，使用它作为列名
        if len(df) > 0:
            first_row = df.iloc[0]
            # 检查第一行是否包含字符串类型的值（可能是列名）
            if first_row.dtype == 'object' or any(isinstance(val, str) for val in first_row.values):
                # 检查是否有重复的列名
                if len(set(first_row.values)) == len(first_row.values):
                    df.columns = first_row.values
                    df = df.iloc[1:].reset_index(drop=True)
        
        # 清理列名：去除空格，处理特殊字符
        df.columns = [str(col).strip() for col in df.columns]
        
        # 确保列名唯一
        df.columns = self._make_unique_columns(df.columns)
        
        return df
    
    def _make_unique_columns(self, columns: List) -> List:
        """确保列名唯一"""
        seen = {}
        result = []
        for col in columns:
            if col in seen:
                seen[col] += 1
                result.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                result.append(col)
        return result
    
    def load_all_files(self) -> Dict[str, pd.DataFrame]:
        """
        加载知识库中的所有Excel文件
        
        Returns:
            文件名到DataFrame的映射
        """
        if not os.path.exists(self.knowledge_base_path):
            return {}
        
        excel_files = [f for f in os.listdir(self.knowledge_base_path) 
                      if f.endswith(('.xlsx', '.xls'))]
        
        for file in excel_files:
            file_path = os.path.join(self.knowledge_base_path, file)
            try:
                self.load_excel_file(file_path)
            except Exception as e:
                print(f"警告: 无法加载文件 {file}: {str(e)}")
        
        return self.processed_files
    
    def get_file_info(self, file_name: str) -> Optional[Dict]:
        """获取文件信息"""
        return self.file_metadata.get(file_name)
    
    def get_all_files_info(self) -> Dict[str, Dict]:
        """获取所有文件的信息"""
        return self.file_metadata
    
    def search_files_by_keywords(self, keywords: List[str]) -> List[str]:
        """
        根据关键词搜索相关文件
        
        Args:
            keywords: 关键词列表
            
        Returns:
            匹配的文件名列表
        """
        matching_files = []
        keywords_lower = [k.lower() for k in keywords]
        
        for file_name, metadata in self.file_metadata.items():
            # 检查文件名
            file_lower = file_name.lower()
            if any(kw in file_lower for kw in keywords_lower):
                matching_files.append(file_name)
                continue
            
            # 检查列名
            columns = [str(col).lower() for col in metadata['columns']]
            if any(kw in ' '.join(columns) for kw in keywords_lower):
                matching_files.append(file_name)
        
        return matching_files

