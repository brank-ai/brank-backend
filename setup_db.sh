#!/bin/bash

# Exit on error
set -e

# Configuration
export PROJECT_ID="brank-484008"
export REGION="us-central1"
export INSTANCE_NAME="brank-db-instance"
export DB_NAME="brank_db"
export DB_USER="postgres"
export DB_PASS="postgres" # Change this for production!
export TIER="db-f1-micro" # Cheapest tier
export SERVICE_ACCOUNT="github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com"
export SERVICE_NAME="brank-backend"

echo "Setting up Cloud SQL for:"
echo "Project: $PROJECT_ID"
echo "Instance: $INSTANCE_NAME"
echo "Tier: $TIER"
echo ""

# 1. Enable APIs
echo "Enabling Cloud SQL Admin API..."
gcloud services enable sqladmin.googleapis.com --project=$PROJECT_ID

# 2. Create Instance
echo "Creating Cloud SQL instance (this will take 5-10 minutes)..."
if ! gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID >/dev/null 2>&1; then
    gcloud sql instances create $INSTANCE_NAME \
        --project=$PROJECT_ID \
        --database-version=POSTGRES_15 \
        --tier=$TIER \
        --region=$REGION \
        --storage-auto-increase \
        --root-password=$DB_PASS
else
    echo "Instance $INSTANCE_NAME already exists."
fi

# 3. Create Database
echo "Creating database '$DB_NAME'..."
if ! gcloud sql databases describe $DB_NAME --instance=$INSTANCE_NAME --project=$PROJECT_ID >/dev/null 2>&1; then
    gcloud sql databases create $DB_NAME --instance=$INSTANCE_NAME --project=$PROJECT_ID
else
    echo "Database $DB_NAME already exists."
fi

# 4. Create User (if specific user needed, otherwise using root 'postgres')
# Using the default 'postgres' user set during creation

# 5. Grant Access to Service Account
echo "Granting Cloud SQL Client role to Service Account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client" >/dev/null

# 6. Get Instance Connection Name
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID --format="value(connectionName)")
echo "Instance Connection Name: $INSTANCE_CONNECTION_NAME"

# 7. Update Cloud Run Service
echo "Updating Cloud Run service with Database Connection..."
# Construct DATABASE_URL for Cloud Run (Unix Socket)
# Format: postgresql+psycopg2://USER:PASS@/DB_NAME?host=/cloudsql/INSTANCE_CONNECTION_NAME
DATABASE_URL="postgresql+psycopg2://$DB_USER:$DB_PASS@/$DB_NAME?host=/cloudsql/$INSTANCE_CONNECTION_NAME"

gcloud run services update $SERVICE_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME \
    --set-env-vars="DATABASE_URL=$DATABASE_URL" \
    --quiet

echo ""
echo "--------------------------------------------------------"
echo "DATABASE SETUP & CONNECTION COMPLETE"
echo "--------------------------------------------------------"
echo "Your Cloud Run service '$SERVICE_NAME' is now connected to Cloud SQL."
