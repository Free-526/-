"""
RAG检索效果评测
评测向量检索的准确率和召回率
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import json
import time
from typing import List, Dict, Tuple
from dataclasses import dataclass

from app.core.embedder import get_embedder
from app.core.faiss_retriever import get_retriever
from app.models.database import get_db_session, Chunk, Paper


@dataclass
class RetrievalTestCase:
    """检索测试用例"""
    query: str
    relevant_chunk_ids: List[int]  # 相关的文本块ID
    paper_id: int  # 所属论文ID
    description: str  # 测试描述


class RetrievalEvaluator:
    """RAG检索评测器"""

    def __init__(self):
        self.embedder = get_embedder()
        self.retriever = get_retriever()
        self.test_cases: List[RetrievalTestCase] = []

    def load_test_cases(self, filepath: str = None):
        """加载测试用例"""
        # 内置测试用例
        self.test_cases = [
            RetrievalTestCase(
                query="这篇论文用了什么数据集？",
                relevant_chunk_ids=[],
                paper_id=1,
                description="数据集查询"
            ),
            RetrievalTestCase(
                query="实验结果怎么样？",
                relevant_chunk_ids=[],
                paper_id=1,
                description="实验结果查询"
            ),
            RetrievalTestCase(
                query="作者提出了什么方法？",
                relevant_chunk_ids=[],
                paper_id=1,
                description="方法查询"
            ),
            RetrievalTestCase(
                query="这篇论文的创新点是什么？",
                relevant_chunk_ids=[],
                paper_id=1,
                description="创新点查询"
            ),
            RetrievalTestCase(
                query="论文的结论是什么？",
                relevant_chunk_ids=[],
                paper_id=1,
                description="结论查询"
            ),
        ]

        # 从文件加载更多测试用例
        if filepath and os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    self.test_cases.append(RetrievalTestCase(**item))

    def evaluate(self, top_k: int = 5) -> Dict:
        """执行评测"""
        if not self.test_cases:
            print("⚠️ 没有测试用例，请先加载")
            return {}

        results = []

        for i, test_case in enumerate(self.test_cases):
            print(f"\n🔍 测试 {i+1}/{len(self.test_cases)}: {test_case.description}")
            print(f"   查询: {test_case.query}")

            # 执行检索
            start_time = time.time()
            query_vector = self.embedder.encode([test_case.query], normalize=True)
            search_results = self.retriever.search(query_vector[0], top_k=top_k, threshold=0.1)
            retrieval_time = (time.time() - start_time) * 1000

            # 计算指标
            result_ids = [r.get('chunk_id') for r in search_results if 'chunk_id' in r]

            # Hit@K
            hits = sum(1 for cid in test_case.relevant_chunk_ids if cid in result_ids)
            hit_at_k = 1 if hits > 0 else 0

            # Recall@K
            recall_at_k = hits / len(test_case.relevant_chunk_ids) if test_case.relevant_chunk_ids else 0

            # MRR
            mrr = 0
            for rank, cid in enumerate(result_ids, 1):
                if cid in test_case.relevant_chunk_ids:
                    mrr = 1 / rank
                    break

            result = {
                'query': test_case.query,
                'description': test_case.description,
                'retrieval_time_ms': retrieval_time,
                'results_count': len(search_results),
                'hit_at_k': hit_at_k,
                'recall_at_k': recall_at_k,
                'mrr': mrr
            }
            results.append(result)

            print(f"   检索时间: {retrieval_time:.2f}ms")
            print(f"   结果数: {len(search_results)}")
            print(f"   Hit@{top_k}: {hit_at_k}")
            print(f"   Recall@{top_k}: {recall_at_k:.2%}")
            print(f"   MRR: {mrr:.4f}")

        # 汇总统计
        avg_recall = sum(r['recall_at_k'] for r in results) / len(results)
        avg_mrr = sum(r['mrr'] for r in results) / len(results)
        avg_time = sum(r['retrieval_time_ms'] for r in results) / len(results)
        total_hits = sum(r['hit_at_k'] for r in results)

        summary = {
            'total_queries': len(results),
            'hit_at_k_rate': total_hits / len(results),
            'avg_recall_at_k': avg_recall,
            'avg_mrr': avg_mrr,
            'avg_retrieval_time_ms': avg_time,
            'details': results
        }

        return summary

    def print_report(self, summary: Dict):
        """打印评测报告"""
        print("\n" + "="*60)
        print("📊 RAG检索评测报告")
        print("="*60)
        print(f"总查询数: {summary['total_queries']}")
        print(f"Hit@K 命中率: {summary['hit_at_k_rate']:.2%}")
        print(f"平均 Recall@K: {summary['avg_recall_at_k']:.2%}")
        print(f"平均 MRR: {summary['avg_mrr']:.4f}")
        print(f"平均检索时间: {summary['avg_retrieval_time_ms']:.2f}ms")
        print("="*60)

        # 评级
        if summary['avg_recall_at_k'] >= 0.8:
            grade = "优秀 🟢"
        elif summary['avg_recall_at_k'] >= 0.6:
            grade = "良好 🟡"
        else:
            grade = "需改进 🔴"

        print(f"\n综合评级: {grade}")

        if summary['avg_recall_at_k'] < 0.6:
            print("\n💡 改进建议:")
            print("  1. 考虑更换更强的嵌入模型")
            print("  2. 调整分块策略（大小/重叠）")
            print("  3. 降低相似度阈值")
            print("  4. 增加重排序(Rerank)步骤")


def generate_test_cases_from_db(output_file: str = "test_cases.json"):
    """从数据库生成测试用例"""
    # 确保数据库表结构被创建
    from app.models.database import init_db
    init_db()

    db = get_db_session()

    try:
        # 获取所有活跃的论文
        papers = db.query(Paper).filter(Paper.status == "active").limit(10).all()

        test_cases = []
        for paper in papers:
            # 获取该论文的chunks
            chunks = db.query(Chunk).filter(Chunk.paper_id == paper.id).all()

            if len(chunks) < 3:
                continue

            # 为前3个chunk生成测试问题（简化版）
            for i, chunk in enumerate(chunks[:3]):
                # 提取chunk的前20字作为查询
                query = chunk.content[:20] + "..."

                test_cases.append({
                    "query": query,
                    "relevant_chunk_ids": [chunk.id],
                    "paper_id": paper.id,
                    "description": f"Paper {paper.id} Chunk {i+1}"
                })

        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, ensure_ascii=False, indent=2)

        print(f"✅ 已生成 {len(test_cases)} 个测试用例到 {output_file}")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='RAG检索评测工具')
    parser.add_argument('--generate', action='store_true', help='从数据库生成测试用例')
    parser.add_argument('--test-file', type=str, help='测试用例文件路径')
    parser.add_argument('--top-k', type=int, default=5, help='检索结果数量')

    args = parser.parse_args()

    if args.generate:
        generate_test_cases_from_db()
    else:
        # 执行评测
        evaluator = RetrievalEvaluator()
        evaluator.load_test_cases(args.test_file)

        if evaluator.test_cases:
            summary = evaluator.evaluate(top_k=args.top_k)
            evaluator.print_report(summary)
        else:
            print("⚠️ 没有测试用例，请先运行 --generate 生成")