"""
Excel文件预处理模块
将复杂Excel表格重塑为二维表，支持复杂表头结构
"""
import hashlib
import json
import logging
import os
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np
import openpyxl
from openpyxl.utils import get_column_letter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExcelPreprocessor:
    """Excel文件预处理器，支持复杂表头结构"""
    
    def __init__(self, knowledge_base_path: str = "knowledge_base", openai_client=None, use_llm_analysis: bool = True):
        """
        初始化预处理器
        
        Args:
            knowledge_base_path: 知识库路径，包含Excel文件
            openai_client: OpenAI客户端（用于LLM分析表头结构）
            use_llm_analysis: 是否使用LLM分析复杂表头（默认True）
        """
        self.knowledge_base_path = knowledge_base_path
        self.openai_client = openai_client
        self.use_llm_analysis = use_llm_analysis
        self.processed_files: Dict[str, pd.DataFrame] = {}
        self.file_metadata: Dict[str, Dict] = {}
        
        # 临时目录用于存储重建的文件
        self.temp_dir = Path(knowledge_base_path) / ".reconstructed"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 确保知识库目录存在
        os.makedirs(knowledge_base_path, exist_ok=True)
    
    def load_excel_file(self, file_path: str) -> pd.DataFrame:
        """
        加载Excel文件并重塑为二维表
        支持复杂表头结构的处理
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            处理后的DataFrame
        """
        try:
            file_name = os.path.basename(file_path)
            
            # 实际用于分析的数据文件路径（默认是原始文件）
            actual_data_path = file_path
            
            # 如果使用LLM分析且OpenAI客户端可用，使用复杂处理流程
            if self.use_llm_analysis and self.openai_client:
                try:
                    logger.info(f"使用LLM分析处理文件: {file_name}")
                    processed_file = self._process_with_llm(file_path)
                    if processed_file and os.path.exists(processed_file):
                        # 从处理后的文件读取
                        df = self._read_processed_file(processed_file)
                        # 对于后续分析和代码执行，应使用重建后的文件路径
                        actual_data_path = processed_file
                    else:
                        # 回退到简单处理
                        logger.warning(f"LLM处理失败，使用简单处理: {file_name}")
                        df = self._simple_load(file_path)
                except Exception as e:
                    logger.warning(f"LLM处理出错，使用简单处理: {file_name}, 错误: {str(e)}")
                    df = self._simple_load(file_path)
            else:
                # 使用简单处理
                df = self._simple_load(file_path)
            
            # 重塑为二维表：清理空行空列，重置索引
            df = self._reshape_to_2d(df)
            
            # 打印预处理后的表头信息
            self._print_preprocessed_headers(file_name, df)
            
            # 存储处理后的数据
            self.processed_files[file_name] = df
            # 将实际用于分析的数据文件路径放入DataFrame属性，作为额外保险
            df.attrs['file_path'] = actual_data_path
            
            # 存储元数据
            self.file_metadata[file_name] = {
                # 这里的path用于后续代码执行，应指向实际的数据文件（重建后文件）
                'path': actual_data_path,
                'columns': list(df.columns),
                'shape': df.shape,
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            return df
            
        except Exception as e:
            raise Exception(f"加载Excel文件失败: {str(e)}")
    
    def _simple_load(self, file_path: str) -> pd.DataFrame:
        """
        简单加载方法（原有逻辑）
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            DataFrame
        """
        excel_file = pd.ExcelFile(file_path)
        sheets = excel_file.sheet_names
        
        # 如果只有一个sheet，直接读取（header=0表示第一行作为列名）
        if len(sheets) == 1:
            df = pd.read_excel(file_path, sheet_name=sheets[0], header=0)
        else:
            # 多个sheet时，尝试找到数据最多的sheet
            max_rows = 0
            best_sheet = sheets[0]
            for sheet in sheets:
                temp_df = pd.read_excel(file_path, sheet_name=sheet, header=0)
                if len(temp_df) > max_rows:
                    max_rows = len(temp_df)
                    best_sheet = sheet
            df = pd.read_excel(file_path, sheet_name=best_sheet, header=0)
        
        return df
    
    def _process_with_llm(self, file_path: str) -> Optional[str]:
        """
        使用LLM处理复杂表头结构
        
        Args:
            file_path: 原始Excel文件路径
            
        Returns:
            处理后的文件路径，如果失败返回None
        """
        try:
            # 检查是否已有处理后的文件
            existing_recon = self._get_reconstructed_path(file_path)
            if existing_recon and os.path.exists(existing_recon):
                # 检查原始文件是否已修改
                original_stat = Path(file_path).stat()
                recon_stat = Path(existing_recon).stat()
                
                if original_stat.st_mtime <= recon_stat.st_mtime:
                    logger.info(f"使用已存在的重建文件: {existing_recon}")
                    return existing_recon
                else:
                    logger.info(f"原始文件已修改，重新生成...")
                    os.remove(existing_recon)
            
            # 生成输出路径
            original_name = Path(file_path).stem
            file_hash = hashlib.md5(str(Path(file_path).absolute()).encode()).hexdigest()[:8]
            output_path = self.temp_dir / f"{original_name}_reconstructed_{file_hash}.xlsx"
            
            logger.info(f"处理Excel文件: {file_path}")
            logger.info(f"重建文件将保存到: {output_path}")
            
            # Step 1: 取消合并单元格并填充
            unmerged_file, merged_info = self._step1_unmerge_and_fill(file_path)
            
            try:
                # Step 2: LLM分析表头结构
                analysis_result = self._step2_model_analysis(unmerged_file, merged_info)
                
                # Step 3: 自动处理（删除标签行，合并多级表头）
                reconstructed_data = self._step3_automated_processing(unmerged_file, analysis_result)
                
                # 写入重建文件
                self._write_reconstructed_file(reconstructed_data, output_path)
                
                logger.info(f"Excel处理完成。重建文件: {output_path}")
                return str(output_path)
                
            finally:
                # 清理临时文件
                if os.path.exists(unmerged_file):
                    os.remove(unmerged_file)
                    
        except Exception as e:
            logger.error(f"LLM处理Excel文件时出错: {e}", exc_info=True)
            return None
    
    def _step1_unmerge_and_fill(self, file_path: str) -> Tuple[str, Dict]:
        """
        Step 1: 预处理 - 取消合并单元格并填充空白
        
        Args:
            file_path: 原始Excel文件路径
            
        Returns:
            (取消合并后的文件路径, 合并信息字典)
        """
        try:
            logger.info("Step 1: 取消合并单元格并填充空白...")
            
            # 创建临时文件
            unmerged_file = str(self.temp_dir / f"unmerged_{uuid.uuid4().hex[:8]}.xlsx")
            
            # 加载工作簿
            wb = openpyxl.load_workbook(file_path, data_only=True)
            merged_info = {}
            
            for ws in wb.worksheets:
                logger.info(f"  处理工作表: {ws.title}")
                sheet_merged_info = []
                
                # 收集合并信息并取消合并
                for merged_range in list(ws.merged_cells.ranges):
                    min_row, min_col, max_row, max_col = (
                        merged_range.min_row, merged_range.min_col,
                        merged_range.max_row, merged_range.max_col
                    )
                    value = ws.cell(row=min_row, column=min_col).value
                    
                    # 存储合并信息
                    sheet_merged_info.append({
                        "range": str(merged_range),
                        "start": (min_row, min_col),
                        "end": (max_row, max_col),
                        "value": value
                    })
                    
                    # 取消合并
                    ws.unmerge_cells(start_row=min_row, start_column=min_col,
                                   end_row=max_row, end_column=max_col)
                    
                    # 填充所有单元格
                    for row in range(min_row, max_row + 1):
                        for col in range(min_col, max_col + 1):
                            ws.cell(row=row, column=col, value=value)
                
                merged_info[ws.title] = sheet_merged_info
                logger.info(f"    取消合并了 {len(sheet_merged_info)} 个合并单元格范围")
            
            # 保存取消合并后的文件
            wb.save(unmerged_file)
            wb.close()
            logger.info(f"Step 1 完成。取消合并文件: {os.path.basename(unmerged_file)}")
            
            return unmerged_file, merged_info
            
        except Exception as e:
            logger.error(f"Step 1 (取消合并) 出错: {e}", exc_info=True)
            raise
    
    def _step2_model_analysis(self, unmerged_file: str, merged_info: Dict) -> List[Dict]:
        """
        Step 2: 模型分析 - 识别表头和标签行
        
        Args:
            unmerged_file: 取消合并后的文件路径
            merged_info: 合并信息字典
            
        Returns:
            分析结果列表
        """
        if self.openai_client is None:
            logger.warning("未提供OpenAI客户端，使用默认分析")
            all_sheets = pd.read_excel(unmerged_file, sheet_name=None, header=None)
            return [
                {sheet_name: {"labels": [], "header": [1]}}
                for sheet_name in all_sheets.keys()
            ]
        
        try:
            logger.info("Step 2: 模型分析 - 识别标签行和表头...")
            
            # 提取前10行作为样本
            excel_info = self._get_excel_data(unmerged_file, head=10)
            
            # 准备合并信息
            merged_info_json = json.dumps(merged_info, ensure_ascii=False, indent=2)
            
            system_prompt = '''你是一个专业的结构化数据处理AI，专门分析Excel表格结构。

核心能力：
1. 准确识别表头行：表头通常是简短的标签（1-5个词），描述数据列。它们出现在表格顶部，结构一致。
2. 区分表头和数据：数据行包含实际值（数字、日期、长描述、带详细信息的产品名称）。表头是简洁的列标签。
3. 识别多级表头：只有顶部连续的行，明显是表头标签（不是数据），才应被视为表头。
4. 识别标签行：工作表级别的描述、标题或注释，出现在实际数据表之前（不是数据行内容）。

关键规则：
- 表头是简短的标签（通常每个单元格1-5个词），不是长描述或数据值
- 如果一行包含长文本、数字或详细的产品信息，它是数据，不是表头
- 多级表头通常最多1-3行，都在最顶部
- 数据行绝不能被视为表头'''
            
            user_prompt = f'''请分析每个工作表的结构并识别：
1. 标签行：要删除的工作表级别标题/注释/描述（在实际表格之前）
2. 表头行：实际的列表头行 - 这些应该是简短的标签，不是数据

重要：表头是简洁的列标签。如果一行包含长描述、产品详细信息或实际数据值，它是数据行，不是表头。

要分析的数据：

1. 取消合并后的Excel文件数据（前10行）：

```
{excel_info}
```

2. 原始合并单元格信息（用于确定表头级别）：

```
{merged_info_json}
```

输出格式：

[
    {{
        "sheet_name1": {{
            "labels": [行号],    # 整个工作表的标签文本行（如果没有则为空列表）
            "header": [行号]      # 多级表头行（必须包含至少1行）
        }},
        "sheet_name2": {{
            "labels": [行号],
            "header": [行号]
        }}
    }}
]

关键指导原则：
1. 表头是简短的标签（每个单元格1-5个词）。长文本 = 数据行，不是表头。
2. 表头通常出现在前1-3行。如果看到实际数据值（数字、带详细信息的产品名称），那是数据行。
3. 多级表头很少见 - 通常只有1-2行。只有当多行明显都是表头标签（简短、描述性）时，才标记多行为表头。
4. 如有疑问，使用更少的表头行。有1个表头行比将数据合并到表头中更好。
5. 标签行是表格之前的工作表级别描述/标题，不是数据内容。
6. 每个工作表独立分析。
7. 工作表名称必须完全匹配。
8. 只输出JSON结果，不要解释。

示例正确输出：

[
    {{"sheet_name1": {{
        "labels": [1, 2],
        "header": [3, 4, 5]
    }}}},
    {{"sheet_name2": {{
        "labels": [],
        "header": [1, 2]
    }}}},
    {{"sheet_name3": {{
        "labels": [],
        "header": [1]
    }}}}
]'''
            
            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            # 清理JSON（可能包含markdown代码块）
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            analysis_result = json.loads(result_text)
            logger.info(f"Step 2 完成。分析了 {len(analysis_result)} 个工作表")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Step 2 (模型分析) 出错: {e}", exc_info=True)
            logger.info("回退到默认分析")
            all_sheets = pd.read_excel(unmerged_file, sheet_name=None, header=None)
            return [
                {sheet_name: {"labels": [], "header": [1]}}
                for sheet_name in all_sheets.keys()
            ]
    
    def _step3_automated_processing(self, unmerged_file: str, analysis_result: List[Dict]) -> Dict:
        """
        Step 3: 自动处理 - 清理和合并
        
        Args:
            unmerged_file: 取消合并后的文件路径
            analysis_result: Step 2的分析结果
            
        Returns:
            重建数据的字典（工作表名 -> DataFrame）
        """
        try:
            logger.info("Step 3: 自动处理 - 清理和合并表头...")
            
            reconstructed_data = {}
            
            for sheet_config in analysis_result:
                for sheet_name, config in sheet_config.items():
                    labels = config.get('labels', [])
                    header = config.get('header', [1])
                    
                    logger.info(f"  处理工作表: {sheet_name}")
                    logger.info(f"    要删除的标签行: {labels}")
                    logger.info(f"    表头行: {header}")
                    
                    # Step 3.1: 先删除标签行（在读取表头之前）
                    df_raw = pd.read_excel(unmerged_file, sheet_name=sheet_name, header=None, dtype=object)
                    
                    if labels:
                        # 转换为0基索引并删除标签行
                        labels_0_based = [x - 1 for x in labels]
                        df_raw = df_raw.drop(labels_0_based, axis=0, errors='ignore')
                        df_raw = df_raw.reset_index(drop=True)
                        logger.info(f"    删除了 {len(labels)} 个标签行")
                    
                    # Step 3.2: 调整表头行号（删除标签行后）
                    header_0_based = self._adjust_header_indices(header, labels, len(df_raw))
                    
                    if header_0_based is None:
                        # 空数据框或无效表头
                        reconstructed_data[sheet_name] = pd.DataFrame()
                        continue
                    
                    # Step 3.3: 设置表头行并提取数据
                    df = self._extract_data_with_headers(df_raw, header_0_based)
                    
                    # 清理列名和数据
                    df.columns = self._clean_column_names(df.columns)
                    
                    if len(header_0_based) > 1:
                        logger.info(f"    将 {len(header_0_based)} 个表头行合并为单行")
                    
                    # 删除完全空的行
                    df = df.dropna(how='all')
                    
                    reconstructed_data[sheet_name] = df
                    logger.info(f"    最终: {len(df)} 行 × {len(df.columns)} 列")
                    
                    # 打印重建后的表头信息
                    print(f"\n📋 工作表 '{sheet_name}' 重建后的表头:")
                    print(f"  列名: {list(df.columns)}")
                    if len(df) > 0:
                        print(f"  前3行数据:")
                        print(df.head(3).to_string())
                        print()
            
            logger.info(f"Step 3 完成。处理了 {len(reconstructed_data)} 个工作表")
            return reconstructed_data
            
        except Exception as e:
            logger.error(f"Step 3 (自动处理) 出错: {e}", exc_info=True)
            raise
    
    def _get_excel_data(self, file_path: str, head: int = 10) -> str:
        """
        获取Excel文件的样本数据用于LLM分析
        
        Args:
            file_path: Excel文件路径
            head: 每个工作表提取的行数
            
        Returns:
            格式化的字符串，包含工作表信息
        """
        try:
            all_sheets_data = pd.read_excel(file_path, sheet_name=None, header=None)
            prompt_parts = []
            
            for sheet_name, data in all_sheets_data.items():
                data.index = data.index + 1  # 1基索引
                excel_col_names = [get_column_letter(i + 1) for i in range(len(data.columns))]
                data.columns = excel_col_names
                
                # 替换字符串中的换行符
                data = data.map(lambda x: str(x).replace('\n', ' ') if isinstance(x, str) else x)
                
                # 使用to_string代替to_markdown，避免依赖tabulate
                try:
                    sheet_sample = data.head(head).to_markdown(index=True)
                except ImportError:
                    # 如果没有tabulate，使用to_string
                    sheet_sample = data.head(head).to_string(index=True)
                
                sheet_info = f"工作表: {sheet_name}\n前 {head} 行:\n\n{sheet_sample}\n\n---"
                prompt_parts.append(sheet_info)
            
            return '\n'.join(prompt_parts)
            
        except Exception as e:
            logger.error(f"提取Excel数据时出错: {e}", exc_info=True)
            raise
    
    def _write_reconstructed_file(self, reconstructed_data: Dict, output_path: Path) -> None:
        """
        将重建数据写入Excel文件
        
        Args:
            reconstructed_data: 工作表名 -> DataFrame 的字典
            output_path: 输出文件路径
        """
        try:
            logger.info(f"写入重建文件: {output_path}")
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, df in reconstructed_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    logger.info(f"  - 工作表 '{sheet_name}': {len(df)} 行 × {len(df.columns)} 列")
            
            logger.info(f"重建文件保存成功")
            
        except Exception as e:
            logger.error(f"写入重建文件时出错: {e}", exc_info=True)
            raise
    
    def _get_reconstructed_path(self, original_path: str) -> Optional[str]:
        """
        获取重建文件路径（如果存在）
        
        Args:
            original_path: 原始文件路径
            
        Returns:
            重建文件路径，如果不存在则返回None
        """
        original_name = Path(original_path).stem
        
        # 查找现有的重建文件
        for file in self.temp_dir.glob(f"{original_name}_reconstructed_*.xlsx"):
            return str(file)
        
        return None
    
    def _read_processed_file(self, processed_file: str) -> pd.DataFrame:
        """
        从处理后的文件读取数据
        
        Args:
            processed_file: 处理后的文件路径
            
        Returns:
            DataFrame
        """
        excel_file = pd.ExcelFile(processed_file)
        sheets = excel_file.sheet_names
        
        # 选择数据最多的sheet
        if len(sheets) == 1:
            return pd.read_excel(processed_file, sheet_name=sheets[0], header=0)
        else:
            max_rows = 0
            best_sheet = sheets[0]
            for sheet in sheets:
                temp_df = pd.read_excel(processed_file, sheet_name=sheet, header=0)
                if len(temp_df) > max_rows:
                    max_rows = len(temp_df)
                    best_sheet = sheet
            return pd.read_excel(processed_file, sheet_name=best_sheet, header=0)
    
    def _adjust_header_indices(self, header: List[int], labels: List[int], df_length: int) -> Optional[List[int]]:
        """
        调整表头行索引（删除标签行后）
        
        Args:
            header: 原始表头行号（1基）
            labels: 已删除的标签行号（1基）
            df_length: 删除标签行后的数据框长度
            
        Returns:
            调整后的表头索引（0基），如果无效则返回None
        """
        if df_length == 0:
            return None
        
        # 调整表头索引（考虑已删除的标签行）
        if labels:
            header_adjusted = [h - sum(1 for l in labels if l < h) for h in header]
        else:
            header_adjusted = header
        
        # 转换为0基并验证边界
        header_0_based = [h - 1 for h in header_adjusted if h > 0]
        header_0_based = [h for h in header_0_based if 0 <= h < df_length]
        
        if not header_0_based:
            logger.warning("    未找到有效的表头行，使用默认值")
            return [0] if df_length > 0 else None
        
        return header_0_based
    
    def _extract_data_with_headers(self, df_raw: pd.DataFrame, header_0_based: List[int]) -> pd.DataFrame:
        """
        使用指定的表头行从数据框提取数据
        
        Args:
            df_raw: 原始数据框（无表头）
            header_0_based: 表头行索引（0基）
            
        Returns:
            设置了表头并提取了数据的DataFrame
        """
        if len(header_0_based) == 1:
            # 单级表头
            header_idx = header_0_based[0]
            if header_idx >= len(df_raw):
                # 表头索引越界，使用默认列名
                df = df_raw.copy()
                df.columns = [f'Column_{i}' for i in range(len(df.columns))]
                return df
            
            df_raw.columns = df_raw.iloc[header_idx]
            data_start = header_idx + 1
            
            if data_start < len(df_raw):
                return df_raw.iloc[data_start:].reset_index(drop=True)
            else:
                # 表头后没有数据行
                return pd.DataFrame(columns=df_raw.iloc[header_idx])
        else:
            # 多级表头：合并为单行
            header_rows_data = df_raw.iloc[header_0_based]
            new_columns = []
            
            for col_idx in range(len(df_raw.columns)):
                col_values = []
                for row_idx in range(len(header_0_based)):
                    val = header_rows_data.iloc[row_idx, col_idx]
                    if pd.notna(val) and str(val).strip() and 'Unnamed' not in str(val):
                        val_str = str(val).strip()
                        # 只包含短值（可能是表头，不是数据）
                        if len(val_str) <= 50:  # 表头通常很短
                            col_values.append(val_str)
                
                # 去重但保持顺序
                col_values_dedup = list(OrderedDict.fromkeys(col_values))
                # 只有在有合理的表头值时才连接
                if col_values_dedup and all(len(v) <= 30 for v in col_values_dedup):
                    col_name = '-'.join(col_values_dedup)
                elif col_values_dedup:
                    # 使用最短/最可能的表头值
                    col_name = min(col_values_dedup, key=len)
                else:
                    col_name = f'Column_{col_idx}'
                new_columns.append(col_name)
            
            df_raw.columns = new_columns
            data_start = max(header_0_based) + 1
            return df_raw.iloc[data_start:].reset_index(drop=True)
    
    def _clean_column_names(self, columns: pd.Index) -> List[str]:
        """
        清理和标准化列名
        
        Args:
            columns: 原始列索引
            
        Returns:
            清理后的列名列表
        """
        return [
            str(col).strip() if col and str(col).strip() else f'Column_{i}'
            for i, col in enumerate(columns)
        ]
    
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
        
        # 清理列名：去除空格，处理特殊字符，处理NaN值
        cleaned_columns = []
        for col in df.columns:
            if pd.isna(col):
                cleaned_columns.append(f"Unnamed_{len(cleaned_columns)}")
            else:
                cleaned_columns.append(str(col).strip())
        df.columns = cleaned_columns
        
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
                logger.warning(f"无法加载文件 {file}: {str(e)}")
        
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
    
    def _print_preprocessed_headers(self, file_name: str, df: pd.DataFrame) -> None:
        """
        打印预处理后的表头信息
        
        Args:
            file_name: 文件名
            df: 预处理后的DataFrame
        """
        print("\n" + "=" * 70)
        print(f"📊 预处理后的表头信息: {file_name}")
        print("=" * 70)
        print(f"数据形状: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"\n列名列表 ({len(df.columns)} 列):")
        print("-" * 70)
        for i, col in enumerate(df.columns, 1):
            dtype = df[col].dtype
            non_null_count = df[col].notna().sum()
            print(f"  {i:2d}. {col:30s} | 类型: {str(dtype):10s} | 非空值: {non_null_count}/{len(df)}")
        
        print("\n前5行数据预览:")
        print("-" * 70)
        if len(df) > 0:
            # 显示前5行，限制列宽以便查看
            preview_df = df.head(5)
            # 如果列太多，只显示前10列
            if len(df.columns) > 10:
                preview_df = preview_df.iloc[:, :10]
                print(f"(仅显示前10列，共{len(df.columns)}列)")
            print(preview_df.to_string())
        else:
            print("  (数据为空)")
        
        print("=" * 70 + "\n")
