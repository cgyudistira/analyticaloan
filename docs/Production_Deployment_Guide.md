# AnalyticaLoan Production Deployment Guide

## Prerequisites

### Required Tools
- Docker 24.0+
- Kubernetes 1.28+ (kubectl configured)
- Helm 3.12+
- Poetry 1.7+
- PostgreSQL 15+
- Redis 7+

### Cloud Accounts
- ☐ Google Cloud Platform (GCP) / AWS / Azure
- ☐ GitHub Container Registry access
- ☐ Domain name configured
- ☐ SSL certificates (Let's Encrypt or purchased)

---

## Phase 1: Infrastructure Setup

### 1.1 Kubernetes Cluster

**GKE (Google Kubernetes Engine):**
```bash
# Create cluster
gcloud container clusters create analyticaloan-prod \
    --zone us-central1-a \
    --num-nodes 3 \
    --machine-type n2-standard-4 \
    --enable-autoscaling \
    --min-nodes 3 \
    --max-nodes 10 \
    --enable-autorepair \
    --enable-autoupgrade

# Get credentials
gcloud container clusters get-credentials analyticaloan-prod --zone us-central1-a
```

**AWS EKS:**
```bash
eksctl create cluster \
    --name analyticaloan-prod \
    --region us-east-1 \
    --nodegroup-name standard-workers \
    --node-type t3.xlarge \
    --nodes 3 \
    --nodes-min 3 \
    --nodes-max 10 \
    --managed
```

### 1.2 Create Namespaces

```bash
kubectl create namespace analyticaloan-production
kubectl create namespace monitoring
kubectl create namespace cert-manager
```

### 1.3 Install Cert-Manager (SSL)

```bash
# Add Helm repo
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --version v1.13.0 \
    --set installCRDs=true
```

---

## Phase 2: Database Setup

### 2.1 PostgreSQL (Cloud SQL / RDS)

**Google Cloud SQL:**
```bash
gcloud sql instances create analyticaloan-db \
    --database-version=POSTGRES_15 \
    --tier=db-custom-4-16384 \
    --region=us-central1 \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --retained-backups-count=30
```

**Create Database:**
```bash
# Create database
gcloud sql databases create analyticaloan \
    --instance=analyticaloan-db

# Create user
gcloud sql users create analyticaloan_user \
    --instance=analyticaloan-db \
    --password=<SECURE_PASSWORD>
```

### 2.2 Run Migrations

```bash
# Set database connection
export DATABASE_URL="postgresql://analyticaloan_user:<PASSWORD>@<DB_HOST>:5432/analyticaloan"

# Run Alembic migrations
poetry run alembic upgrade head

# Seed initial data
poetry run python scripts/seed_data.py
```

### 2.3 Redis (Cloud Memorystore / ElastiCache)

**Google Memorystore:**
```bash
gcloud redis instances create analyticaloan-cache \
    --size=5 \
    --region=us-central1 \
    --redis-version=redis_7_0
```

---

## Phase 3: Secrets Management

### 3.1 Create Kubernetes Secrets

```bash
# Database credentials
kubectl create secret generic db-credentials \
    --from-literal=DATABASE_URL='postgresql://user:pass@host:5432/db' \
    --namespace analyticaloan-production

# Gemini API Key
kubectl create secret generic gemini-api-key \
    --from-literal=GEMINI_API_KEY='your-api-key' \
    --namespace analyticaloan-production

# Encryption key
kubectl create secret generic encryption-key \
    --from-literal=ENCRYPTION_KEY='your-fernet-key' \
    --namespace analyticaloan-production

# JWT secret
kubectl create secret generic jwt-secret \
    --from-literal=JWT_SECRET_KEY='your-jwt-secret' \
    --namespace analyticaloan-production

# GitHub Container Registry
kubectl create secret docker-registry ghcr-secret \
    --docker-server=ghcr.io \
    --docker-username=<GITHUB_USERNAME> \
    --docker-password=<GITHUB_TOKEN> \
    --namespace analyticaloan-production
```

---

## Phase 4: Deploy Services

### 4.1 Deploy Infrastructure Services

```bash
# Deploy PostgreSQL connection pooler (PgBouncer)
kubectl apply -f infrastructure/k8s/production/pgbouncer.yaml

# Deploy Redis
kubectl apply -f infrastructure/k8s/production/redis.yaml

# Deploy Weaviate (Vector DB)
kubectl apply -f infrastructure/k8s/production/weaviate.yaml

# Deploy RabbitMQ
kubectl apply -f infrastructure/k8s/production/rabbitmq.yaml
```

### 4.2 Deploy Application Services

```bash
# Deploy all services
kubectl apply -f infrastructure/k8s/production/

# Verify deployments
kubectl get deployments -n analyticaloan-production
kubectl get pods -n analyticaloan-production
kubectl get services -n analyticaloan-production
```

### 4.3 Configure Ingress

```bash
# Deploy ingress controller (NGINX)
helm install nginx-ingress ingress-nginx/ingress-nginx \
    --namespace analyticaloan-production

# Apply ingress rules
kubectl apply -f infrastructure/k8s/production/ingress.yaml
```

---

## Phase 5: Monitoring & Observability

### 5.1 Deploy Prometheus

```bash
# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --values infrastructure/monitoring/prometheus/values.yaml
```

### 5.2 Deploy Grafana Dashboards

```bash
# Import dashboards
kubectl apply -f infrastructure/monitoring/grafana/dashboards/
```

### 5.3 Deploy Jaeger (Tracing)

```bash
# Install Jaeger operator
kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.50.0/jaeger-operator.yaml

# Deploy Jaeger instance
kubectl apply -f infrastructure/monitoring/jaeger/jaeger.yaml
```

---

## Phase 6: CI/CD Setup

### 6.1 GitHub Actions Secrets

Go to GitHub Repository Settings → Secrets and add:

```
KUBE_CONFIG_STAGING: <base64-encoded-kubeconfig>
KUBE_CONFIG_PRODUCTION: <base64-encoded-kubeconfig>
SLACK_WEBHOOK: <slack-webhook-url>
GEMINI_API_KEY: <your-gemini-key>
```

### 6.2 Trigger Deployment

```bash
# Push to main branch triggers CI/CD
git push origin main

# Monitor deployment
kubectl rollout status deployment/api-gateway -n analyticaloan-production
```

---

## Phase 7: Post-Deployment Verification

### 7.1 Health Checks

```bash
# Check all pods are running
kubectl get pods -n analyticaloan-production

# Check service health endpoints
curl https://analyticaloan.com/health
curl https://analyticaloan.com/api/v1/auth/health
curl https://analyticaloan.com/api/v1/documents/health
```

### 7.2 Smoke Tests

```bash
# Run smoke test suite
poetry run pytest tests/smoke -v

# Or manual API tests
curl -X POST https://analyticaloan.com/api/v1/auth/login \
    -d "username=admin@analyticaloan.com&password=admin123"
```

### 7.3 Load Testing

```bash
# Install k6
brew install k6  # macOS
# or download from https://k6.io/

# Run load test
k6 run tests/performance/load-test.js
```

---

## Phase 8: Backup & Disaster Recovery

### 8.1 Database Backups

```bash
# Automated daily backups (already configured in Cloud SQL)
# Manual backup:
gcloud sql backups create --instance=analyticaloan-db

# Restore from backup:
gcloud sql backups restore <BACKUP_ID> \
    --backup-instance=analyticaloan-db \
    --backup-instance=analyticaloan-db
```

### 8.2 Kubernetes Backup (Velero)

```bash
# Install Velero
velero install \
    --provider gcp \
    --plugins velero/velero-plugin-for-gcp:v1.8.0 \
    --bucket analyticaloan-backups \
    --secret-file ./credentials-velero

# Create backup schedule
velero schedule create daily-backup \
    --schedule="0 2 * * *" \
    --include-namespaces analyticaloan-production
```

---

## Phase 9: Monitoring Alerts

### 9.1 Configure Alertmanager

```yaml
# infrastructure/monitoring/prometheus/alertmanager.yml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: '<SLACK_WEBHOOK>'
        channel: '#alerts'
        title: 'AnalyticaLoan Alert'

route:
  receiver: 'slack'
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
```

### 9.2 Key Alerts

- High error rate (>5%)
- High latency (p95 > 1s)
- Pod crash loops
- Database connection failures
- Out of memory errors
- Disk space > 80%

---

## Troubleshooting

### Common Issues

**1. Pods CrashLooping**
```bash
kubectl logs <pod-name> -n analyticaloan-production
kubectl describe pod <pod-name> -n analyticaloan-production
```

**2. Database Connection Issues**
```bash
# Test from pod
kubectl exec -it <pod-name> -n analyticaloan-production -- sh
nc -zv <DB_HOST> 5432
```

**3. High CPU/Memory**
```bash
kubectl top pods -n analyticaloan-production
kubectl top nodes
```

---

## Production Checklist

- [ ] SSL certificates configured
- [ ] Database backups automated
- [ ] Monitoring alerts configured
- [ ] Load balancer healthy
- [ ] Auto-scaling tested
- [ ] Disaster recovery plan tested
- [ ] Security scan passed
- [ ] POJK compliance verified
- [ ] Performance benchmarks met
- [ ] Documentation updated

---

## Rollback Procedure

```bash
# Rollback to previous version
kubectl rollout undo deployment/api-gateway -n analyticaloan-production

# Rollback to specific revision
kubectl rollout undo deployment/api-gateway \
    --to-revision=2 \
    -n analyticaloan-production

# Check rollout history
kubectl rollout history deployment/api-gateway -n analyticaloan-production
```

---

## Support Contacts

- **DevOps Team:** devops@analyticaloan.com
- **On-Call:** +62-xxx-xxx-xxxx
- **Slack:** #analyticaloan-production
- **PagerDuty:** https://analyticaloan.pagerduty.com

---

**Last Updated:** 2024-01-15  
**Version:** 1.0  
**Maintained by:** DevOps Team
