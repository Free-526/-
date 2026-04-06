"""
性能压测脚本
用于测试API性能和并发能力
"""
import asyncio
import aiohttp
import time
import statistics
from datetime import datetime
from typing import List, Dict
import json


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
        headers: dict = None,
        concurrent: int = 10,
        total_requests: int = 100
    ) -> Dict:
        """压测单个接口"""
        
        url = f"{self.base_url}{endpoint}"
        latencies = []
        errors = 0
        semaphore = asyncio.Semaphore(concurrent)
        
        async def single_request(session):
            async with semaphore:
                try:
                    start = time.time()
                    
                    if method == "GET":
                        async with session.get(url, headers=headers, timeout=30) as resp:
                            await resp.text()
                    else:
                        async with session.post(url, json=data, headers=headers, timeout=30) as resp:
                            await resp.text()
                    
                    latency = (time.time() - start) * 1000  # ms
                    return latency
                except Exception as e:
                    print(f"Request error: {e}")
                    return None
        
        # 执行压测
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = [single_request(session) for _ in range(total_requests)]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result is not None:
                    latencies.append(result)
                else:
                    errors += 1
        
        total_time = time.time() - start_time
        
        if not latencies:
            return {
                "endpoint": endpoint,
                "error": "All requests failed"
            }
        
        latencies.sort()
        
        return {
            "endpoint": endpoint,
            "method": method,
            "concurrent": concurrent,
            "total_requests": total_requests,
            "successful_requests": len(latencies),
            "failed_requests": errors,
            "success_rate": f"{len(latencies)/total_requests*100:.1f}%",
            "qps": len(latencies) / total_time,
            "latency_avg_ms": statistics.mean(latencies),
            "latency_min_ms": min(latencies),
            "latency_max_ms": max(latencies),
            "latency_p50_ms": latencies[int(len(latencies)*0.5)],
            "latency_p95_ms": latencies[int(len(latencies)*0.95)],
            "latency_p99_ms": latencies[int(len(latencies)*0.99)] if len(latencies) >= 100 else max(latencies),
            "total_time_sec": total_time
        }
    
    async def run_all_benchmarks(self):
        """运行所有压测"""
        print("=" * 60)
        print("🚀 API 性能压测开始")
        print("=" * 60)
        
        # 1. 健康检查接口
        print("\n📊 测试: 健康检查接口")
        result = await self.benchmark_endpoint("/api/health", concurrent=50, total_requests=500)
        self.print_result(result)
        self.results.append(result)
        
        # 2. 登录接口
        print("\n📊 测试: 登录接口")
        result = await self.benchmark_endpoint(
            "/api/auth/login",
            method="POST",
            data={"username": "admin", "password": "admin123"},
            concurrent=10,
            total_requests=50
        )
        self.print_result(result)
        self.results.append(result)
        
        # 3. 文献列表接口（需要token）
        # 先获取token
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "admin", "password": "admin123"}
            ) as resp:
                login_data = await resp.json()
                token = login_data.get("data", {}).get("access_token", "")
        
        if token:
            print("\n📊 测试: 文献列表接口")
            result = await self.benchmark_endpoint(
                "/api/papers",
                headers={"Authorization": f"Bearer {token}"},
                concurrent=20,
                total_requests=200
            )
            self.print_result(result)
            self.results.append(result)
        
        # 生成报告
        self.generate_report()
    
    def print_result(self, result: Dict):
        """打印压测结果"""
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
            return
        
        print(f"\n  接口: {result['endpoint']}")
        print(f"  方法: {result['method']}")
        print(f"  并发数: {result['concurrent']}")
        print(f"  总请求: {result['total_requests']}")
        print(f"  成功: {result['successful_requests']}")
        print(f"  失败: {result['failed_requests']}")
        print(f"  成功率: {result['success_rate']}")
        print(f"  QPS: {result['qps']:.2f}")
        print(f"  平均延迟: {result['latency_avg_ms']:.2f}ms")
        print(f"  P95延迟: {result['latency_p95_ms']:.2f}ms")
        print(f"  P99延迟: {result['latency_p99_ms']:.2f}ms")
        print(f"  总耗时: {result['total_time_sec']:.2f}s")
    
    def generate_report(self):
        """生成压测报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "results": self.results
        }
        
        # 保存到文件
        filename = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print(f"✅ 压测报告已保存: {filename}")
        print("=" * 60)


async def main():
    """主函数"""
    benchmark = APIBenchmark()
    await benchmark.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())
