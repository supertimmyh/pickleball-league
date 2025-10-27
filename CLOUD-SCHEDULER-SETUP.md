# Cloud Scheduler Setup Guide

## Overview

This guide explains how to set up Google Cloud Scheduler to automatically regenerate rankings daily on Google Cloud Run. This prevents race conditions that can occur when multiple Cloud Run instances handle concurrent match submissions.

## Problem Solved

When running on Cloud Run with multiple instances:
- Two users might submit matches simultaneously
- Different Cloud Run instances could read rankings at the same time
- Race condition causes one match to be lost or rankings to be corrupted

## Solution Architecture

```
User submits match
       ↓
Flask server saves match to GCS
       ↓
Returns immediately (no ranking update)
       ↓
Cloud Scheduler (daily at 2 AM UTC)
       ↓
Calls endpoint to trigger ranking generation
       ↓
generate_rankings.py acquires lock
       ↓
Check for new matches since last generation
       ↓
If new matches: Generate rankings (only one process at a time)
If no new matches: Skip (efficient!)
       ↓
Release lock and done
```

## Setup Steps

### Step 1: Enable Cloud Scheduler API

```bash
gcloud services enable cloudscheduler.run.googleapis.com
```

### Step 2: Create a Service Account (for authentication)

```bash
# Create service account
gcloud iam service-accounts create pickleball-scheduler \
  --display-name="Pickleball League Scheduler"

# Grant Cloud Run invoker role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:pickleball-scheduler@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/run.invoker
```

Replace `PROJECT_ID` with your actual GCP project ID.

### Step 3: Create the Cloud Scheduler Job

#### Option A: Using gcloud CLI

```bash
gcloud scheduler jobs create http daily-ranking-update \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL/api/regenerate-rankings" \
  --http-method=POST \
  --oidc-service-account-email=pickleball-scheduler@PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience=https://YOUR_CLOUD_RUN_URL
```

Replace:
- `PROJECT_ID`: Your GCP project ID
- `YOUR_CLOUD_RUN_URL`: Your Cloud Run service URL (e.g., `https://pickleball-league-abc123-uc.a.run.app`)

#### Option B: Using Google Cloud Console

1. Go to [Cloud Scheduler](https://console.cloud.google.com/cloudscheduler)
2. Click **Create Job**
3. Fill in the form:
   - **Name:** `daily-ranking-update`
   - **Frequency:** `0 2 * * *` (Daily at 2 AM UTC)
   - **Timezone:** UTC
   - **Execution Timeout:** 600 seconds
4. Click **Continue**
5. Configure the execution:
   - **HTTP Method:** POST
   - **URI:** `https://YOUR_CLOUD_RUN_URL/api/regenerate-rankings`
   - **Auth header:** Add OIDC token
   - **Service account:** `pickleball-scheduler@PROJECT_ID.iam.gserviceaccount.com`
6. Click **Create**

### Step 4: Verify Setup

Test the job manually:

```bash
# List jobs
gcloud scheduler jobs list --location=us-central1

# Run job manually
gcloud scheduler jobs run daily-ranking-update --location=us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=pickleball-league" \
  --limit=50 --format=json
```

Or check logs in [Cloud Run Console](https://console.cloud.google.com/run):
1. Click your service
2. Go to **Logs** tab
3. Look for POST requests to `/api/regenerate-rankings`

## Scheduling Options

### Recommended: Daily at Off-Peak Time

```
0 2 * * *        # 2 AM UTC every day
0 3 * * *        # 3 AM UTC every day
```

### Alternative: Multiple Times Per Day

```
0 2,8,14,20 * * *    # 2 AM, 8 AM, 2 PM, 8 PM UTC
*/30 * * * *         # Every 30 minutes
0 * * * *           # Every hour
```

### Cron Format Reference

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

Use [crontab.guru](https://crontab.guru) to test schedules.

## How Ranking Generation Works Now

### Timeline

1. **User submits match**
   - Flask server saves match file to GCS
   - Returns immediately (fast response)
   - `regenerate_rankings()` function just logs and returns

2. **Cloud Scheduler trigger (at scheduled time)**
   - Calls `/api/regenerate-rankings` endpoint
   - Endpoint calls `generate_rankings.py`

3. **generate_rankings.py execution**
   - **Acquires lock** - Waits if another instance is running
   - **Checks timestamps:**
     - Newest match file timestamp
     - Last generation timestamp
   - **Decision:**
     - If `newest_match > last_generation`: Regenerate rankings
     - If `newest_match <= last_generation`: Skip (no new matches)
     - If no matches exist: Generate empty rankings
   - **Saves timestamp** - Records when generation happened
   - **Releases lock** - Allows other instances to run

### Key Benefits

✅ **No Race Conditions**
- Only one instance can generate rankings at a time (lock mechanism)
- Prevents file corruption and lost data

✅ **Efficient**
- Skips regeneration if no new matches (checks timestamps)
- Saves CPU and costs

✅ **Reliable**
- Retries automatically if lock is held
- 30-second timeout prevents deadlocks
- Comprehensive error logging

✅ **Decoupled**
- Match submission doesn't wait for ranking generation
- Faster user experience
- Better scalability

## Local Testing

Test the scheduler behavior locally:

```bash
# Test ranking generation with locking
python3 scripts/generate_rankings.py

# Test with existing timestamp (should skip)
python3 scripts/generate_rankings.py

# Manually trigger regeneration endpoint
curl -X POST http://localhost:8000/api/regenerate-rankings

# View logs
tail -f scheduled_update.log
```

## Monitoring

### Cloud Logging

View scheduler job execution logs:

```bash
# View recent Cloud Scheduler executions
gcloud scheduler jobs describe daily-ranking-update --location=us-central1 --format=json

# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND httpRequest.requestUrl=~'/api/regenerate-rankings'" \
  --limit=20 --format=table(timestamp,httpRequest.status)
```

### Cloud Run Console

1. Open [Cloud Run Console](https://console.cloud.google.com/run)
2. Click your service
3. Go to **Logs** tab
4. Filter by `/api/regenerate-rankings` or `/scheduled`

### Application Logs

Check `scheduled_update.log` in your Cloud Run service:

```bash
# If running locally
tail -f scheduled_update.log

# For GCS deployment
gsutil cat gs://pickleball-config-data/scheduled_update.log
```

## Troubleshooting

### Issue: Job not triggering

**Check:**
1. Job is enabled: `gcloud scheduler jobs describe daily-ranking-update --location=us-central1 | grep state`
2. Service account has correct permissions
3. Cloud Run URL is correct

**Fix:**
```bash
# Enable job if disabled
gcloud scheduler jobs resume daily-ranking-update --location=us-central1

# Update job with correct URL
gcloud scheduler jobs update http daily-ranking-update \
  --location=us-central1 \
  --uri="https://CORRECT_URL/api/regenerate-rankings"
```

### Issue: 403 Forbidden errors

**Cause:** Service account doesn't have Cloud Run invoker role

**Fix:**
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:pickleball-scheduler@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/run.invoker
```

### Issue: Timeouts (504 errors)

**Cause:** Ranking generation takes too long

**Check:**
1. Number of matches and complexity
2. Cloud Run memory allocation (increase if needed)
3. Timeout setting in scheduler job (should be 600+ seconds)

**Fix:**
```bash
# Increase timeout to 10 minutes
gcloud scheduler jobs update http daily-ranking-update \
  --location=us-central1 \
  --timeout=600s
```

### Issue: Rankings not updating

**Check:**
1. Look for "No new matches" message in logs
2. Verify new matches are being saved to GCS
3. Check `last_generation.timestamp` file exists

**Debug:**
```bash
# Manually trigger job to see detailed output
gcloud scheduler jobs run daily-ranking-update --location=us-central1

# Check execution log
gcloud logging read "labels.job_name=daily-ranking-update" --limit=1 --format=json
```

## Updating the Schedule

Change when rankings regenerate:

```bash
# Update schedule to 3 AM UTC instead of 2 AM
gcloud scheduler jobs update http daily-ranking-update \
  --location=us-central1 \
  --schedule="0 3 * * *"

# Verify change
gcloud scheduler jobs describe daily-ranking-update --location=us-central1
```

## Disabling/Pausing

Temporarily disable the scheduler:

```bash
# Pause job (won't run but can be resumed)
gcloud scheduler jobs pause daily-ranking-update --location=us-central1

# Resume job
gcloud scheduler jobs resume daily-ranking-update --location=us-central1

# Delete job (permanent)
gcloud scheduler jobs delete daily-ranking-update --location=us-central1
```

## Manual Triggering

For urgent ranking updates (outside scheduled time):

**Option 1: API Call**
```bash
curl -X POST https://YOUR_CLOUD_RUN_URL/api/regenerate-rankings \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json"
```

**Option 2: Run scheduled script locally**
```bash
./scheduled_ranking_update.sh
```

**Option 3: Cloud Scheduler manual run**
```bash
gcloud scheduler jobs run daily-ranking-update --location=us-central1
```

## Production Checklist

- [ ] Service account created: `pickleball-scheduler`
- [ ] Service account has `roles/run.invoker` role
- [ ] Cloud Scheduler job created: `daily-ranking-update`
- [ ] Schedule set to appropriate time (e.g., `0 2 * * *`)
- [ ] Cloud Run service URL is correct
- [ ] Test job ran successfully
- [ ] Logs are being recorded
- [ ] Monitoring alerts configured (optional)
- [ ] Admin knows how to manually trigger if needed
- [ ] Timeout is set to 600+ seconds

## Cost Implications

Cloud Scheduler pricing (as of 2024):
- **Free tier:** 3 jobs per month included
- **Paid:** ~$0.10 per job execution

Daily scheduler = ~30 executions/month = ~$3/month (minimal cost)

## Security Considerations

### Current (Local Development)

- ✅ No authentication required on `/api/regenerate-rankings`
- ✅ Safe for private networks only

### Production (Cloud Run)

For public deployment, add authentication:

```python
# In server.py, add to api_regenerate_rankings() function:
from flask import request

# Check authorization header (add your auth logic)
auth_header = request.headers.get('Authorization', '')
if not is_authorized(auth_header):
    return jsonify({"error": "Unauthorized"}), 401
```

Or use Cloud Run's built-in authentication (OIDC tokens) - already set up in the Cloud Scheduler configuration above.

## Next Steps

1. Complete the setup steps above
2. Test the scheduler job manually
3. Monitor logs for the first few days
4. Adjust schedule frequency if needed
5. Document any custom modifications

## References

- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cron Format](https://crontab.guru/)
- [Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
