# Azure Portal Deployment Guide (Alternative to CLI)

If you're having Azure CLI issues, you can deploy directly through the Azure Portal web interface.

## Step 1: Create Azure Web App via Portal

1. **Go to [portal.azure.com](https://portal.azure.com)** and sign in
2. **Click "Create a resource"**
3. **Search for "Web App"** and select it
4. **Click "Create"**

## Step 2: Configure Your Web App

### Basic Settings:
- **Subscription**: Choose your subscription
- **Resource Group**: Create new "ufc-predictor-rg"
- **Name**: "ufc-predictor-app" (must be globally unique)
- **Publish**: Code
- **Runtime stack**: Python 3.9
- **Operating System**: Linux
- **Region**: East US (or nearest to you)

### App Service Plan:
- **Create new plan**: "ufc-predictor-plan"
- **Sku and size**: Basic B1 ($13-15/month)

Click **"Review + create"** then **"Create"**

## Step 3: Deploy Your Code

### Option A: GitHub Integration (Recommended)

1. **Push your code to GitHub** if not already there
2. In Azure Portal, go to your Web App
3. Go to **"Deployment Center"** in the left menu
4. Choose **"GitHub"** as source
5. **Authorize** Azure to access your GitHub
6. Select your **repository** and **branch** (main)
7. Click **"Save"**

### Option B: ZIP Deployment

1. **Create a ZIP file** of your `backend` folder
2. In Azure Portal, go to your Web App
3. Go to **"Advanced Tools"** > **"Go"** (Kudu)
4. Go to **"Tools"** > **"Zip Push Deploy"**
5. **Drag your ZIP file** to deploy

## Step 4: Configure Application Settings

1. In Azure Portal, go to your Web App
2. Go to **"Configuration"** in the left menu
3. Under **"Application settings"**, add:
   - **Name**: `FLASK_ENV`, **Value**: `production`
   - **Name**: `FLASK_DEBUG`, **Value**: `False`
   - **Name**: `SCM_DO_BUILD_DURING_DEPLOYMENT`, **Value**: `true`

4. Click **"Save"**

## Step 5: Test Your Application

1. Go to **"Overview"** in your Web App
2. Click the **URL** to visit your application
3. It should show your UFC Predictor interface

## Troubleshooting

### If the app doesn't start:
1. Go to **"Log stream"** to see error messages
2. Check **"Console"** in Advanced Tools (Kudu)
3. Verify all files are uploaded correctly

### Common issues:
- **Import errors**: Check `requirements.txt` has all dependencies
- **File not found**: Ensure all model files (.joblib) are included
- **Memory errors**: Upgrade to higher App Service Plan

## Cost Management

- **Monitor usage** in "Cost Management + Billing"
- **Set up alerts** for cost thresholds
- **Stop the app** when not in use to save costs

## Next Steps

1. **Set up custom domain** (optional)
2. **Enable HTTPS-only** in TLS/SSL settings
3. **Add Application Insights** for monitoring
4. **Set up backup** for your app 