---
title: multiagent-ai-lab demo
sdk: gradio
sdk_version: 6.32.0
python_version: "3.12"
app_file: app.py
short_description: Chat demo of a local multi-agent RAG platform
pinned: false
---

# multiagent-ai-lab demo

A plain chat with Qwen3.5-9B. Every message runs through the same agent harness as the
platform's API. Questions over files come later.

The demo runs on a shared free GPU (Hugging Face ZeroGPU), so every visitor has a small amount
of GPU time per day. The code and the plan: https://github.com/mdu-ai-lab/multiagent-ai-lab
