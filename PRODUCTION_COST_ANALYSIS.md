# Agent Deen - Production Cost Analysis

## Executive Summary

This document provides a realistic cost breakdown for deploying and maintaining Agent Deen at production scale. Costs are presented for three deployment scenarios: **Startup**, **Growth**, and **Enterprise**.

| Scenario | Monthly Users | Queries/Month | Monthly Cost |
|----------|---------------|---------------|--------------|
| **Startup** | 100-500 | 5,000 | $50 - $100 |
| **Growth** | 1,000-5,000 | 50,000 | $300 - $600 |
| **Enterprise** | 10,000+ | 500,000+ | $1,500 - $4,000+ |

*Note: Costs reduced with Supabase free tier (500MB DB + 1GB Storage)*

---

## Cost Categories Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 MONTHLY COST BREAKDOWN                       │
├─────────────────────────────────────────────────────────────┤
│  1. COMPUTE (Cloud Servers)           30-40% of total       │
│  2. LLM INFERENCE                     25-45% of total       │
│  3. VECTOR DATABASE (Pinecone)        10-20% of total       │
│  4. DATABASE & STORAGE (Supabase)     5-15% of total        │
│  5. SUPPORTING SERVICES               5-10% of total        │
│  6. OPERATIONAL OVERHEAD              5-10% of total        │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Cost Breakdown

### 1. Compute Infrastructure

#### Option A: Self-Hosted Ollama (GPU Required)

| Resource | Specification | Provider | Monthly Cost |
|----------|---------------|----------|--------------|
| **GPU Instance** | NVIDIA T4 (16GB) | AWS g4dn.xlarge | $380 - $520 |
| | | GCP n1-standard-4 + T4 | $350 - $480 |
| | | Azure NC4as_T4_v3 | $370 - $500 |
| **CPU Instance** (API Server) | 4 vCPU, 16GB RAM | AWS t3.xlarge | $120 |
| | | GCP e2-standard-4 | $100 |
| **Reserved Pricing** (1-year) | Same specs | All providers | 30-40% savings |

**GPU Instance Breakdown:**
- On-demand: ~$0.50-0.75/hour
- Spot/Preemptible: ~$0.15-0.25/hour (70% savings, but interruptible)
- Reserved (1-year): ~$0.35-0.50/hour

#### Option B: Claude API Only (No GPU Needed)

| Resource | Specification | Provider | Monthly Cost |
|----------|---------------|----------|--------------|
| **API Server** | 2 vCPU, 8GB RAM | AWS t3.large | $60 |
| | | GCP e2-medium | $50 |
| | | DigitalOcean | $48 |

**Recommendation:** Start with Option B (Claude API) for lower upfront costs, migrate to Option A when query volume justifies GPU investment (~50,000+ queries/month).

---

### 2. LLM Inference Costs

#### Option A: Self-Hosted Ollama

| Component | Cost |
|-----------|------|
| GPU Instance | $350 - $520/month |
| Electricity (included in cloud) | $0 |
| Model Storage (~7GB) | Included |
| **Per-Query Cost** | **$0** (after infrastructure) |

**Break-even Analysis:**
- Fixed cost: ~$450/month
- At 50,000 queries/month: $0.009/query
- At 100,000 queries/month: $0.0045/query
- At 500,000 queries/month: $0.0009/query

#### Option B: Claude API (Recommended for < 50K queries)

| Model | Input Cost | Output Cost | Avg Query Cost |
|-------|------------|-------------|----------------|
| Claude 3.5 Haiku | $0.25/1M tokens | $1.25/1M tokens | ~$0.0015 |
| Claude 3.5 Sonnet | $3.00/1M tokens | $15.00/1M tokens | ~$0.018 |

**Typical Query Token Usage:**
- Input: ~2,000 tokens (context + question)
- Output: ~500 tokens (answer)
- **Cost per query: $0.001 - $0.002**

| Monthly Queries | Claude Haiku Cost | Claude Sonnet Cost |
|-----------------|-------------------|---------------------|
| 5,000 | $7.50 | $90 |
| 10,000 | $15 | $180 |
| 50,000 | $75 | $900 |
| 100,000 | $150 | $1,800 |
| 500,000 | $750 | $9,000 |

#### Option C: Hybrid (Recommended for Production)

```
Query Routing Strategy:
├── Simple queries (70%) → Ollama (FREE after GPU cost)
├── Complex queries (25%) → Claude Haiku ($0.0015/query)
└── Critical queries (5%) → Claude Sonnet ($0.018/query)
```

**Hybrid Cost at 50,000 queries/month:**
- GPU: $450
- 12,500 Haiku queries: $19
- 2,500 Sonnet queries: $45
- **Total: ~$514/month ($0.01/query)**

---

### 3. Vector Database (Pinecone)

#### Pinecone Serverless Pricing

| Component | Rate | Notes |
|-----------|------|-------|
| **Read Units** | $0.04 per 1M RU | 1 query ≈ 5-10 RU |
| **Write Units** | $2.00 per 1M WU | 1 upsert ≈ 1 WU |
| **Storage** | $0.07 per GB/month | Vectors + metadata |

**Cost Calculation by Scale:**

| Scale | Queries/Month | Vectors Stored | Monthly Cost |
|-------|---------------|----------------|--------------|
| Startup | 5,000 | 10,000 | $5 - $10 |
| Growth | 50,000 | 50,000 | $20 - $40 |
| Enterprise | 500,000 | 200,000 | $150 - $300 |

#### Pinecone Pod-Based (Alternative for High Volume)

| Pod Type | Monthly Cost | Max Vectors | Best For |
|----------|--------------|-------------|----------|
| Starter (Free) | $0 | 100,000 | Development |
| s1.x1 | $70 | 1M | Small production |
| p1.x1 | $80 | 1M | Low latency |
| p2.x1 | $130 | 1M | High throughput |

**Recommendation:**
- < 100K queries/month: Serverless ($20-50/month)
- > 100K queries/month: Pod-based p1.x1 ($80/month, predictable)

---

### 4. Database & Storage (Supabase)

#### Supabase Pricing Tiers

| Tier | Database | Storage | Price/Month |
|------|----------|---------|-------------|
| **Free** | 500 MB | 1 GB | $0 |
| **Pro** | 8 GB | 100 GB | $25 |
| **Team** | Unlimited | 100 GB | $599 |
| **Enterprise** | Custom | Custom | Custom |

#### Cost Calculation by Scale

**Startup (< 5,000 queries/month):**
- Database: ~50 MB (chat history, documents metadata)
- Storage: ~500 MB (50-100 PDFs)
- **Cost: FREE tier sufficient**

**Growth (50,000 queries/month):**
- Database: ~200 MB (extensive chat history, 200+ documents)
- Storage: ~2-4 GB (200-500 PDFs)
- **Cost: $25/month (Pro tier)**

**Enterprise (500,000 queries/month):**
- Database: ~1-2 GB (large chat history, 1000+ documents)
- Storage: ~10-20 GB (1000+ PDFs)
- **Cost: $25/month (Pro tier) or $599/month (Team for scaling)**

#### Storage Breakdown

| Content Type | Size | Notes |
|--------------|------|-------|
| **Documents table** | ~1 KB/doc | Metadata only |
| **Chat sessions** | ~500 bytes/session | Title, model, timestamps |
| **Chat messages** | ~2 KB/message | Role, content, sources |
| **PDFs (Storage)** | ~2 MB/file | Average document size |

**Example: 500 documents, 1000 chats with 10 messages each:**
- Documents metadata: 500 KB
- Chat sessions: 500 KB
- Chat messages: 20 MB
- PDFs: 1 GB
- **Total: ~1.02 GB (within Free tier!)**

---

### 5. Storage & Content Delivery (Legacy/Supplemental)

#### Document Storage

| Storage Type | Provider | Cost | Use Case |
|--------------|----------|------|----------|
| **Object Storage** | AWS S3 | $0.023/GB | PDF originals |
| | GCP Cloud Storage | $0.020/GB | PDF originals |
| | Cloudflare R2 | $0.015/GB | PDF originals |
| **Block Storage** | AWS EBS gp3 | $0.08/GB | Database, logs |

**Estimated Storage Needs:**

| Content | Size | Monthly Cost (S3) |
|---------|------|-------------------|
| 500 PDFs (avg 2MB) | 1 GB | $0.02 |
| 2,000 PDFs | 4 GB | $0.09 |
| 10,000 PDFs | 20 GB | $0.46 |
| Chat history (1 year) | 1-5 GB | $0.02 - $0.12 |
| Logs & backups | 10-50 GB | $0.23 - $1.15 |

#### CDN for PDF Serving

| Provider | Free Tier | Paid Tier |
|----------|-----------|-----------|
| Cloudflare | 100GB/month | $0.05/GB after |
| AWS CloudFront | 1TB/month (first year) | $0.085/GB |
| Fastly | None | $0.12/GB |

**Recommendation:** Cloudflare (generous free tier, global edge network)

---

### 6. Supporting Services

#### Translation API (Google Cloud Translation)

| Tier | Characters/Month | Cost |
|------|------------------|------|
| Free | 500,000 | $0 |
| Paid | Per 1M chars | $20 |

**Estimated Usage:**
- Average query: 100 chars input + 500 chars output
- 50,000 queries = 30M characters
- **Cost: ~$600/month** (if all translated)

**Optimization:**
- Cache common translations
- Only translate non-English queries (~30%)
- Estimated real cost: **$50-100/month**

#### Monitoring & Logging

| Service | Free Tier | Paid |
|---------|-----------|------|
| **Sentry** (Error tracking) | 5K events | $26/month (100K) |
| **Datadog** (APM) | None | $31/host/month |
| **Grafana Cloud** | 10K metrics | $8/month |
| **AWS CloudWatch** | Basic | $3/month |
| **Better Stack** (Logs) | 1GB | $24/month |

**Recommendation:** Start with free tiers:
- Sentry Free (error tracking)
- Grafana Cloud Free (metrics)
- CloudWatch Basic (AWS logs)
- **Cost: $0-30/month**

#### Domain & SSL

| Item | Provider | Annual Cost |
|------|----------|-------------|
| Domain (.com) | Cloudflare/Namecheap | $10-15 |
| Domain (.ai) | Various | $50-80 |
| SSL Certificate | Let's Encrypt | FREE |
| SSL (Wildcard) | Cloudflare | FREE |

---

### 7. Operational Overhead

#### Backup & Disaster Recovery

| Component | Strategy | Monthly Cost |
|-----------|----------|--------------|
| Database backups | Daily snapshots | $5-20 |
| PDF archive | Cross-region replication | $2-10 |
| Pinecone | Built-in (included) | $0 |

#### Security

| Service | Purpose | Monthly Cost |
|---------|---------|--------------|
| WAF (Cloudflare) | DDoS protection | FREE (basic) |
| AWS WAF | API protection | $5 + $1/M requests |
| Secrets Manager | API key storage | $0.40/secret |

#### CI/CD & DevOps

| Service | Free Tier | Notes |
|---------|-----------|-------|
| GitHub Actions | 2,000 mins/month | Usually sufficient |
| Docker Hub | 1 private repo | Or use GHCR (free) |
| Terraform Cloud | 500 resources | Infrastructure as code |

---

## Scenario Cost Summaries

### Scenario 1: Startup (5,000 queries/month)

**Target:** MVP launch, proof of concept, pilot users

| Category | Service | Monthly Cost |
|----------|---------|--------------|
| **Compute** | DigitalOcean Droplet (4GB) | $24 |
| **LLM** | Claude Haiku API | $8 |
| **Vector DB** | Pinecone Serverless | $10 |
| **Database** | Supabase Free Tier | $0 |
| **Storage** | Supabase Free Tier (1GB) | $0 |
| **CDN** | Cloudflare Free | $0 |
| **Domain** | .com domain | $1 (amortized) |
| **Monitoring** | Free tiers | $0 |
| **Translation** | Google Free Tier | $0 |
| **Backups** | Supabase automatic | $0 |
| | | |
| **TOTAL** | | **$43/month** |
| **Per Query** | | **$0.009** |

**Optimizations Applied:**
- CPU-only inference (Claude API)
- Serverless Pinecone
- Supabase free tier (500MB DB + 1GB Storage)
- Free monitoring tiers
- Cloudflare free CDN
- Automatic backups included

---

### Scenario 2: Growth (50,000 queries/month)

**Target:** Growing user base, multiple concurrent users

| Category | Service | Monthly Cost |
|----------|---------|--------------|
| **Compute** | AWS t3.xlarge (API) | $120 |
| | AWS g4dn.xlarge (Ollama) - Spot | $180 |
| **LLM** | Hybrid (70% Ollama, 30% Claude) | $25 |
| **Vector DB** | Pinecone p1.x1 Pod | $80 |
| **Database** | Supabase Pro (8GB) | $25 |
| **Storage** | Supabase Pro (100GB included) | $0 |
| **CDN** | Cloudflare Pro | $20 |
| **Domain** | .com + .ai | $8 (amortized) |
| **Monitoring** | Sentry + Grafana | $30 |
| **Translation** | Google Paid | $60 |
| **Backups** | Supabase automatic (included) | $0 |
| **Load Balancer** | AWS ALB | $20 |
| | | |
| **TOTAL** | | **$568/month** |
| **Per Query** | | **$0.011** |

**Infrastructure:**
```
                    ┌─────────────┐
                    │ Cloudflare  │
                    │    CDN      │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  AWS ALB    │
                    └──────┬──────┘
              ┌────────────┼────────────┐
              │            │            │
       ┌──────┴──────┐ ┌───┴───┐ ┌─────┴─────┐
       │ API Server  │ │Ollama │ │ Streamlit │
       │ (t3.xlarge) │ │(g4dn) │ │ (t3.small)│
       └─────────────┘ └───────┘ └───────────┘
```

---

### Scenario 3: Enterprise (500,000 queries/month)

**Target:** Production system, SLA requirements, high availability

| Category | Service | Monthly Cost |
|----------|---------|--------------|
| **Compute** | | |
| - API Servers (2x) | AWS t3.2xlarge | $500 |
| - Ollama GPU (2x) | AWS g4dn.2xlarge Reserved | $800 |
| - Streamlit (2x) | AWS t3.large | $120 |
| **LLM** | Hybrid routing | $200 |
| **Vector DB** | Pinecone p2.x2 (2 replicas) | $260 |
| **Database** | Supabase Team (Unlimited DB) | $599 |
| **Storage** | Supabase Team (100GB included) | $0 |
| **CDN** | Cloudflare Business | $200 |
| **Domain** | Premium + subdomains | $15 |
| **Monitoring** | Datadog APM | $150 |
| **Translation** | Google Paid | $300 |
| **Backups** | Supabase automatic (included) | $0 |
| **Load Balancer** | AWS ALB + WAF | $80 |
| **Security** | AWS WAF + Secrets Manager | $50 |
| **Support** | AWS Business Support | $100 |
| | | |
| **TOTAL** | | **$3,374/month** |
| **Per Query** | | **$0.007** |

**High Availability Architecture:**
```
                         ┌─────────────┐
                         │ Cloudflare  │
                         │  Business   │
                         └──────┬──────┘
                                │
                         ┌──────┴──────┐
                         │   AWS WAF   │
                         └──────┬──────┘
                                │
                         ┌──────┴──────┐
                         │   AWS ALB   │
                         └──────┬──────┘
                    ┌───────────┼───────────┐
                    │           │           │
             ┌──────┴──────┐    │    ┌──────┴──────┐
             │ API Server 1│    │    │ API Server 2│
             │   (AZ-1a)   │    │    │   (AZ-1b)   │
             └─────────────┘    │    └─────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
             ┌──────┴──────┐    │    ┌──────┴──────┐
             │  Ollama 1   │    │    │  Ollama 2   │
             │  (g4dn.2xl) │    │    │  (g4dn.2xl) │
             └─────────────┘    │    └─────────────┘
                                │
                         ┌──────┴──────┐
                         │  Pinecone   │
                         │  (2 replicas)│
                         └─────────────┘
```

---

## Cost Optimization Strategies

### 1. Compute Optimization

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| **Spot/Preemptible Instances** | 60-70% | May be interrupted |
| **Reserved Instances (1-year)** | 30-40% | Commitment required |
| **Auto-scaling** | 20-40% | Complexity |
| **ARM instances (Graviton)** | 20% | Compatibility testing |

### 2. LLM Cost Optimization

| Strategy | Implementation | Savings |
|----------|----------------|---------|
| **Response caching** | Cache common Q&A pairs | 30-50% |
| **Query routing** | Simple → Ollama, Complex → Claude | 40-60% |
| **Prompt optimization** | Reduce context tokens | 20-30% |
| **Batch processing** | Queue non-urgent queries | 10-20% |

### 3. Vector DB Optimization

| Strategy | Implementation | Savings |
|----------|----------------|---------|
| **Metadata filtering** | Reduce search scope | 30-40% |
| **Dimensionality reduction** | 768D → 384D (if quality allows) | 50% storage |
| **Namespace partitioning** | Separate by source/language | Query efficiency |

### 4. Translation Optimization

| Strategy | Implementation | Savings |
|----------|----------------|---------|
| **Translation caching** | Redis cache for common phrases | 60-80% |
| **Detect-before-translate** | Skip if already English | 40-50% |
| **Batch translations** | Queue and batch requests | 20-30% |

---

## Annual Cost Projections

### Year 1 Projection (Growth Trajectory)

| Quarter | Queries | Monthly Cost | Quarterly Total |
|---------|---------|--------------|-----------------|
| Q1 | 5,000 → 15,000 | $43 → $120 | $250 |
| Q2 | 15,000 → 30,000 | $120 → $280 | $600 |
| Q3 | 30,000 → 50,000 | $280 → $568 | $1,270 |
| Q4 | 50,000 → 80,000 | $568 → $750 | $2,000 |
| | | | |
| **Year 1 Total** | | | **$4,120** |

### Year 2 Projection (Scale Phase)

| Quarter | Queries | Monthly Cost | Quarterly Total |
|---------|---------|--------------|-----------------|
| Q1 | 80,000 → 150,000 | $750 → $1,150 | $2,850 |
| Q2 | 150,000 → 250,000 | $1,150 → $1,750 | $4,350 |
| Q3 | 250,000 → 400,000 | $1,750 → $2,350 | $6,150 |
| Q4 | 400,000 → 500,000 | $2,350 → $3,374 | $8,600 |
| | | | |
| **Year 2 Total** | | | **$21,950** |

---

## One-Time Setup Costs

| Item | Cost | Notes |
|------|------|-------|
| **Domain Registration** | $15 - $80 | .com vs .ai |
| **SSL Setup** | $0 | Let's Encrypt |
| **Pinecone Index Creation** | $0 | Free to create |
| **Initial Document Processing** | $20 - $50 | One-time embedding costs |
| **Playwright Browser Install** | $0 | Open source |
| **Development Environment** | $0 - $50 | Local setup |
| | | |
| **Total One-Time** | **$35 - $180** | |

---

## Hidden Costs to Consider

### Often Overlooked

| Cost | Estimate | Frequency |
|------|----------|-----------|
| **Developer time** (maintenance) | $500-2,000 | Monthly |
| **Security audits** | $1,000-5,000 | Annually |
| **Compliance (if needed)** | $2,000-10,000 | Annually |
| **Customer support tools** | $50-200 | Monthly |
| **Documentation hosting** | $0-20 | Monthly |
| **Status page** | $0-30 | Monthly |

### Scaling Surprises

| Trigger | Impact |
|---------|--------|
| **Viral traffic spike** | Auto-scaling costs can 10x overnight |
| **Large document upload** | OCR processing can spike compute |
| **Translation heavy language** | Arabic/Malay queries cost more |
| **Complex queries** | Claude Sonnet fallback increases costs |

---

## Break-Even Analysis

### When to Switch from Claude API to Self-Hosted Ollama

| Variable | Claude API Only | Self-Hosted Ollama |
|----------|-----------------|---------------------|
| Fixed Cost | $60/month (server) | $510/month (GPU + server) |
| Per Query | $0.0015 | $0 |

**Break-even point:**
```
$510 - $60 = $450 (additional fixed cost)
$450 / $0.0015 = 300,000 queries/month
```

**Recommendation:**
- < 100,000 queries/month: **Claude API**
- 100,000 - 300,000 queries/month: **Hybrid approach**
- > 300,000 queries/month: **Self-hosted Ollama primary**

---

## Summary: Recommended Path

### Phase 1: Launch (Month 1-3)
- **Budget:** $40-100/month
- **Stack:** DigitalOcean + Claude API + Pinecone Serverless + Supabase Free
- **Focus:** Validate product-market fit
- **Supabase:** Free tier (500MB DB + 1GB Storage)

### Phase 2: Growth (Month 4-9)
- **Budget:** $280-600/month
- **Stack:** AWS + Hybrid LLM + Pinecone Pods + Supabase Pro
- **Focus:** Optimize costs, add monitoring
- **Supabase:** Pro tier ($25/month - 8GB DB + 100GB Storage)

### Phase 3: Scale (Month 10+)
- **Budget:** $1,150-3,500/month
- **Stack:** Multi-AZ AWS + Self-hosted Ollama + HA Pinecone + Supabase Team
- **Focus:** Reliability, SLA compliance
- **Supabase:** Team tier ($599/month - Unlimited DB + 100GB Storage)

---

## Cost Comparison: Agent Deen vs Alternatives

| Solution | Setup Cost | Monthly (50K queries) | Per Query |
|----------|------------|----------------------|-----------|
| **Agent Deen (Self-hosted + Supabase)** | $100 | $568 | $0.011 |
| **Agent Deen (Claude only + Supabase)** | $50 | $118 | $0.002 |
| **ChatGPT Enterprise** | $0 | $30/user (min 150) | N/A |
| **Custom GPT-4 RAG** | $500 | $2,500+ | $0.05+ |
| **Azure OpenAI + Cognitive** | $200 | $1,500+ | $0.03+ |

**Agent Deen Advantage:** 70-95% cost savings vs. comparable enterprise solutions while maintaining full control over data and customization. Supabase integration eliminates separate storage costs and provides automatic backups.

---

## Appendix: Provider Pricing Links

- [AWS Pricing Calculator](https://calculator.aws/)
- [GCP Pricing Calculator](https://cloud.google.com/products/calculator)
- [Pinecone Pricing](https://www.pinecone.io/pricing/)
- [Anthropic Claude Pricing](https://www.anthropic.com/pricing)
- [Google Cloud Translation Pricing](https://cloud.google.com/translate/pricing)
- [Cloudflare Plans](https://www.cloudflare.com/plans/)

---

## Update Notes

**January 2025 Update:**
- Added Supabase integration (PostgreSQL + Storage)
- Removed separate S3/storage costs (now included in Supabase)
- Automatic backups included with Supabase
- Reduced startup costs: $53/month → $43/month
- Reduced growth costs: $580/month → $568/month
- Enterprise tier now includes Supabase Team ($599/month)
- Total Year 1 cost: ~$4,120 (10-15% savings with Supabase)

---

*Last Updated: January 2025*
*Prices subject to change. Verify with providers before finalizing budget.*
