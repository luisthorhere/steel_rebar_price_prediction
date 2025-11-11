# ===============================================
# Cloud Run Deployment Script
# Author: Luis Diaz
# Project: DeAcero - Steel Rebar Price Prediction
# ===============================================

# --- CONFIGURATION ---
$projectId = "deacero-api"
$serviceName = "steel-rebar-api"
$imageName = "gcr.io/$projectId/$serviceName"
$region = "us-central1"

Write-Host "🚀 Starting deployment for project '$serviceName' on Cloud Run..." -ForegroundColor Cyan

# --- Step 1: Set the active GCP project ---
Write-Host "🔧 Setting active project in gcloud..." -ForegroundColor Yellow
gcloud config set project $projectId

# --- Step 2: Build Docker image and push to Container Registry ---
Write-Host "🐳 Building Docker image..." -ForegroundColor Yellow
gcloud builds submit --tag $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Docker image build failed. Check Cloud Build logs." -ForegroundColor Red
    exit 1
}

# --- Step 3: Deploy new version to Cloud Run ---
Write-Host "☁️ Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $serviceName `
  --image $imageName `
  --platform managed `
  --region $region `
  --allow-unauthenticated

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment completed successfully." -ForegroundColor Green
} else {
    Write-Host "❌ Error: Deployment failed. Check the logs above." -ForegroundColor Red
    exit 1
}

# --- Step 4: Retrieve and display the service URL ---
Write-Host "`n🌐 Fetching service URL..." -ForegroundColor Yellow
$url = gcloud run services describe $serviceName --region $region --format "value(status.url)"

if ($url) {
    Write-Host "✅ Service successfully deployed at: $url" -ForegroundColor Green
} else {
    Write-Host "Could not retrieve service URL. Check Cloud Run console." -ForegroundColor Yellow
}