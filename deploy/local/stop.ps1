# Останавливает демо-стенд: nginx и бэкенд на 8000.
#   powershell -ExecutionPolicy Bypass -File deploy\local\stop.ps1

$nginx = Get-Process nginx -ErrorAction SilentlyContinue
if ($nginx) {
    $exe = $nginx[0].Path
    if ($exe) { & $exe -p (Split-Path $exe -Parent) -s quit 2>$null }
    Start-Sleep -Seconds 1
    Get-Process nginx -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host 'nginx остановлен.'
} else {
    Write-Host 'nginx не запущен.'
}

$conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Stop-Process -Id $conn[0].OwningProcess -Force
    Write-Host 'Бэкенд остановлен.'
} else {
    Write-Host 'Бэкенд не запущен.'
}
