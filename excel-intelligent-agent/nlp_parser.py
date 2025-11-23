"""
自然语言解析模块
使用OpenAI API理解用户意图并提取分析需求
"""
import openai
from typing import Dict, List, Optional
import json
import re


class NLPParser:
    """自然语言解析器"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        初始化NLP解析器
        
        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
        """
        openai.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
    
    def parse_query(self, query: str, available_files: Dict[str, Dict]) -> Dict:
        """
        解析用户查询，提取分析意图
        
        Args:
            query: 用户查询（自然语言）
            available_files: 可用文件信息 {文件名: {columns, shape, dtypes}}
            
        Returns:
            解析结果字典，包含：
            - intent: 分析意图（sum, group, trend, sort, filter等）
            - target_file: 目标文件名
            - target_columns: 目标列名列表
            - operation: 具体操作描述
            - keywords: 提取的关键词
        """
        # 构建文件信息摘要
        files_summary = self._build_files_summary(available_files)
        
        # 构建提示词
        prompt = f"""你是一个数据分析助手。用户想要分析Excel数据。

可用文件信息：
{files_summary}

用户问题：{query}

请分析用户意图并返回JSON格式的结果，包含以下字段：
1. intent: 分析意图，可选值：sum（求和）、group（分组）、trend（趋势分析）、sort（排序）、filter（筛选）、statistics（统计）、correlation（相关性分析）、visualization（可视化）
2. target_file: 最相关的文件名（从可用文件中选择）
3. target_columns: 需要使用的列名列表（从目标文件的列中选择）
4. operation: 具体操作描述（中文）
5. keywords: 从查询中提取的关键词列表
6. analysis_type: 分析类型，如"销售趋势"、"地区统计"等

只返回JSON，不要其他文字说明。
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的数据分析助手，擅长理解用户意图并提取分析需求。只返回JSON格式的结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 提取JSON（可能包含markdown代码块）
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
            
            result = json.loads(result_text)
            
            # 验证和补充结果
            result = self._validate_result(result, available_files)
            
            return result
            
        except Exception as e:
            # 如果API调用失败，使用简单的关键词匹配作为后备
            return self._fallback_parse(query, available_files)
    
    def _build_files_summary(self, available_files: Dict[str, Dict]) -> str:
        """构建文件信息摘要"""
        summary_parts = []
        for file_name, info in available_files.items():
            columns = ', '.join(info.get('columns', []))
            summary_parts.append(f"- {file_name}: 列名=[{columns}], 行数={info.get('shape', (0, 0))[0]}")
        return '\n'.join(summary_parts)
    
    def _validate_result(self, result: Dict, available_files: Dict[str, Dict]) -> Dict:
        """验证和修正解析结果"""
        # 确保target_file存在
        if result.get('target_file') not in available_files:
            # 尝试根据关键词匹配
            keywords = result.get('keywords', [])
            if keywords:
                for file_name in available_files.keys():
                    if any(kw.lower() in file_name.lower() for kw in keywords):
                        result['target_file'] = file_name
                        break
        
        # 如果还是没有找到，使用第一个文件
        if result.get('target_file') not in available_files:
            result['target_file'] = list(available_files.keys())[0] if available_files else None
        
        # 验证列名
        target_file = result.get('target_file')
        if target_file and target_file in available_files:
            available_columns = available_files[target_file].get('columns', [])
            target_columns = result.get('target_columns', [])
            
            # 过滤掉不存在的列
            valid_columns = [col for col in target_columns if col in available_columns]
            
            # 如果所有列都不存在，尝试模糊匹配
            if not valid_columns and target_columns:
                for col in target_columns:
                    for avail_col in available_columns:
                        if col.lower() in avail_col.lower() or avail_col.lower() in col.lower():
                            if avail_col not in valid_columns:
                                valid_columns.append(avail_col)
            
            result['target_columns'] = valid_columns if valid_columns else available_columns[:3]
        
        return result
    
    def _fallback_parse(self, query: str, available_files: Dict[str, Dict]) -> Dict:
        """后备解析方法（基于关键词匹配）"""
        query_lower = query.lower()
        
        # 意图识别
        intent = "statistics"
        if any(word in query_lower for word in ['求和', '总和', 'sum', 'total']):
            intent = "sum"
        elif any(word in query_lower for word in ['分组', 'group', '按']):
            intent = "group"
        elif any(word in query_lower for word in ['趋势', 'trend', '变化', '增长']):
            intent = "trend"
        elif any(word in query_lower for word in ['排序', 'sort', '排名']):
            intent = "sort"
        elif any(word in query_lower for word in ['筛选', 'filter', '过滤']):
            intent = "filter"
        
        # 提取关键词
        keywords = []
        common_words = ['的', '和', '是', '在', '有', '我', '你', '他', '她', '它', 
                       'the', 'is', 'are', 'a', 'an', 'and', 'or', 'but', 'to', 'of']
        words = re.findall(r'\b\w+\b', query_lower)
        keywords = [w for w in words if w not in common_words and len(w) > 1]
        
        # 选择目标文件
        target_file = None
        if available_files:
            # 尝试根据关键词匹配
            for file_name in available_files.keys():
                if any(kw in file_name.lower() for kw in keywords):
                    target_file = file_name
                    break
            
            if not target_file:
                target_file = list(available_files.keys())[0]
        
        # 提取列名关键词
        target_columns = []
        if target_file and target_file in available_files:
            available_columns = available_files[target_file].get('columns', [])
            for col in available_columns:
                if any(kw in col.lower() for kw in keywords):
                    target_columns.append(col)
            
            if not target_columns:
                target_columns = available_columns[:3] if len(available_columns) >= 3 else available_columns
        
        return {
            'intent': intent,
            'target_file': target_file,
            'target_columns': target_columns,
            'operation': f"执行{intent}分析",
            'keywords': keywords,
            'analysis_type': '数据分析'
        }

