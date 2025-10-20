# Script PowerShell pour fixer le problème npm rollup car npm insatlle une version trop récente de rollup qui casse Vite.
# Ce script supprime node_modules et package-lock.json, nettoie le cache npm, réinstalle les dépendances avec --legacy-peer-deps, puis réinstalle le module rollup
# Exécuter avec: .\fix-npm.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Fix npm rollup pour Vite" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Nettoyage des modules npm..." -ForegroundColor Yellow

# Supprimer node_modules si existe
if (Test-Path node_modules) {
    Remove-Item -Recurse -Force node_modules
    Write-Host "✓ node_modules supprimé" -ForegroundColor Green
}

# Supprimer package-lock.json si existe
if (Test-Path package-lock.json) {
    Remove-Item package-lock.json
    Write-Host "✓ package-lock.json supprimé" -ForegroundColor Green
}

# Nettoyer cache npm
Write-Host ""
Write-Host "Nettoyage du cache npm..." -ForegroundColor Yellow
npm cache clean --force
Write-Host "✓ Cache nettoyé" -ForegroundColor Green

# Réinstallation propre des dépendances avec legacy-peer-deps
Write-Host ""
Write-Host "Réinstallation des dépendances (Vite 5.4.11 stable)..." -ForegroundColor Yellow
npm install --legacy-peer-deps
Write-Host "✓ Dépendances installées" -ForegroundColor Green

# Réinstallation du module Rollup binaire pour Windows (corrige le bug npm)
Write-Host ""
Write-Host "Réparation du module Rollup natif (Windows x64)..." -ForegroundColor Yellow
npm install @rollup/rollup-win32-x64-msvc
Write-Host "✓ Rollup natif réinstallé" -ForegroundColor Green

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Installation terminée!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Vous pouvez maintenant lancer:" -ForegroundColor Cyan
Write-Host "  npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Astuce: en cas de problème persistant, essayez plutôt:" -ForegroundColor Yellow
Write-Host "  pnpm install" -ForegroundColor White
Write-Host "  pnpm run dev" -ForegroundColor White
Write-Host ""
