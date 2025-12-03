# Deployment Guide for JobAlign AI

## Overview
This project consists of:
- **Frontend**: React + TypeScript + Vite (deployed on Vercel)
- **Backend**: Python FastAPI (requires separate hosting)

---

## Frontend Deployment on Vercel

### Prerequisites
- GitHub account with your repository
- Vercel account (free at vercel.com)

### Step 1: Prepare Your Repository
1. Ensure all changes are committed to Git
2. Push to your main branch on GitHub
3. Verify `.env` files are in `.gitignore` (they are)

### Step 2: Deploy to Vercel

**Option A: Using Vercel CLI (Recommended)**
```bash
npm install -g vercel
vercel
```

**Option B: Using Vercel Dashboard**
1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure build settings:
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `bun install`

### Step 3: Set Environment Variables in Vercel

In Vercel Dashboard → Settings → Environment Variables, add:

**For Development:**
```
VITE_API_BASE_URL=https://your-backend-dev-url.com
VITE_GOOGLE_CLIENT_ID=your_dev_client_id
VITE_GOOGLE_REDIRECT_URI=https://your-vercel-url.vercel.app/auth/google/callback
VITE_GITHUB_CLIENT_ID=your_dev_github_id
VITE_GITHUB_REDIRECT_URI=https://your-vercel-url.vercel.app/auth/github/callback
```

**For Production:**
```
VITE_API_BASE_URL=https://your-backend-prod-url.com
VITE_GOOGLE_CLIENT_ID=your_prod_client_id
VITE_GOOGLE_REDIRECT_URI=https://jobalign.vercel.app/auth/google/callback
VITE_GITHUB_CLIENT_ID=your_prod_github_id
VITE_GITHUB_REDIRECT_URI=https://jobalign.vercel.app/auth/github/callback
```

### Step 4: Update OAuth Redirect URIs
- **Google Console**: Add your Vercel URL to authorized redirect URIs
- **GitHub OAuth**: Update callback URL in GitHub settings

---

## Backend Deployment Options

Your Python FastAPI backend needs to be hosted separately. Here are the best options:

### Option 1: Railway (⭐ Recommended for Python)

**Pros:**
- Easy Python deployment
- Free tier available
- Database included
- Automatic deployments from GitHub

**Steps:**
1. Go to https://railway.app
2. Create account and connect GitHub
3. Create new project → Deploy from GitHub repo
4. Configure environment variables in Railway dashboard
5. Get your backend URL (e.g., `https://your-app.railway.app`)

### Option 2: Render

**Pros:**
- Free tier with automatic deployments
- PostgreSQL included
- Easy environment variable setup

**Steps:**
1. Go to https://render.com
2. Create new Web Service from GitHub
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables

### Option 3: Heroku (Paid - Free tier ended)

### Option 4: AWS/Azure/DigitalOcean (For production)

---

## Full Deployment Checklist

### Frontend (Vercel)
- [ ] Repository pushed to GitHub
- [ ] `vercel.json` configured
- [ ] `.env.example` created with all required variables
- [ ] Environment variables set in Vercel dashboard
- [ ] Build test: `npm run build` runs successfully
- [ ] Deployment successful

### Backend (Railway/Render)
- [ ] Python dependencies in `requirements.txt`
- [ ] `.env` file with all required keys (kept local, not in repo)
- [ ] Database configured (SQLite or PostgreSQL)
- [ ] Migrations run on deploy
- [ ] All environment variables set on hosting platform
- [ ] API endpoints tested and working

### Integration
- [ ] Update `VITE_API_BASE_URL` to deployed backend URL
- [ ] Test OAuth redirects
- [ ] Test API calls from frontend
- [ ] Test file uploads (if applicable)
- [ ] CORS configured correctly on backend

---

## Common Issues & Solutions

### CORS Errors
**Backend FastAPI** (app/main.py):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-vercel-url.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables Not Loading
- Verify variables are set in Vercel dashboard
- Restart deployment after setting variables
- Check variable names match in code

### OAuth Redirect URI Mismatch
- Exact match required (including protocol and trailing slashes)
- Update in Google/GitHub console when URL changes
- Use exact Vercel deployment URL

### Backend Not Responding
- Check backend is running and accessible
- Verify `VITE_API_BASE_URL` in Vercel environment variables
- Check CORS configuration on backend
- Verify firewall/security rules

---

## Redeployment

**Vercel** (Automatic):
- Every push to main branch triggers automatic rebuild
- Manual redeploy from Vercel dashboard if needed

**Backend** (Depends on platform):
- **Railway**: Auto-deploys on git push
- **Render**: Auto-deploys or manual trigger
- Check platform dashboard for deployment logs

---

## Monitoring

### Vercel
- Dashboard shows deployment status
- Analytics and performance metrics
- Error logs available

### Backend Platform
- Check deployment logs
- Monitor database usage
- Track API response times

---

## Next Steps

1. **Setup Backend Hosting**: Choose Railway or Render
2. **Deploy Frontend**: Connect to Vercel
3. **Test Integration**: Verify frontend-backend communication
4. **Custom Domain**: Add your domain in Vercel settings
5. **SSL/HTTPS**: Automatically configured by Vercel

---

For more help:
- Vercel Docs: https://vercel.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- Railway Docs: https://docs.railway.app
- Render Docs: https://docs.render.com
