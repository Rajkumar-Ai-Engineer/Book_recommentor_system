# Book Recommendation System - Simplified ECS Deployment

## 🚀 Quick Start

This project has been simplified for easy deployment to AWS ECS Fargate with minimal configuration.

### Local Testing
```bash
# Test with Docker Compose
docker-compose up

# Access at http://localhost:8000
```

### Production Deployment to AWS ECS
```bash
# Navigate to AWS folder and deploy
cd .aws
chmod +x deploy-ecs.sh
./deploy-ecs.sh
```

## 📁 Simplified File Structure

```
.aws/
├── ecs-fargate-simple.json     # Single ECS configuration file
├── deploy-ecs.sh               # Automated deployment script  
├── ECS-DEPLOYMENT-SIMPLE.md    # Detailed deployment guide
├── README-SIMPLE-DEPLOY.md     # This file
└── README.md                   # AWS folder overview

Project Root/
├── docker-compose.yml          # Local testing
├── Dockerfile                  # Production-ready container
└── main.py                     # FastAPI application
```

## 🔧 What Was Simplified

### Before (Complex)
- Multiple JSON configuration files (7+ files)
- Separate IAM role definitions
- Complex CloudWatch configurations
- EFS volume configurations
- Manual secret management
- Separate service and task definitions

### After (Simple)
- **Single configuration file** (`ecs-fargate-simple.json`)
- **One deployment script** that handles everything
- **Automatic resource creation** (IAM, security groups, etc.)
- **Simplified logging** (CloudWatch auto-creation)
- **No external dependencies** (EFS, secrets manager optional)
- **Container-native approach**

## 🚦 Deployment Options

### Option 1: Fully Automated (Recommended)
```bash
cd .aws
./deploy-ecs.sh
```
- Creates all AWS resources automatically
- Builds and pushes Docker image
- Deploys to ECS Fargate
- Handles networking and security

### Option 2: Docker Compose (Local)
```bash
docker-compose up --scale book-recommendation=3
```
- Perfect for local development
- Tests container behavior
- Simulates production scaling

### Option 3: Manual (Advanced Users)
Follow the step-by-step guide in `ECS-DEPLOYMENT-SIMPLE.md`

## 📊 Application Features

- **Hybrid ML Recommendation Engine** (Collaborative + Content-Based)
- **FastAPI Web Interface** with real-time suggestions
- **Auto-fallback to Mock Engine** when ML model unavailable
- **Production-ready logging** and health checks
- **Scalable architecture** (2+ instances)

## 🏗️ Architecture

```
Internet → ALB → ECS Fargate Tasks → FastAPI App
                     ↓
               CloudWatch Logs
```

**Simple & Effective**: No complex infrastructure, just containers running your ML application.

## 🔍 Key Improvements

1. **Reduced Complexity**: 7 config files → 1 config file
2. **Faster Deployment**: Manual setup → Automated script
3. **Better Documentation**: Technical specs → User-friendly guides  
4. **Easier Maintenance**: Complex networking → Simple defaults
5. **Cost Effective**: Removed unnecessary EFS, simplified IAM

## 📈 Performance & Scaling

- **CPU**: 1 vCPU per task (adjustable)
- **Memory**: 2GB per task (optimized for ML workloads)
- **Scaling**: Horizontal scaling ready
- **Availability**: Multi-AZ deployment support

## 🛠️ Development Workflow

```bash
# 1. Local development
docker-compose up

# 2. Test changes
curl http://localhost:8000/

# 3. Deploy to production
cd .aws  
./deploy-ecs.sh

# 4. Monitor
aws ecs describe-services --cluster ml-platform-prod --services book-recommendation-system
```

## 📝 Next Steps

1. Navigate to `.aws` folder and run `./deploy-ecs.sh` to deploy to AWS
2. Access your application via the ECS task public IP
3. Scale as needed with `aws ecs update-service --desired-count N`
4. Set up Application Load Balancer for production domain

**Result**: Production-ready ML application deployed to AWS ECS Fargate in minutes, not hours.