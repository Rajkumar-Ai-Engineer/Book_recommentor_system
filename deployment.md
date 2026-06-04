## Flow of Deployment
localrepo -> github repo -> continuous integration -> ecr -> continuous deployment -> ecs [cluster and Fargate]

# Required Environment Variables
1. AWS_SECRET_KEY
2. AWS_ACCESS_KEY_ID
3. AWS_REGION
4. AWS_ACCOUNT_ID
5. ECS_CLUSTER_NAME
6. ECR_REPO_NAME
7. ECS_SERVICE_NAME
8. ECS_TASK_FAMILY
9. ECR_REGISTRY
10. SUBNET_1
11. SUBNET_2
12. SECURITY_GROUP
13. TARGET_GROUP_ARN
14. IMAGE_TAG (default: latest)


