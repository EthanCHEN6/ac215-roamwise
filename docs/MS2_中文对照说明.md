> Earlier retrieval-only build. See [RAG update](RAG.md) and [new verification](RAG_RESULTS.md) for the current release.

# RoamWise：MS2 要求与实现对照

这一版从原始数据重新开始，不依赖之前的 Excel 或页面原型。范围是 **MS2**：先把数据、检索、页面和复现流程跑通。MS3 的模型训练、正式部署和完整行程规划不写成已完成。

## 一、教授要求什么，我们交什么

依据：[课程 MS2 原文](https://harvard-iacs.github.io/2026-AC215/milestone2/)。采用 LLM/RAG 路线，额外保留 category-and-rating baseline。

| 官方要求 | 中文理解 | 本仓库对应内容 |
|---|---|---|
| Virtual Environment Setup | 别人能搭起相同环境 | Docker Desktop / Linux containers；每个 Python 服务有 `pyproject.toml`、`uv.lock`、Dockerfile；README 写明启动条件 |
| End-to-End Containerized Pipeline | 数据进入系统后，各步自动衔接 | `compose.yaml` 依次运行 ingest → preprocess → index → API；评估也在容器里 |
| Initial RAG Pipeline | 查询能检索到真实资料，并提供上下文 | UCSD 地点和评论 → 文本分块 → MiniLM 向量 → Chroma；API 返回地点、原文片段、出处和 context |
| Application Mock-up & Skeleton | 页面必须真的调用后端 | 搜索、城市/类别筛选、两种方法对照、详情与来源、收藏与导出；不是固定推荐列表 |
| Documentation & Evidence | TF 能知道怎么跑、跑出了什么 | 简短英文 README、数据说明、输入输出 JSON、日志、测试、评估结果和截图；另有演示 slides |

**一条命令启动：**

```bash
docker compose up --build
```

看到 API healthy 和 `evaluation_complete` 后，打开 http://localhost:8080。首次运行要下载约 844 MB 原始数据、容器镜像和模型，时间取决于网络与 CPU。后续会校验并复用缓存。

所有 Python 依赖都由 uv 锁定；数据处理、embedding、API、评估、测试都在容器中。静态网页也用 Nginx 容器提供，因此不用处理静态豁免的解释问题。本项目无需 GPU、GCP 费用或 LLM API key。

## 二、数据究竟怎么走

1. **下载**：从 UCSD 下载 Massachusetts 地点和评论 gzip 文件。SHA-256 与仓库里的值不同，就停止。
2. **清洗与筛选**：保留目标城市和坐标范围内的旅游类别；按地点 ID 去重，排除历史记录中的永久关闭地点。博物馆同时有 cafe 标签时，归到 culture。
3. **缩小到能演示的规模**：每类最多 125 个地点，按原始评论数排序；每个地点保留文件顺序中前 6 条不同的非空评论。不是随机抽样，也不是全州数据。
4. **分块**：每块 100 个词，重叠 20 个词；单条评论最多保留 400 个词。每块保留来源文件、行号和地点 ID。
5. **建索引**：MiniLM 在 CPU 上生成 384 维向量，Chroma 保存文本、向量和筛选字段。
6. **查询**：API 检查输入，按城市和类别筛选，按相似度取候选，再按地点去重。网页显示地点和来源片段。

本次真实处理得到 **500 个地点、3,000 条采样评论、3,976 个文本块**。城市分布为 Boston 383、Cambridge 92、Somerville 25。完整计数与校验值见 `evidence/dataset-manifest.json`。

## 三、代码注释式阅读顺序

| 文件 | 读的时候抓住什么 |
|---|---|
| `compose.yaml` | `depends_on` 的成功完成/健康条件控制顺序；volume 保留数据；端口只绑定本机 |
| `services/index/Dockerfile` | 固定基础镜像；复制依赖文件；`uv sync --frozen`；复制代码；启动一个模块 |
| `config/sources.json` | 下载地址和源文件校验值；文件变了不能悄悄继续 |
| `config/pipeline.json` | 城市、范围、抽样大小、分块参数；改变清洗逻辑时也要更新 selection_version |
| `roamwise/ingest.py` | 下载到临时文件，校验成功才替换；已有文件也校验 |
| `roamwise/preprocess.py` | 地点筛选、评论去重、缺失值处理、分块和数据版本 |
| `roamwise/embedding.py`、`index.py` | 同一个 encoder 用于建库和查询；模型归档校验值写进 manifest |
| `roamwise/retrieval.py` | 语义检索与 baseline 的差别、地点去重、引用格式 |
| `roamwise/api.py` | 请求有哪些字段、哪些输入会被拒绝、健康检查如何判断就绪 |
| `frontend/app.js` | `fetch('/api/search')` 真正发请求；返回的内容用 textContent 显示 |
| `roamwise/evaluate.py`、`tests/` | 区分类别代理指标、响应时间与程序正确性测试 |

不要背每一行语法。要能用一个查询解释：输入进了哪个函数、读了什么数据、为什么得到这些结果、哪里可能出错。

## 四、TF 可能追问的几个区别

**这是完整 RAG 吗？** 已完成 RAG 的检索基础和 query → context 流程。本版没有接生成式 LLM，不会编写行程或推荐理由。页面说明与原文引用来自已检索的记录。

**为什么不直接训练模型？** MS2 先适配预训练 MiniLM 并建立可复现链路。保留简单 baseline，下一阶段有了人工相关性标签后再训练 reranker。若 TF 把项目归到 other modalities，应确认该路线是否满足其 baseline 预期。

**相似度 0.6 是 60% 匹配吗？** 不是。它是向量空间里的 cosine similarity，不能当成成功概率，也不等于地点评分。

**评估数字是否代表“80% 推荐准确率”？** 不代表。20 条固定查询只检查返回地点的大类别与预期是否一致，并记录耗时。查询含类别词，天然有利于关键词 baseline；没有人工相关性标签，不能报告 human Precision@5。实际结果见 `docs/RESULTS.md`。

**能说某地今天营业吗？** 不能。资料截至 2021 年；价格和营业时间可能缺失或过时。页面提示核对当前信息，不补造字段。

## 五、演示与提交

按 `docs/DEMO.md` 演示：启动流程 → 搜索 Harvard 附近的艺术博物馆 → 打开来源 → 切 baseline → 展示 manifest、样例和测试 → 说明下一步。英文 slides 在 `slides/RoamWise_MS2.pptx`。

课程页面要求提交 **milestone2 分支**，并在 **10 月 20 日 22:00 ET** 前把完整 commit hash 填到 Canvas。仓库内容和文档可以代为准备；Canvas 提交、实际成员分工和个人问答仍需要团队完成。不要把 AI 辅助生成的代码说成每个成员都已经理解，也不要编造贡献。

提交前确认：TF 能访问仓库；团队成员各自跑过一次；每个人都能解释系统的主要部分；Canvas 上的 hash 对应最终提交。
