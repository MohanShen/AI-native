"""
测试 OpenAI API 配置
运行此脚本来检查 OpenAI API 是否正确配置
"""

import os
from rag_system import RAGSystem

def test_openai_config():
    """测试 OpenAI API 配置"""
    print("=" * 60)
    print("OpenAI API 配置测试")
    print("=" * 60)
    
    # 1. 检查环境变量
    print("\n1. 检查环境变量...")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        # 只显示前10个字符和后4个字符，保护隐私
        masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
        print(f"✅ OPENAI_API_KEY 已设置: {masked_key}")
    else:
        print("❌ OPENAI_API_KEY 未设置")
        print("\n请设置环境变量:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("\n或者:")
        print("  export OPENAI_API_KEY='sk-...'")
        return False
    
    # 2. 初始化 RAG 系统
    print("\n2. 初始化 RAG 系统...")
    try:
        rag = RAGSystem(
            es_host="localhost",
            es_port=9200,
            es_user="elastic",
            es_password="w2b9I2dq",  # 从 ../elastic-start-local/.env 获取
            index_name="rag_documents"
        )
        print("✅ RAG 系统初始化成功")
    except Exception as e:
        print(f"❌ RAG 系统初始化失败: {e}")
        print("\n请确保 Elasticsearch 正在运行:")
        print("  cd ../elastic-start-local")
        print("  ./start.sh")
        return False
    
    # 3. 检查 LLM 客户端
    print("\n3. 检查 OpenAI 客户端...")
    if rag.llm_client:
        print("✅ OpenAI 客户端已初始化")
        print("✅ 将使用 OpenAI API 生成回答")
    else:
        print("❌ OpenAI 客户端未初始化")
        print("\n可能的原因:")
        print("  1. API 密钥格式不正确")
        print("  2. API 密钥无效或过期")
        print("  3. openai 包未正确安装")
        print("\n请检查:")
        print("  - API 密钥是否正确设置")
        print("  - 运行: pip install openai")
        return False
    
    # 4. 测试查询（如果索引中有数据）
    print("\n4. 测试查询...")
    
    # 检查索引中是否有数据
    try:
        stats = rag.get_index_stats()
        if stats['document_count'] > 0:
            print(f"✅ 索引中有 {stats['document_count']} 个文档")
            
            # 执行测试查询
            test_query = "What is this document about?"
            print(f"\n执行测试查询: '{test_query}'")
            
            result = rag.query(test_query, top_k=3, generate_answer=True)
            
            if result['answer']:
                print("\n✅ 查询成功！")
                print("\n生成的回答:")
                print("-" * 60)
                print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
                print("-" * 60)
                
                # 检查是否使用了 OpenAI
                if "注意：这是基于检索结果的简单回答" not in result['answer']:
                    print("\n✅ 确认: 使用了 OpenAI API 生成回答")
                else:
                    print("\n⚠️ 警告: 可能使用了简单回答模式")
            else:
                print("❌ 未生成回答")
        else:
            print("⚠️ 索引中没有文档")
            print("\n请先处理 PDF 文件:")
            print("  rag.process_and_index_pdf('example.pdf')")
    except Exception as e:
        print(f"❌ 测试查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！OpenAI API 配置正确。")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_openai_config()
    
    if not success:
        print("\n" + "=" * 60)
        print("配置说明:")
        print("=" * 60)
        print("\n1. 获取 OpenAI API Key:")
        print("   访问: https://platform.openai.com/api-keys")
        print("   创建新的 API 密钥")
        print("\n2. 设置环境变量:")
        print("   export OPENAI_API_KEY='sk-...'")
        print("\n3. 验证配置:")
        print("   python test_openai.py")
        print("\n4. 查看详细文档:")
        print("   cat OPENAI_SETUP.md")

