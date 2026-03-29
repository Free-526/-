# AI论文小助手 - 产品需求文档 (PRD)

## 1. 项目概述

### 1.1 产品定位
AI论文小助手是一款面向学术研究人员、学生和科研工作者的智能文献管理工具。通过RAG（检索增强生成）技术，结合Kimi大模型能力，实现PDF文献的智能分析、对话问答、综述生成以及数据可视化功能。

### 1.2 核心功能
- 📚 **文献智能库**：多PDF导入、向量化存储、智能检索
- 💬 **智能对话**：基于文献内容的问答系统
- 📝 **综述生成**：自动生成文献综述
- 📊 **图表生成**：Excel/CSV数据可视化（折线图、柱状图）

### 1.3 技术栈
| 模块 | 技术选型 |
|------|----------|
| 后端框架 | Python + FastAPI |
| 大模型 | Kimi (Moonshot AI API) |
| 向量数据库 | FAISS |
| 文档解析 | PyPDF2 / pdfplumber |
| 文本向量化 | sentence-transformers |
| 数据可视化 | matplotlib / plotly |
| 前端 | React / Vue3 |
| 数据存储 | SQLite / 本地文件 |

---

## 2. 系统架构

### 2.1 整体架构图
```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Frontend)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  文献管理页面  │  │  对话问答页面  │  │    图表生成页面       │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API 层 (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ 文献管理API  │  │ 对话问答API  │  │    图表生成API        │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     核心服务层 (Core Services)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ PDF解析服务  │  │ RAG检索服务  │  │   Kimi调用服务       │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ 文本向量化   │  │ 综述生成服务 │  │   数据可视化服务      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据存储层 (Storage)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   SQLite     │  │    FAISS     │  │    本地文件系统       │   │
│  │ (元数据存储) │  │ (向量索引)   │  │  (PDF/Excel/CSV)     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

#### 文献导入流程
```
用户上传PDF → PDF解析 → 文本分块 → 向量化 → FAISS存储 + SQLite元数据
```

#### 对话问答流程
```
用户提问 → 问题向量化 → FAISS相似度检索 → 获取相关文本块 → 
构建Prompt → Kimi API调用 → 返回答案
```

#### 综述生成流程
```
选择文献范围 → 批量检索相关段落 → 构建综述Prompt → 
Kimi生成综述 → 返回结构化综述文本
```

---

## 3. 功能模块详细设计

### 3.1 文献管理模块

#### 3.1.1 PDF导入功能
- **支持格式**：PDF文件（单文件或多文件批量上传）
- **文件大小限制**：单个文件最大50MB，批量上传最多20个文件
- **解析内容**：
  - 标题、作者、摘要、关键词（自动提取）
  - 正文内容（按段落分块）
  - 图表说明文字
- **元数据存储**：
  ```sql
  CREATE TABLE papers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_name TEXT NOT NULL,
      file_path TEXT NOT NULL,
      title TEXT,
      authors TEXT,
      abstract TEXT,
      keywords TEXT,
      upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
      page_count INTEGER,
      vector_index_id TEXT,
      status TEXT DEFAULT 'active'
  );
  ```

#### 3.1.2 文献库管理
- 文献列表展示（支持分页、搜索、筛选）
- 文献删除（同步删除向量库中的数据）
- 文献分类标签（支持自定义标签）
- 批量操作（批量删除、批量导出）

### 3.2 RAG对话模块

#### 3.2.1 文本向量化策略
- **分块策略**：
  - 按段落分割（默认）
  - 按固定token数分割（512 tokens/块，重叠128 tokens）
  - 保留段落完整性
- **向量化模型**：`sentence-transformers/all-MiniLM-L6-v2`（轻量级，384维）
  - 或 `BAAI/bge-large-zh-v1.5`（中文效果更好，1024维）
- **FAISS索引类型**：IndexFlatIP（内积相似度）或 IndexIVFFlat（大规模优化）

#### 3.2.2 检索策略
```python
# 检索参数
retrieval_config = {
    "top_k": 5,                    # 返回最相关的5个文本块
    "similarity_threshold": 0.7,   # 相似度阈值
    "rerank_enabled": True,        # 是否启用重排序
    "context_window": 3            # 上下文窗口（前后各3个段落）
}
```

#### 3.2.3 对话管理
- 多轮对话支持（保留对话历史）
- 对话上下文关联（基于历史问题优化检索）
- 答案溯源（显示引用来源文献及页码）

#### 3.2.4 Prompt设计
```
【系统提示】
你是一位专业的学术助手，擅长分析和总结学术论文。请基于以下提供的文献内容，回答用户的问题。
如果提供的文献内容不足以回答问题，请明确告知。

【文献内容】
{retrieved_context}

【对话历史】
{chat_history}

【用户问题】
{user_question}

【回答要求】
1. 基于文献内容作答，不要编造信息
2. 如涉及多个文献，请分别说明
3. 引用格式：[文献标题, 第X页]
```

### 3.3 综述生成模块

#### 3.3.1 生成模式
- **全文综述**：基于整个文献库生成领域综述
- **选文综述**：基于选定的若干文献生成综述
- **主题综述**：基于特定主题词检索相关文献生成综述

#### 3.3.2 综述结构
```
1. 研究背景与意义
2. 相关研究综述
   2.1 [细分主题1]
   2.2 [细分主题2]
   ...
3. 研究方法对比
4. 主要发现与结论
5. 研究不足与展望
6. 参考文献列表
```

#### 3.3.3 综述Prompt设计
```
【系统提示】
你是一位资深的学术综述撰写专家。请基于以下文献内容，撰写一篇结构化的学术综述。

【任务要求】
- 综述主题：{topic}
- 文献数量：{paper_count}篇
- 字数要求：{word_count}字
- 输出语言：{language}

【文献内容摘要】
{papers_summary}

【详细内容】
{retrieved_content}

【输出格式】
请按以下结构输出：
1. 标题（简洁明确）
2. 摘要（200-300字）
3. 正文（分章节论述）
4. 总结与展望
```

### 3.4 图表生成模块

#### 3.4.1 数据导入
- **支持格式**：Excel (.xlsx, .xls)、CSV (.csv)
- **文件大小限制**：最大10MB
- **数据预览**：导入后显示数据预览（前10行）
- **数据清洗提示**：自动识别缺失值、异常值

#### 3.4.2 图表配置
| 配置项 | 选项 |
|--------|------|
| 图表类型 | 折线图、柱状图、散点图、饼图 |
| X轴 | 选择数据列 / 设置范围 / 设置标签 |
| Y轴 | 选择数据列 / 设置范围 / 设置标签 |
| 数据筛选 | 行范围选择 / 条件筛选 |
| 样式设置 | 颜色主题、标题、图例、网格线 |
| 导出格式 | PNG、JPG、SVG、PDF |

#### 3.4.3 交互功能
- 数据列自动识别（数值型、类别型、时间型）
- 实时预览（配置变更即时刷新图表）
- 图表交互（缩放、悬停提示、数据点选中）

---

## 4. 数据库设计

### 4.1 SQLite 表结构

```sql
-- 文献表
CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    title TEXT,
    authors TEXT,  -- JSON格式存储
    abstract TEXT,
    keywords TEXT,  -- JSON格式存储
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    page_count INTEGER,
    chunk_count INTEGER,
    status TEXT DEFAULT 'active',  -- active, deleted, processing
    UNIQUE(file_path)
);

-- 文本块表（向量化后的文本片段）
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    faiss_id INTEGER,  -- FAISS中的向量ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- 对话会话表
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 对话消息表
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    references TEXT,  -- JSON格式，引用文献信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- 数据集表
CREATE TABLE datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- excel, csv
    sheet_name TEXT,  -- Excel的sheet名
    columns TEXT,  -- JSON格式，列信息
    row_count INTEGER,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 图表配置表
CREATE TABLE chart_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    chart_name TEXT,
    chart_type TEXT NOT NULL,  -- line, bar, scatter, pie
    x_column TEXT NOT NULL,
    y_column TEXT NOT NULL,
    x_range TEXT,  -- JSON格式 [min, max]
    y_range TEXT,
    filter_config TEXT,  -- JSON格式筛选配置
    style_config TEXT,  -- JSON格式样式配置
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);
```

### 4.2 FAISS 索引设计

```python
# 索引结构
class VectorIndex:
    def __init__(self, dim=384):
        self.dim = dim
        # 使用内积作为相似度度量（已归一化的向量等价于余弦相似度）
        self.index = faiss.IndexFlatIP(dim)
        # ID映射：FAISS ID -> (paper_id, chunk_id)
        self.id_map = {}
    
    def add_vectors(self, vectors, metadata):
        """
        Args:
            vectors: numpy array of shape (n, dim)
            metadata: list of dict [{'paper_id': x, 'chunk_id': y}, ...]
        """
        start_id = self.index.ntotal
        self.index.add(vectors)
        for i, meta in enumerate(metadata):
            self.id_map[start_id + i] = meta
    
    def search(self, query_vector, k=5):
        """
        Returns:
            distances, indices, metadata
        """
        distances, indices = self.index.search(query_vector, k)
        metadata = [self.id_map.get(idx) for idx in indices[0]]
        return distances[0], indices[0], metadata
```

---

## 5. API 接口设计

### 5.1 文献管理接口

```yaml
# 上传PDF
POST /api/papers/upload
Content-Type: multipart/form-data
Body:
  files: [File]  # 支持多文件
Response:
  {
    "code": 200,
    "data": {
      "uploaded": [{
        "id": 1,
        "file_name": "paper1.pdf",
        "status": "processing"
      }],
      "failed": []
    }
  }

# 获取文献列表
GET /api/papers?page=1&size=20&keyword=&sort_by=upload_time
Response:
  {
    "code": 200,
    "data": {
      "total": 100,
      "items": [{
        "id": 1,
        "title": "...",
        "authors": [...],
        "upload_time": "2024-01-01T00:00:00",
        "status": "active"
      }]
    }
  }

# 删除文献
DELETE /api/papers/{id}

# 获取文献详情
GET /api/papers/{id}
```

### 5.2 对话接口

```yaml
# 创建会话
POST /api/chat/sessions
Body:
  { "session_name": "新会话" }

# 获取会话列表
GET /api/chat/sessions

# 发送消息
POST /api/chat/messages
Body:
  {
    "session_id": 1,
    "message": "请总结这篇论文的主要贡献",
    "paper_ids": [1, 2, 3]  # 可选，指定文献范围
  }
Response (Stream):
  {
    "type": "content",  # content / reference / done / error
    "data": "..."
  }

# 获取历史消息
GET /api/chat/sessions/{id}/messages
```

### 5.3 综述生成接口

```yaml
# 生成综述
POST /api/review/generate
Body:
  {
    "topic": "深度学习在医学影像中的应用",
    "paper_ids": [1, 2, 3],  # 可选，不传则使用全部文献
    "word_count": 3000,
    "language": "zh",
    "structure": "standard"  # standard / custom
  }
Response (Stream):
  {
    "type": "content",
    "data": "..."
  }

# 导出综述
POST /api/review/export
Body:
  {
    "content": "...",
    "format": "pdf"  # pdf / docx / markdown
  }
```

### 5.4 图表生成接口

```yaml
# 上传数据文件
POST /api/charts/datasets
Content-Type: multipart/form-data
Body:
  file: File
Response:
  {
    "code": 200,
    "data": {
      "id": 1,
      "columns": [
        {"name": "年份", "type": "int"},
        {"name": "销量", "type": "float"}
      ],
      "preview": [...]
    }
  }

# 生成图表
POST /api/charts/generate
Body:
  {
    "dataset_id": 1,
    "chart_type": "line",
    "x_column": "年份",
    "y_column": "销量",
    "x_range": [2010, 2024],
    "y_range": null,
    "style": {
      "title": "年度销量趋势",
      "color": "#1890ff"
    }
  }
Response:
  {
    "code": 200,
    "data": {
      "chart_url": "/static/charts/chart_123.png",
      "chart_data": {...}
    }
  }

# 导出图表
GET /api/charts/{id}/export?format=png
```

---

## 6. 项目目录结构

```
论文小助手/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI入口
│   │   ├── config.py          # 配置文件
│   │   ├── api/               # API路由
│   │   │   ├── __init__.py
│   │   │   ├── papers.py      # 文献接口
│   │   │   ├── chat.py        # 对话接口
│   │   │   ├── review.py      # 综述接口
│   │   │   └── charts.py      # 图表接口
│   │   ├── core/              # 核心业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py  # PDF解析
│   │   │   ├── embedder.py    # 文本向量化
│   │   │   ├── retriever.py   # FAISS检索
│   │   │   ├── kim_client.py  # Kimi API封装
│   │   │   ├── reviewer.py    # 综述生成
│   │   │   └── chart_gen.py   # 图表生成
│   │   ├── models/            # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── database.py    # SQLAlchemy模型
│   │   │   └── schemas.py     # Pydantic模型
│   │   └── services/          # 服务层
│   │       ├── __init__.py
│   │       ├── paper_service.py
│   │       ├── chat_service.py
│   │       └── chart_service.py
│   ├── data/                  # 数据存储
│   │   ├── uploads/           # 上传文件
│   │   ├── vectors/           # FAISS索引文件
│   │   └── charts/            # 生成图表
│   ├── requirements.txt
│   └── run.py
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/        # 组件
│   │   ├── views/             # 页面
│   │   ├── api/               # API封装
│   │   ├── stores/            # 状态管理
│   │   └── utils/             # 工具函数
│   ├── package.json
│   └── vite.config.js
│
├── docs/                       # 文档
│   └── PRD.md
│
└── README.md
```

---

## 7. 核心代码示例

### 7.1 FAISS向量检索实现

```python
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import pickle
import os

class FAISSRetriever:
    def __init__(self, dim: int = 384, index_path: str = None):
        self.dim = dim
        self.index_path = index_path
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.metadata = {}  # faiss_id -> chunk_info
        
        if index_path and os.path.exists(index_path):
            self.load_index()
        else:
            self.index = faiss.IndexFlatIP(dim)  # 内积相似度
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """文本向量化"""
        embeddings = self.encoder.encode(texts, convert_to_numpy=True)
        # L2归一化，使内积等价于余弦相似度
        faiss.normalize_L2(embeddings)
        return embeddings.astype('float32')
    
    def add_documents(self, chunks: List[Dict]):
        """
        添加文档到索引
        chunks: [{"paper_id": 1, "chunk_id": 1, "content": "..."}, ...]
        """
        if not chunks:
            return
        
        texts = [c["content"] for c in chunks]
        embeddings = self.encode(texts)
        
        start_id = self.index.ntotal
        self.index.add(embeddings)
        
        # 保存metadata
        for i, chunk in enumerate(chunks):
            self.metadata[start_id + i] = {
                "paper_id": chunk["paper_id"],
                "chunk_id": chunk["chunk_id"],
                "content": chunk["content"],
                "page_number": chunk.get("page_number")
            }
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索相关文档"""
        query_vector = self.encode([query])
        
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx in self.metadata:
                result = self.metadata[idx].copy()
                result["score"] = float(dist)
                results.append(result)
        
        return results
    
    def save_index(self):
        """保存索引到磁盘"""
        if self.index_path:
            faiss.write_index(self.index, self.index_path)
            with open(self.index_path + ".meta", "wb") as f:
                pickle.dump(self.metadata, f)
    
    def load_index(self):
        """从磁盘加载索引"""
        self.index = faiss.read_index(self.index_path)
        meta_path = self.index_path + ".meta"
        if os.path.exists(meta_path):
            with open(meta_path, "rb") as f:
                self.metadata = pickle.load(f)
```

### 7.2 Kimi API 调用封装

```python
import openai
from typing import List, Dict, Iterator
import os

class KimiClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self.model = "moonshot-v1-128k"  # 或 32k, 8k
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = True,
        temperature: float = 0.3
    ) -> Iterator[str]:
        """
        调用Kimi对话接口
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                temperature=temperature
            )
            
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
                
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def build_rag_prompt(
        self,
        query: str,
        contexts: List[Dict],
        chat_history: List[Dict] = None
    ) -> List[Dict]:
        """
        构建RAG对话的Prompt
        """
        # 构建上下文
        context_text = "\n\n".join([
            f"【文献 {i+1}】{ctx.get('title', 'Unknown')}, 第{ctx.get('page_number', '?')}页\n{ctx['content'][:1000]}"
            for i, ctx in enumerate(contexts)
        ])
        
        system_prompt = f"""你是一位专业的学术助手。请基于以下文献内容回答用户问题。
如果文献内容不足以回答问题，请明确告知。

【相关文献内容】
{context_text}

回答时请：
1. 基于文献内容作答，不要编造
2. 引用来源格式：[文献标题, 第X页]
3. 如涉及多个文献，请分别说明"""

        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史对话
        if chat_history:
            messages.extend(chat_history)
        
        messages.append({"role": "user", "content": query})
        
        return messages
```

### 7.3 PDF解析实现

```python
import pdfplumber
from typing import List, Dict
import re

class PDFParser:
    def __init__(self):
        self.chunk_size = 512  # 每块大约字符数
        self.chunk_overlap = 128
    
    def parse(self, file_path: str) -> Dict:
        """解析PDF文件"""
        result = {
            "title": "",
            "authors": [],
            "abstract": "",
            "keywords": [],
            "chunks": [],
            "page_count": 0
        }
        
        with pdfplumber.open(file_path) as pdf:
            result["page_count"] = len(pdf.pages)
            full_text = ""
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                full_text += f"\n\n--- Page {page_num} ---\n{text}"
            
            # 提取元数据（简化版，实际可用正则或NLP）
            result["title"] = self._extract_title(full_text)
            result["abstract"] = self._extract_abstract(full_text)
            result["chunks"] = self._split_into_chunks(full_text)
        
        return result
    
    def _extract_title(self, text: str) -> str:
        """提取标题（取第一段非空文本）"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        return lines[0] if lines else "Unknown"
    
    def _extract_abstract(self, text: str) -> str:
        """提取摘要"""
        match = re.search(r'Abstract[\s:]*(.+?)(?=\n\n|Keywords|Introduction)', 
                         text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def _split_into_chunks(self, text: str) -> List[Dict]:
        """将文本分块"""
        # 按段落分割
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        current_pages = []
        
        for para in paragraphs:
            # 提取页码信息
            page_match = re.search(r'--- Page (\d+) ---', para)
            if page_match:
                current_pages.append(int(page_match.group(1)))
                continue
            
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "page_number": current_pages[0] if current_pages else 1
                    })
                current_chunk = para
                current_pages = current_pages[-1:] if current_pages else []
            else:
                current_chunk += "\n\n" + para
        
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "page_number": current_pages[0] if current_pages else 1
            })
        
        return chunks
```

### 7.4 图表生成实现

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
import io
import base64

class ChartGenerator:
    def __init__(self):
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        sns.set_style("whitegrid")
    
    def load_data(self, file_path: str, sheet_name: str = None) -> pd.DataFrame:
        """加载数据文件"""
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        else:
            return pd.read_excel(file_path, sheet_name=sheet_name)
    
    def generate_chart(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x_column: str,
        y_column: str,
        x_range: Optional[List] = None,
        y_range: Optional[List] = None,
        style: Dict = None
    ) -> str:
        """
        生成图表，返回base64编码的图片
        """
        style = style or {}
        
        # 数据筛选
        if x_range:
            df = df[(df[x_column] >= x_range[0]) & (df[x_column] <= x_range[1])]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == "line":
            ax.plot(df[x_column], df[y_column], 
                   marker='o', linewidth=2, 
                   color=style.get('color', '#1890ff'))
        elif chart_type == "bar":
            ax.bar(df[x_column], df[y_column], 
                  color=style.get('color', '#1890ff'),
                  alpha=0.8)
        elif chart_type == "scatter":
            ax.scatter(df[x_column], df[y_column], 
                      c=style.get('color', '#1890ff'),
                      alpha=0.6, s=50)
        
        # 设置标签和标题
        ax.set_xlabel(x_column, fontsize=12)
        ax.set_ylabel(y_column, fontsize=12)
        ax.set_title(style.get('title', f'{y_column} vs {x_column}'), fontsize=14)
        
        # 设置坐标轴范围
        if y_range:
            ax.set_ylim(y_range)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 转为base64
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return f"data:image/png;base64,{image_base64}"
```

---

## 8. 部署与配置

### 8.1 环境变量配置

```bash
# .env 文件
KIMI_API_KEY=your_kimi_api_key_here
DB_PATH=./data/papers.db
VECTOR_INDEX_PATH=./data/vectors/faiss.index
UPLOAD_DIR=./data/uploads
CHART_DIR=./data/charts
MAX_FILE_SIZE=52428800  # 50MB
CHUNK_SIZE=512
CHUNK_OVERLAP=128
TOP_K_RETRIEVAL=5
```

### 8.2 依赖安装

```txt
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
sqlalchemy==2.0.23
faiss-cpu==1.7.4
sentence-transformers==2.2.2
pdfplumber==0.10.0
openai==1.3.6
pandas==2.1.3
matplotlib==3.8.2
seaborn==0.13.0
openpyxl==3.1.2
python-dotenv==1.0.0
pydantic==2.5.2
numpy==1.26.2
```

### 8.3 启动命令

```bash
# 后端启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端启动（开发模式）
cd frontend
npm install
npm run dev
```

---

## 9. 功能验收标准

### 9.1 文献管理
- [ ] 支持单次上传最多20个PDF文件
- [ ] 解析准确率 > 90%（标题、作者、摘要）
- [ ] 100页PDF处理时间 < 30秒
- [ ] 向量化存储成功率 100%

### 9.2 智能对话
- [ ] 问答响应时间 < 5秒（不含大模型生成时间）
- [ ] 答案溯源准确率 > 95%
- [ ] 支持多轮对话上下文关联
- [ ] 支持指定文献范围问答

### 9.3 综述生成
- [ ] 生成3000字综述时间 < 60秒
- [ ] 综述结构完整（背景、方法、结论）
- [ ] 引用溯源准确
- [ ] 支持导出PDF/Word/Markdown

### 9.4 图表生成
- [ ] 支持Excel/CSV导入
- [ ] 支持4种图表类型（折线、柱状、散点、饼图）
- [ ] X/Y轴范围可配置
- [ ] 图表导出支持PNG/JPG/SVG/PDF

---

## 10. 后续优化方向

1. **多模态支持**：支持图表、公式的OCR识别
2. **协作功能**：文献共享、评论、批注
3. **AI助手增强**：支持论文润色、翻译、格式检查
4. **知识图谱**：构建文献间的引用关系图谱
5. **移动端适配**：开发iOS/Android应用

---

## 附录

### A. Kimi API 说明
- 官网：https://platform.moonshot.cn/
- 支持模型：moonshot-v1-8k / 32k / 128k
- 计费：按token计费

### B. FAISS 参考资料
- 官方文档：https://github.com/facebookresearch/faiss/wiki
- 中文教程：https://faiss.ai/

### C. 推荐前置知识
- Python异步编程 (async/await)
- FastAPI框架基础
- 向量检索原理
- LLM Prompt Engineering
