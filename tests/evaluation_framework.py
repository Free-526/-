"""
自动化评测脚本
用于评测论文小助手的各项功能和性能指标
"""
import os
import sys
import time
import json
import asyncio
import statistics
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import requests
from concurrent.futures import ThreadPoolExecutor


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    passed: bool
    score: float  # 0-100
    duration_ms: float
    details: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class EvaluationReport:
    """评测报告生成器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
    
    def add_result(self, result: TestResult):
        self.results.append(result)
    
    def generate(self) -> Dict[str, Any]:
        """生成评测报告"""
        total_duration = time.time() - self.start_time
        
        passed_tests = sum(1 for r in self.results if r.passed)
        total_tests = len(self.results)
        avg_score = statistics.mean([r.score for r in self.results]) if self.results else 0
        
        # 按类别分组
        categories = {}
        for result in self.results:
            category = result.test_name.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        category_scores = {}
        for cat, results in categories.items():
            category_scores[cat] = {
                'avg_score': statistics.mean([r.score for r in results]),
                'passed': sum(1 for r in results if r.passed),
                'total': len(results)
            }
        
        return {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'pass_rate': f"{passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "0%",
                'avg_score': f"{avg_score:.2f}",
                'total_duration_sec': f"{total_duration:.2f}",
                'generated_at': datetime.now().isoformat()
            },
            'category_scores': category_scores,
            'details': [asdict(r) for r in self.results]
        }
    
    def save(self, filepath: str):
        """保存报告到文件"""
        report = self.generate()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"✅ 评测报告已保存: {filepath}")
    
    def print_summary(self):
        """打印报告摘要"""
        report = self.generate()
        summary = report['summary']
        
        print("\n" + "="*60)
        print("📊 评测报告摘要")
        print("="*60)
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过数: {summary['passed_tests']}")
        print(f"通过率: {summary['pass_rate']}")
        print(f"平均得分: {summary['avg_score']}")
        print(f"总耗时: {summary['total_duration_sec']}s")
        print("="*60)
        
        print("\n📈 分类得分:")
        for cat, scores in report['category_scores'].items():
            print(f"  {cat}: {scores['avg_score']:.2f} ({scores['passed']}/{scores['total']})")
        
        print("\n❌ 失败的测试:")
        failed = [r for r in self.results if not r.passed]
        if failed:
            for r in failed:
                print(f"  - {r.test_name}: {r.score:.2f}分")
        else:
            print("  无")
        
        print("="*60 + "\n")


class APIBenchmark:
    """API性能压测工具"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    async def benchmark_endpoint(
        self, 
        endpoint: str, 
        method: str = "GET",
        data: dict = None,
        concurrent: int = 10,
        total_requests: int = 100
    ) -> Dict[str, Any]:
        """压测单个接口"""
        
        url = f"{self.base_url}{endpoint}"
        latencies = []
        errors = 0
        
        async def single_request():
            try:
                start = time.time()
                if method == "GET":
                    response = requests.get(url, timeout=30)
                else:
                    response = requests.post(url, json=data, timeout=30)
                
                latency = (time.time() - start) * 1000  # ms
                
                if response.status_code == 200:
                    return latency
                else:
                    return None
            except Exception as e:
                return None
        
        # 执行压测
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(asyncio.run, single_request()) 
                      for _ in range(total_requests)]
            
            for future in futures:
                result = future.result()
                if result is not None:
                    latencies.append(result)
                else:
                    errors += 1
        
        total_time = time.time() - start_time
        
        if not latencies:
            return {
                'endpoint': endpoint,
                'error': 'All requests failed'
            }
        
        return {
            'endpoint': endpoint,
            'concurrent': concurrent,
            'total_requests': total_requests,
            'successful_requests': len(latencies),
            'failed_requests': errors,
            'qps': len(latencies) / total_time,
            'latency_avg_ms': statistics.mean(latencies),
            'latency_min_ms': min(latencies),
            'latency_max_ms': max(latencies),
            'latency_p50_ms': statistics.median(latencies),
            'latency_p95_ms': sorted(latencies)[int(len(latencies)*0.95)],
            'latency_p99_ms': sorted(latencies)[int(len(latencies)*0.99)] if len(latencies) >= 100 else max(latencies)
        }


if __name__ == "__main__":
    # 示例用法
    report = EvaluationReport()
    
    # 添加模拟结果
    report.add_result(TestResult(
        test_name="api_health_check",
        passed=True,
        score=100,
        duration_ms=45.2,
        details={'status_code': 200}
    ))
    
    report.print_summary()
