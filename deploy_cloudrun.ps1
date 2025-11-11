# === Cloud Run Deployment Script ===
$ErrorActionPreference = "Stop"

$projectId   = "deacero-api"
$serviceName = "steel-rebar-api"
$imageName   = "gcr.io/$projectId/$serviceName"
$region      = "us-central1"

Write-Host "Starting deployment for project '$serviceName' on Cloud Run..." -ForegroundColor Cyan

# Step 1: Set active project
Write-Host "Setting active project in gcloud..." -ForegroundColor Yellow
gcloud config set project $projectId | Out-Null

# Step 2: Build Docker image and push
Write-Host "Building Docker image..." -ForegroundColor Yellow
gcloud builds submit --tag $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker image build failed. Check Cloud Build logs." -ForegroundColor Red
    exit 1
}

# Step 3: Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $serviceName `
  --image $imageName `
  --platform managed `
  --region $region `
  --allow-unauthenticated

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Deployment failed. Check the logs above." -ForegroundColor Red
    exit 1
}

# Step 4: Retrieve and display service URL
Write-Host "Fetching service URL..." -ForegroundColor Yellow
$url = gcloud run services describe $serviceName --region $region --format="value(status.url)"

if ($url) {
    Write-Host "Service successfully deployed at: $url" -ForegroundColor Green
} else {
    Write-Host "Failed to retrieve service URL. Check Cloud Run console." -ForegroundColor Yellow
    exit 1
}
