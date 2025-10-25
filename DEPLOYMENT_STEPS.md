# Deployment Steps for Project: pickleball-league

This document outlines the necessary steps to configure your Google Cloud project for deploying the Pickleball League application.

**Project ID:** `pickleball-league`

---

### Pre-flight Check

Make sure you have created the project and have the necessary permissions to execute these commands.

First, set your project ID in your local environment and `gcloud` configuration:

```bash
export PROJECT_ID="pickleball-league"
gcloud config set project $PROJECT_ID
```

---

### 1. Enable Required APIs

You'll need to enable the following APIs for your project:

```bash
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com storage-api.googleapis.com
```

---

### 2. Create Cloud Storage Buckets

Two buckets are needed for your application's data and configuration:

```bash
gsutil mb -p $PROJECT_ID gs://pickleball-matches-data
gsutil mb -p $PROJECT_ID gs://pickleball-config-data
```

---

### 3. Create Service Account

A dedicated service account for the application is recommended:

```bash
gcloud iam service-accounts create pickleball-app --display-name="Pickleball League Application"
```

---

### 4. Grant Permissions

The service account needs permissions to access Cloud Storage and write logs:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com --role=roles/storage.objectAdmin
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:pickleball-app@$PROJECT_ID.iam.gserviceaccount.com --role=roles/logging.logWriter
```

---

### 5. Upload Initial Data

You'll need to upload your existing data to the newly created buckets:

```bash
gsutil -m cp -r matches/* gs://pickleball-matches-data/
gsutil cp players.csv gs://pickleball-config-data/
gsutil cp config.json gs://pickleball-config-data/
gsutil cp rankings.json gs://pickleball-config-data/
gsutil cp index.html gs://pickleball-config-data/
gsutil -m cp -r static/* gs://pickleball-config-data/static/
```

---

Once you have completed these steps, you will be ready to deploy the application to Cloud Run.
