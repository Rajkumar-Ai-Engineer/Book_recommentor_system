# Book Recommendation System - AWS ECS Fargate Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Book Recommendation System to AWS ECS Fargate with production-grade configurations, security best practices, and monitoring setup.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [Infrastructure Setup](#infrastructure-setup)
4. [IAM Configuration](#iam-configuration)
5. [Docker Image Preparation](#docker-image-preparation)
6. [ECS Deployment](#ecs-deployment)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Auto-Scaling](#auto-scaling)
9. [Cost Optimization](#cost-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- AWS CLI v2 (configured with credentials)
- Docker CLI (for local image testing)
- git (for repository management)
- jq (for JSON parsing)

### AWS Permissions Required
- ECR (Elastic Container Registry)
- ECS (Elastic Container Service)
- EC2 (for networking: VPC, subnets, security groups)
- IAM (for role management)
- CloudWatch (for logging and monitoring)
- Secrets Manager (for sensitive data)
- EFS (Elastic File System, for persistent volumes)
- ALB (Application Load Balancer)

### Environment Variables
```bash
export AWS_REGION="us-east-1"                    # Change to your region
export AWS_ACCOUNT_ID="123456789012"             # Your AWS Account ID
export ECR_REPOSITORY="book-recommendation-system"
export IMAGE_TAG="latest"
export MONGODB_URI="<Your MongoDB Connection String>"
export MLFLOW_BUCKET="book-recommendation-mlflow"
```

---

## AWS Account Setup

### 1. Create ECR Repository
```bash
aws ecr create-repository \
  --repository-name ${ECR_REPOSITORY} \
  --region ${AWS_REGION} \
  --encryption-configuration encryptionType=KMS \
  --image-tag-mutability IMMUTABLE \
  --image-scanning-configuration scanOnPush=true

# Enable lifecycle policies to clean up old images
aws ecr put-lifecycle-policy \
  --repository-name ${ECR_REPOSITORY} \
  --lifecycle-policy-text '{
    "rules": [{
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "tagged",
        "tagPrefixList": ["v"],
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {"type": "expire"}
    }]
  }' \
  --region ${AWS_REGION}
```

### 2. Store Secrets in AWS Secrets Manager
```bash
# Create secret for MongoDB URI
aws secretsmanager create-secret \
  --name book-recommendation/mongodb-uri \
  --description "MongoDB connection string for Book Recommendation System" \
  --secret-string "{\"MONGODB_URI\":\"${MONGODB_URI}\"}" \
  --region ${AWS_REGION} \
  --add-replica-regions RegionCode=${AWS_REGION}

# Verify secret creation
aws secretsmanager describe-secret \
  --secret-id book-recommendation/mongodb-uri \
  --region ${AWS_REGION}
```

### 3. Create CloudWatch Log Group
```bash
aws logs create-log-group \
  --log-group-name /ecs/book-recommendation-system \
  --region ${AWS_REGION}

aws logs put-retention-policy \
  --log-group-name /ecs/book-recommendation-system \
  --retention-in-days 30 \
  --region ${AWS_REGION}

# Add encryption (optional but recommended)
aws logs associate-kms-key \
  --log-group-name /ecs/book-recommendation-system \
  --kms-key-id arn:aws:kms:${AWS_REGION}:${AWS_ACCOUNT_ID}:key/key-id \
  --region ${AWS_REGION}
```

---

## Infrastructure Setup

### 1. VPC and Networking
**Prerequisites**: Existing VPC with public/private subnets

```bash
# Get existing VPC and subnets
export VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --region ${AWS_REGION} \
  --query 'Vpcs[0].VpcId' \
  --output text)

# Get 2 subnets (for high availability)
export SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --region ${AWS_REGION} \
  --query 'Subnets[0:2].SubnetId' \
  --output text)

echo "VPC: ${VPC_ID}"
echo "Subnets: ${SUBNET_IDS}"
```

### 2. Security Groups
```bash
# Create security group for ECS tasks
aws ec2 create-security-group \
  --group-name book-rec-ecs-sg \
  --description "Security group for Book Recommendation ECS tasks" \
  --vpc-id ${VPC_ID} \
  --region ${AWS_REGION}

export SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=book-rec-ecs-sg" "Name=vpc-id,Values=${VPC_ID}" \
  --region ${AWS_REGION} \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

# Allow inbound on port 8000 from ALB
aws ec2 authorize-security-group-ingress \
  --group-id ${SG_ID} \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0 \
  --region ${AWS_REGION}

# Allow outbound to internet (for MongoDB, MLFlow, etc.)
aws ec2 authorize-security-group-egress \
  --group-id ${SG_ID} \
  --protocol -1 \
  --cidr 0.0.0.0/0 \
  --region ${AWS_REGION}
```

### 3. Application Load Balancer
```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name book-rec-alb \
  --subnets ${SUBNET_IDS} \
  --security-groups ${SG_ID} \
  --scheme internet-facing \
  --type application \
  --region ${AWS_REGION}

export ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names book-rec-alb \
  --region ${AWS_REGION} \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

export ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names book-rec-alb \
  --region ${AWS_REGION} \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

# Create target group
aws elbv2 create-target-group \
  --name book-rec-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id ${VPC_ID} \
  --target-type ip \
  --health-check-protocol HTTP \
  --health-check-path / \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 3 \
  --unhealthy-threshold-count 3 \
  --matcher HttpCode=200 \
  --region ${AWS_REGION}

export TG_ARN=$(aws elbv2 describe-target-groups \
  --names book-rec-tg \
  --region ${AWS_REGION} \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn ${ALB_ARN} \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=${TG_ARN} \
  --region ${AWS_REGION}

echo "ALB created at: http://${ALB_DNS}"
```

### 4. EFS for Persistent Volumes (Model Artifacts & Logs)
```bash
# Create EFS file system
aws efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --encrypted \
  --kms-key-id arn:aws:kms:${AWS_REGION}:${AWS_ACCOUNT_ID}:key/key-id \
  --tags Key=Name,Value=book-recommendation-efs Key=Application,Value=BookRecommendationSystem \
  --region ${AWS_REGION}

export EFS_ID=$(aws efs describe-file-systems \
  --query 'FileSystems[0].FileSystemId' \
  --output text \
  --region ${AWS_REGION})

# Create mount targets for each subnet
for SUBNET in ${SUBNET_IDS}; do
  aws efs create-mount-target \
    --file-system-id ${EFS_ID} \
    --subnet-id ${SUBNET} \
    --security-groups ${SG_ID} \
    --region ${AWS_REGION}
done

# Create access points for different paths
aws efs create-access-point \
  --file-system-id ${EFS_ID} \
  --posix-user Uid=1000,Gid=1000 \
  --root-directory Path="/artifacts",CreationInfo=OwnerUid=1000,OwnerGid=1000,Permissions=755 \
  --region ${AWS_REGION}

export ARTIFACTS_AP=$(aws efs describe-access-points \
  --file-system-id ${EFS_ID} \
  --query 'AccessPoints[0].AccessPointId' \
  --output text \
  --region ${AWS_REGION})

aws efs create-access-point \
  --file-system-id ${EFS_ID} \
  --posix-user Uid=1000,Gid=1000 \
  --root-directory Path="/logs",CreationInfo=OwnerUid=1000,OwnerGid=1000,Permissions=755 \
  --region ${AWS_REGION}

export LOGS_AP=$(aws efs describe-access-points \
  --file-system-id ${EFS_ID} \
  --query 'AccessPoints[1].AccessPointId' \
  --output text \
  --region ${AWS_REGION})

echo "EFS: ${EFS_ID}"
echo "Artifacts Access Point: ${ARTIFACTS_AP}"
echo "Logs Access Point: ${LOGS_AP}"
```

---

## IAM Configuration

### 1. Create ECS Task Execution Role
This role allows ECS to pull Docker images, read secrets, and write logs.

```bash
# Create the role
aws iam create-role \
  --role-name ecsTaskExecutionRole-BookRecommendationSystem \
  --assume-role-policy-document file://.aws/iam-trust-policy.json \
  --region ${AWS_REGION}

# Attach the execution policy
aws iam put-role-policy \
  --role-name ecsTaskExecutionRole-BookRecommendationSystem \
  --policy-name ecsTaskExecutionPolicy \
  --policy-document file://.aws/iam-task-execution-role.json \
  --region ${AWS_REGION}

# Attach standard policy for ECR access
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole-BookRecommendationSystem \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  --region ${AWS_REGION}
```

### 2. Create ECS Task Role
This role defines what the application itself can do (access MongoDB, write metrics, etc.).

```bash
# Create the role
aws iam create-role \
  --role-name ecsTaskRole-BookRecommendationSystem \
  --assume-role-policy-document file://.aws/iam-trust-policy.json \
  --region ${AWS_REGION}

# Attach the task policy
aws iam put-role-policy \
  --role-name ecsTaskRole-BookRecommendationSystem \
  --policy-name ecsTaskPolicy \
  --policy-document file://.aws/iam-task-role.json \
  --region ${AWS_REGION}
```

### 3. Verify Role ARNs
```bash
export TASK_EXECUTION_ROLE_ARN=$(aws iam get-role \
  --role-name ecsTaskExecutionRole-BookRecommendationSystem \
  --query 'Role.Arn' \
  --output text)

export TASK_ROLE_ARN=$(aws iam get-role \
  --role-name ecsTaskRole-BookRecommendationSystem \
  --query 'Role.Arn' \
  --output text)

echo "Task Execution Role: ${TASK_EXECUTION_ROLE_ARN}"
echo "Task Role: ${TASK_ROLE_ARN}"
```

---

## Docker Image Preparation

### 1. Build Docker Image Locally
```bash
# From repository root
docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} .

# Verify image works locally (optional)
docker run -it \
  -p 8000:8000 \
  -e MONGODB_URI="${MONGODB_URI}" \
  ${ECR_REPOSITORY}:${IMAGE_TAG}

# Test health check
curl http://localhost:8000/
```

### 2. Push to ECR
```bash
# Get ECR login token
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Tag image for ECR
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}

docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

# Verify upload
aws ecr describe-images \
  --repository-name ${ECR_REPOSITORY} \
  --region ${AWS_REGION}
```

### Image Optimization Details
- **Base Image**: `python:3.12-slim` (minimal dependencies, ~160MB)
- **Multi-stage Build**: Separates build-time from runtime dependencies
  - Builder stage: Compiles all dependencies (850MB)
  - Runtime stage: Only Python runtime + compiled wheels (450MB)
- **Non-root User**: Runs as `appuser:appuser` (UID/GID 1000)
- **Final Size**: ~480MB (uncompressed), ~150MB (compressed in ECR)

---

## ECS Deployment

### 1. Create ECS Cluster
```bash
aws ecs create-cluster \
  --cluster-name ml-platform-prod \
  --cluster-settings name=containerInsights,value=enabled \
  --region ${AWS_REGION}

# Enable Container Insights for monitoring
aws ecs put-cluster-capacity-providers \
  --cluster ml-platform-prod \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
  --region ${AWS_REGION}
```

### 2. Register Task Definition
```bash
# Update placeholders in ecs-task-definition.json
sed -e "s|\${AWS_REGION}|${AWS_REGION}|g" \
    -e "s|\${AWS_ACCOUNT_ID}|${AWS_ACCOUNT_ID}|g" \
    -e "s|\${ECR_REGISTRY}|${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com|g" \
    -e "s|\${ECR_REPOSITORY}|${ECR_REPOSITORY}|g" \
    -e "s|\${IMAGE_TAG}|${IMAGE_TAG}|g" \
    -e "s|\${EFS_FILESYSTEM_ID}|${EFS_ID}|g" \
    -e "s|\${ARTIFACTS_ACCESS_POINT_ID}|${ARTIFACTS_AP}|g" \
    -e "s|\${LOGS_ACCESS_POINT_ID}|${LOGS_AP}|g" \
    .aws/ecs-task-definition.json > /tmp/task-definition.json

# Register the task definition
aws ecs register-task-definition \
  --cli-input-json file:///tmp/task-definition.json \
  --region ${AWS_REGION}

# Verify registration
aws ecs describe-task-definition \
  --task-definition book-recommendation-system \
  --region ${AWS_REGION}
```

### 3. Create ECS Service
```bash
# Update placeholders in ecs-service-config.json
sed -e "s|subnet-xxxxxxxx|$(echo ${SUBNET_IDS} | cut -d' ' -f1)|g" \
    -e "s|subnet-yyyyyyyy|$(echo ${SUBNET_IDS} | cut -d' ' -f2)|g" \
    -e "s|sg-xxxxxxxx|${SG_ID}|g" \
    -e "s|arn:aws:elasticloadbalancing:region:account-id:targetgroup/book-rec-tg/xxxxxxxx|${TG_ARN}|g" \
    .aws/ecs-service-config.json > /tmp/service-config.json

# Create the service
aws ecs create-service \
  --cluster ml-platform-prod \
  --service-name book-recommendation-system \
  --task-definition book-recommendation-system:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[$(echo ${SUBNET_IDS} | tr ' ' ',')],securityGroups=[${SG_ID}],assignPublicIp=DISABLED}" \
  --load-balancers targetGroupArn=${TG_ARN},containerName=book-recommendation-app,containerPort=8000 \
  --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" \
  --enable-ecs-managed-tags \
  --propagate-tags TASK_DEFINITION \
  --tags key=Application,value=BookRecommendationSystem key=Environment,value=production \
  --region ${AWS_REGION}

# Wait for service to be active
aws ecs wait services-stable \
  --cluster ml-platform-prod \
  --services book-recommendation-system \
  --region ${AWS_REGION}

echo "Service is ready!"
echo "Access at: http://${ALB_DNS}"
```

---

## Monitoring and Logging

### 1. View Container Logs
```bash
# Real-time log streaming
aws logs tail /ecs/book-recommendation-system --follow --region ${AWS_REGION}

# View specific time range
aws logs filter-log-events \
  --log-group-name /ecs/book-recommendation-system \
  --start-time $(($(date +%s) - 3600))000 \
  --region ${AWS_REGION}

# Count errors in the last hour
aws logs filter-log-events \
  --log-group-name /ecs/book-recommendation-system \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s) - 3600))000 \
  --region ${AWS_REGION} | jq '.events | length'
```

### 2. Create CloudWatch Dashboards
```bash
aws cloudwatch put-dashboard \
  --dashboard-name BookRecommendationSystem \
  --dashboard-body file://.aws/cloudwatch-dashboard.json \
  --region ${AWS_REGION}
```

### 3. Set Up Alarms (via cloudwatch-config.json)
```bash
# Apply metric filters
aws logs put-metric-filter \
  --log-group-name /ecs/book-recommendation-system \
  --filter-name ErrorCount \
  --filter-pattern "[ERROR]" \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=BookRecommendationSystem,metricValue=1 \
  --region ${AWS_REGION}

# Create alarm for high error rate
aws cloudwatch put-metric-alarm \
  --alarm-name book-rec-high-errors \
  --alarm-description "Alert on high error rate" \
  --metric-name ErrorCount \
  --namespace BookRecommendationSystem \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:${AWS_REGION}:${AWS_ACCOUNT_ID}:AlertTopic \
  --region ${AWS_REGION}
```

### 4. View ECS Task Metrics
```bash
# List running tasks
aws ecs list-tasks \
  --cluster ml-platform-prod \
  --service-name book-recommendation-system \
  --region ${AWS_REGION}

# Describe tasks for details
aws ecs describe-tasks \
  --cluster ml-platform-prod \
  --tasks <task-arn> \
  --region ${AWS_REGION}

# Get CPU/Memory metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=book-recommendation-system Name=ClusterName,Value=ml-platform-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region ${AWS_REGION}
```

---

## Auto-Scaling

### 1. Create Auto-Scaling Target
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/ml-platform-prod/book-recommendation-system \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10 \
  --region ${AWS_REGION}
```

### 2. Create Scaling Policies
```bash
# Scale up on high CPU
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling-up \
  --service-namespace ecs \
  --resource-id service/ml-platform-prod/book-recommendation-system \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    TargetValue=70.0,PredefinedMetricSpecification='{PredefinedMetricType=ECSServiceAverageCPUUtilization}',ScaleOutCooldown=60,ScaleInCooldown=300 \
  --region ${AWS_REGION}

# Scale on high memory
aws application-autoscaling put-scaling-policy \
  --policy-name memory-scaling-up \
  --service-namespace ecs \
  --resource-id service/ml-platform-prod/book-recommendation-system \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    TargetValue=80.0,PredefinedMetricSpecification='{PredefinedMetricType=ECSServiceAverageMemoryUtilization}',ScaleOutCooldown=60,ScaleInCooldown=300 \
  --region ${AWS_REGION}

# Scale on ALB request count
aws application-autoscaling put-scaling-policy \
  --policy-name alb-requests-scaling \
  --service-namespace ecs \
  --resource-id service/ml-platform-prod/book-recommendation-system \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    TargetValue=1000.0,CustomizedMetricSpecification='{MetricName=RequestCountPerTarget,Namespace=AWS/ApplicationELB,Statistic=Sum,Unit=Count}',ScaleOutCooldown=60,ScaleInCooldown=300 \
  --region ${AWS_REGION}
```

---

## Cost Optimization

### 1. Use Fargate Spot Instances
```bash
# Update service to use Fargate Spot for cost savings (up to 70% cheaper)
aws ecs update-service \
  --cluster ml-platform-prod \
  --service book-recommendation-system \
  --capacity-provider-strategy capacityProvider=FARGATE,weight=1 capacityProvider=FARGATE_SPOT,weight=3 \
  --region ${AWS_REGION}
```

### 2. Right-Size Resources
- **Current Recommendation**: 1 vCPU (1024) + 2 GB RAM (2048)
- **Monitoring**: Track actual usage for 2-4 weeks
- **Adjustment**: Reduce if utilization consistently <30%, increase if >80%

### 3. Reserved Capacity
- For sustained traffic, use AWS Compute Savings Plans
- Estimated monthly cost (on-demand): $150-200
- With Savings Plan: $100-130 (30-35% discount)

---

## Troubleshooting

### Issue: Tasks Keep Restarting
```bash
# Check task logs for errors
aws logs tail /ecs/book-recommendation-system --follow

# Describe tasks to see stop codes
aws ecs describe-tasks \
  --cluster ml-platform-prod \
  --tasks <task-arn> \
  --query 'tasks[0].[lastStatus,stoppedReason,stopCode]' \
  --region ${AWS_REGION}

# Common issues:
# - stopCode=CannotPullContainerImage: Image doesn't exist in ECR
# - stopCode=OutOfMemory: Increase task memory
# - stopCode=EssentialContainerExited: Container crashed
```

### Issue: Service Can't Connect to MongoDB
```bash
# Verify secret is accessible
aws secretsmanager get-secret-value \
  --secret-id book-recommendation/mongodb-uri \
  --region ${AWS_REGION}

# Check IAM permissions for task role
aws iam list-role-policies \
  --role-name ecsTaskRole-BookRecommendationSystem \
  --region ${AWS_REGION}

# Test MongoDB connectivity from task
aws ecs execute-command \
  --cluster ml-platform-prod \
  --task <task-id> \
  --container book-recommendation-app \
  --interactive \
  --command "/bin/bash" \
  --region ${AWS_REGION}
```

### Issue: Service Unhealthy (ALB Health Check Failing)
```bash
# Verify security group allows port 8000
aws ec2 describe-security-groups \
  --group-ids ${SG_ID} \
  --region ${AWS_REGION}

# Check health check endpoint
curl http://<task-ip>:8000/

# Update target group health check if needed
aws elbv2 modify-target-group \
  --target-group-arn ${TG_ARN} \
  --health-check-protocol HTTP \
  --health-check-path / \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 2 \
  --region ${AWS_REGION}
```

### Issue: High Latency
```bash
# Check request metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum \
  --dimensions Name=TargetGroup,Value=targetgroup/book-rec-tg/xxx \
  --region ${AWS_REGION}

# Check task resource utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=book-recommendation-system \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum \
  --region ${AWS_REGION}
```

---

## Updating Deployments

### Rolling Deployment
```bash
# Rebuilds image and redeploys automatically
docker build -t ${ECR_REPOSITORY}:v1.1.0 .
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:v1.1.0

# Register new task definition
aws ecs register-task-definition \
  --cli-input-json file:///tmp/task-definition.json \
  --region ${AWS_REGION}

# Update service (old tasks drain, new tasks start)
aws ecs update-service \
  --cluster ml-platform-prod \
  --service book-recommendation-system \
  --task-definition book-recommendation-system:2 \
  --force-new-deployment \
  --region ${AWS_REGION}

# Wait for stability
aws ecs wait services-stable \
  --cluster ml-platform-prod \
  --services book-recommendation-system \
  --region ${AWS_REGION}
```

### Rollback to Previous Version
```bash
aws ecs update-service \
  --cluster ml-platform-prod \
  --service book-recommendation-system \
  --task-definition book-recommendation-system:1 \
  --force-new-deployment \
  --region ${AWS_REGION}
```

---

## Security Hardening

### 1. Enable Task IAM Roles (Already Configured)
- ✅ Task Execution Role: Pulls images, reads secrets, writes logs
- ✅ Task Role: What the application can do (access MongoDB, etc.)

### 2. Network Security
- ✅ Private subnets (no public IPs)
- ✅ Security groups restrict traffic
- ✅ Only ALB can reach tasks

### 3. Container Security
- ✅ Non-root user (appuser)
- ✅ Read-only root filesystem (can implement)
- ✅ No hardcoded secrets

### 4. Encryption
- ✅ EFS encrypted at rest
- ✅ Secrets Manager KMS encryption
- ✅ CloudWatch Logs KMS encryption
- ✅ ECR image scanning enabled

---

## Maintenance

### Regular Tasks
- **Daily**: Monitor CloudWatch logs for errors
- **Weekly**: Review cost reports in AWS Billing
- **Bi-weekly**: Check auto-scaling effectiveness
- **Monthly**: Review and update task definition with new images

### Backup Considerations
- EFS snapshots: Enable automatic snapshots (1/day)
- MongoDB backups: Handled by Atlas (automatic)
- Task definition versions: AWS keeps last 200 revisions

---

## References
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
