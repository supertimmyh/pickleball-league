# Google Cloud Run + Cloud Storage Migration Plan

**Last Updated:** October 22, 2025
**Status:** Planning Phase
**Estimated Effort:** ~90 minutes

---

## 🎯 Overview

Migrate the Flask pickleball league app from local Python hosting to Google Cloud Run (serverless) with Google Cloud Storage for persistent data storage.

---

## 🏗️ Architecture Changes

### Current Architecture (Local)
- **Server:** Flask on local machine (port 8000)
- **Storage:** Local filesystem (`matches/`, `players.csv`, `rankings.json`, `index.html`)
- **Data:** YAML files in `matches/singles/` and `matches/doubles/`

### Target Architecture (Google Cloud)
- **Server:** Cloud Run (serverless, auto-scaling, pay-per-use)
- **Storage:** Google Cloud Storage buckets
  - `matches-data-bucket` → `matches/` directory structure
  - `config-data-bucket` → `players.csv`, `config.json`, `rankings.json`, `index.html`
- **Deployment:** Docker container in Container Registry
- **CI/CD:** Cloud Build (automated deployments)

### What Stays the Same
- ✅ Flask framework and routing
- ✅ Ranking algorithm (ELO system)
- ✅ HTML generation logic
- ✅ Business logic unchanged
- ✅ Frontend (HTML/CSS/JavaScript)
- ✅ API endpoints and structure

---

## 📋 Implementation Steps

### Phase 1: Google Cloud Project Setup (10 mins)

**Prerequisites:**
- Google Cloud account
- `gcloud` CLI installed locally
- Project with billing enabled

**Steps:**
1. Create Google Cloud Project (if not exists)
2. Create Cloud Storage bucket for match files
   ```bash
   gsutil mb gs://pickleball-matches-data
   ```
3. Create Cloud Storage bucket for configuration
   ```bash
   gsutil mb gs://pickleball-config-data
   ```
4. Enable required APIs:
   - Cloud Run API
   - Container Registry API
   - Cloud Build API
5. Create service account for Cloud Run:
   ```bash
   gcloud iam service-accounts create pickleball-app
   ```
6. Grant necessary IAM roles to service account:
   - `roles/storage.objectAdmin` (to read/write Cloud Storage)
   - `roles/logging.logWriter` (for Cloud Logging)

**Output Files:**
- Project ID (save for reference)
- Service account email
- Bucket names

---

### Phase 2: Code Modifications (30-40 mins)

#### 2.1 Update `server.py`
**Changes needed:**
- Import `google.cloud.storage`
- Replace `Path`-based file operations with Cloud Storage client
- Update file read operations:
  - `PLAYERS_FILE` → read from `gs://pickleball-config-data/players.csv`
  - `INDEX_FILE` → read from `gs://pickleball-config-data/index.html`
  - `RANKINGS_FILE` → read from `gs://pickleball-config-data/rankings.json`
- Update file write operations for match YAML files → Cloud Storage
- Initialize Storage client on startup
- Add environment variable support for bucket names
- Add error handling for Cloud Storage operations

**Key functions to update:**
- `load_players()` - read from GCS
- `submit_match()` - write YAML to GCS
- `regenerate_rankings()` - subprocess stays same, but file I/O uses GCS
- `index()`, `record_match()`, `get_rankings_json()` - serve from GCS

#### 2.2 Update `scripts/generate_rankings.py`
**Changes needed:**
- Import `google.cloud.storage`
- Modify `RankingsGenerator.__init__()` to accept bucket/client
- Update `load_yaml_file()` to read from Cloud Storage
- Update `generate_all_rankings()` to write `rankings.json` to Cloud Storage
- Support both local (for testing) and Cloud Storage modes via environment variable

**Key changes:**
- Read YAML files from `gs://pickleball-matches-data/singles/` and `gs://pickleball-matches-data/doubles/`
- Write `rankings.json` to `gs://pickleball-config-data/rankings.json`
- Add fallback for local filesystem if `GOOGLE_CLOUD_PROJECT` env var not set

#### 2.3 Update `scripts/build_pages.py`
**Changes needed:**
- Import `google.cloud.storage`
- Update to read `rankings.json` from Cloud Storage
- Update to read `config.json` from Cloud Storage
- Update to write `index.html` to Cloud Storage
- Support Cloud Storage and local modes

**Key changes:**
- Read from: `gs://pickleball-config-data/rankings.json`
- Read from: `gs://pickleball-config-data/config.json`
- Write to: `gs://pickleball-config-data/index.html`

#### 2.4 Update `requirements-server.txt`
**Add:**
```
flask>=3.0.0
pyyaml>=6.0
google-cloud-storage>=2.10.0
```

#### 2.5 Create `.env.example` file
**Content:**
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GCS_MATCHES_BUCKET=pickleball-matches-data
GCS_CONFIG_BUCKET=pickleball-config-data
```

---

### Phase 3: Containerization (10 mins)

#### 3.1 Create `Dockerfile`
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements-server.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-server.txt

# Copy application code
COPY server.py .
COPY scripts/ scripts/
COPY match-form.html .
COPY config.json .

# Set environment variables
ENV PORT=8080
ENV FLASK_APP=server.py

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/')"

# Run Flask app
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --worker-class gthread --timeout 60 server:app
```

#### 3.2 Create `.dockerignore`
```
.git
.gitignore
.DS_Store
__pycache__
*.pyc
.env
.env.local
*.md
matches/
players.csv
rankings.json
index.html
```

#### 3.3 Create `cloudbuild.yaml`
```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/pickleball-app:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/pickleball-app:latest'
      - '.'

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/pickleball-app:$SHORT_SHA'

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gke-deploy'
    args:
      - 'run'
      - '--filename=.'
      - '--image=gcr.io/$PROJECT_ID/pickleball-app:$SHORT_SHA'
      - '--location=us-central1'
      - '--output=/dev/null'

images:
  - 'gcr.io/$PROJECT_ID/pickleball-app:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/pickleball-app:latest'

timeout: '900s'
```

#### 3.4 Create `app.yaml` (optional, for gcloud deployment)
```yaml
runtime: python311
service: default

env: standard
entrypoint: gunicorn --bind :$PORT --workers 1 --threads 8 --worker-class gthread server:app

env_variables:
  GOOGLE_CLOUD_PROJECT: "${GCLOUD_PROJECT}"
  GCS_MATCHES_BUCKET: "pickleball-matches-data"
  GCS_CONFIG_BUCKET: "pickleball-config-data"

automatic_scaling:
  min_instances: 0
  max_instances: 10
```

---

### Phase 4: Deployment (10-15 mins)

#### Option A: Using Cloud Build (Recommended for CI/CD)
```bash
# Commit code to git repository
git add .
git commit -m "Migrate to Google Cloud Run and Cloud Storage"
git push origin main

# Connect Cloud Build to repository
gcloud builds connect --region=us-central1

# Create build trigger in Cloud Console
# (Triggers automatic deployment on push)

# Manual build if needed
gcloud builds submit --config cloudbuild.yaml
```

#### Option B: Direct Deployment to Cloud Run
```bash
# Build and push manually
gcloud builds submit --tag gcr.io/$PROJECT_ID/pickleball-app

# Deploy to Cloud Run
gcloud run deploy pickleball-app \
  --image gcr.io/$PROJECT_ID/pickleball-app \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 50 \
  --service-account pickleball-app@$PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GCS_MATCHES_BUCKET=pickleball-matches-data,GCS_CONFIG_BUCKET=pickleball-config-data \
  --allow-unauthenticated
```

#### Configuration Options
- **Memory:** 512Mi (suitable for this app, can increase if needed)
- **CPU:** 1 (standard)
- **Concurrency:** 50 (max requests per instance)
- **Timeout:** 60 seconds
- **Min instances:** 0 (auto-scale, costs less)
- **Max instances:** 10 (prevent runaway costs)

#### Output
- Cloud Run service URL (e.g., `https://pickleball-app-xxxxx.run.app`)
- Service account permissions confirmed

---

### Phase 5: Initial Data Upload (5 mins)

#### Upload existing data to Cloud Storage

```bash
# Create directories in buckets
gsutil -m cp -r matches/* gs://pickleball-matches-data/

# Upload configuration files
gsutil cp players.csv gs://pickleball-config-data/
gsutil cp config.json gs://pickleball-config-data/
gsutil cp rankings.json gs://pickleball-config-data/
gsutil cp index.html gs://pickleball-config-data/
```

---

### Phase 6: Testing (15 mins)

#### Local Testing (Before Cloud Run deployment)
```bash
# Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export GCS_MATCHES_BUCKET=pickleball-matches-data
export GCS_CONFIG_BUCKET=pickleball-config-data

# Test with local storage
python server.py

# Test with Cloud Storage (requires gcloud auth)
gcloud auth application-default login
python server.py
```

#### Cloud Run Testing
1. **Test rankings page:**
   - Visit: `https://pickleball-app-xxxxx.run.app/`
   - Verify rankings display correctly

2. **Test match form:**
   - Visit: `https://pickleball-app-xxxxx.run.app/record`
   - Verify form loads

3. **Test match submission:**
   - Submit a test match
   - Verify it appears in Cloud Storage: `gsutil ls gs://pickleball-matches-data/`
   - Verify rankings updated
   - Verify `rankings.json` updated in Cloud Storage

4. **Test API endpoints:**
   ```bash
   curl https://pickleball-app-xxxxx.run.app/api/players
   curl https://pickleball-app-xxxxx.run.app/rankings.json
   ```

5. **Test multi-user concurrency:**
   - Open multiple browser windows
   - Submit matches from each window simultaneously
   - Verify all are processed correctly

6. **Check Cloud Logs:**
   ```bash
   gcloud run logs read pickleball-app --limit 50 --region us-central1
   ```

---

## 🔧 Technical Considerations

### Cloud Storage Structure
```
pickleball-matches-data/
├── singles/
│   ├── 2025-10-22-alice-vs-bob-120000.yml
│   └── ...
└── doubles/
    ├── 2025-10-22-doubles-120000.yml
    └── ...

pickleball-config-data/
├── players.csv
├── config.json
├── rankings.json
└── index.html
```

### Error Handling
- Handle missing Cloud Storage buckets gracefully
- Implement retry logic for transient errors
- Log all Cloud Storage operations
- Add monitoring/alerts for failed operations

### Cost Optimization
- Use Cloud Run's auto-scaling (min: 0, max: 10)
- Cloud Storage pricing: ~$0.023/GB/month
- Cloud Run: ~$0.0000667 per CPU-second, ~$0.0000042 per memory-GB-second
- Estimate: <$5/month for typical usage

### Security
- Service account has minimal permissions (storage.objectAdmin only)
- Cloud Run endpoint publicly accessible (good for league members)
- Data encrypted at rest and in transit
- Could add authentication layer if needed later

### Monitoring
- Enable Cloud Logging for Flask app
- Set up Cloud Monitoring alerts
- Track API response times
- Monitor Cloud Storage operations

---

## 📝 Environment Variables

The application will use these environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `my-pickleball-project` |
| `GCS_MATCHES_BUCKET` | Bucket for match YAML files | `pickleball-matches-data` |
| `GCS_CONFIG_BUCKET` | Bucket for config/output files | `pickleball-config-data` |
| `PORT` | Cloud Run port (auto-set) | `8080` |
| `FLASK_ENV` | Environment mode | `production` |

---

## 🚀 Quick Deployment Checklist

- [ ] Google Cloud project created and billing enabled
- [ ] Service account created with Cloud Storage permissions
- [ ] Cloud Storage buckets created
- [ ] Code modified to use Cloud Storage client
- [ ] `requirements-server.txt` updated with `google-cloud-storage`
- [ ] `Dockerfile` created
- [ ] `cloudbuild.yaml` created
- [ ] Existing data uploaded to Cloud Storage
- [ ] Cloud Run service deployed
- [ ] Environment variables configured
- [ ] Tested match submission
- [ ] Tested rankings generation
- [ ] Verified data in Cloud Storage
- [ ] Cloud logging configured
- [ ] Monitoring/alerts set up

---

## 🆘 Troubleshooting

### Cloud Run Permission Issues
```bash
# Fix: Grant service account proper roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### Cloud Storage 403 Errors
```bash
# Verify bucket permissions
gsutil iam ch serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectAdmin gs://pickleball-matches-data
gsutil iam ch serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectAdmin gs://pickleball-config-data
```

### Container Build Failures
```bash
# Check build logs
gcloud builds log <BUILD_ID>

# Rebuild with verbose output
gcloud builds submit --config cloudbuild.yaml --no-cache
```

### Subprocess Errors in Cloud Run
- `generate_rankings.py` and `build_pages.py` run as subprocesses
- Ensure they're packaged in Docker image
- Add error logging to catch subprocess failures

---

## 📚 Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Cloud Storage Client Library](https://cloud.google.com/python/docs/reference/storage/latest)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)
- [Flask on Cloud Run](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/python)

---

## 💾 Rollback Plan

If issues arise after Cloud Run deployment:

1. **Immediate rollback:**
   ```bash
   # Deploy previous version
   gcloud run deploy pickleball-app --image gcr.io/$PROJECT_ID/pickleball-app:previous-tag
   ```

2. **Data recovery:**
   - All data remains in Cloud Storage buckets
   - Can redeploy local Flask version using same buckets
   - YAML files never deleted, only added

3. **Version control:**
   - Keep Git history of code changes
   - Tag Docker images with commit SHA
   - Easy to deploy any previous version

---

## 🎯 Next Steps After Migration

### Immediate (Phase 1.5)
1. Monitor Cloud Run service for 1 week
2. Track costs and performance
3. Adjust instance configuration if needed
4. Set up automated backups of Cloud Storage

### Short-term (Phase 2)
1. Add user authentication
2. Implement match edit/delete functionality
3. Add player statistics page
4. Email notifications for match results

### Long-term (Phase 3)
1. Consider migrating to Cloud Datastore for more complex queries
2. Add mobile app integration
3. Real-time notifications with Cloud Pub/Sub
4. Advanced analytics dashboard

---

**Remember:** Keep this plan updated as you progress through the migration!
