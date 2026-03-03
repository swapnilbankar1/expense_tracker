# Expense Tracker - Cloud Deployment Guide

## Table of Contents
1. [Deployment Options](#deployment-options)
2. [Prerequisites](#prerequisites)
3. [Containerization (Docker)](#containerization)
4. [Deploy to AWS](#deploy-to-aws)
5. [Deploy to Google Cloud](#deploy-to-google-cloud)
6. [Deploy to Heroku](#deploy-to-heroku)
7. [Deploy to Railway](#deploy-to-railway)
8. [Deploy to DigitalOcean](#deploy-to-digitalocean)
9. [Frontend Deployment (Vercel/Netlify)](#frontend-deployment)
10. [CI/CD Setup](#cicd-setup)
11. [Environment Configuration](#environment-configuration)
12. [Production Considerations](#production-considerations)

---

## Deployment Options

### Architecture Overview
```
┌─────────────────────────────────────────────────────────┐
│                     CLOUD DEPLOYMENT                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐         ┌──────────────────┐       │
│  │   Frontend     │         │     Backend      │       │
│  │   (Angular)    │◄────────┤    (FastAPI)     │       │
│  │                │  CORS   │                  │       │
│  │  Vercel/       │         │  AWS/GCP/        │       │
│  │  Netlify       │         │  Heroku          │       │
│  └────────────────┘         └────────┬─────────┘       │
│                                      │                  │
│                             ┌────────▼─────────┐        │
│                             │   PostgreSQL     │        │
│                             │   Database       │        │
│                             │                  │        │
│                             │  AWS RDS/        │        │
│                             │  GCP CloudSQL/   │        │
│                             │  Heroku Postgres │        │
│                             └──────────────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Recommended Stacks

| Stack | Frontend | Backend | Database | Cost |
|-------|----------|---------|----------|------|
| **Simple** | Vercel Free | Railway Free | Railway Postgres | $0-5/month |
| **AWS** | S3 + CloudFront | EC2/ECS | RDS PostgreSQL | $15-50/month |
| **GCP** | Firebase Hosting | Cloud Run | Cloud SQL | $10-40/month |
| **Heroku** | Heroku Static | Heroku Dyno | Heroku Postgres | $7-25/month |
| **Full Cloud** | Netlify | AWS Lambda + API Gateway | Aurora Serverless | $5-30/month |

---

## Prerequisites

### Required Accounts
- [ ] Cloud provider account (AWS/GCP/Heroku/Railway)
- [ ] GitHub account (for CI/CD)
- [ ] Domain name (optional)

### Required Tools
```bash
# Install Docker
brew install docker  # macOS
# or download from https://docker.com

# Install Cloud CLI tools
brew install awscli          # AWS
brew install google-cloud-sdk # GCP
brew install heroku/brew/heroku # Heroku

# Install Node.js and Python
brew install node python
```

---

## Containerization

### 1. Create Dockerfile for Backend

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "python -m app.scripts.init_db && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### 2. Create requirements.txt

Create `backend/requirements.txt`:
```txt
fastapi==0.128.0
uvicorn==0.40.0
sqlalchemy==2.0.39
psycopg2-binary==2.9.11
pdfplumber==0.11.9
python-multipart
pydantic==2.10.3
```

### 3. Create Frontend Dockerfile

Create `frontend/Dockerfile`:
```dockerfile
# Build stage
FROM node:20 as build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist/expense-tracker/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 4. Create nginx.conf for Frontend

Create `frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

### 5. Create docker-compose.yml (Full Stack)

Create `docker-compose.yml` in project root:
```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: expense_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: expense_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U expense_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://expense_user:${DB_PASSWORD}@postgres:5432/expense_db
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend/data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 6. Test Docker Build Locally

```bash
# Build and run
docker-compose up --build

# Test backend
curl http://localhost:8000/

# Test frontend
open http://localhost
```

---

## Deploy to AWS

### Architecture
```
Internet → Route 53 (DNS) → CloudFront (CDN)
                                ↓
                         S3 (Frontend)
                                ↓
                         ALB (Load Balancer)
                                ↓
                         ECS/EC2 (Backend)
                                ↓
                         RDS PostgreSQL
```

### Option 1: AWS ECS (Elastic Container Service)

#### Step 1: Setup Database (RDS)

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier expense-tracker-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username expense_user \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20 \
  --backup-retention-period 7

# Get database endpoint
aws rds describe-db-instances \
  --db-instance-identifier expense-tracker-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

#### Step 2: Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name expense-tracker-backend

# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
cd backend
docker build -t expense-tracker-backend .
docker tag expense-tracker-backend:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/expense-tracker-backend:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/expense-tracker-backend:latest
```

#### Step 3: Create ECS Cluster and Service

```bash
# Create cluster
aws ecs create-cluster --cluster-name expense-tracker-cluster

# Create task definition (task-definition.json)
cat > task-definition.json <<EOF
{
  "family": "expense-tracker-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/expense-tracker-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://expense_user:PASSWORD@DB_ENDPOINT:5432/expense_db"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/expense-tracker",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster expense-tracker-cluster \
  --service-name expense-tracker-service \
  --task-definition expense-tracker-backend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

#### Step 4: Deploy Frontend to S3 + CloudFront

```bash
# Build frontend
cd frontend
npm run build

# Create S3 bucket
aws s3 mb s3://expense-tracker-frontend

# Configure bucket for static website
aws s3 website s3://expense-tracker-frontend \
  --index-document index.html \
  --error-document index.html

# Upload files
aws s3 sync dist/expense-tracker/browser/ s3://expense-tracker-frontend/

# Create CloudFront distribution (optional, for CDN)
aws cloudfront create-distribution \
  --origin-domain-name expense-tracker-frontend.s3.amazonaws.com \
  --default-root-object index.html
```

### Option 2: AWS Amplify (Simplified)

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize Amplify
cd frontend
amplify init

# Add hosting
amplify add hosting

# Publish
amplify publish
```

---

## Deploy to Google Cloud

### Architecture
```
Internet → Cloud Load Balancer
              ↓
         Cloud Run (Backend)
              ↓
         Cloud SQL (PostgreSQL)
         
         Firebase Hosting (Frontend)
```

### Step 1: Setup GCP Project

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Login and set project
gcloud auth login
gcloud config set project expense-tracker-project
gcloud config set compute/region us-central1
```

### Step 2: Deploy Database (Cloud SQL)

```bash
# Create Cloud SQL instance
gcloud sql instances create expense-tracker-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Set root password
gcloud sql users set-password postgres \
  --instance=expense-tracker-db \
  --password=YOUR_PASSWORD

# Create database
gcloud sql databases create expense_db \
  --instance=expense-tracker-db
```

### Step 3: Deploy Backend to Cloud Run

```bash
# Build and push to Container Registry
cd backend
gcloud builds submit --tag gcr.io/expense-tracker-project/backend

# Deploy to Cloud Run
gcloud run deploy expense-tracker-backend \
  --image gcr.io/expense-tracker-project/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="postgresql://postgres:PASSWORD@/expense_db?host=/cloudsql/PROJECT:REGION:INSTANCE" \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE

# Get service URL
gcloud run services describe expense-tracker-backend \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

### Step 4: Deploy Frontend to Firebase Hosting

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize Firebase
cd frontend
firebase init hosting

# Build and deploy
npm run build
firebase deploy --only hosting
```

---

## Deploy to Heroku

### Easiest Option for Small Projects

#### Step 1: Install Heroku CLI

```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku

# Login
heroku login
```

#### Step 2: Deploy Backend

```bash
cd backend

# Create Heroku app
heroku create expense-tracker-backend

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Create Procfile
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git init
git add .
git commit -m "Initial commit"
git push heroku main

# Run migrations
heroku run python -m app.scripts.init_db

# Open app
heroku open
```

#### Step 3: Deploy Frontend

```bash
cd frontend

# Update environment with Heroku backend URL
# Edit src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://expense-tracker-backend.herokuapp.com'
};

# Build
npm run build

# Deploy to Heroku (or use Vercel/Netlify)
heroku create expense-tracker-frontend --buildpack heroku/nodejs
heroku buildpacks:add heroku-community/nginx
git push heroku main
```

---

## Deploy to Railway

### Simplest Option with Free Tier

#### Step 1: Deploy Backend

1. Visit [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your repository
5. Railway auto-detects Dockerfile
6. Add PostgreSQL database from Railway marketplace
7. Set environment variables:
   ```
   DATABASE_URL=${POSTGRES_CONNECTION_STRING}
   PORT=8000
   ```
8. Deploy!

#### Step 2: Deploy Frontend

1. Create new Railway service
2. Select frontend folder
3. Add build command: `npm run build`
4. Add start command: `npx http-server dist/expense-tracker/browser`
5. Set environment variable:
   ```
   API_URL=https://your-backend.railway.app
   ```
6. Deploy!

**Railway Benefits:**
- Free tier: 500 hours/month
- Auto SSL certificates
- GitHub integration
- Zero config PostgreSQL

---

## Deploy to DigitalOcean

### Using App Platform

#### Step 1: Create App

```bash
# Install doctl
brew install doctl

# Authenticate
doctl auth init

# Create app spec (app.yaml)
cat > app.yaml <<EOF
name: expense-tracker
services:
  - name: backend
    github:
      repo: YOUR_USERNAME/expense-tracker
      branch: main
      deploy_on_push: true
    source_dir: /backend
    dockerfile_path: Dockerfile
    envs:
      - key: DATABASE_URL
        value: \${db.DATABASE_URL}
    http_port: 8000
  
  - name: frontend
    github:
      repo: YOUR_USERNAME/expense-tracker
      branch: main
    source_dir: /frontend
    build_command: npm run build
    run_command: npx http-server dist/expense-tracker/browser

databases:
  - name: db
    engine: PG
    version: "15"
EOF

# Create app
doctl apps create --spec app.yaml

# Get app info
doctl apps list
```

---

## Frontend Deployment

### Option 1: Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

cd frontend

# Deploy
vercel

# Production deployment
vercel --prod
```

**vercel.json** configuration:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### Option 2: Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

cd frontend

# Deploy
netlify deploy

# Production deployment
netlify deploy --prod
```

**netlify.toml** configuration:
```toml
[build]
  command = "npm run build"
  publish = "dist/expense-tracker/browser"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

## CI/CD Setup

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: expense-tracker-backend
          IMAGE_TAG: ${{ github.sha }}
        run: |
          cd backend
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster expense-tracker-cluster \
            --service expense-tracker-service \
            --force-new-deployment

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Build
        run: |
          cd frontend
          npm run build
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
```

---

## Environment Configuration

### Backend Environment Variables

Create `.env` file in production:
```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# App Config
PORT=8000
DEBUG=false
ALLOWED_ORIGINS=https://your-frontend.com

# Storage (for S3)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=expense-statements

# Optional: LLM for categorization
OPENAI_API_KEY=your_openai_key
```

### Frontend Environment Variables

Update `src/environments/environment.prod.ts`:
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://api.yourdomain.com',
  uploadSizeLimit: 10485760, // 10MB
};
```

---

## Production Considerations

### 1. Security

#### Backend Security Checklist
- [ ] Use HTTPS only (TLS/SSL certificates)
- [ ] Enable CORS with specific origins
- [ ] Add rate limiting
- [ ] Implement authentication (JWT)
- [ ] Sanitize file uploads
- [ ] Use environment variables for secrets
- [ ] Enable SQL injection protection
- [ ] Add request validation
- [ ] Use security headers

**Add rate limiting** (`backend/app/main.py`):
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/statements/upload")
@limiter.limit("5/minute")
async def upload_statement(request: Request, file: UploadFile):
    # ...
```

#### Frontend Security Checklist
- [ ] Use environment variables for API URLs
- [ ] Implement Content Security Policy
- [ ] Enable HTTPS
- [ ] Sanitize user inputs
- [ ] Add CSRF protection

### 2. Monitoring

#### Setup Application Monitoring

**Backend - Add Sentry:**
```python
# pip install sentry-sdk
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

**Frontend - Add Google Analytics:**
```typescript
// npm install @angular/google-analytics
import { GoogleAnalyticsService } from 'ngx-google-analytics';
```

#### Setup Infrastructure Monitoring
- AWS CloudWatch for AWS deployments
- Google Cloud Monitoring for GCP
- Heroku Metrics for Heroku
- Custom: Prometheus + Grafana

### 3. Backup Strategy

#### Database Backups
```bash
# AWS RDS - Enable automated backups
aws rds modify-db-instance \
  --db-instance-identifier expense-tracker-db \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"

# Manual backup
pg_dump -h your-db-host -U expense_user expense_db > backup.sql
```

### 4. Scaling Strategy

#### Horizontal Scaling
```yaml
# AWS ECS - Auto Scaling
AutoScalingTarget:
  Type: AWS::ApplicationAutoScaling::ScalableTarget
  Properties:
    MinCapacity: 1
    MaxCapacity: 10
    ResourceId: service/expense-tracker-cluster/expense-tracker-service
    ScalableDimension: ecs:service:DesiredCount
    ServiceNamespace: ecs
```

### 5. Cost Optimization

| Service | Free Tier | Estimated Cost |
|---------|-----------|----------------|
| Railway | 500 hours/month | $0-5/month |
| Vercel | 100GB bandwidth | $0/month |
| Heroku | 1000 dyno hours | $7/month |
| AWS EC2 t3.micro | 750 hours/month | $10-15/month |
| AWS RDS db.t3.micro | None | $15-20/month |
| GCP Cloud Run | 2M requests/month | $0-10/month |

**Optimization Tips:**
- Use serverless for low traffic
- Enable auto-scaling down to 0 for development
- Use CDN for static assets
- Compress images and assets
- Enable database connection pooling

---

## Quick Start Commands

### Deploy to Railway (Fastest)
```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy"
git push origin main

# 2. Go to railway.app
# 3. Click "New Project" → "Deploy from GitHub"
# 4. Add PostgreSQL from marketplace
# 5. Done! ✅
```

### Deploy to Heroku
```bash
# Backend
cd backend
heroku create expense-tracker-backend
heroku addons:create heroku-postgresql:mini
git push heroku main

# Frontend
cd frontend
npm run build
vercel --prod
```

### Deploy to AWS (Production)
```bash
# 1. Setup infrastructure
terraform init
terraform apply

# 2. Push Docker images
./scripts/deploy-backend.sh

# 3. Deploy frontend
cd frontend && npm run build
aws s3 sync dist/ s3://your-bucket/
```

---

## Troubleshooting

### Common Issues

**Issue: CORS errors in production**
```python
# Fix: Update CORS origins in backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Issue: Database connection timeout**
```python
# Fix: Add connection pooling
from sqlalchemy.pool import NullPool
engine = create_engine(DATABASE_URL, poolclass=NullPool)
```

**Issue: File upload fails in production**
```python
# Fix: Increase max file size
from fastapi import FastAPI, File, UploadFile

app = FastAPI()
app.add_middleware(
    middleware_class=CORSMiddleware,
    max_age=3600,
    max_request_size=10485760  # 10MB
)
```

---

## Conclusion

**Recommended Deployment Path:**

1. **Development**: Local Docker Compose
2. **Staging**: Railway (free tier)
3. **Production**: AWS/GCP with proper scaling

**Best Practices:**
✅ Always use environment variables
✅ Enable HTTPS
✅ Setup monitoring and logging
✅ Implement CI/CD
✅ Regular database backups
✅ Use CDN for static assets
✅ Enable auto-scaling
✅ Set up alerts for errors

Your expense tracker is now ready for the cloud! 🚀
