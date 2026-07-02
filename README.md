# AI 短剧自动生产平台

基于 Vue3 + FastAPI + LangGraph + Ollama + ComfyUI + FFmpeg 的 AI 短剧自动生成系统。

## 功能（MVP）

- 故事输入 → 自动分镜 → 生成 3 个镜头 → 拼接 15 秒视频
- **竖屏歌词 MV（抖音风）**：上传 Suno 歌曲 + 歌词 → 自动分镜 → Ken Burns 画面 → 原曲混流 + ASS 字幕
- 角色上传 / AI 生成 / 角色库选用
- WebSocket 实时进度
- Ollama / ComfyUI 离线时自动 Mock + 占位图模式

## 快速启动

### 方式 A：Docker Compose（推荐，适合云主机 / 一键部署）

详见 **[doc/Docker-Compose部署指南.md](../doc/Docker-Compose部署指南.md)**

```powershell
cd E:\ai\ai-drama-platform
copy .env.docker.example .env

# 无 GPU：Mock 模式
docker compose --profile app up -d --build

# 有 GPU：完整 AI 栈
docker compose --profile app --profile gpu up -d --build
.\scripts\docker-pull-models.ps1
```

访问：http://localhost

### 方式 B：裸机开发

#### 1. 后端

```powershell
cd E:\ai\ai-drama-platform
copy .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> Windows 建议使用 `py` 启动 Python（需 Python 3.9+，推荐 3.11+）。

API 文档：http://localhost:8000/docs

#### 2. 前端

```powershell
cd E:\ai\ai-drama-platform\frontend
npm install
npm run dev
```

访问：http://localhost:5173

#### 3. 外部依赖（可选，提升生成质量）

| 服务 | 用途 | 安装指南 |
|-----|------|---------|
| Ollama + qwen3:8b | 故事解析/分镜 | `doc/组件安装与配置指南.md` |
| ComfyUI + Flux | 图像/视频生成 | 同上 |
| FFmpeg | 视频拼接 | `winget install Gyan.FFmpeg` |

## 项目结构

```
ai-drama-platform/
├── backend/          # FastAPI + Agents + Pipeline
├── frontend/         # Vue3 + Element Plus
├── storage/          # 运行时数据（数据库、媒体文件）
├── docker/           # Dockerfile 与 Nginx 配置
├── data/comfyui/     # ComfyUI 模型挂载（Docker）
├── scripts/          # Docker 辅助脚本
├── docker-compose.yml
├── .env.example          # 裸机开发环境变量
├── .env.docker.example   # Docker 部署环境变量
```

## 开发路线

- **Phase 1（当前）**：MVP 端到端 Pipeline
- **Phase 2**：IPAdapter 角色一致、LangGraph 完整整合
- **Phase 3**：Celery 队列、字幕/BGM

详细方案见 `doc/AI短剧自动生产平台-产品与技术方案.md`  
MV 功能见 `doc/MV功能规划.md`
