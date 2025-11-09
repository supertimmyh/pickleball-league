# Quick Reference - Cloud Migration

**TL;DR** - Get started quickly with key commands and code snippets.

---

## 🚀 Run Locally (Default)

```bash
# No setup needed - works exactly like before
pip3 install -r requirements-server.txt
python3 server.py

# Open http://localhost:8000
```

---

## 🌩️ Run with Cloud Storage (Local)

```bash
# Prerequisites: GCP setup and gcloud auth
export USE_GCS=true
export GOOGLE_CLOUD_PROJECT=your-project-id
export GCS_MATCHES_BUCKET=pickleball-matches-data
export GCS_CONFIG_BUCKET=pickleball-config-data

gcloud auth application-default login
python3 server.py
```

---

## ☁️ Deploy to Cloud Run

```bash
# Prerequisites: GCP project, buckets, service account

gcloud run deploy pickleball-app \
  --source=. \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars=USE_GCS=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GCS_MATCHES_BUCKET=pickleball-matches-data,GCS_CONFIG_BUCKET=pickleball-config-data
```

---

## 🐳 Docker Commands

```bash
# Build image
docker build -t pickleball-app:latest .

# Run locally (local mode)
docker run -p 8080:8080 -e USE_GCS=false pickleball-app:latest

# Run with Cloud Storage
docker run -p 8080:8080 \
  -e USE_GCS=true \
  -e GOOGLE_CLOUD_PROJECT=your-project \
  -e GCS_MATCHES_BUCKET=pickleball-matches-data \
  -e GCS_CONFIG_BUCKET=pickleball-config-data \
  pickleball-app:latest
```

---

## 📦 GCP Setup (Quick)

```bash
# Set project ID
export PROJECT_ID=pickleball-league-prod

# Create project
gcloud projects create $PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com storage-api.googleapis.com

# Create buckets
gsutil mb gs://pickleball-matches-data
gsutil mb gs://pickleball-config-data

# Create service account
gcloud iam service-accounts create pickleball-app

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin

# Upload data
gsutil -m cp -r matches/* gs://pickleball-matches-data/
gsutil cp players.csv config.json rankings.json index.html gs://pickleball-config-data/
```

---

## 📝 Environment Variables

```bash
# For local cloud testing
export USE_GCS=true
export GOOGLE_CLOUD_PROJECT=my-project-id
export GCS_MATCHES_BUCKET=pickleball-matches-data
export GCS_CONFIG_BUCKET=pickleball-config-data
export PORT=8000

# Or create .env file and source it
cp .env.example .env
nano .env
source .env
```

---

## 🧪 Testing Endpoints

```bash
# Get players list
curl http://localhost:8000/api/players

# Get rankings data
curl http://localhost:8000/rankings.json

# Get rankings page
curl http://localhost:8000/

# Get match form
curl http://localhost:8000/record

# Submit a match
curl -X POST http://localhost:8000/api/matches \
  -H "Content-Type: application/json" \
  -d '{
    "type": "singles",
    "date": "2025-10-23",
    "players": ["Player1", "Player2"],
    "games": [{"player1_score": 11, "player2_score": 9}],
    "winner": "Player1"
  }'

  # Regenerate Rankings
  curl -X POST http://localhost:8000/api/regenerate-rankings
```

---

## ☁️ Cloud Storage Commands

```bash
# List files
gsutil ls gs://pickleball-matches-data/
gsutil ls gs://pickleball-config-data/

# Upload files
gsutil cp matches/singles/*.yml gs://pickleball-matches-data/singles/
gsutil cp players.csv gs://pickleball-config-data/

# Upload static files (images, logos, etc.)
gsutil -m cp -r static/* gs://pickleball-config-data/static/

# Download files
gsutil cp gs://pickleball-config-data/rankings.json .

# View file content
gsutil cat gs://pickleball-config-data/rankings.json | head -20

# Delete files
gsutil rm gs://pickleball-matches-data/singles/2025-10-22-*.yml
```

---

## 🖼️ Static Files (Logo, Images)

```bash
# Upload all static files at once
gsutil -m cp -r static/* gs://pickleball-config-data/static/

# Upload specific file
gsutil cp static/picktopia_logo.png gs://pickleball-config-data/static/picktopia_logo.png

# Verify upload
gsutil ls gs://pickleball-config-data/static/

# Test access
curl https://storage.googleapis.com/pickleball-config-data/static/picktopia_logo.png -o /tmp/test.png

# View files in HTML
gsutil cat gs://pickleball-config-data/index.html | grep "picktopia_logo.png"
```

---

## 📊 Monitoring Commands

```bash
# View Cloud Run service
gcloud run services describe pickleball-app --region=us-central1

# View recent logs
gcloud run logs read pickleball-app --limit=50 --region=us-central1

# Stream logs
gcloud run logs read pickleball-app --region=us-central1 --follow

# View service URL
gcloud run services describe pickleball-app --region=us-central1 --format='value(status.url)'
```

---

## 🔑 Key Code Changes

### Enable Cloud Storage in server.py
```python
# Check if GCS is enabled
if USE_GCS:
    storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)

# Read from GCS
csv_data = read_file_from_gcs(GCS_CONFIG_BUCKET, 'players.csv')

# Write to GCS
write_file_to_gcs(GCS_MATCHES_BUCKET, 'singles/match.yml', content)
```

### In scripts/generate_rankings.py
```python
# Initialize with GCS
generator = RankingsGenerator(
    base_dir,
    use_gcs=True,
    gcs_project=PROJECT_ID,
    gcs_matches_bucket=BUCKET,
    gcs_config_bucket=CONFIG_BUCKET
)

# Generate rankings (automatically saves to GCS if enabled)
generator.generate_all_rankings()
```

---

## 🆘 Common Issues

### "Cannot import google.cloud.storage"
```bash
pip3 install google-cloud-storage
```

### "Permission denied" on Cloud Storage
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### "Bucket not found"
```bash
# Verify bucket exists
gsutil ls

# Create if missing
gsutil mb gs://pickleball-matches-data
gsutil mb gs://pickleball-config-data
```

### Application not finding files
```bash
# Check logs
gcloud run logs read pickleball-app

# Verify environment variables
gcloud run services describe pickleball-app --region=us-central1 | grep -A20 "env:"

# Test with local mode first
export USE_GCS=false
python3 server.py
```

---

## 📚 Full Documentation

- **MIGRATION_SUMMARY.md** - Overview of changes
- **CLOUD_MIGRATION_GUIDE.md** - Detailed guide to implementation
- **CLOUD_RUN_DEPLOYMENT.md** - Step-by-step deployment
- **google-app-migration-plan.md** - Original migration plan

---

## 🎯 Decision Tree

```
Do you want to:

├─ Use locally (no changes)?
│  └─ python3 server.py ✓
│
├─ Test cloud setup locally?
│  ├─ Set up GCP
│  ├─ export USE_GCS=true
│  └─ python3 server.py ✓
│
└─ Deploy to Cloud Run?
   ├─ Follow CLOUD_RUN_DEPLOYMENT.md
   └─ gcloud run deploy ... ✓
```

---

## 📋 Pre-Deployment Checklist

- [ ] Application runs locally with `USE_GCS=false`
- [ ] GCP project created
- [ ] Cloud Storage buckets created
- [ ] Service account created with permissions
- [ ] Data uploaded to Cloud Storage
- [ ] Static files (logo/images) uploaded to GCS
- [ ] Logo displays correctly on rankings and match form pages
- [ ] Environment variables configured
- [ ] Docker image builds: `docker build -t pickleball-app .`
- [ ] Docker container runs: `docker run -p 8080:8080 pickleball-app:latest`
- [ ] Cloud Run deploy command ready

---

## 🚀 One-Line Deployment

```bash
# Complete setup and deploy (if GCP is already configured)
gsutil mb gs://pickleball-matches-data && \
gsutil mb gs://pickleball-config-data && \
gsutil cp players.csv config.json rankings.json index.html gs://pickleball-config-data/ && \
gcloud run deploy pickleball-app --source=. --region=us-central1 --allow-unauthenticated --set-env-vars=USE_GCS=true,GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
```

---

## 💡 Tips

- **Local development:** Use `USE_GCS=false` (default)
- **Testing cloud:** Use `USE_GCS=true` locally with auth
- **Production:** Deploy Docker container to Cloud Run
- **Debugging:** Check logs with `gcloud run logs read pickleball-app`
- **Cost:** Cloud Run free tier covers typical usage
- **Backup:** Always backup Cloud Storage data regularly

---

**Need more detail?** See the full guides mentioned above.

**Last Updated:** October 23, 2025
