# GitHub Actions CI/CD Workflows

This folder contains automated CI/CD workflows for the Book Recommendation System.

## 📁 Workflows

### 1. `ci.yml` - Continuous Integration
**Triggers**: 
- Push to `main` or `production` branches
- Pull requests to `main` or `production`

**What it does**:
- ✅ Runs all tests (`pytest`)
- 🔒 Security scanning with Trivy
- 🐳 Validates Docker build
- 🐍 Checks Python application startup

### 2. `deploy-ecs.yml` - Continuous Deployment
**Triggers**:
- After CI workflow completes successfully
- Manual workflow dispatch
- Direct push to `main`/`production` (with path filters)

**What it does**:
- 🏗️ Builds Docker image
- 📦 Pushes to AWS ECR
- 🚀 Deploys to ECS Fargate
- 🔄 Updates or creates ECS service
- 📊 Provides deployment summary

## 🔧 Setup Requirements

### AWS Secrets (Required)
Add these secrets in your GitHub repository settings:

```
AWS_ACCESS_KEY_ID     # Your AWS access key
AWS_SECRET_ACCESS_KEY # Your AWS secret key
```

### AWS Resources (Auto-created by workflow)
The deployment workflow automatically creates:
- ECR Repository: `book-recommendation-system`
- ECS Cluster: `ml-platform-prod`
- ECS Service: `book-recommendation-system` 
- IAM Roles: `ecsTaskExecutionRole-BookRecommendation`, `ecsTaskRole-BookRecommendation`
- Security Group: `book-recommendation-sg`
- Task Definition with proper configuration

## 🚀 Deployment Process

### Automatic (Recommended)
1. **Push code to `main` branch**
2. **CI workflow runs** (tests, security scan)
3. **If CI passes**, CD workflow automatically deploys to ECS
4. **Access your app** at the ECS task public IP on port 8000

### Manual Deployment
1. Go to **Actions** tab in GitHub
2. Select **"CI/CD to ECS Fargate - Book Recommendation System"**
3. Click **"Run workflow"**
4. Choose branch and click **"Run workflow"**

## 📊 Workflow Features

### Smart Deployment
- **Path-based triggers**: Only deploys when relevant files change
- **Dependency checking**: CD only runs after successful CI
- **Resource auto-creation**: Sets up AWS infrastructure automatically
- **Service management**: Updates existing services or creates new ones

### Production Ready
- **Health checks**: Container health monitoring
- **Logging**: CloudWatch integration
- **Security**: Non-root container, security scanning
- **Scalability**: Ready for horizontal scaling
- **Monitoring**: Task and service status reporting

### Error Handling
- **Rollback capability**: ECS deployment circuit breaker enabled
- **Wait for stability**: Ensures deployment completion
- **Detailed logging**: Clear error messages and success indicators
- **Network automation**: Auto-configures VPC, subnets, security groups

## 🔍 Monitoring Deployment

### GitHub Actions
- Check the **Actions** tab for workflow status
- View detailed logs for each step
- See deployment summary with public IPs

### AWS Console
The workflow provides direct links to:
- ECS Service: `https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/ml-platform-prod/services`
- CloudWatch Logs: `/ecs/book-recommendation-system`
- ECR Repository: `book-recommendation-system`

### Application Access
After successful deployment:
```bash
# The workflow outputs will show:
📍 http://<PUBLIC_IP>:8000
```

## 🛠️ Customization

### Environment Variables
Modify in `deploy-ecs.yml`:
```yaml
env:
  AWS_REGION: us-east-1                    # Change AWS region
  ECR_REPOSITORY: book-recommendation-system # Change ECR repo name
  ECS_SERVICE: book-recommendation-system   # Change service name
  ECS_CLUSTER: ml-platform-prod            # Change cluster name
```

### Resource Configuration
Adjust CPU/Memory in the task definition section:
```json
"cpu": "1024",        # 1 vCPU
"memory": "2048",     # 2 GB RAM
```

### Scaling
Change desired task count:
```bash
--desired-count 2     # Number of running tasks
```

## 🚨 Troubleshooting

### Common Issues
1. **AWS Permissions**: Ensure secrets have ECS, ECR, IAM, EC2 permissions
2. **Docker Build Fails**: Check Dockerfile and dependencies
3. **Service Won't Start**: Check CloudWatch logs for application errors
4. **Network Issues**: Verify security group allows port 8000

### Debug Commands
```bash
# Check service status
aws ecs describe-services --cluster ml-platform-prod --services book-recommendation-system

# View logs
aws logs tail /ecs/book-recommendation-system --follow

# List tasks
aws ecs list-tasks --cluster ml-platform-prod --service-name book-recommendation-system
```

This CI/CD setup provides a complete, production-ready deployment pipeline for the Book Recommendation System on AWS ECS Fargate.