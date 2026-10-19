param(
    [Parameter(Mandatory=$true)][string]$ProjectId,
    [string]$Region = 'us-central1',
    [string]$Model = 'gemini-3.1-flash-lite',
    [string]$Tag = 'rag-v1'
)
$ErrorActionPreference = 'Stop'
function Run-Gcloud { & gcloud @args; if ($LASTEXITCODE -ne 0) { throw 'A gcloud command failed; deployment stopped.' } }
if (-not (Test-Path -LiteralPath 'data/processed/manifest.json')) { throw 'Export the verified processed snapshot before deployment. See docs/DEPLOYMENT.md.' }
Run-Gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com places.googleapis.com --project=$ProjectId
& gcloud artifacts repositories describe roamwise --location=$Region --project=$ProjectId *> $null
if ($LASTEXITCODE -ne 0) { Run-Gcloud artifacts repositories create roamwise --repository-format=docker --location=$Region --project=$ProjectId }
$ServiceAccount = "roamwise-runtime@$ProjectId.iam.gserviceaccount.com"
& gcloud iam service-accounts describe $ServiceAccount --project=$ProjectId *> $null
if ($LASTEXITCODE -ne 0) { Run-Gcloud iam service-accounts create roamwise-runtime --display-name='RoamWise runtime' --project=$ProjectId }
Run-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$ServiceAccount" --role=roles/aiplatform.user --condition=None --format='value(version)'
Run-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$ServiceAccount" --role=roles/serviceusage.serviceUsageConsumer --condition=None --format='value(version)'
Run-Gcloud builds submit . --config=deploy/cloudbuild.yaml --region=$Region --project=$ProjectId --substitutions="_REGION=$Region,_TAG=$Tag"
$Image = "$Region-docker.pkg.dev/$ProjectId/roamwise/app:$Tag"
Run-Gcloud run deploy roamwise-rag --image=$Image --region=$Region --project=$ProjectId --service-account=$ServiceAccount --port=8080 --cpu=1 --memory=2Gi --min=0 --max=1 --no-cpu-boost --concurrency=8 --timeout=300 --allow-unauthenticated --set-env-vars="LLM_PROVIDER=vertex,LLM_MODEL=$Model,GOOGLE_CLOUD_PROJECT=$ProjectId,GOOGLE_CLOUD_LOCATION=global,GOOGLE_PLACES_AUTH=adc,REQUESTS_PER_HOUR=60"
Run-Gcloud run services describe roamwise-rag --region=$Region --project=$ProjectId --format='value(status.url)'
