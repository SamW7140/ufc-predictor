# Azure Deployment Guide for UFC Predictor

## Prerequisites

1. **Azure Account**: Create a free account at [azure.microsoft.com](https://azure.microsoft.com)
2. **Azure CLI**: Install from [docs.microsoft.com/cli/azure](https://docs.microsoft.com/cli/azure)
3. **Git**: Ensure your project is in a Git repository

## Deployment Options

### Frontend Deployment (Optional)
Deploy your frontend (`index.html`, `script.js`, `style.css`) to Azure Static Web Apps or Storage:

#### Option A: Azure Static Web Apps
```bash
az staticwebapp create --name ufc-fight-frontend --resource-group ufc-fight-predictor-2024-rg --source https://github.com/YOUR_GITHUB_USERNAME/ufc-predictor --branch main --app-location "/frontend" --login-with-github
```

#### Option B: Azure Storage (Static Website)
```bash
# Create storage account (name must be globally unique)
az storage account create --name ufcfightfrontend2024 --resource-group ufc-fight-predictor-2024-rg --location "East US" --sku Standard_LRS

# Enable static website
az storage blob service-properties update --account-name ufcfightfrontend2024 --static-website --index-document index.html

# Get the website URL
az storage account show --name ufcfightfrontend2024 --resource-group ufc-fight-predictor-2024-rg --query "primaryEndpoints.web" --output tsv

# Upload frontend files
az storage blob upload-batch --account-name ufcfightfrontend2024 --source ./frontend --destination '$web'
```

### Backend Deployment

#### Option 1: Azure App Service (Recommended)

#### Step 1: Login to Azure
```bash
az login
```

#### Step 2: Create Resource Group
```bash
az group create --name ufc-fight-predictor-2024-rg --location "East US"
```

#### Step 3: Create App Service Plan
```bash
az appservice plan create --name ufc-ml-service-plan --resource-group ufc-fight-predictor-2024-rg --sku B1 --is-linux
```

#### Step 4: Create Web App
```bash
az webapp create --resource-group ufc-fight-predictor-2024-rg --plan ufc-ml-service-plan --name ufc-fight-ml-api --runtime "PYTHON|3.9" --deployment-local-git
```

#### Step 5: Configure App Settings
```bash
az webapp config appsettings set --resource-group ufc-fight-predictor-2024-rg --name ufc-fight-ml-api --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

#### Step 6: Deploy Code
```bash
# Get deployment credentials from Azure portal, then add Azure remote
git remote add azure https://YOUR_DEPLOYMENT_USERNAME@ufc-fight-ml-api.scm.azurewebsites.net/ufc-fight-ml-api.git

# Deploy
git push azure main
```

#### Option 2: Azure Container Instances

#### Step 1: Create Dockerfile
Create a `Dockerfile` in the backend directory:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

#### Step 2: Build and Push to Azure Container Registry
```bash
# Create ACR (name must be globally unique)
az acr create --resource-group ufc-fight-predictor-2024-rg --name ufcfightmlregistry2024 --sku Basic

# Login to ACR
az acr login --name ufcfightmlregistry2024

# Build and push image
docker build -t ufcfightmlregistry2024.azurecr.io/ufc-fight-predictor:v1.0 ./backend
docker push ufcfightmlregistry2024.azurecr.io/ufc-fight-predictor:v1.0

# Get ACR password
az acr credential show --resource-group ufc-fight-predictor-2024-rg --name ufcfightmlregistry2024

# Create container instance (replace PASSWORD_FROM_ABOVE with actual password)
az container create --resource-group ufc-fight-predictor-2024-rg --name ufc-ml-container-app --image ufcfightmlregistry2024.azurecr.io/ufc-fight-predictor:v1.0 --cpu 1 --memory 2 --registry-login-server ufcfightmlregistry2024.azurecr.io --registry-username ufcfightmlregistry2024 --registry-password PASSWORD_FROM_ABOVE --dns-name-label ufc-fight-ml-api --ports 5000
```

## Configuration Notes

### Environment Variables
Set these in Azure App Service Configuration:

- `FLASK_ENV`: `production`
- `FLASK_DEBUG`: `False`
- `PORT`: `5000` (Azure will set this automatically)

### File Structure for Deployment
Your backend folder should contain:
- `app.py` (main Flask application)
- `requirements.txt` (Python dependencies)
- `runtime.txt` (Python version)
- `startup.sh` (startup script)
- All model files (.joblib)
- All data files (.csv)

### Cost Considerations

#### Azure App Service (B1 Basic)
- **Cost**: ~$13-15/month
- **Features**: 1.75 GB RAM, 10 GB storage
- **Best for**: Production applications

#### Azure Container Instances
- **Cost**: Pay-per-use (~$0.0012/hour for 1 vCPU, 1 GB RAM)
- **Features**: More flexible scaling
- **Best for**: Development/testing

## Troubleshooting

### Common Issues

1. **Module Import Errors**: Ensure all dependencies are in `requirements.txt`
2. **File Path Issues**: Use relative paths for model and data files
3. **Memory Issues**: Upgrade to higher SKU if models are large
4. **Timeout Issues**: Increase timeout settings in Azure portal

### Logs and Monitoring
```bash
# View application logs
az webapp log tail --name ufc-fight-ml-api --resource-group ufc-fight-predictor-2024-rg

# Enable application insights
az monitor app-insights component create --app ufc-fight-ml-insights --location "East US" --resource-group ufc-fight-predictor-2024-rg --application-type web

# Enable logging
az webapp log config --name ufc-fight-ml-api --resource-group ufc-fight-predictor-2024-rg --application-logging filesystem --level information
```

## Security Recommendations

1. **Use Application Insights** for monitoring
2. **Enable HTTPS only** in Azure portal
3. **Set up custom domain** if needed
4. **Configure CORS** for your frontend:
   ```bash
   # If using Static Web App
   az webapp cors add --resource-group ufc-fight-predictor-2024-rg --name ufc-fight-ml-api --allowed-origins https://ufc-fight-frontend.azurestaticapps.net
   
   # If using Storage Static Website  
   az webapp cors add --resource-group ufc-fight-predictor-2024-rg --name ufc-fight-ml-api --allowed-origins https://ufcfightfrontend2024.z13.web.core.windows.net
   
   # For local development
   az webapp cors add --resource-group ufc-fight-predictor-2024-rg --name ufc-fight-ml-api --allowed-origins http://localhost:3000
   ```
5. **Use Key Vault** for sensitive configuration

## Scaling Options

1. **Vertical Scaling**: Increase App Service Plan SKU
2. **Horizontal Scaling**: Enable auto-scaling rules
3. **Azure Front Door**: Add CDN for global distribution

## Maintenance

1. **Regular Updates**: Keep dependencies updated
2. **Monitor Performance**: Use Application Insights
3. **Backup Strategy**: Regular backups of models and data
4. **Health Checks**: Configure health check endpoints

## Quick Reference - Resource Names Used

### App Service Deployment:
- **Resource Group**: `ufc-fight-predictor-2024-rg`
- **App Service Plan**: `ufc-ml-service-plan`
- **Web App**: `ufc-fight-ml-api`
- **Application Insights**: `ufc-fight-ml-insights`

### Container Deployment:
- **Container Registry**: `ufcfightmlregistry2024`
- **Container Instance**: `ufc-ml-container-app`
- **Image**: `ufcfightmlregistry2024.azurecr.io/ufc-fight-predictor:v1.0`

### Frontend Deployment:
- **Static Web App**: `ufc-fight-frontend`
- **Storage Account**: `ufcfightfrontend2024`

### URLs (after deployment):
- **Backend API**: `https://ufc-fight-ml-api.azurewebsites.net`
- **Frontend (Static Web App)**: `https://ufc-fight-frontend.azurestaticapps.net`
- **Frontend (Storage)**: `https://ufcfightfrontend2024.z13.web.core.windows.net`
- **Container Instance**: `http://ufc-fight-ml-api.eastus.azurecontainer.io:5000` 