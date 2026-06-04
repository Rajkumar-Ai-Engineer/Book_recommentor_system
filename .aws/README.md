# AWS ECS Deployment - CI/CD Automated

This folder contains ECS Fargate configuration for the Book Recommendation System.

## 📁 Files Structure

```
.aws/
├── ecs-fargate-simple.json      # ECS configuration template (reference)
├── README-SIMPLE-DEPLOY.md      # Legacy manual deployment guide  
├── DEPLOYMENT_CHECKLIST.md      # Original deployment checklist
├── DEPLOYMENT_GUIDE.md          # Original deployment guide
└── README.md                    # This file
```

## 🚀 Deployment

### Automated CI/CD (Recommended)
**The GitHub Actions workflow handles everything automatically:**

1. **Push to main branch**
2. **CI runs tests**
3. **CD deploys to ECS Fargate**
4. **Access your app** at the provided public IP:8000

**No manual steps needed!** ✨

### Manual Deployment (If needed)
Use the AWS CLI with the configuration template as reference:

```bash
# The ecs-fargate-simple.json shows the structure
# GitHub Actions generates the actual task definition dynamically
```

## 📋 What's Automated

### GitHub Actions Handles:
- ✅ **Docker build & push** to ECR
- ✅ **AWS resource creation** (ECR, ECS, IAM, Security Groups)
- ✅ **Task definition generation** with latest image
- ✅ **ECS service deployment** and updates
- ✅ **Health monitoring** and status reporting

### Configuration Reference:
- **`ecs-fargate-simple.json`** - Shows ECS structure (for reference only)
- **GitHub Actions** - Uses this structure to generate actual deployments

## 🎯 Benefits

1. **No Manual Scripts**: GitHub Actions replaces manual deployment
2. **Auto Resource Management**: Creates/updates AWS resources automatically  
3. **CI/CD Integration**: Tests → Build → Deploy pipeline
4. **Zero Configuration**: Just push code and deploy
5. **Production Ready**: Health checks, logging, security included

## 🔧 Requirements

**Only GitHub Secrets needed:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**Everything else is automated** by the CI/CD pipeline.

## 🌐 Access Your App

After deployment, check the GitHub Actions workflow output for:
```
📍 http://<PUBLIC_IP>:8000
```

Or visit the ECS console:
- `https://us-east-1.console.aws.amazon.com/ecs/home#/clusters/ml-platform-prod/services`