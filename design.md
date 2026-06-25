可以。我们先把 **RecHarness** 定义成一个真正像主流 agent harness 的开源项目，而不是一个“推荐系统小 demo”。

我的建议是：**RecHarness v0.1 先做成 agent-side recommendation quality layer**。它可以被 general agent、shopping agent、browser agent、LangGraph agent、OpenAI Agents SDK agent、MCP client 调用，用来提升“购物/物品推荐”的可靠性。

---

# 0. 项目一句话定位

## RecHarness

> **An agent-agnostic harness for reliable product recommendation by general-purpose agents.**

中文：

> **面向通用智能体的商品推荐增强、验证与评测框架。**

它不是完整购物 agent，而是给 agent 提供一组标准能力：

```text
理解用户需求
→ 检索候选商品
→ 结构化比较
→ 多目标排序
→ 约束验证
→ 推荐证据追踪
→ 失败诊断
→ 评测复现
```

这个定位很贴近当前 agent harness 的主流趋势：agent 不再只是调用一个模型，而是由 tools、state、tracing、evaluation、guardrails 等外部执行层共同决定表现。OpenAI Agents SDK 官方文档也把 tools 和 tracing 作为 agent runtime 的核心能力；MCP 官方则把 MCP 定义为连接 AI 应用与外部系统、工具和数据源的开放协议。([OpenAI Developers][1])

---

# 1. RecHarness 的核心 thesis

项目和论文都可以围绕这个 claim：

> General agents are becoming shopping interfaces, but they frequently produce recommendations that violate user constraints, hallucinate product attributes, overfit to vague preferences, or lack evidence. RecHarness wraps general agents with structured preference extraction, grounded retrieval, constraint verification, recommendation bundling, and trace-level evaluation.

更短一点：

> **RecHarness makes general-purpose agents reliable recommenders without replacing the agents themselves.**

---

# 2. RecHarness 的三种使用模式

这个项目不要只做一种 API。建议一开始就设计成三种模式。

## Mode A：Assist mode

agent 在推荐前调用 RecHarness，让 RecHarness 帮它找候选、排序、比较、验证。

```text
User query
→ RecHarness
→ recommendation bundle
→ General agent writes final answer
```

适合：

```text
ChatGPT tool
Claude tool
Gemini tool
LangGraph node
OpenAI Agents SDK tool
MCP server
```

---

## Mode B：Verify mode

用户或 agent 已经有一组推荐结果，RecHarness 检查它们是否靠谱。

```text
User query + agent recommendation
→ RecHarness verifier
→ violations / unsupported claims / better alternatives
```

这是最适合 MVP 的模式，因为它最容易做出效果。

例如：

```text
用户要求：
1000 元以内、防水、重量 1kg 以下的通勤背包

agent 推荐：
1299 元、防泼水、1.3kg 的背包

RecHarness 输出：
FAIL
- price exceeds budget
- waterproof claim unsupported
- weight exceeds limit
```

---

## Mode C：Eval mode

研究者用 RecHarness 批量评测不同 agent。

```text
missions.jsonl
+ catalog.jsonl
+ agent outputs
→ RecHarness evaluator
→ metrics + traces + leaderboard
```

这直接服务论文。

当前购物 agent 的 benchmark 价值正在变强。Shopping Reasoning Bench 用 525 个购物任务评估多轮购物助手，发现模型总体通过率约 57%–77%，并且多轮对话后续表现会下降；EComAgentBench 也强调购物需求会分散在显式 query、profile 和 clarification 中，最强模型总体准确率也只有约 57.1%。这些结果说明购物推荐 agent 的主要问题已经不是“能不能聊天”，而是“能不能持续发现约束、验证候选、给出可靠选择”。([arXiv][2])

---

# 3. 项目边界：做什么，不做什么

## v0.1 做

```text
1. 商品 catalog 的本地加载和标准化
2. 用户需求结构化解析
3. 候选商品检索
4. 约束验证
5. 多目标排序
6. recommendation bundle 生成
7. agent 推荐结果验证
8. trace logging
9. batch benchmark runner
10. MCP server
11. CLI demo
12. Python SDK
```

## v0.1 不做

```text
1. 不做完整支付 checkout
2. 不爬取实时电商网站
3. 不依赖某一个 agent 平台
4. 不做复杂商家侧 schema，这留给 AgentCatalog
5. 不做大规模线上 A/B 测试
6. 不做金融/医疗等高风险推荐
```

这个边界非常重要。RecHarness 第一阶段应该聚焦在：

> **recommendation quality control for general agents**

而不是“重新造一个电商平台”。

---

# 4. 总体架构

```text
                           ┌──────────────────────┐
                           │   General Agent       │
                           │ ChatGPT / Claude /    │
                           │ Gemini / LangGraph /  │
                           │ Browser Agent         │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │      RecHarness       │
                           └──────────┬───────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌────────────────┐          ┌──────────────────┐          ┌─────────────────┐
│ Preference      │          │ Product Retrieval │          │ Constraint       │
│ Understanding   │          │ + Ranking         │          │ Verification     │
└────────────────┘          └──────────────────┘          └─────────────────┘
        │                             │                             │
        └─────────────────────────────┼─────────────────────────────┘
                                      ▼
                         ┌────────────────────────┐
                         │ Recommendation Bundle  │
                         └──────────┬─────────────┘
                                    ▼
                         ┌────────────────────────┐
                         │ Trace + Evaluation     │
                         └────────────────────────┘
```

核心思想：

> agent 负责自然语言交互，RecHarness 负责推荐过程的结构化、可验证、可复现。

---

# 5. 关键抽象设计

## 5.1 ProductItem

RecHarness 不需要一开始设计复杂商家 schema，但必须有最小 product schema。

```python
class ProductItem(BaseModel):
    product_id: str
    title: str
    category: str
    brand: str | None = None

    price: Money | None = None
    availability: Literal["in_stock", "out_of_stock", "unknown"] = "unknown"

    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    description: str | None = None
    review_summary: str | None = None

    evidence: list[Evidence] = Field(default_factory=list)
    source: str | None = None
```

v0.1 只要求商品可以支持这些字段：

```text
price
category
brand
attributes
description
review_summary
evidence
availability
```

---

## 5.2 UserNeed

把用户自然语言需求结构化。

```python
class UserNeed(BaseModel):
    raw_query: str
    category: str | None = None
    scenario: list[str] = Field(default_factory=list)

    hard_constraints: list[Constraint] = Field(default_factory=list)
    soft_preferences: list[Preference] = Field(default_factory=list)
    negative_preferences: list[Preference] = Field(default_factory=list)

    missing_slots: list[str] = Field(default_factory=list)
    urgency: Literal["low", "normal", "high"] = "normal"
```

例如：

```json
{
  "raw_query": "帮我找一个适合通勤的防水双肩包，预算1500以内，不要太商务",
  "category": "backpack",
  "scenario": ["commute"],
  "hard_constraints": [
    {
      "field": "price",
      "operator": "<=",
      "value": 1500,
      "unit": "CNY"
    }
  ],
  "soft_preferences": [
    {
      "field": "water_resistance",
      "value": "water_resistant_or_better",
      "weight": 0.8
    }
  ],
  "negative_preferences": [
    {
      "field": "style",
      "value": "too_business",
      "weight": 0.7
    }
  ]
}
```

---

## 5.3 Constraint

约束必须一等公民化。

```python
class Constraint(BaseModel):
    field: str
    operator: Literal["=", "!=", "<", "<=", ">", ">=", "contains", "not_contains", "exists"]
    value: Any
    unit: str | None = None
    severity: Literal["hard", "soft"] = "hard"
    source: Literal["user", "profile", "system", "inferred"] = "user"
```

原因：论文里的核心指标就是 constraint satisfaction。

---

## 5.4 RecommendationCandidate

```python
class RecommendationCandidate(BaseModel):
    product: ProductItem
    retrieval_score: float | None = None
    preference_score: float | None = None
    constraint_score: float | None = None
    final_score: float | None = None

    matched_constraints: list[ConstraintCheck] = Field(default_factory=list)
    violations: list[Violation] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
```

---

## 5.5 RecommendationBundle

这是 RecHarness 给 agent 的核心输出。

```python
class RecommendationBundle(BaseModel):
    user_need: UserNeed
    candidates: list[RecommendationCandidate]

    recommended: list[RecommendationCandidate]
    rejected: list[RecommendationCandidate]

    comparison_axes: list[str]
    constraint_report: ConstraintReport

    clarification_questions: list[ClarificationQuestion]
    summary_for_agent: str

    trace_id: str
```

agent 最终面向用户输出时，应该基于 bundle，而不是自由发挥。

---

## 5.6 Trace

Trace 是 research 和 harness 主流化的关键。OpenAI Agents SDK 官方 tracing 文档也强调 tracing 会记录 agent run 中的 LLM generation、tool calls、handoffs、guardrails 和 custom events，用于调试、可视化和监控。([OpenAI GitHub][3])

RecHarness 的 trace 可以先做成 JSONL：

```python
class TraceEvent(BaseModel):
    trace_id: str
    step: int
    event_type: Literal[
        "parse_preferences",
        "retrieve",
        "rank",
        "verify",
        "clarify",
        "bundle",
        "evaluate",
        "error"
    ]
    payload: dict[str, Any]
    timestamp: datetime
```

---

# 6. 推荐核心流程

## 6.1 Assist mode 流程

```text
Input:
- user_query
- optional user_profile
- catalog

Step 1: parse_user_need
Step 2: decide_clarification_or_recommendation
Step 3: retrieve_candidates
Step 4: verify_candidates_against_constraints
Step 5: rank_candidates
Step 6: generate_recommendation_bundle
Step 7: log_trace

Output:
- RecommendationBundle
```

伪代码：

```python
bundle = harness.assist(
    user_query="找一个通勤背包，预算1500以内，能放14寸电脑，不要太商务",
    top_k=5
)

print(bundle.recommended)
print(bundle.constraint_report)
print(bundle.summary_for_agent)
```

---

## 6.2 Verify mode 流程

```text
Input:
- user_query
- product recommendations from an agent
- catalog

Step 1: parse_user_need
Step 2: resolve recommended products against catalog
Step 3: check existence
Step 4: check hard constraints
Step 5: check soft preferences
Step 6: check unsupported claims
Step 7: suggest fixes

Output:
- VerificationReport
```

伪代码：

```python
report = harness.verify_agent_recommendation(
    user_query="预算1500以内，防水，适合通勤的双肩包",
    agent_answer="""
    推荐 Urban Pro 30L，售价1899，完全防水，很适合通勤。
    """
)

print(report.status)
print(report.violations)
print(report.unsupported_claims)
print(report.repair_suggestions)
```

---

## 6.3 Eval mode 流程

```text
Input:
- missions.jsonl
- catalog.jsonl
- agent outputs or callable agent adapter

Step:
- run each mission
- collect bundle / answer / trace
- compute metrics

Output:
- metrics.json
- traces.jsonl
- leaderboard.csv
```

CLI：

```bash
recharness eval \
  --missions data/missions/backpack_300.jsonl \
  --catalog data/catalogs/backpacks.jsonl \
  --agent openai:gpt-4.1 \
  --harness full \
  --out runs/backpack_gpt41_full/
```

---

# 7. 模块设计

## 7.1 Preference Parser

第一版建议支持两种 parser：

```text
RuleBasedPreferenceParser
LLMPreferenceParser
```

默认用 rule-based，保证开源项目可跑；LLM parser 做 optional adapter。

接口：

```python
class PreferenceParser(Protocol):
    def parse(self, query: str, profile: UserProfile | None = None) -> UserNeed:
        ...
```

Rule-based 支持：

```text
价格：under 1000 / 1000元以内 / below $200
尺寸：14寸 / 15-inch
重量：轻量 / under 1kg
颜色：black / 黑色
场景：commute / travel / gaming / running
否定偏好：不要 / avoid / not
```

LLM parser 输出必须过 Pydantic validation，不能直接信任模型。

---

## 7.2 Retriever

接口：

```python
class Retriever(Protocol):
    def retrieve(self, need: UserNeed, catalog: Catalog, top_k: int) -> list[ScoredProduct]:
        ...
```

v0.1 支持三种：

```text
KeywordRetriever
AttributeFilterRetriever
HybridRetriever
```

不要一开始强依赖向量数据库。可以先用：

```text
BM25 / rapidfuzz / sklearn TF-IDF
```

这样 Codex 实现会简单、测试稳定。

---

## 7.3 Ranker

接口：

```python
class Ranker(Protocol):
    def rank(
        self,
        need: UserNeed,
        candidates: list[RecommendationCandidate],
        top_k: int
    ) -> list[RecommendationCandidate]:
        ...
```

v0.1 排序公式可以简单透明：

```text
final_score =
  0.45 * hard_constraint_score
+ 0.25 * soft_preference_score
+ 0.15 * retrieval_score
+ 0.10 * evidence_score
+ 0.05 * diversity_bonus
```

第一版不要追求复杂模型，重点是可解释和可 ablation。

---

## 7.4 Constraint Verifier

这是核心模块。

接口：

```python
class ConstraintVerifier:
    def verify_product(
        self,
        need: UserNeed,
        product: ProductItem
    ) -> ConstraintReport:
        ...
```

需要支持：

```text
数值比较：price <= 1500, weight < 1.0
字符串匹配：category = backpack
集合匹配：tags contains waterproof
否定条件：style not_contains business
存在性检查：attribute exists
兼容性检查：laptop_size >= 14
```

输出：

```python
class Violation(BaseModel):
    constraint: Constraint
    observed_value: Any
    severity: Literal["hard", "soft"]
    message: str
```

---

## 7.5 Claim Verifier

这个模块检查 agent 的推荐理由是否有证据支持。

例如 agent 说：

> 这款包完全防水。

但 product item 里只有：

```json
{
  "water_resistance": "splash_resistant"
}
```

则输出：

```text
unsupported_or_overstated_claim:
agent says "waterproof"
catalog says "splash_resistant"
```

v0.1 可以先做 pattern-based：

```text
waterproof vs water-resistant vs splash-resistant
lightweight vs weight > threshold
fits 14-inch laptop vs laptop_size_inches < 14
under budget vs price > budget
in stock vs availability != in_stock
```

后续再做 LLM entailment。

---

## 7.6 Clarification Policy

先做一个简单 policy。

```python
class ClarificationPolicy:
    def propose_questions(self, need: UserNeed, catalog_stats: CatalogStats) -> list[ClarificationQuestion]:
        ...
```

规则：

```text
缺预算 → 问预算
缺尺寸/兼容性 → 问尺寸
候选太多且风格分散 → 问风格
候选太少 → 放宽 soft preference，不问
硬约束缺失且影响大 → 问
软偏好缺失 → 不一定问，推荐时给多样选项
```

输出：

```json
[
  {
    "question": "你的预算上限大概是多少？",
    "reason": "预算会显著影响候选商品范围",
    "slot": "price_max",
    "priority": 0.95
  }
]
```

---

## 7.7 Recommendation Bundle Builder

将推荐结果组织成 agent 可使用的结构。

```python
class BundleBuilder:
    def build(
        self,
        need: UserNeed,
        ranked: list[RecommendationCandidate],
        questions: list[ClarificationQuestion],
        trace_id: str
    ) -> RecommendationBundle:
        ...
```

`summary_for_agent` 可以是：

```text
User wants a commuting backpack under 1500 CNY, preferably water-resistant and not overly business-looking. Recommend Product A as the safest choice, Product B as the lightweight choice, and Product C as the value choice. Do not claim any product is fully waterproof unless evidence says waterproof.
```

这个字段非常重要，因为 general agent 可以直接基于它生成最终回答。

---

# 8. MCP server 设计

RecHarness 应该一开始就做 MCP server，因为这让它贴近 agent harness 主流生态。MCP 官方文档说明 MCP server 可以向模型暴露 tools，每个 tool 有唯一名称和 schema，可让模型查询数据库、调用 API 或执行计算等外部能力。([Model Context Protocol][4])

## MCP tools

```text
recharness.parse_preferences
recharness.retrieve_products
recharness.rank_products
recharness.verify_product
recharness.verify_recommendation
recharness.build_recommendation_bundle
recharness.ask_clarifying_questions
recharness.evaluate_answer
```

## 示例 tool schema

```python
@mcp.tool()
def verify_recommendation(
    user_query: str,
    agent_answer: str,
    catalog_path: str
) -> dict:
    """Verify whether an agent's product recommendations satisfy the user's constraints."""
```

## MCP 使用场景

```text
Claude Desktop / Cursor / Codex-like agent / 自建 MCP client
→ 调用 RecHarness MCP server
→ 获得结构化推荐验证结果
```

---

# 9. LangGraph / OpenAI Agents SDK 适配

不要把项目绑死在某个框架，但要提供 adapters。

LangGraph 官方定位是面向 stateful agents 的低层 orchestration 框架，强调 durable execution、streaming、human-in-the-loop 等能力；所以 RecHarness 可以作为 LangGraph 里的一个 node。([LangChain Docs][5])

OpenAI Agents SDK 则可以通过 tools 和 tracing 集成 RecHarness；其文档说明 tools 让 agents 执行外部动作，比如获取数据、运行代码和调用 API。([OpenAI GitHub][6])

建议做：

```text
integrations/
  openai_agents.py
  langgraph_node.py
  mcp_server.py
```

示例：

```python
from recharness.integrations.langgraph import create_recharness_node

recommendation_node = create_recharness_node(harness)
```

---

# 10. 项目目录结构

建议 Codex 按这个结构创建。

```text
recharness/
  pyproject.toml
  README.md
  LICENSE
  CONTRIBUTING.md

  recharness/
    __init__.py

    core/
      harness.py
      config.py
      exceptions.py

    schema/
      money.py
      evidence.py
      product.py
      user_need.py
      constraint.py
      candidate.py
      bundle.py
      verification.py
      trace.py
      mission.py
      metrics.py

    catalog/
      base.py
      jsonl_catalog.py
      csv_catalog.py
      duckdb_catalog.py
      stats.py

    preference/
      base.py
      rule_parser.py
      llm_parser.py
      slot_extractor.py

    retrieval/
      base.py
      keyword.py
      attribute_filter.py
      hybrid.py

    ranking/
      base.py
      simple_ranker.py
      diversity.py

    verification/
      constraint_verifier.py
      claim_verifier.py
      recommendation_verifier.py

    clarification/
      policy.py
      question.py

    bundle/
      builder.py
      formatter.py

    tracing/
      logger.py
      jsonl.py

    evaluation/
      runner.py
      metrics.py
      graders.py
      leaderboard.py

    integrations/
      mcp_server.py
      openai_agents.py
      langgraph_node.py

    cli/
      main.py

  examples/
    backpacks/
      catalog.jsonl
      missions.jsonl
      demo_assist.py
      demo_verify.py

  tests/
    test_rule_parser.py
    test_constraint_verifier.py
    test_retriever.py
    test_ranker.py
    test_bundle.py
    test_eval_runner.py

  docs/
    quickstart.md
    concepts.md
    schemas.md
    mcp.md
    evaluation.md
    paper_experiments.md
```

---

# 11. Python SDK 设计

## 11.1 初始化

```python
from recharness import RecHarness

harness = RecHarness.from_jsonl_catalog(
    "examples/backpacks/catalog.jsonl"
)
```

---

## 11.2 Assist

```python
bundle = harness.assist(
    user_query="帮我找一个1500元以内、适合通勤、能放14寸电脑、不要太商务的双肩包",
    top_k=5
)

for item in bundle.recommended:
    print(item.product.title, item.final_score)

print(bundle.constraint_report.summary)
print(bundle.summary_for_agent)
```

---

## 11.3 Verify

```python
report = harness.verify_agent_recommendation(
    user_query="找一个1500元以内、防水、适合通勤的双肩包",
    agent_answer="我推荐 Urban Pro 30L，售价1899，完全防水。"
)

print(report.status)
print(report.violations)
print(report.unsupported_claims)
print(report.repair_suggestions)
```

---

## 11.4 Evaluate

```python
from recharness.evaluation import EvalRunner

runner = EvalRunner(
    harness=harness,
    missions_path="examples/backpacks/missions.jsonl"
)

result = runner.run_with_agent_outputs(
    outputs_path="runs/baseline_agent_outputs.jsonl"
)

print(result.metrics)
```

---

# 12. CLI 设计

CLI 很重要，开源项目第一印象会更强。

## 12.1 检查 catalog

```bash
recharness catalog validate examples/backpacks/catalog.jsonl
```

输出：

```text
Catalog valid: 128 products
Fields coverage:
- price: 100%
- weight_kg: 83%
- laptop_size_inches: 91%
- water_resistance: 76%
```

---

## 12.2 Assist

```bash
recharness assist \
  --catalog examples/backpacks/catalog.jsonl \
  --query "1500元以内，适合通勤，能放14寸电脑，不要太商务的双肩包" \
  --top-k 5
```

---

## 12.3 Verify

```bash
recharness verify \
  --catalog examples/backpacks/catalog.jsonl \
  --query "1500元以内、防水、适合通勤的双肩包" \
  --answer-file examples/backpacks/agent_answer.txt
```

---

## 12.4 Eval

```bash
recharness eval \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --agent-outputs runs/agent_outputs.jsonl \
  --out runs/eval_baseline/
```

---

## 12.5 MCP

```bash
recharness mcp serve \
  --catalog examples/backpacks/catalog.jsonl
```

---

# 13. 数据格式

## 13.1 catalog.jsonl

```json
{"product_id":"bag_001","title":"UrbanLite Commuter Backpack 22L","category":"backpack","brand":"UrbanLite","price":{"amount":899,"currency":"CNY"},"availability":"in_stock","attributes":{"capacity_liters":22,"laptop_size_inches":14,"weight_kg":0.85,"water_resistance":"water_resistant","style":["minimal","casual"],"use_cases":["commute","short_trip"]},"description":"A lightweight commuter backpack with a padded laptop compartment.","review_summary":"Users like its lightweight design and clean look, but some say it is not suitable for heavy rain.","evidence":[{"field":"laptop_size_inches","value":14,"source_type":"manufacturer_spec"},{"field":"weight_kg","value":0.85,"source_type":"manufacturer_spec"},{"field":"water_resistance","value":"water_resistant","source_type":"manufacturer_spec"}]}
```

---

## 13.2 missions.jsonl

```json
{"mission_id":"backpack_001","user_query":"我需要一个1500元以内、适合通勤、能放14寸电脑、不要太商务的双肩包。","required_constraints":[{"field":"price.amount","operator":"<=","value":1500,"severity":"hard"},{"field":"attributes.laptop_size_inches","operator":">=","value":14,"severity":"hard"}],"preferred_constraints":[{"field":"attributes.style","operator":"not_contains","value":"business","severity":"soft"},{"field":"attributes.water_resistance","operator":"contains","value":"water_resistant","severity":"soft"}],"gold_product_ids":["bag_001","bag_014"],"rubrics":[{"name":"under_budget","weight":3},{"name":"fits_laptop","weight":3},{"name":"commute_suitable","weight":2},{"name":"not_too_business","weight":1}]}
```

---

## 13.3 agent_outputs.jsonl

```json
{"mission_id":"backpack_001","agent_name":"baseline_llm","answer":"我推荐 UrbanLite Commuter Backpack 22L，因为它价格899元，能放14寸电脑，适合通勤。"}
```

---

# 14. 评测指标

v0.1 先做自动可计算指标。

```text
constraint_satisfaction_rate
hard_violation_rate
soft_preference_match_rate
product_existence_rate
unsupported_claim_rate
overstated_claim_rate
price_accuracy_rate
attribute_accuracy_rate
top_k_recall_against_gold
mean_reciprocal_rank
evidence_coverage
recommendation_diversity
repair_success_rate
```

最重要的四个核心指标：

| Metric                       | 含义                |
| ---------------------------- | ----------------- |
| Hard Constraint Satisfaction | 推荐是否满足硬约束         |
| Product Groundedness         | 推荐商品是否存在于 catalog |
| Claim Support                | 推荐理由是否被商品证据支持     |
| Preference Coverage          | 是否覆盖用户关键偏好        |

论文里可以先证明：

```text
RecHarness 显著降低 hard constraint violation 和 unsupported claims。
```

---

# 15. Benchmark 设计

## v0.1 数据集

先做一个小而精的 benchmark：

```text
品类：backpacks
商品：100–300 个
任务：100–300 个
类型：
- single-turn recommendation
- verify agent answer
- budget-constrained selection
- compatibility-aware selection
- style preference selection
```

为什么先选背包：

```text
1. 约束丰富：预算、容量、重量、电脑尺寸、防水
2. 主观偏好明显：通勤、商务、休闲、户外
3. 风险较低
4. 数据容易构造
5. 用户直觉强，demo 容易理解
```

## v0.2 再加

```text
headphones
running shoes
baby stroller
keyboard / mouse
travel suitcase
```

---

# 16. Harness variants for paper

论文实验要做 ablation。

```text
H0: Direct Agent
agent 直接推荐，不用 RecHarness

H1: Retrieval Only
只给 agent 候选商品

H2: Retrieval + Preference Parser
先结构化用户需求，再检索

H3: Retrieval + Constraint Verifier
过滤违反硬约束的候选

H4: Retrieval + Verifier + Ranker
加入多目标排序

H5: Full RecHarness
parser + retrieval + verifier + ranker + bundle + repair suggestions
```

你要证明：

```text
H5 > H4 > H3 > H2 > H1 > H0
```

但更有意思的结果可能是：

```text
retrieval alone 不一定够；
constraint verifier 是最大增益来源；
bundle 可以减少 agent 最终表达里的 unsupported claims；
弱模型 + full harness 可能接近强模型 + no harness。
```

---

# 17. Failure taxonomy

RecHarness 要内置 failure taxonomy，这会让论文更有“诊断系统”的味道。

```text
F1 Product Hallucination
推荐了 catalog 中不存在的商品

F2 Hard Constraint Violation
违反预算、尺寸、兼容性等硬约束

F3 Soft Preference Neglect
忽略风格、颜色、场景等偏好

F4 Unsupported Claim
推荐理由没有证据

F5 Overstated Claim
把防泼水说成防水，把轻量说成超轻

F6 Premature Recommendation
关键信息缺失时过早推荐

F7 Poor Trade-off Explanation
没有解释为什么牺牲某个偏好

F8 Candidate Set Collapse
推荐结果过于相似，缺乏选择空间

F9 Hidden Requirement Miss
没有发现用户 profile 或多轮反馈中的隐含需求

F10 Repair Failure
发现错误后未能修复推荐
```

---

# 18. README 第一屏设计

开源项目 README 第一屏建议这样写：

````markdown
# RecHarness

RecHarness is an agent-agnostic harness for making general-purpose agents better product recommenders.

It wraps shopping agents with:

- structured preference extraction
- grounded product retrieval
- constraint verification
- evidence-aware ranking
- recommendation bundle generation
- trace-level evaluation

## Quickstart

```python
from recharness import RecHarness

harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

bundle = harness.assist(
    user_query="Find a commuting backpack under 1500 RMB that fits a 14-inch laptop.",
    top_k=3,
)

print(bundle.summary_for_agent)
print(bundle.constraint_report)
````

## Verify an agent recommendation

```python
report = harness.verify_agent_recommendation(
    user_query="Find a waterproof commuting backpack under 1500 RMB.",
    agent_answer="I recommend Urban Pro 30L. It costs 1899 RMB and is fully waterproof."
)

print(report.violations)
```

````

---

# 19. Codex 执行顺序

我建议让 Codex 按 8 个 PR 来做。

## PR 1：Project skeleton + schemas

目标：

```text
建立 pyproject.toml
建立目录结构
实现 Pydantic schemas
加入基础 tests
````

交付：

```text
ProductItem
UserNeed
Constraint
Evidence
RecommendationCandidate
RecommendationBundle
VerificationReport
TraceEvent
```

---

## PR 2：Catalog loader

目标：

```text
实现 JSONL catalog loader
实现 catalog validation
实现 catalog stats
```

交付：

```text
JsonlCatalog
Catalog.validate()
CatalogStats
recharness catalog validate CLI
```

---

## PR 3：Rule-based preference parser

目标：

```text
实现不用 LLM 的需求解析器
支持中英文基础表达
```

交付：

```text
RuleBasedPreferenceParser
price extraction
category extraction
negative preference extraction
scenario extraction
missing slot detection
```

---

## PR 4：Constraint verifier

目标：

```text
实现核心约束验证能力
```

交付：

```text
ConstraintVerifier
nested field resolution
numeric comparisons
contains / not_contains
exists
Violation report
tests
```

---

## PR 5：Retriever + ranker

目标：

```text
实现候选召回和简单排序
```

交付：

```text
KeywordRetriever
AttributeFilterRetriever
HybridRetriever
SimpleRanker
top_k assist flow
```

---

## PR 6：Recommendation bundle + verify mode

目标：

```text
实现 assist 和 verify 两个核心闭环
```

交付：

```text
RecHarness.assist()
RecHarness.verify_agent_recommendation()
BundleBuilder
ClaimVerifier v0
repair suggestions
```

---

## PR 7：CLI + examples

目标：

```text
让用户可以不写代码直接跑
```

交付：

```text
recharness assist
recharness verify
recharness catalog validate
examples/backpacks/catalog.jsonl
examples/backpacks/missions.jsonl
README quickstart
```

---

## PR 8：Evaluation runner + MCP server

目标：

```text
完成 research 和 agent integration 基础
```

交付：

```text
recharness eval
metrics.json
traces.jsonl
leaderboard.csv
recharness mcp serve
MCP tools
```

---

# 20. 给 Codex 的总 prompt

你可以直接把下面这段给 Codex。

```text
Build an open-source Python package called RecHarness.

RecHarness is an agent-agnostic harness for reliable product recommendation by general-purpose agents. It should not be a full shopping agent. It should provide SDK, CLI, and MCP server interfaces for:
1. parsing user shopping needs into structured constraints and preferences,
2. loading and validating local product catalogs,
3. retrieving candidate products,
4. ranking candidates with transparent multi-objective scoring,
5. verifying products and agent recommendations against user constraints,
6. checking unsupported or overstated product claims,
7. generating a structured RecommendationBundle for downstream agents,
8. logging traces,
9. running batch evaluations on benchmark missions.

Implement the project in Python using Pydantic models and pytest tests. Keep the first version deterministic and runnable without external LLM APIs. Optional LLM integrations can be added later behind adapters.

Create the following modules:
- recharness/schema
- recharness/catalog
- recharness/preference
- recharness/retrieval
- recharness/ranking
- recharness/verification
- recharness/clarification
- recharness/bundle
- recharness/tracing
- recharness/evaluation
- recharness/integrations
- recharness/cli

Implement at least:
- ProductItem
- Money
- Evidence
- Constraint
- Preference
- UserNeed
- RecommendationCandidate
- RecommendationBundle
- VerificationReport
- TraceEvent
- JsonlCatalog
- RuleBasedPreferenceParser
- KeywordRetriever
- AttributeFilterRetriever
- HybridRetriever
- SimpleRanker
- ConstraintVerifier
- ClaimVerifier
- BundleBuilder
- RecHarness.assist()
- RecHarness.verify_agent_recommendation()
- CLI commands: catalog validate, assist, verify, eval
- example backpack catalog and missions
- pytest coverage for parser, catalog loader, verifier, retriever, ranker, and assist flow

Use clean typing, docstrings, and small composable classes. Do not hardcode the backpack domain except in examples. The code should support arbitrary product categories through attributes and constraints.
```

---

# 21. 第一版最小验收标准

Codex 做完后，必须能跑通这四件事。

## 21.1 Validate catalog

```bash
recharness catalog validate examples/backpacks/catalog.jsonl
```

应该输出字段覆盖率和商品数量。

---

## 21.2 Assist

```bash
recharness assist \
  --catalog examples/backpacks/catalog.jsonl \
  --query "1500元以内，适合通勤，能放14寸电脑，不要太商务的双肩包"
```

应该输出：

```text
Top recommendations
Constraint report
Why recommended
Risks
Questions to ask
```

---

## 21.3 Verify bad answer

```bash
recharness verify \
  --catalog examples/backpacks/catalog.jsonl \
  --query "1500元以内、防水、适合通勤的双肩包" \
  --answer "我推荐 Urban Pro 30L，售价1899元，完全防水。"
```

应该识别：

```text
price violation
waterproof claim unsupported or overstated
```

---

## 21.4 Run eval

```bash
recharness eval \
  --catalog examples/backpacks/catalog.jsonl \
  --missions examples/backpacks/missions.jsonl \
  --out runs/demo/
```

应该生成：

```text
metrics.json
traces.jsonl
leaderboard.csv
```

---

# 22. 论文方向和开源项目如何绑定

开源项目 v0.1 对应论文主实验：

## Paper title

```text
RecHarness: An Agent-Agnostic Harness for Reliable Product Recommendation by General-Purpose Agents
```

## Contributions

```text
1. 提出 agent-agnostic recommendation harness 的系统设计。
2. 提出 RecommendationBundle 和 trace-level evaluation 格式。
3. 构建 constraint-heavy product recommendation benchmark。
4. 通过 ablation 证明 parser、retriever、verifier、ranker、bundle 各组件的贡献。
5. 证明 RecHarness 降低 hallucinated products、hard constraint violations 和 unsupported claims。
```

## 实验表格

| Variant            | Product Groundedness | Hard Constraint Satisfaction | Claim Support | Avg. Score |
| ------------------ | -------------------: | ---------------------------: | ------------: | ---------: |
| Direct Agent       |             baseline |                     baseline |      baseline |   baseline |
| Retrieval Only     |                    ↑ |                     slight ↑ |      slight ↑ |          ↑ |
| Retrieval + Parser |                    ↑ |                            ↑ |      slight ↑ |          ↑ |
| + Verifier         |                    ↑ |                      large ↑ |             ↑ |         ↑↑ |
| + Bundle           |                    ↑ |                      large ↑ |       large ↑ |         ↑↑ |
| Full RecHarness    |                 best |                         best |          best |       best |

---

# 23. 你现在应该让 Codex 先做什么

不要一开始让 Codex 做完整项目。第一条任务应该非常具体：

```text
Initialize the RecHarness repository with pyproject.toml, package structure, Pydantic schemas, JSONL catalog loader, and tests. Do not implement retrieval, ranking, MCP, or evaluation yet.
```

第一阶段只要把地基打好：

```text
schemas
catalog loader
validation
tests
example catalog
```

然后第二阶段再上：

```text
parser + verifier
```

因为 RecHarness 的成败不在模型调用，而在 schema 和 verifier 是否设计稳。

---

# 24. 最推荐的 v0.1 slogan

```text
Do not trust shopping agents. Harness them.
```

或者更学术一点：

```text
Reliable recommendation requires harness-level structure, not just stronger models.
```

这句话可以贯穿 README、论文和 demo。

[1]: https://developers.openai.com/api/docs/guides/agents?utm_source=chatgpt.com "Agents SDK | OpenAI API"
[2]: https://arxiv.org/abs/2606.12608?utm_source=chatgpt.com "Shopping Reasoning Bench: An Expert-Authored Benchmark for Multi-Turn Conversational Shopping Assistants"
[3]: https://openai.github.io/openai-agents-python/tracing/?utm_source=chatgpt.com "Tracing - OpenAI Agents SDK"
[4]: https://modelcontextprotocol.io/specification/2025-06-18/server/tools?utm_source=chatgpt.com "Tools"
[5]: https://docs.langchain.com/oss/python/langgraph/overview?utm_source=chatgpt.com "LangGraph overview - Docs by LangChain"
[6]: https://openai.github.io/openai-agents-python/tools/?utm_source=chatgpt.com "Tools - OpenAI Agents SDK"
