# qwen2API

qwen2API v2 — 将 `chat.qwen.ai` 转换为兼容 OpenAI / Anthropic / Gemini 格式的 API 接口。

## 简介
这是一个轻量级的 API 适配器，通过 FastAPI 提供服务，可将对通义千问网页版的请求无缝转换为符合主流模型调用规范的 API，方便各类客户端和开发工具直接接入使用。

## 特性
- **多平台兼容**：支持 OpenAI、Anthropic、Gemini API 格式。
- **轻量高效**：基于 FastAPI 和 Uvicorn 构建异步服务。
- **网页自动化支持**：通过 Playwright 实现对网页版接口的底层模拟。

## 安装与运行

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **启动服务**：
   ```bash
   python qwen2api.py --port 8080 --api-key sk-xxx --workers 3
   ```
   参数说明：
   - `--port`: 服务监听端口（默认 8080）
   - `--api-key`: 设置调用 API 时的密钥
   - `--workers`: 工作进程数（默认 3）

## 分支说明
- `main`: 默认分支，存放稳定可用版本，用于对外展示和供大家直接使用。
- `dev`: 开发分支，存放最新特性代码和正在测试中的修改。
