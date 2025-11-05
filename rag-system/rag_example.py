"""
RAG 系统使用示例
"""

import os
from rag_system import RAGSystem


def example_1_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)
    
    # 初始化 RAG 系统
    # 注意：密码请根据 ../elastic-start-local/.env 文件中的 ES_LOCAL_PASSWORD 值修改
    rag = RAGSystem(
        es_host="localhost",
        es_port=9200,
        es_user="elastic",
        es_password="w2b9I2dq",  # 请根据 ../elastic-start-local/.env 文件中的实际值修改
        index_name="rag_documents",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        reranker_method="rrf",
        chunk_size=500,
        chunk_overlap=50
    )
    
    # 处理 PDF 文件
    pdf_path = "example.pdf"  # 替换为你的 PDF 文件路径
    if os.path.exists(pdf_path):
        rag.process_and_index_pdf(pdf_path)
    else:
        print(f"PDF 文件不存在: {pdf_path}")
        return
    
    # 查询
    question = "What is this document about?"
    result = rag.query(question, top_k=5)
    
    print(f"\n问题: {result['question']}")
    print(f"\n回答:\n{result['answer']}")
    print(f"\n找到 {result['num_results']} 个相关文档")


def example_2_multiple_pdfs():
    """处理多个 PDF 文件示例"""
    print("=" * 60)
    print("示例 2: 处理多个 PDF 文件")
    print("=" * 60)
    
    # 注意：密码请根据 ../elastic-start-local/.env 文件中的 ES_LOCAL_PASSWORD 值修改
    rag = RAGSystem(
        es_host="localhost",
        es_port=9200,
        es_user="elastic",
        es_password="w2b9I2dq",  # 请根据实际情况修改
        index_name="rag_documents"
    )
    
    # 处理多个 PDF 文件
    pdf_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    
    for pdf_path in pdf_files:
        if os.path.exists(pdf_path):
            print(f"\n处理 PDF: {pdf_path}")
            rag.process_and_index_pdf(pdf_path)
        else:
            print(f"PDF 文件不存在: {pdf_path}")
    
    # 查询（会在所有文档中搜索）
    question = "What are the main topics discussed?"
    result = rag.query(question, top_k=10)
    
    print(f"\n问题: {result['question']}")
    print(f"\n回答:\n{result['answer']}")


def example_3_with_reranker():
    """使用 reranker model 示例"""
    print("=" * 60)
    print("示例 3: 使用 reranker model")
    print("=" * 60)
    
    # 使用 reranker model 而不是 RRF
    # 注意：密码请根据 ../elastic-start-local/.env 文件中的 ES_LOCAL_PASSWORD 值修改
    rag = RAGSystem(
        es_host="localhost",
        es_port=9200,
        es_user="elastic",
        es_password="w2b9I2dq",  # 请根据实际情况修改
        index_name="rag_documents",
        reranker_method="reranker",
        reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2"  # 可选：使用 reranker model
    )
    
    pdf_path = "example.pdf"
    if os.path.exists(pdf_path):
        rag.process_and_index_pdf(pdf_path)
    
    # 查询
    question = "What are the key findings?"
    result = rag.query(question, top_k=5)
    
    print(f"\n问题: {result['question']}")
    print(f"\n回答:\n{result['answer']}")


def example_4_search_only():
    """仅搜索，不生成回答"""
    print("=" * 60)
    print("示例 4: 仅搜索")
    print("=" * 60)
    
    # 注意：密码请根据 ../elastic-start-local/.env 文件中的 ES_LOCAL_PASSWORD 值修改
    rag = RAGSystem(
        es_host="localhost",
        es_port=9200,
        es_user="elastic",
        es_password="w2b9I2dq",  # 请根据实际情况修改
        index_name="rag_documents"
    )
    
    # 搜索
    query = "machine learning"
    results = rag.search(query, top_k=5, use_reranker=True)
    
    print(f"\n搜索查询: {query}")
    print(f"\n找到 {len(results)} 个结果:\n")
    
    for i, result in enumerate(results, 1):
        source = result.get('_source', {})
        print(f"{i}. [页码: {source.get('page', 0)}]")
        print(f"   {source.get('text', '')[:200]}...")
        print()


def example_5_index_stats():
    """获取索引统计信息"""
    print("=" * 60)
    print("示例 5: 索引统计")
    print("=" * 60)
    
    # 注意：密码请根据 ../elastic-start-local/.env 文件中的 ES_LOCAL_PASSWORD 值修改
    rag = RAGSystem(
        es_host="localhost",
        es_port=9200,
        es_user="elastic",
        es_password="w2b9I2dq",  # 请根据实际情况修改
        index_name="rag_documents"
    )
    
    stats = rag.get_index_stats()
    
    print(f"\n索引名称: {stats['index_name']}")
    print(f"文档数量: {stats['document_count']}")
    print(f"索引大小: {stats['size']} bytes ({stats['size'] / 1024 / 1024:.2f} MB)")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("RAG 系统使用示例")
    print("=" * 60)
    
    # 检查 Elasticsearch 是否运行
    try:
        # 注意：密码请根据 ../elastic-start-local/.env 文件中的 ES_LOCAL_PASSWORD 值修改
        rag = RAGSystem(
            es_host="localhost",
            es_port=9200,
            es_user="elastic",
            es_password="w2b9I2dq"  # 请根据实际情况修改
        )
    except Exception as e:
        print(f"\n❌ 无法连接到 Elasticsearch: {e}")
        print("\n请确保 Elasticsearch 正在运行:")
        print("  cd ../elastic-start-local")
        print("  ./start.sh")
        return
    
    # 运行示例
    print("\n选择要运行的示例:")
    print("1. 基本使用")
    print("2. 处理多个 PDF 文件")
    print("3. 使用 reranker model")
    print("4. 仅搜索")
    print("5. 索引统计")
    
    choice = input("\n请输入选择 (1-5): ").strip()
    
    if choice == "1":
        example_1_basic_usage()
    elif choice == "2":
        example_2_multiple_pdfs()
    elif choice == "3":
        example_3_with_reranker()
    elif choice == "4":
        example_4_search_only()
    elif choice == "5":
        example_5_index_stats()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()

