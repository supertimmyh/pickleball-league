# Google Cloud Run Deployment Guide

**Last Updated:** October 26, 2025
**Status:** Consolidated Guide
**Target Platform:** Google Cloud Run + Google Cloud Storage

---

## 🎯 Overview

This guide provides comprehensive instructions for deploying the Pickleball League application to Google Cloud Run, using Google Cloud Storage for data persistence. It covers everything from initial setup to deployment, verification, and maintenance.

The application is designed with a dual-backend architecture, allowing it to run in two modes:
-   **Local Mode (default):** Uses the local filesystem for all data.
-   **Cloud Mode (`USE_GCS=true`):** Uses Google Cloud Storage for data.

This guide focuses on deploying the application in **Cloud Mode**.

---

## 🏗️ Architecture

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

## 📋 Prerequisites

1.  **Google Cloud Account:** An active account with billing enabled.
2.  **gcloud CLI:** The Google Cloud command-line interface. Install from [here](https://cloud.google.com/sdk/docs/install).
3.  **Docker:** (Optional) For building and testing container images locally.
4.  **Git:** For version control.

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

This section provides a complete walkthrough from project setup to a running application on Cloud Run.

### Step 1: Create Google Cloud Project (5 mins)

```bash
# Set your desired project ID and name
export PROJECT_ID="pickleball-league-prod"
PROJECT_NAME="Pickleball League"

# Create the project
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"

# Set it as default for gcloud
gcloud config set project $PROJECT_ID

# Verify
gcloud config get-value project
```

### Step 2: Enable Required APIs (3 mins)

```bash
# Enable APIs for Cloud Run, Container Registry, Cloud Build, and Cloud Storage
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com storage-api.googleapis.com

# Verify all APIs are enabled
gcloud services list --enabled | grep -E "(run|container|build|storage)"
```

### Step 3: Create Cloud Storage Buckets (2 mins)

Two buckets are needed for your application\'s data and configuration:

```bash
# Create matches data bucket
gsutil mb -p $PROJECT_ID gs://pickleball-matches-data

# Create configuration bucket
gsutil mb -p $PROJECT_ID gs://pickleball-config-data

# Verify buckets were created
gsutil ls
```

### Step 4: Create Service Account (3 mins)

A dedicated service account for the application is recommended for security.

```bash
# Create service account
gcloud iam service-accounts create pickleball-app --display-name="Pickleball League Application"

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

You\'ll need to upload your existing data to the newly created buckets.

```bash
# Navigate to your local project directory
cd /path/to/pickleball-league

# Upload matches (if any exist)
gsutil -m cp -r matches/* gs://pickleball-matches-data/

# Upload configuration and static files
gsutil cp players.csv gs://pickleball-config-data/
gsutil cp config.json gs://pickleball-config-data/
gsutil cp rankings.json gs://pickleball-config-data/
gsutil cp index.html gs://pickleball-config-data/
gsutil -m cp -r static/* gs://pickleball-config-data/static/

# Verify uploads
gsutil ls gs://pickleball-matches-data/
gsutil ls gs://pickleball-config-data/
```

### Step 6: Deploy to Cloud Run (5-10 mins)

You can deploy using the command line or the web interface.

#### Option A: Direct Deployment via Command Line (Recommended)

This command builds and deploys your application in one step.

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
```

#### Option B: Deployment via Web Interface

1.  **Navigate to Cloud Run:**
    *   Open the [Google Cloud Console](https://console.cloud.google.com).
    *   In the navigation menu, select **Cloud Run**.

2.  **Create Service:**
    *   Click the **Create Service** button.
    *   Select **Cloud Run (fully managed)**.

3.  **Source:**
    *   Select **Continuously deploy new revisions from a source repository**.
    *   Click **Set up with Cloud Build**, connect your repository, and select the branch (e.g., `main`).
    *   Ensure the "Build Type" is set to use the `Dockerfile` in your repository.
    *   Click **Save**.

4.  **Service Settings:**
    *   **Service name:** `pickleball-app`
    *   **Region:** `us-central1`

5.  **Authentication:**
    *   Select **Allow unauthenticated invocations**.

6.  **Container(s), volumes, networking, security:**
    *   Expand this section.
    *   **Container** tab: Set Memory to `512Mi`, CPU to `1`, and Concurrency to `50`.
    *   **Variables & Secrets** tab: Add the environment variables listed in the **Configuration** section below.
    *   **Security** tab: Select the `pickleball-app` service account.

7.  **Deploy:**
    *   Click the **Create** button.

---

## 🧪 Post-Deployment Verification

After deployment, test the application to ensure it\'s working correctly.

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe pickleball-app --region=us-central1 --format='value(status.url)')
echo "Service URL: $SERVICE_URL"

# Test endpoints
curl $SERVICE_URL/
curl $SERVICE_URL/api/players
curl $SERVICE_URL/record

# Test match submission
curl -X POST $SERVICE_URL/api/matches \
  -H "Content-Type: application/json" \
  -d \
'{
    "type": "singles",
    "date": "2025-10-26",
    "players": ["Alice Johnson", "Bob Smith"],
    "games": [{"player1_score": 11, "player2_score": 7}],
    "winner": "Alice Johnson"
  }'

# Verify data in Cloud Storage
gsutil ls gs://pickleball-matches-data/singles/
```

---

## 📊 Configuration

### Environment Variables

These are critical for running the application in Cloud Mode.

| Variable | Default | Purpose |
|---|---|---|
| `USE_GCS` | `false` | Must be `true` to enable Cloud Storage backend. |
| `GOOGLE_CLOUD_PROJECT`| None | Your GCP project ID. |
| `GCS_MATCHES_BUCKET`| `pickleball-matches-data` | Bucket for match YAML files. |
| `GCS_CONFIG_BUCKET` | `pickleball-config-data` | Bucket for config and static files. |
| `PORT` | `8080` | Server port (set automatically by Cloud Run). |
| `FLASK_ENV` | `production` | Flask environment. |

---

## 📝 Code Changes for Cloud Migration

This section details the modifications made to the codebase to support Google Cloud.

### 1. **server.py** - Flask Backend
-   Added Google Cloud Storage client initialization.
-   Added `read_file_from_gcs()` and `write_file_to_gcs()` helper functions.
-   Updated all file I/O operations to use these helpers when `USE_GCS` is true.
-   Added `PORT` environment variable support for Cloud Run.

### 2. **scripts/generate_rankings.py** - Ranking Generator
-   Added GCS support to the `RankingsGenerator` class.
-   The script now lists, reads, and writes files to/from GCS buckets when `USE_GCS` is true.

### 3. **scripts/build_pages.py** - HTML Generator
-   Updated to read `config.json` from GCS and write the generated `index.html` to GCS when `USE_GCS` is true.

### 4. **requirements-server.txt** - Dependencies
-   Added `google-cloud-storage>=2.10.0` and `gunicorn>=21.0.0`.

### 5. **New Files**
-   `.env.example`: Template for environment variables.
-   `Dockerfile`: Container configuration for Cloud Run.
-   `.dockerignore`: Files to exclude from the Docker image.
-   `cloudbuild.yaml`: Cloud Build CI/CD configuration.

---

## 🆘 Troubleshooting

### "Cannot connect to Cloud Storage" or "Permission denied"
1.  Verify `USE_GCS=true` is set in your Cloud Run service\'s environment variables.
2.  Verify `GOOGLE_CLOUD_PROJECT` is correct.
3.  Ensure the service account (`pickleball-app@...`) has the `Storage Object Admin` role.
4.  Verify the bucket names in the environment variables are correct.

### Service Won\'t Start
-   Check the logs in the Cloud Run console for errors.
-   Common issues include missing environment variables or incorrect service account permissions.

### Static Files (Logo) Not Displaying
-   Verify the `static` folder and its contents were uploaded to the `pickleball-config-data` bucket.
-   Check the `GCS_CONFIG_BUCKET` environment variable is set correctly.
-   Ensure the service account has permissions to read from the bucket.

---

## 💰 Cost Optimization

-   **Memory:** `512Mi` (suitable for this app)
-   **CPU:** `1`
-   **Min instances:** `0` (auto-scales to zero, saving costs when idle)
-   **Estimated Cost:** Typically **< $5/month**, falling mostly within the free tier.

---

## 🔄 Continuous Deployment (CI/CD)

For automatic deployments on `git push`:

```bash
# Connect Cloud Build to your repository
gcloud builds connect --region=us-central1

# On every push to your main branch, Cloud Build will now:
# 1. Build the Docker image using the Dockerfile.
# 2. Push the image to the Container Registry.
# 3. Deploy the new revision to Cloud Run.
```

---

## 🛑 Cleanup

To avoid ongoing charges, you can delete the created resources.

```bash
# Delete the Cloud Run service
gcloud run services delete pickleball-app --region=us-central1

# Delete the Cloud Storage buckets (WARNING: This is permanent!)
gsutil -m rm -r gs://pickleball-matches-data
gsutil -m rm -r gs://pickleball-config-data

# Delete the Cloud Project
gcloud projects delete $PROJECT_ID
```