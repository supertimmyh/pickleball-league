# Cloud Migration Guide

**Last Updated:** October 23, 2025
**Status:** Migration Complete ✅
**Target:** Google Cloud Run + Cloud Storage

---

## 🎯 Overview

This guide explains the changes made to support Google Cloud deployment and how to use them.

### What Changed

The application now supports **both** local filesystem and Google Cloud Storage backends:

- **Local Mode** - Works exactly like before (default)
- **Cloud Mode** - Uses Google Cloud Storage for data

All existing functionality is preserved. You can switch between modes by setting the `USE_GCS` environment variable.

---

## 🏗️ Architecture Changes

### Before (Local)
```
┌─────────────────┐
│  Flask Server   │
│  (Port 8000)    │
└────────┬────────┘
         │
    ┌────▼─────────────────────┐
    │  Local Filesystem        │
    │ - matches/singles/       │
    │ - matches/doubles/       │
    │ - players.csv            │
    │ - rankings.json          │
    │ - index.html             │
    └──────────────────────────┘
```

### After (Cloud Ready)
```
┌─────────────────────────┐
│  Cloud Run Service      │
│  (Serverless)           │
└────────┬────────────────┘
         │
    ┌────▼────────────────────────────────┐
    │  Google Cloud Storage               │
    │  ┌──────────────────────────────┐   │
    │  │ pickleball-matches-data      │   │
    │  │ - singles/                   │   │
    │  │ - doubles/                   │   │
    │  └──────────────────────────────┘   │
    │  ┌──────────────────────────────┐   │
    │  │ pickleball-config-data       │   │
    │  │ - players.csv                │   │
    │  │ - config.json                │   │
    │  │ - rankings.json              │   │
    │  │ - index.html                 │   │
    │  └──────────────────────────────┘   │
    └─────────────────────────────────────┘
```

---

## 📝 Files Modified

### 1. **server.py** - Flask Backend
**Changes:**
- Added Google Cloud Storage client initialization
- Added `read_file_from_gcs()` and `write_file_to_gcs()` helper functions
- Updated `load_players()` to read from GCS
- Updated `submit_match()` to write YAML files to GCS
- Updated routes (`/`, `/rankings.json`) to serve from GCS
- Added PORT environment variable support for Cloud Run
- Updated startup messages for cloud-aware output

**Key Functions Updated:**
- `load_players()` - Lines 87-109
- `submit_match()` - Lines 208-283
- `index()` - Lines 159-171
- `get_rankings_json()` - Lines 184-198

### 2. **scripts/generate_rankings.py** - Ranking Generator
**Changes:**
- Added GCS support to `RankingsGenerator` class
- Added `list_gcs_files()` method for listing bucket objects
- Updated `load_yaml_file()` to support GCS blobs
- Updated `get_sorted_match_files()` to list GCS files
- Updated `generate_all_rankings()` to write to GCS
- Added environment variable detection in `main()`

**Key Methods Added:**
- `list_gcs_files()` - Lines 83-94
- GCS support in `__init__()` - Lines 46-63

### 3. **scripts/build_pages.py** - HTML Generator
**Changes:**
- Added GCS helper functions
- Updated `load_config()` to read from GCS
- Updated `generate_index_page()` to write to GCS
- Added environment variable detection in `main()`

**Key Functions Updated:**
- `load_config()` - Lines 49-69
- `generate_index_page()` - Now accepts GCS parameters

### 4. **requirements-server.txt** - Dependencies
**Added:**
```
google-cloud-storage>=2.10.0
gunicorn>=21.0.0
```

### 5. **New Files Created**

| File | Purpose |
|------|---------|
| `.env.example` | Template for environment variables |
| `Dockerfile` | Container configuration for Cloud Run |
| `.dockerignore` | Files to exclude from Docker image |
| `cloudbuild.yaml` | Cloud Build CI/CD configuration |
| `CLOUD_RUN_DEPLOYMENT.md` | Step-by-step deployment guide |
| `CLOUD_MIGRATION_GUIDE.md` | This file |

---

## 🔧 How to Use

### Local Mode (Default)

No changes needed! Use exactly as before:

```bash
# Install dependencies
pip3 install -r requirements-server.txt

# Run server
python3 server.py

# Visit http://localhost:8000
```

This uses local filesystem for all data storage.

### Cloud Mode (Google Cloud)

Set environment variables and deploy:

```bash
# Set environment variables
export USE_GCS=true
export GOOGLE_CLOUD_PROJECT=your-project-id
export GCS_MATCHES_BUCKET=pickleball-matches-data
export GCS_CONFIG_BUCKET=pickleball-config-data

# Run server (will use Cloud Storage)
python3 server.py
```

Or create a `.env` file:

```bash
# Copy template
cp .env.example .env

# Edit .env
nano .env
# Set USE_GCS=true and your GCP project ID

# Run with python-dotenv
pip3 install python-dotenv
python3 server.py
```

---

## 🚀 Deployment Methods

### Method 1: Direct Deployment (Easiest)

```bash
# Deploy directly from source code
gcloud run deploy pickleball-app \
  --source=. \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars=USE_GCS=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,...
```

### Method 2: Using Cloud Build (CI/CD)

```bash
# Commit code to Git
git add .
git commit -m "Migrate to Cloud Run"
git push origin main

# Cloud Build will automatically:
# 1. Build Docker image (using Dockerfile)
# 2. Push to Container Registry
# 3. Deploy to Cloud Run
```

### Method 3: Manual Docker Build

```bash
# Build locally
docker build -t pickleball-app:latest .

# Test locally
docker run -p 8080:8080 \
  -e USE_GCS=false \
  pickleball-app:latest

# Tag for registry
docker tag pickleball-app gcr.io/$PROJECT_ID/pickleball-app

# Push to registry
docker push gcr.io/$PROJECT_ID/pickleball-app

# Deploy to Cloud Run
gcloud run deploy pickleball-app \
  --image=gcr.io/$PROJECT_ID/pickleball-app
```

---

## 📋 Environment Variables

### Required (for Cloud Mode)

```bash
USE_GCS=true                              # Enable Cloud Storage
GOOGLE_CLOUD_PROJECT=your-project-id     # Your GCP project ID
GCS_MATCHES_BUCKET=pickleball-matches-data
GCS_CONFIG_BUCKET=pickleball-config-data
```

### Optional

```bash
PORT=8080                  # Server port (auto-set by Cloud Run)
FLASK_ENV=production       # Flask environment
```

### How to Set

**Method 1: Environment file (.env)**
```bash
cp .env.example .env
# Edit .env
nano .env
```

**Method 2: System environment**
```bash
export USE_GCS=true
export GOOGLE_CLOUD_PROJECT=my-project
```

**Method 3: Cloud Run deployment**
```bash
gcloud run deploy pickleball-app \
  --set-env-vars=USE_GCS=true,GOOGLE_CLOUD_PROJECT=...
```

---

## 🗄️ Data Storage Structure

### Cloud Storage Buckets

#### Bucket 1: `pickleball-matches-data`
```
pickleball-matches-data/
├── singles/
│   ├── 2025-10-22-alice-vs-bob-120000.yml
│   └── ...
└── doubles/
    ├── 2025-10-22-doubles-120000.yml
    └── ...
```

#### Bucket 2: `pickleball-config-data`
```
pickleball-config-data/
├── players.csv           # Player list
├── config.json           # League configuration
├── rankings.json         # Generated rankings data
└── index.html            # Generated rankings page
```

### YAML Format (Unchanged)

**Singles:**
```yaml
date: '2025-10-22'
players:
  - Alice Johnson
  - Bob Smith
games:
  - player1_score: 11
    player2_score: 7
  - player1_score: 9
    player2_score: 11
winner: Alice Johnson
```

**Doubles:**
```yaml
date: '2025-10-22'
team1:
  - Alice Johnson
  - Bob Smith
team2:
  - Carol White
  - Dave Brown
games:
  - team1_score: 11
    team2_score: 8
  - team1_score: 9
    team2_score: 11
winner_team: 1
```

---

## 🔄 Data Migration

### From Local to Cloud

```bash
# Prerequisites
export PROJECT_ID=your-project-id
export GCS_MATCHES_BUCKET=pickleball-matches-data
export GCS_CONFIG_BUCKET=pickleball-config-data

# Upload existing match files
gsutil -m cp -r matches/* gs://$GCS_MATCHES_BUCKET/

# Upload configuration
gsutil cp players.csv gs://$GCS_CONFIG_BUCKET/
gsutil cp config.json gs://$GCS_CONFIG_BUCKET/
gsutil cp rankings.json gs://$GCS_CONFIG_BUCKET/
gsutil cp index.html gs://$GCS_CONFIG_BUCKET/

# Verify
gsutil ls -r gs://$GCS_MATCHES_BUCKET/
gsutil ls -r gs://$GCS_CONFIG_BUCKET/
```

### From Cloud to Local

```bash
# Download all data from Cloud Storage
mkdir -p local-backup
gsutil -m cp -r gs://$GCS_MATCHES_BUCKET/* local-backup/matches/
gsutil -m cp gs://$GCS_CONFIG_BUCKET/* local-backup/

# Now you can use local mode
cp local-backup/* .
python3 server.py  # USE_GCS=false by default
```

---

## 🧪 Testing

### Test Locally (Local Mode)

```bash
# Default is local mode
python3 server.py

# Visit http://localhost:8000
# Submit a match
# Check local files were created:
ls -la matches/singles/
ls -la matches/doubles/
cat rankings.json
```

### Test Locally with GCS (Requires GCP Auth)

```bash
# Authenticate with GCP
gcloud auth application-default login

# Enable Cloud Storage
export USE_GCS=true
export GOOGLE_CLOUD_PROJECT=your-project-id
export GCS_MATCHES_BUCKET=pickleball-matches-data
export GCS_CONFIG_BUCKET=pickleball-config-data

# Run server
python3 server.py

# Test endpoints
curl http://localhost:8000/api/players
curl http://localhost:8000/rankings.json
```

### Test in Docker

```bash
# Build image
docker build -t pickleball-app:latest .

# Run with local mode (no GCS)
docker run -p 8080:8080 \
  -e USE_GCS=false \
  pickleball-app:latest

# Visit http://localhost:8080
```

---

## 🐛 Troubleshooting

### "Cannot connect to Cloud Storage"

**Symptoms:** Errors reading from/writing to buckets

**Solutions:**
1. Verify `USE_GCS=true` is set
2. Verify `GOOGLE_CLOUD_PROJECT` is correct
3. Run `gcloud auth application-default login`
4. Check service account has `storage.objectAdmin` role
5. Verify bucket names are correct

### "Bucket not found"

**Symptoms:** 404 errors when accessing buckets

**Solutions:**
1. Verify buckets exist: `gsutil ls`
2. Verify bucket names match environment variables
3. Verify service account has permissions on buckets
4. Bucket names are case-sensitive

### "Permission denied"

**Symptoms:** 403 errors from Cloud Storage

**Solutions:**
1. Update service account permissions:
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member=serviceAccount:sa@$PROJECT_ID.iam.gserviceaccount.com \
     --role=roles/storage.objectAdmin
   ```

### "PORT is not recognized"

**Symptoms:** Flask runs on wrong port

**Solutions:**
1. Cloud Run sets PORT automatically
2. For local testing, set `PORT=8000` manually
3. The app respects `PORT` environment variable

### Files not updating in Cloud Storage

**Symptoms:** Changes don't appear in buckets

**Solutions:**
1. Verify write operations succeed (check server logs)
2. Check bucket permissions
3. Use `gsutil ls -L` to verify objects exist
4. May need to clear browser cache when viewing HTML

---

## ✅ Migration Checklist

### Before Deployment
- [ ] Read this guide completely
- [ ] Review all modified files
- [ ] Test locally with `USE_GCS=false`
- [ ] Set up Google Cloud project
- [ ] Create Cloud Storage buckets
- [ ] Create service account
- [ ] Upload initial data to Cloud Storage
- [ ] Test with `USE_GCS=true` locally (optional)

### Deployment
- [ ] Build Docker image
- [ ] Test Docker image locally
- [ ] Deploy to Cloud Run
- [ ] Verify all endpoints work
- [ ] Test match submission
- [ ] Check Cloud Storage for new files
- [ ] Review Cloud Run logs

### Post-Deployment
- [ ] Share service URL with users
- [ ] Monitor logs and metrics
- [ ] Set up alerts (optional)
- [ ] Document any customizations
- [ ] Plan backup strategy

---

## 📊 Comparison: Local vs Cloud

| Feature | Local | Cloud |
|---------|-------|-------|
| **Setup** | Simple (2 commands) | More complex (GCP setup) |
| **Cost** | None | <$5/month typical |
| **Scaling** | Manual | Automatic |
| **Maintenance** | Your computer | Google managed |
| **Uptime** | Depends on your machine | 99.95% SLA |
| **Access** | Local network only | From anywhere |
| **Backup** | Manual | Handled by GCP |
| **Data Security** | Local storage | Encrypted in GCP |

---

## 🚀 Next Steps

1. **Understand the Changes** - Review the modified files
2. **Test Locally** - Verify app still works without GCS
3. **Set Up GCP** - Follow CLOUD_RUN_DEPLOYMENT.md
4. **Deploy** - Choose a deployment method
5. **Monitor** - Check logs and metrics
6. **Optimize** - Adjust resources based on usage

---

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Google Cloud Python Client Library](https://cloud.google.com/python/docs/reference/storage/latest)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Cloud Storage Pricing](https://cloud.google.com/storage/pricing)

---

## ❓ FAQ

### Q: Do I have to use Cloud Storage?
**A:** No! Set `USE_GCS=false` (default) and use local filesystem.

### Q: Can I switch between local and cloud?
**A:** Yes! Change the `USE_GCS` environment variable. Files stay on each backend.

### Q: Will my existing data be lost?
**A:** No! All existing local files remain. Upload them to Cloud Storage as needed.

### Q: How much will it cost?
**A:** Estimated <$5/month for typical usage. See pricing details in deployment guide.

### Q: Can I use a different cloud provider?
**A:** The code is written for Google Cloud Storage specifically, but could be adapted for AWS S3 or Azure Blob Storage.

### Q: What if I don't want to use the cloud?
**A:** No problem! Use the app exactly as before with local mode. All changes are backward compatible.

---

**Happy deploying!** 🚀

For step-by-step deployment instructions, see [CLOUD_RUN_DEPLOYMENT.md](./CLOUD_RUN_DEPLOYMENT.md).
