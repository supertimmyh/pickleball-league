# GCP Setup Summary

This document summarizes the Google Cloud project setup for testing the pickleball league application.

## 1. Google Cloud Project Created

A new Google Cloud project was created using the web interface:

- **Project Name:** `Pickleball League Test`
- **Project ID:** `pickleball-league-test`

## 2. Enabled APIs

The following APIs were enabled in the project:

- Cloud Run Admin API
- Google Container Registry API
- Cloud Build API
- Cloud Storage API

## 3. Cloud Storage Buckets

Two Cloud Storage buckets were created for test data, with public access prevention enforced:

- `pickleball-matches-data-test`
- `pickleball-config-data-test`

## 4. Service Account

A service account was created to allow the application to interact with GCP services securely:

- **Service Account Name:** `pickleball-app`
- **Roles Granted:**
    - `Storage Object Admin`
    - `Logs Writer`

## 5. Data Upload

Initial data from the local project directory was uploaded to the Cloud Storage buckets using the web interface:

- The contents of the `matches/` folder were uploaded to `pickleball-matches-data-test`.
- `players.csv`, `config.json`, `rankings.json`, and `index.html` were uploaded to `pickleball-config-data-test`.

## Next Steps

After restarting the terminal session, the next step is to authenticate the local environment by running `gcloud auth application-default login` to proceed with testing the application against the live GCP backend.
