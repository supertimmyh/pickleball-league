# Google Cloud Run Deployment Guide

**Last Updated:** October 23, 2025
**Status:** Ready for Deployment
**Target Platform:** Google Cloud Run + Google Cloud Storage

---

## 📋 Quick Start

### Prerequisites

1. **Google Cloud Account** - Active account with billing enabled
2. **gcloud CLI** - Install from https://cloud.google.com/sdk/docs/install
3. **Docker** (optional) - For local testing before deployment
4. **Git** - For version control

### Verify Prerequisites

```bash
# Check gcloud is installed
gcloud --version

# Check Docker (optional)
docker --version

# Verify git
git --version
```

---

## 🚀 Deployment Steps

### Step 1: Create Google Cloud Project (5 mins)

```bash
# Set your desired project ID and name
PROJECT_ID="pickleball-league-prod"
PROJECT_NAME="Pickleball League"

# Create the project
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"

# Set it as default
gcloud config set project $PROJECT_ID

# Verify
gcloud config get-value project
```

### Step 2: Enable Required APIs (3 mins)

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com

# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage-api.googleapis.com

# Verify all APIs are enabled
gcloud services list --enabled | grep -E "(run|container|build|storage)"
```

### Step 3: Create Cloud Storage Buckets (2 mins)

```bash
# Create matches data bucket
gsutil mb -p $PROJECT_ID gs://pickleball-matches-data

# Create configuration bucket
gsutil mb -p $PROJECT_ID gs://pickleball-config-data

# Verify buckets were created
gsutil ls
```

### Step 4: Create Service Account (3 mins)

```bash
# Create service account
gcloud iam service-accounts create pickleball-app \
  --display-name="Pickleball League Application"

# Grant Cloud Storage permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin

# Grant Cloud Logging permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/logging.logWriter

# Verify service account
gcloud iam service-accounts list
```

### Step 5: Upload Initial Data to Cloud Storage (2 mins)

```bash
# Navigate to project directory
cd /path/to/pickleball-league

# Upload matches (if any existing matches)
gsutil -m cp -r matches/* gs://pickleball-matches-data/

# Upload configuration files
gsutil cp players.csv gs://pickleball-config-data/
gsutil cp config.json gs://pickleball-config-data/
gsutil cp rankings.json gs://pickleball-config-data/
gsutil cp index.html gs://pickleball-config-data/

# Verify uploads
gsutil ls gs://pickleball-matches-data/
gsutil ls gs://pickleball-config-data/
```

### Step 6: Deploy to Cloud Run (5-10 mins)

#### Option A: Direct Deployment (Recommended for first deployment)

```bash
# Build and deploy in one command
gcloud run deploy pickleball-app \
  --source=. \
  --platform=managed \
  --region=us-central1 \
  --memory=512Mi \
  --cpu=1 \
  --concurrency=50 \
  --service-account=pickleball-app@$PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --set-env-vars=USE_GCS=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GCS_MATCHES_BUCKET=pickleball-matches-data,GCS_CONFIG_BUCKET=pickleball-config-data

# You'll be prompted to create a Cloud Build service account - allow it
```

#### Option B: Using Cloud Build (For CI/CD)

```bash
# Connect Cloud Build to your repository
gcloud builds connect --region=us-central1

# Manually trigger a build
gcloud builds submit --config cloudbuild.yaml
```

### Step 7: Verify Deployment (5 mins)

```bash
# Get the service URL
gcloud run services describe pickleball-app --region=us-central1

# Test the application
SERVICE_URL=$(gcloud run services describe pickleball-app \
  --region=us-central1 --format='value(status.url)')

echo "Service URL: $SERVICE_URL"

# Test endpoints
curl $SERVICE_URL/
curl $SERVICE_URL/api/players
curl $SERVICE_URL/record
```

---

## 🧪 Testing After Deployment

### 1. Test Rankings Page

```bash
# Visit in browser or curl
curl https://pickleball-app-xxxxx.run.app/

# Should return HTML with rankings
```

### 2. Test Match Form

```bash
curl https://pickleball-app-xxxxx.run.app/record

# Should return match form HTML
```

### 3. Test Players API

```bash
curl https://pickleball-app-xxxxx.run.app/api/players

# Should return JSON list of players from Cloud Storage
```

### 4. Test Match Submission

```bash
curl -X POST https://pickleball-app-xxxxx.run.app/api/matches \
  -H "Content-Type: application/json" \
  -d '{
    "type": "singles",
    "date": "2025-10-23",
    "players": ["Alice Johnson", "Bob Smith"],
    "games": [
      {"player1_score": 11, "player2_score": 7},
      {"player1_score": 9, "player2_score": 11},
      {"player1_score": 11, "player2_score": 5}
    ],
    "winner": "Alice Johnson"
  }'

# Should return success message
```

### 5. Verify Data in Cloud Storage

```bash
# Check new match file was created
gsutil ls gs://pickleball-matches-data/singles/

# Check rankings were updated
gsutil cat gs://pickleball-config-data/rankings.json | head -20

# Download and view the generated HTML
gsutil cp gs://pickleball-config-data/index.html /tmp/index.html
open /tmp/index.html  # On macOS
```

### 6. Check Cloud Run Logs

```bash
# View recent logs
gcloud run logs read pickleball-app --limit=50 --region=us-central1

# Stream logs in real-time
gcloud run logs read pickleball-app --region=us-central1 --follow
```

---

## 📊 Configuration

### Environment Variables

The following environment variables are available:

| Variable | Default | Purpose |
|----------|---------|---------|
| `USE_GCS` | `false` | Enable/disable Cloud Storage backend |
| `GOOGLE_CLOUD_PROJECT` | None | GCP project ID |
| `GCS_MATCHES_BUCKET` | `pickleball-matches-data` | Bucket for match YAML files |
| `GCS_CONFIG_BUCKET` | `pickleball-config-data` | Bucket for config files |
| `PORT` | `8080` | Server port (set by Cloud Run) |
| `FLASK_ENV` | `production` | Flask environment |

### Update Environment Variables

```bash
gcloud run services update pickleball-app \
  --update-env-vars=GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --region=us-central1
```

### View Current Configuration

```bash
gcloud run services describe pickleball-app --region=us-central1
```

---

## 🔒 Security Considerations

### Current Setup
- ✅ Service account with minimal permissions (Cloud Storage only)
- ✅ Data encrypted at rest and in transit
- ✅ HTTPS enforced by Cloud Run
- ✅ Public endpoint (good for league members)

### To Add Authentication
If you want to restrict access to match submission:

```bash
# Remove --allow-unauthenticated
gcloud run deploy pickleball-app \
  --no-allow-unauthenticated \
  --region=us-central1

# Users will need Google Cloud authentication to access
```

---

## 💰 Cost Optimization

### Current Configuration
- **Memory:** 512Mi (suitable for this app)
- **CPU:** 1
- **Min instances:** 0 (auto-scales, saves cost)
- **Max instances:** 10

### Estimated Costs

```
Cloud Run:
  - ~$0.0000667 per CPU-second
  - ~$0.0000042 per memory-GB-second
  - Free tier: 2M invocations/month, 360,000 GB-seconds/month

Cloud Storage:
  - ~$0.023/GB/month for storage
  - $0.005 per 10,000 write operations
  - $0.0004 per 10,000 read operations

Estimated monthly cost for typical usage: <$5
```

### Cost Saving Tips

1. Delete old match files periodically
2. Set Cloud Storage object lifecycle policies
3. Monitor usage with Cloud Monitoring

---

## 🔄 Continuous Deployment

### Automatic Deployment on Git Push

```bash
# Create Cloud Build trigger
gcloud builds connect --region=us-central1

# This connects your GitHub/GitLab repository to Cloud Build
# On every push to main, Cloud Build will:
# 1. Build the Docker image
# 2. Push to Container Registry
# 3. Deploy to Cloud Run
```

### Manual Deployment

```bash
# After making code changes
git add .
git commit -m "Update app functionality"
git push origin main

# Or manually trigger
gcloud builds submit --config cloudbuild.yaml
```

---

## 🆘 Troubleshooting

### Service Won't Start

Check logs for errors:
```bash
gcloud run logs read pickleball-app --limit=100 --region=us-central1
```

Common issues:
- Missing environment variables
- Service account permissions
- Cloud Storage bucket doesn't exist

### Permission Denied on Cloud Storage

```bash
# Re-grant permissions to service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### Container Build Fails

```bash
# Check build logs
gcloud builds log <BUILD_ID>

# Rebuild with verbose output
gcloud builds submit --config cloudbuild.yaml --no-cache
```

### Slow Response Times

- Check Cloud Run metrics
- Verify Cloud Storage bucket is in same region
- Increase memory allocation
- Check YAML file count (large number may slow rankings generation)

---

## 📈 Monitoring

### Set Up Monitoring

```bash
# View Cloud Run metrics
gcloud monitoring metrics-descriptors list --filter="resource.type:cloud_run_revision"

# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="Cloud Run Error Rate Alert"
```

### Key Metrics to Monitor

1. **Request count** - Total API requests
2. **Error rate** - Failed requests
3. **Latency** - Response times
4. **Concurrency** - Simultaneous requests
5. **Cloud Storage operations** - Read/write success

---

## 🔄 Update and Rollback

### Deploy New Version

```bash
# After making code changes
git add .
git commit -m "Feature: Add new feature"
git push origin main

# Cloud Build will automatically deploy (if connected)
# Or manually deploy:
gcloud run deploy pickleball-app \
  --source=. \
  --region=us-central1
```

### Rollback to Previous Version

```bash
# View revision history
gcloud run revisions list --region=us-central1

# Promote previous revision
gcloud run services update-traffic pickleball-app \
  --to-revisions=REVISION_ID=100 \
  --region=us-central1
```

### Backup Cloud Storage Data

```bash
# Create backup bucket
gsutil mb gs://pickleball-backup

# Copy data
gsutil -m cp -r gs://pickleball-matches-data/* gs://pickleball-backup/matches/
gsutil -m cp -r gs://pickleball-config-data/* gs://pickleball-backup/config/

# Verify backup
gsutil ls gs://pickleball-backup/
```

---

## 🛑 Stopping and Cleanup

### Pause the Service

```bash
# Set to 0 minimum instances (no cost when idle)
gcloud run services update pickleball-app \
  --min-instances=0 \
  --region=us-central1

# Or delete the service entirely
gcloud run services delete pickleball-app --region=us-central1
```

### Delete Cloud Storage Buckets

```bash
# Delete buckets (WARNING: This is permanent!)
gsutil -m rm -r gs://pickleball-matches-data
gsutil -m rm -r gs://pickleball-config-data

# Delete backup bucket
gsutil -m rm -r gs://pickleball-backup
```

### Delete Cloud Project

```bash
gcloud projects delete $PROJECT_ID
```

---

## 🖼️ Static Files (Images, Logos, etc.)

### Overview

The application uses **GCS-based static file serving** in production. Static files (like the league logo) are stored in Google Cloud Storage and served directly from the `/static/` route.

### Setup Static Files

#### 1. Prepare Your Static Files

Your static files should include the league logo. Example structure:
```
static/
├── picktopia_logo.png        # League logo (or your custom logo)
└── [other static files]
```

#### 2. Upload Static Files to GCS

Upload static files to the `pickleball-config-data` bucket:

```bash
# Set your bucket name
GCS_CONFIG_BUCKET="pickleball-config-data"

# Upload all static files
gsutil -m cp -r static/* gs://$GCS_CONFIG_BUCKET/static/

# Verify upload
gsutil ls gs://$GCS_CONFIG_BUCKET/static/
```

Or upload individual files:

```bash
# Upload just the logo
gsutil cp static/picktopia_logo.png gs://$GCS_CONFIG_BUCKET/static/picktopia_logo.png

# Verify
gsutil cat gs://$GCS_CONFIG_BUCKET/static/picktopia_logo.png > /tmp/logo.png
open /tmp/logo.png  # Verify it's correct
```

#### 3. How Static Files Are Served

When `USE_GCS=true`:
- Browser requests `/static/picktopia_logo.png`
- Flask server fetches from `gs://pickleball-config-data/static/picktopia_logo.png`
- File is returned with correct MIME type (image/png, etc.)

When `USE_GCS=false` (local development):
- Files are served from the local `static/` directory
- No GCS access required

#### 4. Update Logo in Your Pages

The logo is referenced in:
- `index.html` - Displays on rankings page
- `match-form.html` - Displays on match recording form
- Both use: `<img src="/static/picktopia_logo.png" alt="League Logo">`

The `scripts/build_pages.py` automatically includes this image reference when generating `index.html`.

#### 5. Supported Static File Types

Any file type can be served (with automatic MIME type detection):
- Images: `.png`, `.jpg`, `.gif`, `.svg`
- Stylesheets: `.css`
- Scripts: `.js`
- Fonts: `.woff`, `.woff2`, `.ttf`
- Documents: `.pdf`, `.txt`

#### 6. Troubleshooting Static Files

**Logo not displaying on rankings page?**

```bash
# Verify file exists in GCS
gsutil ls gs://pickleball-config-data/static/picktopia_logo.png

# Check permissions
gsutil acl ch -u AllUsers:R gs://pickleball-config-data/static/picktopia_logo.png

# Test direct download
curl https://storage.googleapis.com/pickleball-config-data/static/picktopia_logo.png \
  -o /tmp/test-logo.png

# Verify index.html contains the img tag
gsutil cat gs://pickleball-config-data/index.html | grep "picktopia_logo.png"
```

**Static files working locally but not on Cloud Run?**

1. Verify files are uploaded to GCS
2. Check `GCS_CONFIG_BUCKET` environment variable is set
3. Verify service account has `storage.objects.get` permission
4. Check Cloud Run logs: `gcloud run logs read pickleball-app`

---

## 📚 Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)

---

## ✅ Deployment Checklist

- [ ] Google Cloud project created
- [ ] Billing enabled
- [ ] Required APIs enabled
- [ ] Cloud Storage buckets created
- [ ] Service account created with permissions
- [ ] Initial data uploaded to Cloud Storage
- [ ] Static files uploaded to GCS (logo, images, etc.)
- [ ] Application deployed to Cloud Run
- [ ] Environment variables configured
- [ ] Tested rankings page
- [ ] Tested match form (with logo displaying)
- [ ] Tested match submission
- [ ] Verified data in Cloud Storage
- [ ] Verified static files serving from GCS
- [ ] Reviewed Cloud Run logs
- [ ] Set up monitoring/alerts (optional)
- [ ] Configured CI/CD with Cloud Build (optional)
- [ ] Tested from multiple devices
- [ ] Documented service URL for team

---

## 🎯 Next Steps

1. **Share Service URL** - Distribute to league members
2. **Monitor Usage** - Check logs and metrics regularly
3. **Optimize** - Adjust resource allocation based on usage
4. **Enhance** - Consider adding features from roadmap
5. **Scale** - Increase concurrency limits if needed

---

## 📞 Support

For issues with your Cloud Run deployment:

1. Check Cloud Run logs: `gcloud run logs read pickleball-app`
2. Review this guide's troubleshooting section
3. Check [Cloud Run Documentation](https://cloud.google.com/run/docs)
4. Use Google Cloud Console for visual debugging

For issues with your application code:

1. Check application error messages in logs
2. Review code changes in git history
3. Test locally: `USE_GCS=false python3 server.py`

---

**Congratulations!** Your pickleball league app is now running on Google Cloud Run! 🎉
