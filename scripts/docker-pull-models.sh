#!/usr/bin/env sh
# 首次启动 GPU 栈后，拉取 Ollama 模型
# 用法: sh scripts/docker-pull-models.sh [model]
# 示例: sh scripts/docker-pull-models.sh qwen3:8b

MODEL="${1:-qwen3:8b}"

if ! docker ps --format '{{.Names}}' | grep -q '^drama-ollama$'; then
  echo "错误: drama-ollama 容器未运行。请先执行:"
  echo "  docker compose --profile app --profile gpu up -d"
  exit 1
fi

echo "正在拉取模型: ${MODEL}"
docker exec drama-ollama ollama pull "${MODEL}"
docker exec drama-ollama ollama list
echo "完成。"
