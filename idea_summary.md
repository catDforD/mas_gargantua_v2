# Idea

**撰写日期**：2026.1.14

## 一、智能体安全信用评估

### 1.1 参考文献
```
A-Trust: Attention_Knows_Whom_to_Trust_Attention_based.pdf
Attention-tracker: Attention Tracker: Detecting Prompt Injection Attacks in LLMs
ITI: The Internal State of an LLM Knows When It’s Lying
Qwen3Guard-Gen（生成式安全分类器）
```
### 1.2 该部分目标
- 基于  、Attention-tracker、ITI等方法，复现相关论文的实验结果。
- 分析不同方法在不同场景下的效果。
- 选取相应维度作为系统安全评估指标。
    - 安全性
    - 诚实性
    - 可靠性
    - 工具调用安全 (optional)
- 构建一个针对多智能体系统的评估系统，该系统能够根据以上指标对系统中每个 agent 进行评估。

### 1.3 部分实验结果
- Attention tracker 能够有效检测提示注入攻击，准确率 0.932 ,针对 prompt-injections 等数据集。
- 针对 A-Trust 进行了原理复现，其中对可靠性指标得分基本在 0.8 以上。
- 对于 iti 论文进行了复现和改进，针对 truthful_qa 数据集，准确率在 0.82 左右（phi3-3.8b 模型）。
- 对于 Qwen3Guard-Gen 进行了简单测试，它更针对的是的不安全内容的审查，并非针对注入攻击，可以作为系统安全评估的一部分。

### 1.4 新的建议
- 四个维度分别训练四个 模型 进行评分，以此作为安全评分系统

## 二、多智能体系统自动生成
### 2.1 参考文献&开源项目
```
AUTOMATED DESIGN OF AGENTIC SYSTEMS
AFLOW: AUTOMATING AGENTIC WORKFLOW GENERATION
AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors
Flow: Modularized Agentic Workflow Automation
```

### 2.2 该部分目标
- 设计或寻找一个符合要求的自动生成多智能体系统的框架。
- 可以参考 oh-my-opencode 插件和 opencode 组织架构来配置智能体池。
- 然后参考 Flow 的任务拆分机制，先拆分任务，再分配给各个智能体来完成。


## 2.3 当前计划
- 基于 LangGraph 自己实现一个多智能体系统自动生成框架。

## 三、内生安全的多智能体系统自动构建
### 3.1 参考文献
```
暂无
```
### 3.2 该部分目标
- 基于以上两部分内容，综合设计一个内生安全的多智能体系统自动构建框架。
- 该框架能够根据用户需求，自动构建符合要求的多智能体系统，确保系统在生成时就有安全保证，同时在系统持续运行时候能够进行防御和安全性的迭代。

## 四、压力场景测试
- 攻击面： 模型层/智能体层/传染性
- 构建 Threat model