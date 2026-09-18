# Media Transcoder

An Azure-backed media processing API. Clients upload a source file, the API stores it in private Blob Storage, and a queue-driven worker transcodes it with FFmpeg.

## Architecture

- FastAPI API accepts uploads and returns a job ID.
- Azure Blob Storage stores inputs, outputs, and JSON job status.
- Azure Storage Queue dispatches transcode jobs.
- The same container image runs the API or the worker process.
- Terraform provisions the storage account, queue, Log Analytics workspace, and Azure Container Apps API.

## Run locally

Set `AZURE_STORAGE_CONNECTION_STRING` and start the API:

```powershell
python -m uvicorn app.main:app --reload
```

Start a worker in a second terminal:

```powershell
python -m app.worker
```

Submit a job:

```powershell
curl.exe -F "file=@sample.mp4" -F "preset=web" http://localhost:8000/jobs
```

## Deploy infrastructure

Build and publish the image to a registry first, then configure Terraform:

```powershell
Copy-Item terraform/terraform.tfvars.example terraform/terraform.tfvars
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan
terraform -chdir=terraform apply
```

Terraform provisions both the public API Container App and a private worker Container App that continuously polls the queue.

## GitHub Actions

The workflow in `.github/workflows/ci-cd.yml` validates pull requests and deploys `main` through Azure OIDC. Configure these GitHub environment values in the `production` environment:

- Secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- Variables: `AZURE_RESOURCE_GROUP`, `AZURE_LOCATION`, `APP_NAME`, `AZURE_STORAGE_ACCOUNT`, `AZURE_CONTAINER_REGISTRY`, `TF_STATE_RESOURCE_GROUP`, `TF_STATE_STORAGE_ACCOUNT`, `TF_STATE_CONTAINER`

Create the remote Terraform state storage account and private blob container before enabling deployment. The Azure federated identity needs permission to read/write that state and create/update the application resources. The workflow bootstraps the infrastructure, builds the image with `az acr build`, then applies the immutable commit-tagged image to both Container Apps.

## API

- `GET /health`
- `POST /jobs` with multipart `file` and `preset` (`web` or `audio`)
- `GET /jobs/{job_id}`