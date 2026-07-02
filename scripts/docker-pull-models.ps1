# 拉取 Ollama 模型（Windows PowerShell）
# 用法: .\scripts\docker-pull-models.ps1
#       .\scripts\docker-pull-models.ps1 qwen3:14b

param(
    [string]$Model = "qwen3:8b"
)

$running = docker ps --format "{{.Names}}" | Select-String -Pattern "^drama-ollama$"
if (-not $running) {
    Write-Host "错误: drama-ollama 容器未运行。请先执行:"
    Write-Host "  docker compose --profile app --profile gpu up -d"
    exit 1
}

Write-Host "正在拉取模型: $Model"
docker exec drama-ollama ollama pull $Model
docker exec drama-ollama ollama list
Write-Host "完成。"
