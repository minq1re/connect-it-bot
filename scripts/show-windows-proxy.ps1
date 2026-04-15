# Показывает системный прокси Windows (WinINET). То же, что бот теперь подхватывает автоматически.
$path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
try {
    $en = (Get-ItemProperty -Path $path -Name ProxyEnable -ErrorAction Stop).ProxyEnable
    $sv = (Get-ItemProperty -Path $path -Name ProxyServer -ErrorAction Stop).ProxyServer
    Write-Host "ProxyEnable: $en"
    Write-Host "ProxyServer: $sv"
    if ($en -ne 1) { Write-Host "Системный прокси выключен — в VPN включите «использовать системный прокси» или задайте TELEGRAM_PROXY_URL в backend/.env" }
} catch {
    Write-Host "Не удалось прочитать настройки: $_"
}
