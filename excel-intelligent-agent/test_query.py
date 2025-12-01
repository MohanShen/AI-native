#!/usr/bin/env python3
"""
测试查询功能的脚本
"""
import os
import sys
sys.path.insert(0, '.')

from excel_preprocessor import ExcelPreprocessor
from nlp_parser import NLPParser
from code_generator import CodeGenerator
from code_executor import CodeExecutor

def test_query(query_text: str, api_key: str):
    """测试查询功能"""
    print("=" * 70)
    print(f"测试查询: {query_text}")
    print("=" * 70)
    
    # 1. 初始化组件
    print("\n1. 初始化组件...")
    preprocessor = ExcelPreprocessor(knowledge_base_path="knowledge_base")
    preprocessor.load_all_files()
    files_info = preprocessor.get_all_files_info()
    print(f"   ✓ 加载了 {len(files_info)} 个文件")
    
    # 2. 初始化NLP解析器
    print("\n2. 初始化NLP解析器...")
    try:
        nlp_parser = NLPParser(api_key=api_key)
        print("   ✓ NLP解析器初始化成功")
    except Exception as e:
        print(f"   ✗ NLP解析器初始化失败: {e}")
        return False
    
    # 3. 解析查询
    print("\n3. 解析查询意图...")
    try:
        intent = nlp_parser.parse_query(query_text, files_info)
        print(f"   ✓ 意图解析成功")
        print(f"   - 分析类型: {intent.get('intent')}")
        print(f"   - 目标文件: {intent.get('target_file')}")
        print(f"   - 目标列: {intent.get('target_columns', [])}")
        print(f"   - 操作: {intent.get('operation')}")
    except Exception as e:
        print(f"   ✗ 意图解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 获取目标文件
    target_file = intent.get('target_file')
    if not target_file or target_file not in preprocessor.processed_files:
        print(f"\n   ✗ 找不到目标文件: {target_file}")
        print(f"   可用文件: {list(files_info.keys())}")
        return False
    
    df = preprocessor.processed_files[target_file]
    file_path = preprocessor.file_metadata[target_file]['path']
    df.attrs['file_path'] = file_path
    print(f"   ✓ 找到目标文件: {target_file}")
    
    # 5. 生成代码
    print("\n4. 生成分析代码...")
    try:
        code_generator = CodeGenerator()
        generated_code = code_generator.generate_code(intent, file_path, df)
        used_columns = code_generator.get_used_columns()
        print(f"   ✓ 代码生成成功")
        print(f"   - 使用的列: {used_columns}")
        print(f"\n   生成的代码预览:")
        print("   " + "-" * 66)
        for i, line in enumerate(generated_code.split('\n')[:10], 1):
            print(f"   {i:2d} | {line}")
        if len(generated_code.split('\n')) > 10:
            print(f"   ... ({len(generated_code.split('\n')) - 10} more lines)")
        print("   " + "-" * 66)
    except Exception as e:
        print(f"   ✗ 代码生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. 执行代码
    print("\n5. 执行分析代码...")
    try:
        executor = CodeExecutor(file_path)
        execution_result = executor.execute(generated_code)
        
        if execution_result['success']:
            print(f"   ✓ 代码执行成功")
            print(f"\n   执行输出:")
            print("   " + "-" * 66)
            output_lines = execution_result['output'].split('\n')[:20]
            for line in output_lines:
                print(f"   {line}")
            if len(execution_result['output'].split('\n')) > 20:
                print(f"   ... (more output)")
            print("   " + "-" * 66)
            
            if execution_result.get('result'):
                print(f"\n   结果摘要:")
                result = execution_result['result']
                if isinstance(result, dict):
                    for key, value in list(result.items())[:5]:
                        print(f"   - {key}: {value}")
        else:
            print(f"   ✗ 代码执行失败")
            print(f"   错误信息: {execution_result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"   ✗ 代码执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)
    return True

if __name__ == '__main__':
    # 获取API密钥
    api_key = os.environ.get('OPENAI_API')
    if not api_key:
        print("错误: 未找到 OPENAI_API 环境变量")
        print("请设置: export OPENAI_API='your-api-key'")
        sys.exit(1)
    
    # 测试查询
    query = "开题的学生中，有几个来自经济（2）班"
    success = test_query(query, api_key)
    
    sys.exit(0 if success else 1)

