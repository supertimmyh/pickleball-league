#!/bin/bash
#
# Scheduled Ranking Update Script for Cloud Scheduler
#
# This script is meant to be run by Cloud Scheduler at regular intervals.
# It handles ranking generation with proper locking to prevent race conditions
# in multi-instance Cloud Run environments.
#
# Usage:
#   ./scheduled_ranking_update.sh
#
# Environment Variables (set via Cloud Scheduler or Cloud Run config):
#   USE_GCS - Set to "true" for Google Cloud Storage backend
#   GOOGLE_CLOUD_PROJECT - GCP project ID
#   GCS_MATCHES_BUCKET - GCS bucket for match files
#   GCS_CONFIG_BUCKET - GCS bucket for config files
#

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/scripts/generate_rankings.py"
BUILD_SCRIPT="${SCRIPT_DIR}/scripts/build_pages.py"

# Logging
LOG_FILE="${SCRIPT_DIR}/scheduled_update.log"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $1" | tee -a "${LOG_FILE}"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[${timestamp}] ERROR: $1${NC}" | tee -a "${LOG_FILE}"
}

log_success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[${timestamp}] SUCCESS: $1${NC}" | tee -a "${LOG_FILE}"
}

# Main execution
log "Starting scheduled ranking update..."

# Check if Python script exists
if [ ! -f "${PYTHON_SCRIPT}" ]; then
    log_error "Python script not found: ${PYTHON_SCRIPT}"
    exit 1
fi

# Export environment variables for the Python script
export USE_GCS="${USE_GCS:-false}"
if [ "${USE_GCS}" = "true" ]; then
    export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT}"
    export GCS_MATCHES_BUCKET="${GCS_MATCHES_BUCKET:-pickleball-matches-data}"
    export GCS_CONFIG_BUCKET="${GCS_CONFIG_BUCKET:-pickleball-config-data}"
fi

log "Configuration:"
log "  USE_GCS: ${USE_GCS}"
log "  Python Script: ${PYTHON_SCRIPT}"
log "  Build Script: ${BUILD_SCRIPT}"

# Run ranking generation with error handling
log "Running ranking generation..."
if python3 "${PYTHON_SCRIPT}"; then
    log "✓ Ranking generation completed"
else
    log_error "Ranking generation failed with exit code $?"
    exit 1
fi

# Run page building
log "Running page building..."
if python3 "${BUILD_SCRIPT}"; then
    log "✓ Page building completed"
else
    log_error "Page building failed with exit code $?"
    exit 1
fi

log_success "Scheduled ranking update completed successfully"
exit 0
