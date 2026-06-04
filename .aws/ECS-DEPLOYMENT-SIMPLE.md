# Simple ECS Fargate Deployment Guide

This simplified deployment approach consolidates all ECS Fargate configuration into a single file and deployment script.

## Files Overview

- `ecs-fargate-simple.json` - Consolidated configuration with task definition, service, and required resources
- `deploy-ecs.sh` - Automated deployment script that handles everything
- `Dockerfile` - Already optimized for production use

## Quick Deployment

### Manual Deployment

Follow these steps for manual deployment:

#### 1. Build and Push Image
```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create ECR repository
aws ecr create-repository --repository-name book-recommendation-system

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t book-recommendation-system .
docker tag book-recommendation-system:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/book-recommendation-system:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/book-recommendation-system:latest
```

#### 2. Create Required Resources

Replace placeholders in `ecs-fargate-simple.json`:
- `{{AWS_ACCOUNT_ID}}` - Your AWS account ID
- `{{ECR_REGISTRY}}` - Your ECR registry URI
- `{{SUBNET_1}}`, `{{SUBNET_2}}` - Your VPC subnet IDs
- `{{SECURITY_GROUP}}` - Security group ID allowing port 8000
- `{{TARGET_GROUP_ARN}}` - Optional: Load balancer target group

#### 3. Deploy to ECS

```bash
# Create cluster
aws ecs create-cluster --cluster-name ml-platform-prod

# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-fargate-simple.json

# Create service
aws ecs create-service \
  --cluster ml-platform-prod \
  --service-name book-recommendation-system \
  --task-definition book-recommendation-system \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## Configuration Details

### Resource Requirements
- **CPU**: 1024 units (1 vCPU)
- **Memory**: 2048 MB (2 GB)
- **Port**: 8000 (FastAPI application)
- **Launch Type**: Fargate (serverless)

### Key Features
- **Auto-scaling**: Ready for horizontal scaling
- **Health checks**: Built-in application health monitoring  
- **Logging**: CloudWatch logs integration
- **Security**: Non-root container execution
- **High availability**: Multi-AZ deployment support

### Environment Variables
- `PYTHONUNBUFFERED=1` - Immediate stdout/stderr output
- `LOG_LEVEL=INFO` - Application logging level
- `APP_ENV=production` - Runtime environment

## Monitoring

### Check Deployment Status
```bash
# Service status
aws ecs describe-services --cluster ml-platform-prod --services book-recommendation-system

# Task status
aws ecs list-tasks --cluster ml-platform-prod --service-name book-recommendation-system

# Logs
aws logs describe-log-groups --log-group-name-prefix "/ecs/book-recommendation-system"
```

### Access Application
1. Get task public IP from ECS console
2. Access via `http://<PUBLIC_IP>:8000`
3. Or use Application Load Balancer if configured

## Scaling

### Manual Scaling
```bash
aws ecs update-service --cluster ml-platform-prod --service book-recommendation-system --desired-count 4
```

### Auto Scaling (Optional)
Add Application Auto Scaling policies for CPU/memory-based scaling.

## Cleanup

```bash
# Delete service
aws ecs update-service --cluster ml-platform-prod --service book-recommendation-system --desired-count 0
aws ecs delete-service --cluster ml-platform-prod --service book-recommendation-system

# Delete cluster
aws ecs delete-cluster --cluster ml-platform-prod

# Delete ECR repository
aws ecr delete-repository --repository-name book-recommendation-system --force
```

## Troubleshooting

### Common Issues
1. **Task stops immediately**: Check CloudWatch logs for errors
2. **Image pull errors**: Verify ECR permissions and image URI
3. **Network issues**: Check security group and subnet configuration
4. **Health check failures**: Ensure application starts on port 8000

### Debug Commands
```bash
# View task logs
aws ecs describe-tasks --cluster ml-platform-prod --tasks <task-id>

# CloudWatch logs
aws logs get-log-events --log-group-name "/ecs/book-recommendation-system" --log-stream-name "ecs/book-recommendation-app/<task-id>"
```

This simplified approach removes the complexity of multiple configuration files while maintaining all essential ECS Fargate functionality.

**Note**: For automated deployment, use the `deploy-ecs.sh` script in this folder which handles all these steps automatically.