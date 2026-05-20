# IAF — Intent Alignment Framework

> 基于论文《意图对齐框架：人机意图通信的形式化规范 v0.3》的完整 Python 实现。

**IAF** 提供了一套形式化工具，用于精确表达、组合、验证和演化人类意图，确保 AI 系统的行为与人类真实意图对齐。

---

## 核心理念

传统的人机交互依赖自然语言的模糊性，IAF 通过 **意图原子（Intent Atoms）** 和 **形式化语义（Formal Semantics）** 将意图提升为可计算、可验证、可演化的数学对象：

```
Intent = (P, N, A)
         │   │   │
         │   │   └─ Autonomy — AI 自主决策空间
         │   └───── Negative — 需要避免的（软约束）
         └───────── Positive — 必须满足的（硬约束）
```

### 关键特性

| 特性 | 说明 |
|------|------|
| **27 个意图原子** | 覆盖存在、关系、行为、约束、偏好、不确定性 6 大类 |
| **形式化语义** | 每个原子带有 LaTeX 形式化语义，可追溯 |
| **代数组合** | 6 个组合操作符（∥ → ▷ ⊕ ⊓ ⊔），支持模块化构建 |
| **三步一致性** | 语法 → 语义 → 自主权，逐级检查 |
| **分层验证** | L0-L3 四级对齐验证（语法/结构/模拟/同构） |
| **意图演化** | 6 种变换 + 弱可逆性保证 + 版本控制 |
| **Minimax 评分** | 硬约束失败则总分为 0，符合安全优先原则 |
| **零外部依赖** | 仅使用 Python 标准库 |

---

## 安装

```bash
# 克隆或下载项目后直接导入
cd /Users/apple/IAF-system
python3 -c "from iaf_core import *; print('OK')"
```

**要求：** Python 3.10+（使用 `dataclass(frozen=True)`、`|` 类型联合等特性）

---

## 快速开始

### 1. 构造意图

```python
from iaf_core import *

# "我想要一个电商平台，用户能浏览、搜索、加购、付款"
intent = Intent(
    P={
        exists('user'),           # 存在用户
        exists('order'),          # 存在订单
        reachable('home', 'browse'),  # 首页可达浏览
        atomic('payment'),        # 支付是原子操作
        always('inventory >= 0'), # 库存永不小于 0
    },
    N={
        avoid('complex'),         # 避免复杂设计
    },
    A={
        autonomy('layout'),       # AI 自主决定布局
        autonomy('color_scheme'), # AI 自主决定配色
    },
    label='E-commerce',
)
```

### 2. 良构性检查

```python
ok, errors = intent.well_formed()
# ok = True, errors = []
```

### 3. 三步一致性检查

```python
from iaf_core.consistency import check_consistency, check_all, ConsistencyLevel

# 逐级检查
result = check_consistency(intent, ConsistencyLevel.SYNTACTIC)  # 语法
result = check_consistency(intent, ConsistencyLevel.SEMANTIC)   # 语义
result = check_consistency(intent, ConsistencyLevel.AUTONOMY)   # 自主权

# 一次全查
all_results = check_all(intent)
```

### 4. 组合操作符

```python
from iaf_core.operators import combine, CombineOp, detect_conflict

# 并行组合（所有约束取并集）
combined = combine(intent_a, intent_b, CombineOp.PARALLEL)

# 顺序组合（自主空间取交集 — 缩小）
sequential = combine(intent_a, intent_b, CombineOp.SEQUENTIAL)

# 优先组合（第一个意图优先）
prioritized = combine(intent_a, intent_b, CombineOp.PRIORITY)

# 检测两个意图间的冲突
conflicts = detect_conflict(intent_a, intent_b)
```

### 5. 分层验证（Human vs AI）

```python
from iaf_core.verification import layered_verify, VerifyLevel

# L0: 语法检查 — 双方是否良构
# L1: 结构覆盖 — AI 是否覆盖所有人类原子
# L2: 模拟关系 — AI 的行为是否模拟人类意图
# L3: 同构 — 完全等价（最强）
result = layered_verify(human_intent, ai_intent, level=VerifyLevel.L2)
print(f"Passed: {result.passed}, Score: {result.score}")
```

### 6. 意图演化

```python
from iaf_core.evolution import evolve, diff, Delta, TransformType, VersionedIntent

# 初始版本
v0 = VersionedIntent(intent=intent, version=0, message="Initial spec")

# 添加新约束：支持退货
delta = Delta(type=TransformType.ADD, atom=always('return_window >= 7'), space='P')
v1 = evolve(intent, delta, "Added return policy")

# 查看版本间差异
for change in diff(v0.intent, v1.intent):
    print(change)

# 查看演化历史
print(v1.history)  # ['Added return policy']
```

---

## 项目结构

```
IAF-system/
├── iaf_core/                    # 核心引擎（✅ 已实现）
│   ├── __init__.py              # 公共 API 导出
│   ├── atoms.py                 # 27 个意图原子 + TraceState + 形式化语义
│   ├── spaces.py                # Intent(P, N, A) 三元组 + minimax 评分
│   ├── operators.py             # 6 个组合操作符 + 冲突检测
│   ├── consistency.py           # 三步一致性检查（语法→语义→自主权）
│   ├── verification.py          # L0-L3 分层验证协议
│   └── evolution.py             # 6 种变换 + 弱可逆性 + 版本控制
│
├── iaf_parser/                  # ⬜ 待实现：多模态表达层（NL → Intent）
├── iaf_modules/                 # ⬜ 待实现：可复用模块库（UserAuth, CRUD, Payment...）
├── iaf_cli/                     # ⬜ 待实现：命令行交互工具
│
├── tests/                       # 测试套件（116 用例，全部通过）
│   ├── test_atoms.py            # 原子语义、便捷函数、TraceState
│   ├── test_spaces.py           # Intent 良构性、组合、评分
│   ├── test_operators.py        # 组合操作符、冲突检测、代数性质
│   ├── test_consistency.py      # 三步一致性检查
│   ├── test_verification.py     # L0-L3 分层验证
│   └── test_evolution.py        # 变换、可逆性、版本演化
│
├── examples/
│   └── ecommerce.py             # 电商系统完整示例流水线
├── pyproject.toml
└── README.md
```

---

## 27 个意图原子

### 分类矩阵

| 类别 | 原子 | 数学符号 | 数量 |
|------|------|----------|------|
| **存在** | Exists | ∃x | 4 |
| | ExistsUnique | ∃!x | |
| | NonEmpty | D ≠ ∅ | |
| | Empty | D = ∅ | |
| **关系** | Assoc | x ↔ y | 5 |
| | Subset | X ⊆ Y | |
| | Disjoint | X ∩ Y = ∅ | |
| | Dep | x → y (T₁⊸T₂) | |
| | Precedes | e₁ ≺ e₂ | |
| **行为** | Reachable | a ↝ b | 4 |
| | Reversible | a ⇄ b | |
| | Idempotent | f(f(x)) = f(x) | |
| | Atomic | atomic(f) | |
| **约束** | Always | □φ (LTL) | 5 |
| | Eventually | ◇φ (LTL) | |
| | ForAll | ∀x∈S, C(x) | |
| | ForSome | ∃x∈S, C(x) | |
| | Bound | lo ≤ x ≤ hi | |
| **偏好** | Prefer | a ≻ b | 5 |
| | PreferEq | a ⪰ b | |
| | Avoid | ¬x | |
| | Weight | w(x) | |
| | Soft | soft(x) | |
| **不确定** | Autonomy | A(x) | 4 |
| | Confirm | confirm(x) | |
| | Fuzzy | μ(x) ∈ [0,1] | |
| | Probabilistic | P(x) ≥ p | |

### 依赖类型（Dep）

```python
from iaf_core import DepType

DepType.FUNCTIONAL   # 函数依赖 (F): x → y
DepType.MULTIVALUED  # 多值依赖 (M): x →→ y
DepType.JOIN         # 连接依赖 (J): ⋈[R₁, R₂]
```

---

## API 参考

### Intent(P, N, A)

```python
Intent(
    P: Iterable[IntentAtom],   # 正向约束（硬约束）
    N: Iterable[IntentAtom],   # 负向约束（软约束/避免）
    A: Iterable[IntentAtom],   # 自主空间（AI 决策权）
    label: str = "",           # 可选标签
    metadata: dict = None,     # 可选元数据
)
```

**方法：**

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `well_formed()` | `(bool, list[str])` | 良构性检查（P∩N=∅, 无重复等） |
| `combine(other, op)` | `Intent` | 使用指定操作符组合另一个意图 |
| `satisfaction(trace)` | `(float, float)` | minimax 评分 — (P得分, N得分) |
| `empty(label="")` | `Intent` | 类方法：创建空意图 |

### 组合操作符语义

| 操作符 | P | N | A | 含义 |
|--------|---|---|---|------|
| ∥ parallel | P₁ ∪ P₂ | N₁ ∪ N₂ | A₁ ∪ A₂ | 完全并行，所有约束叠加 |
| → sequential | P₁ ∪ P₂ | N₁ ∪ N₂ | A₁ ∩ A₂ | 顺序执行，自主空间缩小 |
| ▷ priority | P₁ ∪ (P₂ − N₁) | N₁ ∪ N₂ | A₁ ∪ (A₂ − P₁) | 第一意图优先 |
| ⊕ exclusive | (P₁ − P₂) ∪ (P₂ − P₁) | N₁ ∪ N₂ | A₁ ∪ A₂ | 互斥选择 |
| ⊓ merge | P₁ ∩ P₂ | N₁ ∩ N₂ | A₁ ∪ A₂ | 取交集，最保守 |
| ⊔ join | P₁ ∪ P₂ | N₁ ∪ N₂ | A₁ ∩ A₂ | 取并集，最宽松 |

### 分层验证

| 级别 | 名称 | 可判定性 | 说明 |
|------|------|----------|------|
| L0 | Syntax | 可判定 | 双方均良构 |
| L1 | Structure | 可判定 | AI 覆盖人类所有原子 |
| L2 | Simulation | 半可判定 | AI 意图模拟人类意图（P_H ⊆ P_A, N_H ⊆ N_A, A_A ⊆ A_H） |
| L3 | Isomorphism | 不可判定 | 结构同构（图同构问题） |

### 意图演化

| 变换 | 说明 | 可逆性 |
|------|------|--------|
| ADD | 添加原子到某个空间 | 强可逆 |
| REMOVE | 从空间移除原子 | 强可逆 |
| MODIFY | 替换原子 | 强可逆 |
| PROMOTE | 软约束→硬约束 | 弱可逆 |
| DEMOTE | 硬约束→软约束 | 弱可逆 |
| MIGRATE | 原子跨空间迁移 | 弱可逆 |

---

## 运行测试

```bash
cd /Users/apple/IAF-system
python3 -m pytest tests/ -v          # 详细输出
python3 -m pytest tests/ --tb=short  # 简短回溯
python3 -m pytest tests/ -q          # 静默模式
```

当前状态：**116 passed** ✅

---

## 运行示例

```bash
cd /Users/apple/IAF-system
python3 examples/ecommerce.py
```

电商示例演示了完整流水线：

1. 定义意图原子（22 个，覆盖 6 个实体、6 个行为、4 个约束、2 个避免、4 个自主）
2. 构建 Intent(P, N, A) 三元组
3. 三步一致性检查
4. AI 细化意图 + L0/L1/L2 分层验证
5. 意图演化（v0 → v1 → v2）+ Diff 展示

---

## 待实现模块

| 模块 | 计划功能 | 优先级 |
|------|----------|--------|
| `iaf_parser` | 自然语言 → Intent 解析器，支持多模态表达 | P0 |
| `iaf_modules` | 可复用意图模块库（UserAuth, CRUD, Payment, Search...） | P1 |
| `iaf_cli` | 命令行交互工具，可视化意图结构、实时验证 | P2 |

---

## 设计原则

1. **零外部依赖** — 仅用 stdlib（dataclass, enum, abc, typing, datetime）
2. **不可变数据结构** — Intent、IntentAtom、Delta 均为 frozen dataclass
3. **TDD 驱动** — 116 个测试用例定义 API 接口，全部通过
4. **形式化可追溯** — 每个原子都有 LaTeX 形式化语义（`atom.formal_semantics`）
5. **安全优先** — Minimax 评分：硬约束失败则总分为 0

---

## 相关论文

> 《意图对齐框架：人机意图通信的形式化规范 v0.3》
>
> 定义了意图原子、形式化语义、组合操作符、一致性检查、分层验证和演化引擎的完整理论框架。

---

## License

MIT
