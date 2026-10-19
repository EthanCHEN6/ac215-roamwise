# 新版讲解与 TF 问答

## 原版和新版有什么不同

原版有向量检索。它把问题转成向量，从数据库找相近的评论和地点。它没有调用大语言模型写行程。因此，原版是 RAG 的检索部分，不宜说成完整的生成式 RAG。

新版增加两个模型步骤。第一步把用户偏好转成几次查询。第二步读取检索资料，生成带引用的行程。服务器再检查输出。RAG 就是：先找资料，再依据资料生成回答。

我们没有训练大语言模型。MiniLM 是现成的嵌入模型，负责把文本转成向量。Gemini 是生成模型，负责理解需求和写草稿。Chroma 保存向量及其来源信息。

## 一次请求怎样完成

例如，用户选 Cambridge、一天、博物馆和午餐。

1. 网页把偏好发送给 Python API。
2. 模型提出最多四个搜索，例如艺术博物馆、附近餐饮。
3. 服务器强制限制城市和类别。模型不能绕过这些条件。
4. 数据库返回地点和资料。网页展示结果，用户选择地点。
5. 服务器重新取得这些地点的资料，不接受浏览器提交的“证据”。
6. 模型安排顺序和建议停留时间，并标出引用。
7. 程序检查地点是否存在、是否重复、引用是否属于该地点、每天是否排得下。
8. 检查失败时最多重写一次，再失败就报告错误。

地图使用地点坐标，连线仅表示游览顺序。交通时间根据距离和假定速度估算。没有调用真实路线规划器，不能说“最优路线”或“准确通勤时间”。

## 怎样对应 TF 的建议

**资料维护部分**：检查历史数据库，发现并维护 Google place ID，按需查询当前资料。这是受控的容器任务，不是自主决策的 LLM agent。新查询的 Google API 内容有存储限制，因此不直接写入历史向量库。

**用户规划部分**：模型理解意图，分多次搜索，再生成行程草稿。程序限制工具和检查输出。

可以说我们实现了两个连接的组件。不要夸大成两个持续自主工作的智能体。维护 Google ID 也不等于实时更新所有评论。

## 约三分钟的英文展示稿

“RoamWise helps users draft short trips in Greater Boston. Our earlier version retrieved places and source passages. This version adds a language model before and after retrieval.

First, the model converts preferences into a small search plan. The server applies city and category filters. It retrieves source passages from Chroma and lets the user select places.

Next, the server retrieves context again. The model produces a structured itinerary with citations. We check place IDs, citation membership, duplicate stops and the daily schedule. We allow one repair attempt. If it still fails, we return an error.

Our historical database contains 500 places. Its source ends in 2021. Current opening hours and prices need a separate check. Travel times are estimates. We do not claim that the route is optimal or that every generated statement is correct.

All Python services use uv and run in containers. Cloud Run hosts the website and API, so teammates can use the app without my laptop. We record dataset, index, prompt and model versions to make each run easier to inspect.”

## TF 可能问的问题

| 问题 | 回答要点 |
|---|---|
| RAG 在哪里？ | 检索上下文进入生成模型，结果有可回看的来源。向量搜索本身只是检索部分。 |
| 为什么不直接问 Gemini？ | 限制候选地点，并展示模型使用的具体资料。仍要评估资料是否被正确使用。 |
| 你们训练了模型吗？ | 没有。使用预训练 MiniLM 和现成 Gemini。API 调用不是训练。 |
| 为什么选这些地点？ | 先按城市和类别过滤，再做语义检索。样本偏向高评论量地点。 |
| 为什么阈值是 0.25？ | 这是初始值，尚未用人工标签校准。它不是概率或已证明的最佳参数。 |
| 怎样减少幻觉？ | 限制上下文、结构化输出、引用检查、地点校验和一次修复。尚未自动验证每句话的含义。 |
| 预算能保证吗？ | 不能。缺少可靠的当前价格。预算目前是偏好，不是已验证约束。 |
| 数据会更新吗？ | 校验历史快照、维护 Google ID、按需查询当前资料。全量评论更新尚未实现。 |
| 测试通过等于效果好吗？ | 不等于。单元测试检查程序与失败路径，真实质量需要人工评价。 |
| 为什么容器化和 uv？ | 固定环境和依赖，方便组员和 TF 复现。 |
| 怎样控制费用？ | 空闲缩到零、最多一个实例、限制并发和请求。它们不是硬性账单上限。 |

## 展示前

用真实请求演示完整流程。打开一条引用，核对它是否支持推荐理由。说明历史数据日期，并准备解释一个失败案例。旧 PPT 描述检索版本，不应直接用于声称已展示新版 RAG。

写作参考 ASD-STE100 的短句、明确动作和一致术语原则。中文说明不声称符合该英文受控语言标准的正式认证。
