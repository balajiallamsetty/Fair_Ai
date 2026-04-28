# Deployment Guide - Fair AI Guardian

This guide provides step-by-step instructions to deploy the Fair AI Guardian project:
- **Backend** → Render (Python FastAPI)
- **Frontend** → Vercel (React + TypeScript)

---

## Table of Contents
1. [Backend Deployment (Render)](#backend-deployment-render)
2. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
3. [Post-Deployment Configuration](#post-deployment-configuration)
4. [Troubleshooting](#troubleshooting)

---

## Backend Deployment (Render)

### Prerequisites
- Render account (free tier available at [https://render.com](https://render.com))
- GitHub repository with backend code
- Python requirements.txt file

### Step 1: Prepare Backend for Deployment

1.1 Ensure `requirements.txt` is updated:
```bash
cd backend
pip freeze > requirements.txt
```

1.2 Create a `render.yaml` configuration file in the project root:
```bash
touch render.yaml
```

1.3 Add the following content to `render.yaml`:
```yaml
services:
  - type: web
    name: fair-ai-guardian-api
    env: python
    plan: free
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        scope: service
        sync: false
      - key: ENVIRONMENT
        value: production
      - key: SECRET_KEY
        scope: service
        sync: false
```

1.4 Update `backend/app/main.py` to load environment variables:
```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fair AI Guardian API", version="1.0.0")

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 2: Push Code to GitHub

```bash
git add .
git commit -m "Add render.yaml for deployment"
git push origin main
```

### Step 3: Connect Render to GitHub

3.1 Go to [https://dashboard.render.com](https://dashboard.render.com)

3.2 Click **"New +"** → **"Web Service"**

3.3 Select **"Deploy existing repository"** or connect your GitHub account

3.4 Choose the `Fair_Ai` repository

3.5 Fill in the configuration:
   - **Name**: `fair-ai-guardian-api`
   - **Environment**: Python
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or Paid if needed)

### Step 4: Set Environment Variables on Render

4.1 In the Render dashboard, go to your service → **Environment**

4.2 Add the following environment variables:
   - `DATABASE_URL`: Your PostgreSQL/MongoDB connection string
   - `SECRET_KEY`: A strong secret key (use `openssl rand -hex 32`)
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGINS`: `https://your-frontend-domain.vercel.app` (add after frontend deployment)

4.3 Click **"Deploy"**

### Step 5: Verify Backend Deployment

5.1 Wait for the build to complete (2-5 minutes)

5.2 Once deployed, you'll get a URL like: `https://fair-ai-guardian-api.onrender.com`

5.3 Test the API:
```bash
curl https://fair-ai-guardian-api.onrender.com/docs
```

5.4 Save the API URL for frontend configuration

---

## Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (free tier at [https://vercel.com](https://vercel.com))
- GitHub repository with frontend code
- Node.js 16+ (local development only)

### Step 1: Prepare Frontend for Deployment

1.1 Ensure `frontend/.env.production` is set up:
```bash
cd frontend
touch .env.production
```

1.2 Add the backend API URL to `.env.production`:
```env
VITE_API_URL=https://fair-ai-zp5c.onrender.com
```

1.3 Update `frontend/src/services/http.ts` to use environment variable:
```typescript
import axios from 'axios';

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const httpClient = axios.create({
  baseURL: apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

1.4 Verify `package.json` build script:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  }
}
```

### Step 2: Push Changes to GitHub

```bash
git add .
git commit -m "Add environment configuration for Vercel deployment"
git push origin main
```

### Step 3: Connect Vercel to GitHub

3.1 Go to [https://vercel.com](https://vercel.com) and sign in

3.2 Click **"Add New Project"**

3.3 Select **"Import Git Repository"**

3.4 Choose the `Fair_Ai` repository

3.5 Configure the project:
   - **Framework**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### Step 4: Set Environment Variables on Vercel

4.1 In the Vercel project settings, go to **Settings** → **Environment Variables**

4.2 Add the following:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://fair-ai-zp5c.onrender.com` (your backend URL)
   - **Environments**: Production, Preview, Development

4.3 Click **"Save"**

### Step 5: Deploy Frontend

5.1 Click **"Deploy"**

5.2 Wait for the build to complete (2-5 minutes)

5.3 Once deployed, you'll get a URL like: `https://fair-ai-guardian.vercel.app`

5.4 Test the frontend by visiting the URL

### Step 6: Update Backend CORS

6.1 Go back to Render dashboard

6.2 Update the `CORS_ORIGINS` environment variable to include your Vercel URL:
```
https://fair-ai-sable.vercel.app,https://your-custom-domain.com
```

6.3 The service will automatically restart

---

## Post-Deployment Configuration

### Step 1: Connect Custom Domain (Optional)

#### For Vercel:
1.1 Go to Vercel Project → **Settings** → **Domains**

1.2 Add your custom domain

1.3 Follow DNS configuration instructions

#### For Render:
1.4 Go to Render Service → **Settings** → **Custom Domain**

1.5 Add your custom domain and update DNS records

### Step 2: Set Up Monitoring

2.1 **Vercel Analytics**: 
   - Go to **Analytics** tab to monitor performance
   - View deployment logs in **Deployments** tab

2.2 **Render Logs**:
   - View real-time logs in the Render dashboard
   - Set up email alerts for failures

### Step 3: Enable Auto-Deployment

3.1 Both Render and Vercel automatically redeploy when you push to the `main` branch

3.2 Monitor deployment status in their respective dashboards

---

## Troubleshooting

### Backend Issues

#### Problem: Build fails on Render
**Solution**:
- Check the build logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Ensure Python version compatibility (3.9+)

#### Problem: Database connection fails
**Solution**:
- Verify `DATABASE_URL` environment variable is set correctly
- Check database credentials and network access
- Ensure firewall allows Render's IP addresses

#### Problem: CORS errors on frontend
**Solution**:
- Update `CORS_ORIGINS` environment variable on Render
- Include your Vercel domain: `https://your-app.vercel.app`

### Frontend Issues

#### Problem: Blank page on Vercel
**Solution**:
- Check browser console for errors
- Verify `VITE_API_URL` environment variable is set
- Check network requests in DevTools
- Ensure backend API is accessible

#### Problem: API calls fail with 404
**Solution**:
- Verify backend URL is correct in `.env.production`
- Check backend is running and accessible
- Ensure routes match between frontend and backend

#### Problem: Build fails on Vercel
**Solution**:
- Check build logs: **Deployments** → View Build Logs
- Verify TypeScript compilation: `npm run build` locally
- Check for missing dependencies in `package.json`

---

## Deployment Checklist

- [ ] Backend `requirements.txt` is updated
- [ ] `render.yaml` is created and configured
- [ ] Backend environment variables are set on Render
- [ ] Frontend `.env.production` has `VITE_API_URL`
- [ ] `frontend/src/services/http.ts` uses environment variable
- [ ] Frontend `package.json` build script is correct
- [ ] Both repositories are pushed to GitHub
- [ ] Render deployment is successful and accessible
- [ ] Vercel deployment is successful and accessible
- [ ] Frontend can communicate with backend API
- [ ] CORS is properly configured
- [ ] Custom domains are set up (if applicable)

---

## Quick Reference URLs

After deployment, save these URLs:

- **Backend API**: `https://fair-ai-zp5c.onrender.com`
- **Backend API Docs**: `https://fair-ai-zp5c.onrender.com/docs`
- **Frontend App**: `https://fair-ai-sable.vercel.app`
- **Render Dashboard**: `https://dashboard.render.com`
- **Vercel Dashboard**: `https://vercel.com/dashboard`

---

## Next Steps

1. Monitor both deployments for errors
2. Set up error tracking (e.g., Sentry)
3. Configure logging and monitoring
4. Set up automated backups for database
5. Implement CI/CD pipeline for automatic testing
6. Set up SSL certificates (auto-configured by both platforms)

---

**Last Updated**: April 28, 2026
