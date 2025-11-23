"""
代码执行模块
执行生成的Python代码并返回结果
"""
import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, Optional
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端


class CodeExecutor:
    """代码执行器"""
    
    def __init__(self, file_path: str):
        """
        初始化代码执行器
        
        Args:
            file_path: Excel文件路径
        """
        self.file_path = file_path
        self.execution_result = None
        self.execution_error = None
        self.output_text = ""
    
    def execute(self, code: str) -> Dict[str, Any]:
        """
        执行Python代码
        
        Args:
            code: 要执行的Python代码字符串
            
        Returns:
            执行结果字典，包含：
            - success: 是否成功
            - output: 输出文本
            - result: 执行结果（如果有result变量）
            - error: 错误信息（如果有）
        """
        # 准备执行环境
        exec_globals = {
            'pd': pd,
            'np': __import__('numpy'),
            'plt': __import__('matplotlib.pyplot'),
            'datetime': __import__('datetime').datetime,
            '__builtins__': __builtins__
        }
        
        # 捕获输出
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # 执行代码
                exec(code, exec_globals)
            
            # 获取输出
            stdout_text = stdout_capture.getvalue()
            stderr_text = stderr_capture.getvalue()
            
            # 获取result变量（如果存在）
            result = exec_globals.get('result', None)
            
            # 组合输出
            output = stdout_text
            if stderr_text:
                output += f"\n警告:\n{stderr_text}"
            
            self.output_text = output
            self.execution_result = result
            self.execution_error = None
            
            return {
                'success': True,
                'output': output,
                'result': result,
                'error': None
            }
            
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.execution_error = error_msg
            self.output_text = ""
            
            return {
                'success': False,
                'output': "",
                'result': None,
                'error': error_msg
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        格式化执行结果
        
        Args:
            result: 执行结果字典
            
        Returns:
            格式化后的字符串
        """
        if not result['success']:
            return f"执行失败:\n{result['error']}"
        
        output_parts = []
        
        # 添加输出文本
        if result['output']:
            output_parts.append("执行输出:")
            output_parts.append(result['output'])
        
        # 添加结果摘要
        if result['result']:
            result_data = result['result']
            output_parts.append("\n" + "=" * 50)
            output_parts.append("分析结果摘要:")
            output_parts.append("=" * 50)
            
            if isinstance(result_data, dict):
                for key, value in result_data.items():
                    if key != 'data' and key != 'correlation_matrix' and key != 'statistics':
                        output_parts.append(f"{key}: {value}")
        
        return "\n".join(output_parts)
    
    def get_result_data(self) -> Optional[Dict]:
        """获取结果数据"""
        return self.execution_result

