# ============================================
# AXCESS CRM - Script de deploiement VPS
# Double-clic pour deployer quand t'es pret
# ============================================

$VPS_IP = "151.80.232.127"
$VPS_USER = "ubuntu"
$LOCAL_PATH = "C:\Users\antoi\Documents\axcess-crm"
$REMOTE_PATH = "/opt/crm/axcess-crm"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   AXCESS CRM - Deploiement VPS" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "VPS cible : $VPS_IP" -ForegroundColor Yellow
Write-Host "Dossier local : $LOCAL_PATH" -ForegroundColor Yellow
Write-Host ""

# Confirmation avant de deployer
$confirm = Read-Host "Deployer maintenant ? (oui/non)"
if ($confirm -ne "oui") {
    Write-Host "Deploiement annule." -ForegroundColor Red
    pause
    exit
}

Write-Host ""
Write-Host "[1/3] Transfert des fichiers vers le VPS..." -ForegroundColor Green

# Transfert avec scp en excluant les dossiers inutiles
# On transfere uniquement backend et frontend (le code)
scp -r "$LOCAL_PATH\backend" "${VPS_USER}@${VPS_IP}:${REMOTE_PATH}/"
scp -r "$LOCAL_PATH\frontend\src" "${VPS_USER}@${VPS_IP}:${REMOTE_PATH}/frontend/"
scp "$LOCAL_PATH\frontend\package.json" "${VPS_USER}@${VPS_IP}:${REMOTE_PATH}/frontend/"
scp "$LOCAL_PATH\docker-compose.yml" "${VPS_USER}@${VPS_IP}:${REMOTE_PATH}/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR : Transfert echoue." -ForegroundColor Red
    pause
    exit
}

Write-Host "[2/3] Rebuild et redemarrage des containers..." -ForegroundColor Green

# Rebuild sur le VPS
ssh "${VPS_USER}@${VPS_IP}" "cd ${REMOTE_PATH} && docker compose up -d --build"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR : Build Docker echoue." -ForegroundColor Red
    pause
    exit
}

Write-Host ""
Write-Host "[3/3] Verification..." -ForegroundColor Green
ssh "${VPS_USER}@${VPS_IP}" "cd ${REMOTE_PATH} && docker compose ps"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   Deploiement termine !" -ForegroundColor Green
Write-Host "   CRM disponible sur http://10.0.0.1" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
pause
