# AWS ECS Fargate Deployment Checklist

Use this checklist to ensure all prerequisites are met and deployment is successful.

---

## Pre-Deployment Setup

### AWS Account Preparation

- [ ] AWS Account created and active
- [ ] AWS credentials configured locally (`aws configure`)
- [ ] AWS CLI v2 installed and updated
- [ ] IAM user has necessary permissions (ECS, ECR, EC2, IAM, CloudWatch, Secrets Manager)
- [ ] Billing alerts configured in AWS Billing
- [ ] CloudTrail enabled for audit logging

### Environment Configuration

- [ ] AWS Region selected (e.g., `us-east-1`)
- [ ] MongoDB URI obtained from Atlas
- [ ] AWS Account ID noted: `_____________`
- [ ] AWS Region set: `_____________`

### GitHub Configuration

- [ ] GitHub repository has Actions enabled
- [ ] GitHub Secrets added:
  - [ ] `AWS_REGION` = (your region, e.g., `us-east-1`)
  - [ ] `AWS_ROLE_TO_ASSUME` = (OIDC role ARN)
- [ ] GitHub environment `production` created with required approvers

### Docker Setup (Local Testing)

- [ ] Docker Desktop installed
- [ ] Docker version: `docker --version`
- [ ] Dockerfile reviewed and understood
- [ ] `.dockerignore` verified

---

## Infrastructure Setup (One-Time)

### VPC & Networking

- [ ] VPC created with CIDR block (e.g., `10.0.0.0/16`)
- [ ] Public subnet 1: `_____________` (for ALB)
- [ ] Public subnet 2: `_____________` (for ALB)
- [ ] Private subnet 1: `_____________` (for ECS tasks)
- [ ] Private subnet 2: `_____________` (for ECS tasks)
- [ ] Route tables configured (IGW for public, NAT for private)
- [ ] VPC endpoint configured for Secrets Manager (optional)

### Security Groups

- [ ] ALB security group created: `_____________`
  - [ ] Inbound: 80/443 from 0.0.0.0/0
  - [ ] Outbound: All to 0.0.0.0/0
- [ ] ECS task security group created: `_____________`
  - [ ] Inbound: 8000 from ALB security group
  - [ ] Outbound: All to 0.0.0.0/0
- [ ] MongoDB security group allows outbound to Atlas

### Application Load Balancer

- [ ] ALB created: `book-rec-alb`
  - [ ] Subnets: Public subnets selected
  - [ ] Security group: ALB security group
  - [ ] Scheme: Internet-facing (public)
- [ ] Target group created: `book-rec-tg`
  - [ ] Protocol: HTTP, Port: 8000
  - [ ] Health check path: `/`
  - [ ] Health check interval: 30s
  - [ ] Healthy threshold: 2
  - [ ] Unhealthy threshold: 3
- [ ] Listener created on port 80
  - [ ] Default action: Forward to target group
- [ ] ALB DNS name noted: `_____________`

### EFS (Persistent Storage)

- [ ] EFS file system created: `_____________`
  - [ ] Encryption: Enabled (KMS)
  - [ ] Performance mode: General purpose
  - [ ] Throughput mode: Bursting
- [ ] Mount targets created for all private subnets
  - [ ] Security group allows NFS (2049/TCP)
- [ ] Access points created:
  - [ ] Artifacts access point: `_____________`
  - [ ] Logs access point: `_____________`

### ECR Repository

- [ ] ECR repository created: `book-recommendation-system`
  - [ ] Image scanning: Enabled
  - [ ] Immutable tags: Enabled
  - [ ] Encryption: KMS (optional but recommended)
- [ ] Lifecycle policy configured (keep last 10 images)
- [ ] Repository URI noted: `_____________`

### CloudWatch

- [ ] Log group created: `/ecs/book-recommendation-system`
  - [ ] Retention: 30 days
  - [ ] Encryption: KMS (optional)
- [ ] Metric filters created:
  - [ ] ErrorCount filter
  - [ ] WarningCount filter
- [ ] Alarms created:
  - [ ] High error rate alarm
  - [ ] High latency alarm
  - [ ] SNS topic configured for notifications

### Secrets Manager

- [ ] Secret created: `book-recommendation/mongodb-uri`
  - [ ] Secret value: `{"MONGODB_URI":"your-connection-string"}`
  - [ ] Encryption: KMS key configured
- [ ] Resource-based policy allows ECS task role access
- [ ] Secret ARN noted: `_____________`

### IAM Roles & Policies

#### Task Execution Role

- [ ] Role created: `ecsTaskExecutionRole-BookRecommendationSystem`
  - [ ] Trust policy: Added (ecs-tasks.amazonaws.com)
  - [ ] Policies attached:
    - [ ] Custom execution policy (.aws/iam-task-execution-role.json)
    - [ ] AmazonECSTaskExecutionRolePolicy (AWS managed)
- [ ] Role ARN: `_____________`
- [ ] Verify permissions:
  - [ ] ECR GetAuthorizationToken
  - [ ] CloudWatch Logs
  - [ ] Secrets Manager GetSecretValue
  - [ ] KMS Decrypt
  - [ ] EFS ClientMount

#### Task Role

- [ ] Role created: `ecsTaskRole-BookRecommendationSystem`
  - [ ] Trust policy: Added (ecs-tasks.amazonaws.com)
  - [ ] Policy attached: Custom task policy (.aws/iam-task-role.json)
- [ ] Role ARN: `_____________`
- [ ] Verify permissions:
  - [ ] Secrets Manager GetSecretValue
  - [ ] CloudWatch PutMetricData
  - [ ] S3 (for MLFlow if applicable)
  - [ ] EFS ClientWrite

### ECS Cluster

- [ ] Cluster created: `ml-platform-prod`
  - [ ] Launch type: Fargate
  - [ ] Container Insights: Enabled
  - [ ] Capacity providers: FARGATE + FARGATE_SPOT
- [ ] VPC configuration:
  - [ ] VPC selected
  - [ ] Subnets: Private subnets selected
  - [ ] Security group: ECS task security group
- [ ] CloudWatch container logs: Enabled

---

## Container Image Preparation

### Local Build & Test

- [ ] Dockerfile reviewed for best practices
- [ ] Build command runs without errors:
  ```bash
  docker build -t book-recommendation-system:test .
  ```
- [ ] Image size reasonable (~480MB)
- [ ] Image runs locally without errors:
  ```bash
  docker run -it -p 8000:8000 -e MONGODB_URI="..." book-recommendation-system:test
  ```
- [ ] Health check responds: `curl http://localhost:8000/`
- [ ] Endpoints tested:
  - [ ] GET /: Returns HTML (200)
  - [ ] GET /suggestions?q=Harry: Returns suggestions
  - [ ] POST /recommend: Returns recommendations
- [ ] Container logs appear in console
- [ ] Container stops gracefully (Ctrl+C → 30s shutdown)

### Push to ECR

- [ ] Logged in to ECR:
  ```bash
  aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <ecr-uri>
  ```
- [ ] Image tagged for ECR:
  ```bash
  docker tag book-recommendation-system:test <ecr-uri>/book-recommendation-system:v1.0.0
  docker tag book-recommendation-system:test <ecr-uri>/book-recommendation-system:latest
  ```
- [ ] Image pushed to ECR:
  ```bash
  docker push <ecr-uri>/book-recommendation-system:v1.0.0
  docker push <ecr-uri>/book-recommendation-system:latest
  ```
- [ ] Verify in ECR console
- [ ] Image scanning completed (no critical vulnerabilities)
- [ ] ECR image URI noted: `_____________`

---

## ECS Deployment

### Task Definition

- [ ] Task definition file updated with placeholders:
  - [ ] `${AWS_REGION}` → your region
  - [ ] `${AWS_ACCOUNT_ID}` → your account ID
  - [ ] `${ECR_REGISTRY}` → ECR URI
  - [ ] `${ECR_REPOSITORY}` → `book-recommendation-system`
  - [ ] `${IMAGE_TAG}` → image tag (e.g., `v1.0.0`)
  - [ ] `${EFS_FILESYSTEM_ID}` → EFS ID
  - [ ] `${ARTIFACTS_ACCESS_POINT_ID}` → artifacts AP ID
  - [ ] `${LOGS_ACCESS_POINT_ID}` → logs AP ID
  - [ ] Task execution role ARN
  - [ ] Task role ARN
- [ ] Task definition registered:
  ```bash
  aws ecs register-task-definition --cli-input-json file://.aws/ecs-task-definition.json
  ```
- [ ] Task definition appears in ECS console
- [ ] Task definition revision noted: `_____________`

### Service Creation

- [ ] Service configuration file updated with:
  - [ ] Cluster name: `ml-platform-prod`
  - [ ] Task definition: `book-recommendation-system:1`
  - [ ] Subnets: Private subnets
  - [ ] Security groups: ECS task security group
  - [ ] Target group ARN: `book-rec-tg`
- [ ] Service created:
  ```bash
  aws ecs create-service --cli-input-json file://.aws/ecs-service-config.json
  ```
- [ ] Service appears in ECS console
- [ ] Initial task deployment started
- [ ] Wait for service stabilization:
  ```bash
  aws ecs wait services-stable --cluster ml-platform-prod --services book-recommendation-system
  ```

---

## Post-Deployment Verification

### Task Startup

- [ ] Tasks created and starting
- [ ] Task count: Desired = 2, Running = 2, Pending = 0
- [ ] Tasks have assigned IP addresses
- [ ] Task status: RUNNING
- [ ] No recent task stops or restarts

### Health Checks

- [ ] CloudWatch logs show startup messages
- [ ] ALB target group shows: Healthy (2/2 targets)
- [ ] Load balancer health check responses: 200 OK
- [ ] Container health status: HEALTHY
- [ ] No health check timeouts or failures

### Application Functionality

- [ ] Test via ALB:
  ```bash
  curl http://<ALB-DNS>/
  ```
  - Response: HTML with model status (200)
  
- [ ] Test suggestions endpoint:
  ```bash
  curl "http://<ALB-DNS>/suggestions?q=Harry"
  ```
  - Response: JSON array with suggestions
  
- [ ] Test recommendation endpoint:
  ```bash
  curl -X POST http://<ALB-DNS>/recommend -F "book_name=Harry Potter"
  ```
  - Response: JSON with recommendations

### CloudWatch Monitoring

- [ ] Log group created with entries
- [ ] Recent logs appear in CloudWatch console
- [ ] No ERROR messages in logs
- [ ] Metrics available:
  - [ ] CPUUtilization
  - [ ] MemoryUtilization
  - [ ] TaskCount (running)
- [ ] Container Insights dashboard shows healthy metrics

### Auto-Scaling

- [ ] Auto-scaling target registered
- [ ] Scaling policies created:
  - [ ] CPU-based (target: 70%)
  - [ ] Memory-based (target: 80%)
  - [ ] Request-based (target: 1000 req/task)
- [ ] Can scale to 10 tasks maximum
- [ ] Can scale to 2 tasks minimum

---

## Security Verification

### Network Security

- [ ] Tasks in private subnets (no public IPs)
- [ ] Security groups restrict traffic correctly
- [ ] Only ALB can reach tasks on port 8000
- [ ] Tasks can reach MongoDB (outbound allowed)
- [ ] DNS works (can resolve names)

### Container Security

- [ ] Running as non-root user (`appuser`)
- [ ] No hardcoded secrets in image or logs
- [ ] No credentials in environment variables (except from Secrets Manager)
- [ ] Image scanning shows no critical vulnerabilities

### Secrets Management

- [ ] MongoDB URI stored in Secrets Manager
- [ ] Secret encrypted with KMS
- [ ] Task role can read secret
- [ ] Environment variable injected correctly
- [ ] Connection to MongoDB successful
- [ ] Secret not visible in logs

### IAM Verification

- [ ] Task execution role has only needed permissions
- [ ] Task role has only needed permissions
- [ ] Public IP association denied (in task role)
- [ ] No wildcard permissions (except where necessary)
- [ ] CloudTrail logs available

---

## Monitoring & Alerting Setup

### CloudWatch Alarms

- [ ] High error rate alarm created and tested
- [ ] High latency alarm created and tested
- [ ] SNS topic configured for notifications
- [ ] Alarm emails received (test notification sent)

### Log Insights Queries

- [ ] Test error query:
  ```
  fields @timestamp, @message | filter @message like /ERROR/
  ```
- [ ] Test latency query (if logging latency)
- [ ] Can identify issues from logs

### Container Insights

- [ ] Container Insights dashboard accessible
- [ ] Cluster-level metrics visible
- [ ] Service-level metrics visible
- [ ] Task-level metrics visible
- [ ] No metric anomalies detected

---

## GitHub Actions CI/CD

### Workflow Configuration

- [ ] Workflow file (.github/workflows/main.yml) reviewed
- [ ] Environment variables set correctly:
  - [ ] `AWS_REGION`
  - [ ] `ECR_REPOSITORY`
  - [ ] `ECS_SERVICE`
  - [ ] `ECS_CLUSTER`
  - [ ] `CONTAINER_NAME`

### OIDC Configuration (No Secrets)

- [ ] OIDC provider configured in GitHub
- [ ] OIDC role created in AWS
- [ ] Trust relationship: GitHub Actions → AWS
- [ ] No long-term AWS credentials in GitHub Secrets

### Workflow Execution

- [ ] Test push to `main` branch (e.g., update README)
- [ ] Workflow starts automatically
- [ ] Build step completes without errors
- [ ] Image pushed to ECR
- [ ] Task definition registered
- [ ] Service updated
- [ ] Deployment completes successfully
- [ ] Workflow appears in "Actions" tab
- [ ] Can view logs and artifacts

---

## Load Testing & Performance

### Local Load Test

- [ ] Use Apache Bench or similar tool:
  ```bash
  ab -n 1000 -c 10 http://<ALB-DNS>/
  ```
- [ ] Response times reasonable (<500ms)
- [ ] No errors under load
- [ ] No task restarts during test

### Scaling Test

- [ ] Generate load to trigger auto-scaling:
  ```bash
  while true; do curl http://<ALB-DNS>/ & done
  ```
- [ ] Monitor task count in ECS console
- [ ] Verify new tasks start within 2-3 minutes
- [ ] Verify load balances across tasks
- [ ] Verify scale-down after load stops

---

## Troubleshooting Verification

### Service Not Starting

- [ ] Check error logs:
  ```bash
  aws logs tail /ecs/book-recommendation-system --follow
  ```
- [ ] Check task definition is correct
- [ ] Verify image exists in ECR
- [ ] Verify IAM roles have correct permissions
- [ ] Verify MongoDB URI in Secrets Manager

### Health Checks Failing

- [ ] Verify endpoint responds:
  ```bash
  curl http://<task-ip>:8000/
  ```
- [ ] Check security group allows port 8000
- [ ] Verify health check path is `/`
- [ ] Check logs for startup errors
- [ ] Increase health check start-period if needed

### MongoDB Connection Issues

- [ ] Test MongoDB URI locally
- [ ] Verify network connectivity (outbound allowed)
- [ ] Check Secrets Manager has correct URI
- [ ] Verify MongoDB Atlas IP whitelist includes ECS tasks
- [ ] Check application logs for connection errors

---

## Final Production Checklist

- [ ] All infrastructure components operational
- [ ] All security measures in place
- [ ] All monitoring and alerting active
- [ ] CI/CD pipeline tested and working
- [ ] Application responds correctly to requests
- [ ] No errors in CloudWatch logs
- [ ] Auto-scaling policies active
- [ ] Alarms configured and tested
- [ ] Team notified of deployment
- [ ] Documentation updated
- [ ] Rollback plan understood

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| DevOps Engineer | __________ | __________ | __________ |
| Platform Lead | __________ | __________ | __________ |
| Security Lead | __________ | __________ | __________ |

---

## Important Notes

- **Estimated Setup Time**: 2-3 hours for first-time deployment
- **Cost**: ~$100/month for 2-task service with ALB
- **Support**: See DEPLOYMENT_GUIDE.md for detailed instructions
- **Rollback**: If deployment fails, automatic rollback occurs
- **Monitoring**: Check CloudWatch hourly for first 24 hours

---

## Deployment Date: ___________________

**Status**: ☐ In Progress  ☐ Completed  ☐ Failed

**Notes**:
```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

---

**Last Updated**: June 2, 2024
