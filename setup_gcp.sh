#!/bin/bash

# Exit on error
set -e

# 1. Set Variables
export PROJECT_ID="brank-484008"
export SERVICE_NAME="brank-backend"
export REGION="us-central1"
export REPO="anirudhreddyrachamalla/brank-backend"

echo "Setting up GCP resources for:"
echo "Project ID: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Repo: $REPO"
echo ""

# 2. Enable APIs
echo "Enabling required APIs..."
gcloud services enable artifactregistry.googleapis.com run.googleapis.com iamcredentials.googleapis.com --project=$PROJECT_ID

# 3. Create Artifact Registry
echo "Creating Artifact Registry repository..."
if ! gcloud artifacts repositories describe $SERVICE_NAME-repo --project=$PROJECT_ID --location=$REGION >/dev/null 2>&1; then
    gcloud artifacts repositories create $SERVICE_NAME-repo \
        --project=$PROJECT_ID \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for $SERVICE_NAME"
else
    echo "Repository $SERVICE_NAME-repo already exists."
fi

# 4. Create Service Account & Workload Identity Pool
echo "Creating Service Account..."
if ! gcloud iam service-accounts describe github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID >/dev/null 2>&1; then
    gcloud iam service-accounts create github-actions-deployer \
        --project=$PROJECT_ID \
        --display-name="GitHub Actions Deployer"
else
    echo "Service Account github-actions-deployer already exists."
fi

echo "Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin" >/dev/null

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" >/dev/null

gcloud artifacts repositories add-iam-policy-binding $SERVICE_NAME-repo \
    --project=$PROJECT_ID \
    --location=$REGION \
    --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer" >/dev/null

# Create the Identity Pool
echo "Creating Workload Identity Pool..."
if ! gcloud iam workload-identity-pools describe "github-actions-pool" --project=$PROJECT_ID --location="global" >/dev/null 2>&1; then
    gcloud iam workload-identity-pools create "github-actions-pool" \
      --project=$PROJECT_ID \
      --location="global" \
      --display-name="GitHub Actions Pool"
else
    echo "Workload Identity Pool 'github-actions-pool' already exists."
fi

# Create the Provider
echo "Creating Workload Identity Worker Provider..."
if ! gcloud iam workload-identity-pools providers describe "github-provider" --project=$PROJECT_ID --location="global" --workload-identity-pool="github-actions-pool" >/dev/null 2>&1; then
    gcloud iam workload-identity-pools providers create-oidc "github-provider" \
      --project=$PROJECT_ID \
      --location="global" \
      --workload-identity-pool="github-actions-pool" \
      --display-name="GitHub Provider" \
      --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
      --issuer-uri="https://token.actions.githubusercontent.com"
else
    echo "Provider 'github-provider' already exists."
fi

# Allow your specific repo to use this Service Account
echo "Binding Service Account to Repo..."
gcloud iam service-accounts add-iam-policy-binding "github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/$REPO" >/dev/null

# 5. Get the Provider Name
echo ""
echo "--------------------------------------------------------"
echo "SETUP COMPLETE. COPY THE OUTPUT BELOW FOR GITHUB ACTIONS:"
echo "--------------------------------------------------------"
gcloud iam workload-identity-pools providers describe "github-provider" \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --format="value(name)"
