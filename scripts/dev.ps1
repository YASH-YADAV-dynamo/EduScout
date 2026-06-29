# Start the MCP server for ChatGPT connector testing.
# Clears shell BASE_URL so .env PUBLIC_BASE_URL is not overridden.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Remove-Item Env:BASE_URL -ErrorAction SilentlyContinue
$env:PYTHONPATH = (Get-Location).Path

Write-Host "PUBLIC_BASE_URL from .env should match your ngrok URL."
Write-Host "Connector URL: check https://YOUR-NGROK-URL/health -> chatgpt_connector_url"
Write-Host ""

$port = if ($env:PORT) { $env:PORT } else { "8000" }
Write-Host "Starting on port $port — run: ngrok http $port"
Write-Host ""

.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port $port --reload
