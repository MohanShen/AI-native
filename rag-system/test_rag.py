"""
测试 RAG 系统
使用 example.pdf 进行完整测试
"""

import os
import sys
from rag_system import RAGSystem

def test_rag_system():
    """测试 RAG 系统"""
    print("=" * 60)
    print("RAG 系统测试")
    print("=" * 60)
    
    # 检查 PDF 文件
    pdf_path = "example.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return
    
    print(f"✅ 找到 PDF 文件: {pdf_path}")
    file_size = os.path.getsize(pdf_path) / 1024 / 1024
    print(f"   文件大小: {file_size:.2f} MB")
    
    # 初始化 RAG 系统
    print("\n" + "=" * 60)
    print("初始化 RAG 系统...")
    print("=" * 60)
    
    try:
        rag = RAGSystem(
            es_host="localhost",
            es_port=9200,
            es_user="elastic",
            es_password="w2b9I2dq",  # 从 ../elastic-start-local/.env 获取
            index_name="rag_documents",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            reranker_method="rrf",
            chunk_size=500,
            chunk_overlap=50
        )
        print("✅ RAG 系统初始化成功")
    except Exception as e:
        print(f"❌ RAG 系统初始化失败: {e}")
        print("\n请确保 Elasticsearch 正在运行:")
        print("  cd ../elastic-start-local")
        print("  ./start.sh")
        return
    
    # 处理 PDF 文件
    print("\n" + "=" * 60)
    print("处理 PDF 文件...")
    print("=" * 60)
    
    try:
        result = rag.process_and_index_pdf(
            pdf_path,
            extract_images=True,
            extract_tables=True
        )
        print("\n✅ PDF 处理完成")
        print(f"   文本块数: {result['text_chunks_count']}")
        print(f"   图片数: {result['images_count']}")
        print(f"   表格数: {result['tables_count']}")
        print(f"   索引文档数: {result['indexed_documents']}")
    except Exception as e:
        print(f"❌ PDF 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 获取索引统计
    print("\n" + "=" * 60)
    print("索引统计...")
    print("=" * 60)
    
    try:
        stats = rag.get_index_stats()
        print(f"索引名称: {stats['index_name']}")
        print(f"文档数量: {stats['document_count']}")
        print(f"索引大小: {stats['size'] / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"⚠️ 获取索引统计失败: {e}")
    
    # 测试搜索
    print("\n" + "=" * 60)
    print("测试搜索功能...")
    print("=" * 60)
    
    test_queries = [
        "What is this document about?",
        "What are the main topics?",
        "What is the conclusion?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试查询 {i} ---")
        print(f"查询: {query}")
        
        try:
            # 搜索
            results = rag.search(query, top_k=5, use_reranker=True)
            print(f"找到 {len(results)} 个结果")
            
            # 显示前 3 个结果
            for j, result in enumerate(results[:3], 1):
                source = result.get('_source', {})
                text = source.get('text', '')
                page = source.get('page', 0)
                print(f"\n结果 {j} [页码: {page}]:")
                print(f"  {text[:200]}...")
            
            # 生成回答
            print(f"\n生成回答...")
            answer = rag.generate_answer(query, results)
            print(f"回答:\n{answer[:500]}...")
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 测试完整查询流程
    print("\n" + "=" * 60)
    print("测试完整查询流程...")
    print("=" * 60)
    
    test_question = "What is the main topic of this document?"
    print(f"问题: {test_question}")
    
    try:
        result = rag.query(test_question, top_k=5, generate_answer=True)
        print(f"\n✅ 查询成功")
        print(f"找到 {result['num_results']} 个相关文档")
        print(f"\n回答:\n{result['answer']}")
        
        # 显示搜索结果摘要
        print(f"\n搜索结果摘要:")
        for i, search_result in enumerate(result['search_results'][:3], 1):
            source = search_result.get('_source', {})
            page = source.get('page', 0)
            text = source.get('text', '')
            print(f"\n{i}. [页码: {page}]")
            print(f"   {text[:150]}...")
            
    except Exception as e:
        print(f"❌ 完整查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_rag_system()

