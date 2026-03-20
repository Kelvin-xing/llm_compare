---
title: LLM Compare
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "6.9.0"
app_file: app.py
pinned: false
---

# LLM Compare

A Gradio web app for side-by-side LLM comparison. Compare your own model (via any OpenAI-compatible API endpoint) against reference models from OpenAI, Anthropic, Google Gemini, Qwen, and Yi.

## Features

- **Two-column layout**: Your custom model on the left, a selectable reference model on the right
- **Multiple providers**: OpenAI (GPT-4o), Anthropic (Claude), Google Gemini, Qwen, Yi
- **Evaluation workflow**: Comment and grade (1–10) each model's response
- **Nickname tracking**: All evaluations tagged with user nickname
- **Excel export**: Download all evaluation data as `.xlsx`

## Setup

```bash
pip install -r requirements.txt
python app.py
```

## Environment Variables

Set these as env vars (or HuggingFace Spaces secrets) to provide default API keys:

| Variable | Provider |
|---|---|
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |
| `GOOGLE_API_KEY` | Google Gemini |
| `DASHSCOPE_API_KEY` | Qwen (DashScope) |
| `YI_API_KEY` | Yi (01.AI) |

Users can override keys per-session in the UI. Keys are never stored.

## Deployment

Deploy on HuggingFace Spaces with Gradio SDK. Set the API keys as repository secrets.

