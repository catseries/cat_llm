# cat_llm

用于 AI 大模型学习。本仓库提供一个可直接调用智谱（Z.ai / 智谱 AI）Chat Completions API 的“三国历史知识小助手”示例。

## 功能

- 通过智谱 API 调用大模型回答三国历史问题。
- 内置“三国史小助手”系统提示词，强调区分正史与《三国演义》。 
- 支持普通输出和流式输出。
- 只依赖 Python 标准库，便于快速运行。

## 准备工作

1. 准备 Python 3.10+。
2. 在智谱开放平台创建 API Key。
3. 设置环境变量（推荐使用 `ZAI_API_KEY`）：

```bash
export ZAI_API_KEY="你的智谱API Key"
```

> 兼容旧命名：如果没有设置 `ZAI_API_KEY`，程序也会读取 `ZHIPUAI_API_KEY`。

## 快速开始

普通问答：

```bash
python -m src.sanguo_assistant.cli "赤壁之战为什么会发生？"
```

流式输出：

```bash
python -m src.sanguo_assistant.cli --stream "诸葛亮北伐的主要困难是什么？"
```

指定模型、温度和最大输出长度：

```bash
python -m src.sanguo_assistant.cli \
  --model glm-4-plus \
  --temperature 0.3 \
  --max-tokens 2048 \
  "请比较正史和演义中关羽的形象差异"
```

## 示例问题

- “官渡之战中曹操为什么能以少胜多？”
- “刘备入蜀的历史背景是什么？”
- “正史中的周瑜和《三国演义》里的周瑜有什么不同？”
- “司马氏为什么能最终统一三国？”

## 参考接口

当前脚本默认调用智谱开放平台的 Chat Completions 接口：

```text
POST https://open.bigmodel.cn/api/paas/v4/chat/completions
Authorization: Bearer $ZAI_API_KEY
Content-Type: application/json
```

默认模型为 `glm-4-plus`。你可以通过 `--model` 改成账号可用的其他智谱模型。
