# Custom Pickleball League Deployment Guide

This guide provides instructions for deploying multiple, customized instances of the Pickleball League application, one for each of the following leagues:

1.  Launchpad Ladder League
2.  Club Ladder League
3.  Challenger Ladder League
4.  Pinnacle Ladder League
5.  Club Ladder League Afternoon

Each league will have its own dedicated Google Cloud Run service and Google Cloud Storage buckets to ensure data isolation.

## 1. Customizing the Application for Each League

The primary way to customize the application for a specific league is by modifying the `config.json` file. This file controls the league name, description, and other settings that are displayed on the web interface.

### 1.1. Create a Configuration File for Each League

You will need to create a separate `config.json` file for each league. Here are templates for each of the five leagues. You should save each of these as a separate file (e.g., `config-launchpad.json`, `config-club.json`, etc.)

**Launchpad Ladder League (`config-launchpad.json`)**
```json
{
  "league_name": "Launchpad Ladder League",
  "league_description": "The first step on the competitive ladder.",
  "ranking_methods": [
    "ELO Rating System",
    "Points Difference",
    "Win/Loss Record"
  ],
  "colors": {
    "primary": "#082946",
    "accent": "#e0672b"
  },
  "logo_path": "/static/picktopia_logo.png",
  "elo_k_factor": 32,
  "default_rating": 1200
}
```

**Club Ladder League (`config-club.json`)**
```json
{
  "league_name": "Club Ladder League",
  "league_description": "The main competitive league for club members.",
  "ranking_methods": [
    "ELO Rating System",
    "Points Difference",
    "Win/Loss Record"
  ],
  "colors": {
    "primary": "#082946",
    "accent": "#e0672b"
  },
  "logo_path": "/static/picktopia_logo.png",
  "elo_k_factor": 32,
  "default_rating": 1200
}
```

**Challenger Ladder League (`config-challenger.json`)**
```json
{
  "league_name": "Challenger Ladder League",
  "league_description": "For players aspiring to reach the top.",
  "ranking_methods": [
    "ELO Rating System",
    "Points Difference",
    "Win/Loss Record"
  ],
  "colors": {
    "primary": "#082946",
    "accent": "#e0672b"
  },
  "logo_path": "/static/picktopia_logo.png",
  "elo_k_factor": 32,
  "default_rating": 1200
}
```

**Pinnacle Ladder League (`config-pinnacle.json`)**
```json
{
  "league_name": "Pinnacle Ladder League",
  "league_description": "The highest level of competition.",
  "ranking_methods": [
    "ELO Rating System",
    "Points Difference",
    "Win/Loss Record"
  ],
  "colors": {
    "primary": "#082946",
    "accent": "#e0672b"
  },
  "logo_path": "/static/picktopia_logo.png",
  "elo_k_factor": 32,
  "default_rating": 1200
}
```

**Club Ladder League Afternoon (`config-club-afternoon.json`)**
```json
{
  "league_name": "Club Ladder League Afternoon",
  "league_description": "The afternoon session of the main competitive league.",
  "ranking_methods": [
    "ELO Rating System",
    "Points Difference",
    "Win/Loss Record"
  ],
  "colors": {
    "primary": "#082946",
    "accent": "#e0672b"
  },
  "logo_path": "/static/picktopia_logo.png",
  "elo_k_factor": 32,
  "default_rating": 1200
}
```

## 2. Deploying to Google Cloud Platform

The following steps will guide you through deploying each league\'s application to its own Cloud Run service.

## 2. Deploying to Google Cloud Platform (via Web Interface)

The following steps will guide you through deploying each league's application to its own Cloud Run service using the Google Cloud Console. You will repeat these steps for each of your five leagues.

**For each league, you will need to define the following unique identifiers:**

*   **`LEAGUE_SLUG`**: A kebab-case identifier for the league (e.g., `launchpad-ladder-league`, `club-ladder-league`).
*   **`LEAGUE_CONFIG_FILE`**: The name of the `config.json` file you created for this specific league (e.g., `config-launchpad.json`).
*   **`SERVICE_NAME`**: The name for your Cloud Run service (e.g., `pickleball-league-launchpad-ladder-league`).
*   **`MATCHES_BUCKET_NAME`**: The name for the GCS bucket storing match data (e.g., `pickleball-matches-launchpad-ladder-league`).
*   **`CONFIG_BUCKET_NAME`**: The name for the GCS bucket storing configuration and static files (e.g., `pickleball-config-launchpad-ladder-league`).
*   **`SERVICE_ACCOUNT_NAME`**: The name for the service account (e.g., `pickleball-app-launchpad-ladder-league`).

---

### Step 1: Create Google Cloud Project (One-time setup)

If you haven't already, create a Google Cloud Project.
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Click on the project selector dropdown at the top.
3.  Click "New Project" and follow the prompts. Note your `PROJECT_ID`.

### Step 2: Enable Required APIs (One-time setup)

Ensure the necessary APIs are enabled for your project.
1.  In the Cloud Console, navigate to **APIs & Services > Enabled APIs & Services**.
2.  Search for and enable the following APIs:
    *   `Cloud Run API`
    *   `Cloud Build API`
    *   `Cloud Storage API`
    *   `Container Registry API` (or `Artifact Registry API` if you prefer)

### Step 3: Create Cloud Storage Buckets for Each League

For each league, you will create two unique Cloud Storage buckets.

1.  In the Cloud Console, navigate to **Cloud Storage > Buckets**.
2.  Click **"CREATE BUCKET"**.
3.  **For the Matches Bucket:**
    *   **Name your bucket:** Enter a unique name like `pickleball-matches-<LEAGUE_SLUG>` (e.g., `pickleball-matches-launchpad-ladder-league`).
    *   Choose a region (e.g., `us-central1`).
    *   Choose a storage class (e.g., `Standard`).
    *   Choose "Fine-grained" for access control.
    *   Click **"CREATE"**.
4.  **For the Config Bucket:**
    *   Repeat the process, naming this bucket `pickleball-config-<LEAGUE_SLUG>` (e.g., `pickleball-config-launchpad-ladder-league`).
    *   Ensure it's in the same region and has the same settings as the matches bucket.
    *   Click **"CREATE"**.

### Step 4: Upload Initial Data to Cloud Storage for Each League

For each league, upload the necessary files to its dedicated config bucket.

1.  In the Cloud Console, navigate to **Cloud Storage > Buckets**.
2.  Click on the `pickleball-config-<LEAGUE_SLUG>` bucket you just created.
3.  **Upload `config.json`:**
    *   Click **"UPLOAD FILES"**.
    *   Select the `config-<LEAGUE_SLUG>.json` file from your local project directory.
    *   **Important:** In the "Upload files" dialog, click "Rename" next to the file and change its name to `config.json`.
    *   Click **"UPLOAD"**.
4.  **Upload other shared files:**
    *   Click **"UPLOAD FILES"** and select `players.csv`, `rankings.json`, and `index.html` from your local project directory.
    *   Click **"UPLOAD"**.
5.  **Upload `static` folder:**
    *   Click **"UPLOAD FOLDER"**.
    *   Select the `static` folder from your local project directory.
    *   Click **"UPLOAD"**.

### Step 5: Create Service Account for Each League

Create a dedicated service account for each league's Cloud Run service and grant it the necessary permissions.

1.  In the Cloud Console, navigate to **IAM & Admin > Service Accounts**.
2.  Click **"+ CREATE SERVICE ACCOUNT"**.
3.  **Service account details:**
    *   **Service account name:** Enter `pickleball-app-<LEAGUE_SLUG>` (e.g., `pickleball-app-launchpad-ladder-league`).
    *   **Service account ID:** This will be auto-generated.
    *   **Service account description:** Add a descriptive text like "Service account for Pickleball League App - [LEAGUE NAME]".
    *   Click **"CREATE AND CONTINUE"**.
4.  **Grant this service account access to project:**
    *   Click **"+ ADD ANOTHER ROLE"**.
    *   Search for and select `Storage Object Admin`.
    *   Click **"+ ADD ANOTHER ROLE"**.
    *   Search for and select `Logging Log Writer`.
    *   Click **"CONTINUE"**.
5.  **Grant users access to this service account:** (Optional, if you need other users to impersonate this SA)
    *   Click **"DONE"**.

### Step 6: Deploy to Cloud Run via Web Interface for Each League

Now, deploy the application for each league to Cloud Run.

1.  In the Cloud Console, navigate to **Cloud Run**.
2.  Click **"CREATE SERVICE"**.
3.  **Deployment platform:** Select "Cloud Run (fully managed)".
4.  **Source:**
    *   Select **"Deploy a revision from an existing container image"**.
    *   **Important:** Since you're deploying from source, you'll need to connect your repository to Cloud Build first. If you haven't done this, go to **Cloud Build > Triggers**, click **"CONNECT REPOSITORY"**, and follow the steps to connect your Git repository (e.g., GitHub, GitLab, Bitbucket).
    *   Once connected, select **"Continuously deploy new revisions from a source repository"**.
    *   Select your repository and branch (e.g., `main`).
    *   Ensure the "Build Type" is set to use the `Dockerfile` in your repository.
    *   Click **"SAVE"**.
5.  **Service settings:**
    *   **Service name:** Enter `pickleball-league-<LEAGUE_SLUG>` (e.g., `pickleball-league-launchpad-ladder-league`).
    *   **Region:** Select the same region you used for your GCS buckets (e.g., `us-central1`).
6.  **Authentication:**
    *   Select **"Allow unauthenticated invocations"**.
7.  **Container(s), volumes, networking, security:**
    *   Expand this section.
    *   **Container** tab:
        *   Set **Memory** to `512Mi`.
        *   Set **CPU** to `1`.
        *   Set **Concurrency** to `50`.
    *   **Variables & Secrets** tab:
        *   Click **"ADD VARIABLE"** and add the following environment variables:
            *   `USE_GCS`: `true`
            *   `GOOGLE_CLOUD_PROJECT`: Your Google Cloud `PROJECT_ID`
            *   `GCS_MATCHES_BUCKET`: `pickleball-matches-<LEAGUE_SLUG>` (e.g., `pickleball-matches-launchpad-ladder-league`)
            *   `GCS_CONFIG_BUCKET`: `pickleball-config-<LEAGUE_SLUG>` (e.g., `pickleball-config-launchpad-ladder-league`)
    *   **Security** tab:
        *   Under "Service account", select the service account you created for this league (e.g., `pickleball-app-launchpad-ladder-league`).
8.  Click **"CREATE"**.

After the deployment is complete, Cloud Run will provide you with a URL for your new service. Repeat these steps for each of your remaining leagues.
