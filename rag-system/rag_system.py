"""
RAG (Retrieval-Augmented Generation) System
支持处理 PDF 文件，包括文本、图片和表格的提取和处理
"""

import os
import json
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import time

# PDF processing
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import pandas as pd

# Text processing
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Reranking
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# LLM for answer generation
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not available. Using simple answer generation.")


class PDFProcessor:
    """PDF 处理器，提取文本、图片和表格"""
    
    def __init__(self):
        self.text_chunks = []
        self.images = []
        self.tables = []
    
    def extract_text(self, pdf_path: str) -> List[str]:
        """使用多种方法提取 PDF 文本"""
        text_chunks = []
        
        # 方法1: 使用 PyMuPDF (fitz) - 更好的文本提取
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_chunks.append({
                        'page': page_num + 1,
                        'text': text.strip(),
                        'method': 'pymupdf'
                    })
            doc.close()
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
        
        # 方法2: 使用 pdfplumber - 更好的布局保持
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        text_chunks.append({
                            'page': page_num + 1,
                            'text': text.strip(),
                            'method': 'pdfplumber'
                        })
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
        
        # 方法3: 使用 PyPDF2 - 备用方法
        if not text_chunks:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        if text.strip():
                            text_chunks.append({
                                'page': page_num + 1,
                                'text': text.strip(),
                                'method': 'pypdf2'
                            })
            except Exception as e:
                print(f"PyPDF2 extraction failed: {e}")
        
        return text_chunks
    
    def extract_images(self, pdf_path: str, output_dir: str = "extracted_images") -> List[Dict]:
        """提取 PDF 中的图片"""
        images = []
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                        image_path = os.path.join(output_dir, image_filename)
                        
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        images.append({
                            'page': page_num + 1,
                            'index': img_index + 1,
                            'path': image_path,
                            'format': image_ext
                        })
                    except Exception as e:
                        print(f"Error extracting image {img_index} from page {page_num + 1}: {e}")
            
            doc.close()
        except Exception as e:
            print(f"Image extraction failed: {e}")
        
        return images
    
    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """提取 PDF 中的表格"""
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    for table_index, table in enumerate(page_tables):
                        if table:
                            try:
                                # 转换为 DataFrame
                                df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
                                
                                # 转换为文本表示
                                table_text = df.to_string(index=False)
                                
                                tables.append({
                                    'page': page_num + 1,
                                    'index': table_index + 1,
                                    'dataframe': df,
                                    'text': table_text,
                                    'shape': df.shape
                                })
                            except Exception as e:
                                print(f"Error processing table {table_index} from page {page_num + 1}: {e}")
        except Exception as e:
            print(f"Table extraction failed: {e}")
        
        return tables
    
    def process_pdf(self, pdf_path: str, extract_images: bool = True, extract_tables: bool = True) -> Dict:
        """处理完整的 PDF 文件"""
        print(f"Processing PDF: {pdf_path}")
        
        # 提取文本
        print("Extracting text...")
        text_chunks = self.extract_text(pdf_path)
        # 为每个文本块添加 pdf_path
        for chunk in text_chunks:
            chunk['pdf_path'] = pdf_path
        print(f"Extracted {len(text_chunks)} text chunks from {len(set(c['page'] for c in text_chunks))} pages")
        
        # 提取图片
        images = []
        if extract_images:
            print("Extracting images...")
            images = self.extract_images(pdf_path)
            print(f"Extracted {len(images)} images")
        
        # 提取表格
        tables = []
        if extract_tables:
            print("Extracting tables...")
            tables = self.extract_tables(pdf_path)
            print(f"Extracted {len(tables)} tables")
        
        return {
            'text_chunks': text_chunks,
            'images': images,
            'tables': tables,
            'pdf_path': pdf_path
        }


class TextSplitter:
    """文本切分器，将内容拆分成可检索的单元"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
    
    def split_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """切分文本并保留元数据"""
        chunks = self.text_splitter.split_text(text)
        
        result = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                'chunk_id': i,
                'text': chunk,
                'chunk_size': len(chunk)
            }
            if metadata:
                chunk_data.update(metadata)
            result.append(chunk_data)
        
        return result
    
    def split_text_chunks(self, text_chunks: List[Dict]) -> List[Dict]:
        """切分多个文本块"""
        all_chunks = []
        
        for text_chunk in text_chunks:
            metadata = {
                'page': text_chunk.get('page', 0),
                'source': text_chunk.get('pdf_path', 'unknown'),
                'method': text_chunk.get('method', 'unknown')
            }
            
            split_chunks = self.split_text(text_chunk['text'], metadata)
            all_chunks.extend(split_chunks)
        
        return all_chunks


class Vectorizer:
    """向量化器，为文本生成向量"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Embedding dimension: {self.dimension}")
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """为文本列表生成向量"""
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()
    
    def encode_single(self, text: str) -> List[float]:
        """为单个文本生成向量"""
        embedding = self.model.encode([text])
        return embedding[0].tolist()


class Reranker:
    """重排序器，使用 RRF 或 reranker model"""
    
    def __init__(self, method: str = "rrf", model_name: Optional[str] = None):
        self.method = method
        
        if method == "reranker" and model_name:
            print(f"Loading reranker model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.eval()
            if torch.cuda.is_available():
                self.model = self.model.cuda()
        else:
            self.tokenizer = None
            self.model = None
    
    def rrf(self, results: List[Dict], k: int = 60) -> List[Dict]:
        """Reciprocal Rank Fusion (RRF) 重排序"""
        # 收集所有文档的分数
        doc_scores = {}
        
        for search_result in results:
            rank = search_result.get('rank', 0)
            doc_id = search_result.get('_id')
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'score': 0.0,
                    'doc': search_result
                }
            
            # RRF 分数计算
            rrf_score = 1.0 / (k + rank + 1)
            doc_scores[doc_id]['score'] += rrf_score
        
        # 按分数排序
        ranked_docs = sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)
        
        return [item['doc'] for item in ranked_docs]
    
    def rerank_with_model(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        """使用 reranker model 重排序"""
        if not self.model or not self.tokenizer:
            return documents[:top_k]
        
        # 准备输入
        pairs = [[query, doc.get('_source', {}).get('text', '')] for doc in documents]
        
        # Tokenize
        inputs = self.tokenizer(
            pairs,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        )
        
        # 移动到 GPU（如果可用）
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # 计算分数
        with torch.no_grad():
            scores = self.model(**inputs).logits
        
        # 添加分数并排序
        for i, doc in enumerate(documents):
            doc['rerank_score'] = float(scores[i].item())
        
        # 按分数排序
        ranked_docs = sorted(documents, key=lambda x: x.get('rerank_score', 0), reverse=True)
        
        return ranked_docs[:top_k]
    
    def rerank(self, query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
        """执行重排序"""
        if self.method == "rrf":
            return self.rrf(results, k=60)[:top_k]
        elif self.method == "reranker" and self.model:
            return self.rerank_with_model(query, results, top_k)
        else:
            return results[:top_k]


class RAGSystem:
    """RAG 系统主类"""
    
    def __init__(
        self,
        es_host: str = "localhost",
        es_port: int = 9200,
        es_user: str = "elastic",
        es_password: str = "changeme",
        index_name: str = "rag_documents",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        reranker_method: str = "rrf",
        reranker_model: Optional[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        # 初始化组件
        self.pdf_processor = PDFProcessor()
        self.text_splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.vectorizer = Vectorizer(model_name=embedding_model)
        self.reranker = Reranker(method=reranker_method, model_name=reranker_model)
        
        # 连接 Elasticsearch
        self.es_client = Elasticsearch(
            [f"http://{es_host}:{es_port}"],
            basic_auth=(es_user, es_password),
            verify_certs=False,
            request_timeout=60
        )
        self.index_name = index_name
        
        # 检查 Elasticsearch 连接
        try:
            if not self.es_client.ping():
                raise Exception("Cannot connect to Elasticsearch")
            print("✅ Connected to Elasticsearch")
        except Exception as e:
            print(f"❌ Elasticsearch connection failed: {e}")
            raise
        
        # 创建索引
        self._create_index()
        
        # LLM 客户端（可选）
        self.llm_client = None
        if OPENAI_AVAILABLE:
            try:
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.llm_client = OpenAI(api_key=api_key)
                    print("✅ OpenAI client initialized")
            except Exception as e:
                print(f"⚠️ OpenAI client not available: {e}")
    
    def _create_index(self):
        """创建 Elasticsearch 索引"""
        # 检查索引是否存在
        if self.es_client.indices.exists(index=self.index_name):
            print(f"Index {self.index_name} already exists")
            return
        
        # 创建索引映射
        mapping = {
            "mappings": {
                "properties": {
                    "text": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "text_vector": {
                        "type": "dense_vector",
                        "dims": self.vectorizer.dimension,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "page": {
                        "type": "integer"
                    },
                    "source": {
                        "type": "keyword"
                    },
                    "chunk_id": {
                        "type": "integer"
                    },
                    "metadata": {
                        "type": "object",
                        "enabled": False
                    }
                }
            }
        }
        
        self.es_client.indices.create(index=self.index_name, body=mapping)
        print(f"✅ Created index: {self.index_name}")
    
    def process_and_index_pdf(self, pdf_path: str, extract_images: bool = True, extract_tables: bool = True):
        """处理 PDF 并索引到 Elasticsearch"""
        print(f"\n{'='*60}")
        print(f"Processing PDF: {pdf_path}")
        print(f"{'='*60}")
        
        # 1. 处理 PDF
        pdf_data = self.pdf_processor.process_pdf(
            pdf_path,
            extract_images=extract_images,
            extract_tables=extract_tables
        )
        
        # 2. 切分文本
        print("\nSplitting text into chunks...")
        text_chunks = self.text_splitter.split_text_chunks(pdf_data['text_chunks'])
        print(f"Created {len(text_chunks)} text chunks")
        
        # 3. 生成向量
        print("\nGenerating embeddings...")
        texts = [chunk['text'] for chunk in text_chunks]
        embeddings = self.vectorizer.encode(texts)
        
        # 4. 准备文档索引
        print("\nPreparing documents for indexing...")
        documents = []
        for i, chunk in enumerate(text_chunks):
            doc = {
                "_index": self.index_name,
                "_id": hashlib.md5(f"{chunk['source']}_{chunk['page']}_{chunk['chunk_id']}".encode()).hexdigest(),
                "_source": {
                    "text": chunk['text'],
                    "text_vector": embeddings[i],
                    "page": chunk.get('page', 0),
                    "source": chunk.get('source', pdf_path),
                    "chunk_id": chunk.get('chunk_id', i),
                    "metadata": {
                        "method": chunk.get('method', 'unknown'),
                        "chunk_size": chunk.get('chunk_size', 0)
                    }
                }
            }
            documents.append(doc)
        
        # 5. 批量索引到 Elasticsearch
        print(f"\nIndexing {len(documents)} documents to Elasticsearch...")
        success, failed = bulk(self.es_client, documents, chunk_size=100, request_timeout=60)
        print(f"✅ Indexed {success} documents")
        if failed:
            print(f"⚠️ Failed to index {len(failed)} documents")
        
        # 刷新索引
        self.es_client.indices.refresh(index=self.index_name)
        print("✅ Index refreshed")
        
        return {
            'text_chunks_count': len(text_chunks),
            'images_count': len(pdf_data['images']),
            'tables_count': len(pdf_data['tables']),
            'indexed_documents': success
        }
    
    def hybrid_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """混合搜索（向量搜索 + BM25 搜索）"""
        # 1. 向量搜索
        query_vector = self.vectorizer.encode_single(query)
        
        vector_search = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'text_vector') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
        
        # 2. BM25 搜索
        bm25_search = {
            "match": {
                "text": {
                    "query": query,
                    "boost": 1.0
                }
            }
        }
        
        # 3. 混合搜索
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        vector_search,
                        bm25_search
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": top_k * 2,  # 获取更多结果用于重排序
            "_source": ["text", "page", "source", "chunk_id"]
        }
        
        response = self.es_client.search(index=self.index_name, body=search_body)
        results = response['hits']['hits']
        
        # 添加排名信息
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return results
    
    def search(self, query: str, top_k: int = 10, use_reranker: bool = True) -> List[Dict]:
        """搜索并重排序"""
        print(f"\nSearching for: '{query}'")
        
        # 1. 混合搜索
        search_results = self.hybrid_search(query, top_k=top_k * 2)
        print(f"Found {len(search_results)} results from hybrid search")
        
        # 2. 重排序
        if use_reranker and len(search_results) > 0:
            print(f"Reranking results using {self.reranker.method}...")
            reranked_results = self.reranker.rerank(query, search_results, top_k=top_k)
            print(f"Returning top {len(reranked_results)} results")
            return reranked_results
        else:
            return search_results[:top_k]
    
    def generate_answer(self, query: str, search_results: List[Dict], max_tokens: int = 500) -> str:
        """基于检索结果生成回答"""
        # 构建上下文
        context_parts = []
        for i, result in enumerate(search_results[:5]):  # 使用前5个结果
            source = result.get('_source', {})
            text = source.get('text', '')
            page = source.get('page', 0)
            context_parts.append(f"[来源: {source.get('source', 'unknown')}, 页码: {page}]\n{text}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # 如果有 OpenAI API，使用 GPT 生成回答
        if self.llm_client:
            try:
                prompt = f"""基于以下检索到的文档内容回答问题。

问题: {query}

相关文档:
{context}

请基于以上文档内容回答问题。如果文档中没有相关信息，请说明。回答要准确、简洁。"""
                
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是一个基于文档回答问题的助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                return response.choices[0].message.content
            except Exception as e:
                print(f"Error generating answer with OpenAI: {e}")
                return self._simple_answer(query, context, max_tokens)
        else:
            # 简单的回答生成（基于检索结果）
            return self._simple_answer(query, context, max_tokens)
    
    def _simple_answer(self, query: str, context: str, max_tokens: int = 500) -> str:
        """简单的回答生成（当没有 LLM API 时）"""
        # 找到最相关的段落
        best_match = context.split("\n\n---\n\n")[0] if context else ""
        
        answer = f"""基于检索到的文档，相关信息如下：

{best_match[:max_tokens]}

---
注意：这是基于检索结果的简单回答。要获得更好的回答，请配置 OpenAI API 密钥。"""
        
        return answer
    
    def query(self, question: str, top_k: int = 10, generate_answer: bool = True) -> Dict:
        """完整的查询流程：搜索 -> 重排序 -> 生成回答"""
        # 1. 搜索
        search_results = self.search(question, top_k=top_k, use_reranker=True)
        
        # 2. 生成回答
        answer = None
        if generate_answer:
            answer = self.generate_answer(question, search_results)
        
        return {
            'question': question,
            'answer': answer,
            'search_results': search_results,
            'num_results': len(search_results)
        }
    
    def get_index_stats(self) -> Dict:
        """获取索引统计信息"""
        stats = self.es_client.indices.stats(index=self.index_name)
        count = self.es_client.count(index=self.index_name)
        
        return {
            'index_name': self.index_name,
            'document_count': count['count'],
            'size': stats['indices'][self.index_name]['total']['store']['size_in_bytes']
        }


def main():
    """示例使用"""
    # 初始化 RAG 系统
    # 注意：密码请根据 ../elastic-start-local/.env 文件中的 ES_LOCAL_PASSWORD 值修改
    rag = RAGSystem(
        es_host="localhost",
        es_port=9200,
        es_user="elastic",
        es_password="w2b9I2dq",  # 请根据 ../elastic-start-local/.env 文件中的实际值修改
        index_name="rag_documents",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        reranker_method="rrf",  # 或 "reranker"
        chunk_size=500,
        chunk_overlap=50
    )
    
    # 处理 PDF 文件（请替换为实际的 PDF 文件路径）
    pdf_path = "example.pdf"  # 替换为你的 PDF 文件路径
    if os.path.exists(pdf_path):
        rag.process_and_index_pdf(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")
        print("Please provide a PDF file path to process.")
    
    # 查询示例
    question = "What is this document about?"
    result = rag.query(question, top_k=5)
    
    print(f"\n{'='*60}")
    print(f"Question: {result['question']}")
    print(f"{'='*60}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\n{'='*60}")
    print(f"Found {result['num_results']} relevant documents")
    print(f"{'='*60}")
    
    # 显示索引统计
    stats = rag.get_index_stats()
    print(f"\nIndex Statistics:")
    print(f"  Documents: {stats['document_count']}")
    print(f"  Size: {stats['size']} bytes")


if __name__ == "__main__":
    main()

