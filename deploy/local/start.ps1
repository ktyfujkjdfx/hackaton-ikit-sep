# Поднимает демо-стенд на одном адресе http://localhost
#
#   бэкенд  uvicorn 127.0.0.1:8000   (свой процесс, живёт после закрытия терминала)
#   nginx   0.0.0.0:80               отдаёт frontend/dist и проксирует /api на бэкенд
#
# Запуск:   powershell -ExecutionPolicy Bypass -File deploy\local\start.ps1
# Остановка: deploy\local\stop.ps1

$ErrorActionPreference = 'Stop'
$root    = (Resolve-Path "$PSScriptRoot\..\..").Path
$backend = Join-Path $root 'backend'
$dist    = Join-Path $root 'frontend\dist'
$python  = Join-Path $backend '.venv\Scripts\python.exe'
$logs    = Join-Path $root 'deploy\local\logs'

function Find-Nginx {
    $cmd = Get-Command nginx -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -like '*.exe') { return $cmd.Source }
    $pkg = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Directory -ErrorAction SilentlyContinue |
           Where-Object Name -like '*nginx*' | Select-Object -First 1
    if ($pkg) {
        $dir = Get-ChildItem $pkg.FullName -Directory | Where-Object Name -like 'nginx-*' | Select-Object -First 1
        if ($dir) { return (Join-Path $dir.FullName 'nginx.exe') }
    }
    throw 'nginx не найден. Установите: winget install --id nginxinc.nginx'
}

if (-not (Test-Path $python)) { throw "Нет виртуального окружения: $python. Смотрите README, раздел «Как запустить локально»." }
if (-not (Test-Path (Join-Path $dist 'index.html'))) {
    throw "Нет собранного фронтенда: $dist. Выполните: cd frontend; npm run build"
}
New-Item -ItemType Directory -Force -Path $logs | Out-Null

# --- бэкенд -----------------------------------------------------------------
if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) {
    Write-Host 'Бэкенд уже слушает 8000 — пропускаю.'
} else {
    $env:NLU_MODE      = 'onnx'          # наша нейросеть; без неё откатится на sklearn
    $env:EXPLAIN_MODE  = 'templates'     # детерминированные ответы, без видеокарты
    $env:PYTHONUTF8    = '1'
    $env:CORS_ORIGINS  = 'http://localhost,http://127.0.0.1,http://localhost:5173'
    Start-Process -FilePath $python `
        -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' `
        -WorkingDirectory $backend -WindowStyle Hidden `
        -RedirectStandardOutput "$logs\backend.out.log" -RedirectStandardError "$logs\backend.err.log"
    Write-Host 'Бэкенд запускается...'
}

# --- nginx ------------------------------------------------------------------
$nginxExe = Find-Nginx
$nginxDir = Split-Path $nginxExe -Parent
Copy-Item (Join-Path $PSScriptRoot 'nginx.win.conf') (Join-Path $nginxDir 'conf\fincom.conf') -Force
& $nginxExe -p $nginxDir -c 'conf\fincom.conf' -t
if (Get-Process nginx -ErrorAction SilentlyContinue) {
    & $nginxExe -p $nginxDir -c 'conf\fincom.conf' -s reload
    Write-Host 'nginx перечитал конфигурацию.'
} else {
    Start-Process -FilePath $nginxExe -ArgumentList '-p',"`"$nginxDir`"",'-c','conf\fincom.conf' `
        -WorkingDirectory $nginxDir -WindowStyle Hidden
    Write-Host 'nginx запущен.'
}

# --- проверка ---------------------------------------------------------------
$ok = $false
foreach ($i in 1..40) {
    Start-Sleep -Milliseconds 500
    try {
        $health = Invoke-RestMethod 'http://localhost/api/health' -TimeoutSec 3
        if ($health.ok) { $ok = $true; break }
    } catch { }
}
if (-not $ok) { throw "Стенд не поднялся. Смотрите $logs\backend.err.log" }

$checks = Invoke-RestMethod 'http://localhost/api/checks' -TimeoutSec 60
Write-Host ''
Write-Host "Готово: http://localhost"
Write-Host ("  модель: {0}, пояснения: {1}" -f $health.nlu, $health.explain)
Write-Host ("  эталонные проверки: {0} из {1}" -f $checks.passed, $checks.total)
$ip = (Get-NetIPAddress -AddressFamily IPv4 |
       Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
       Select-Object -First 1).IPAddress
if ($ip) { Write-Host "  в локальной сети: http://$ip" }
