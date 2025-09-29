# atlas aopcs lambda

## Table of Contents

- [Local installation](#local-installation)
- [Environment variables](#environment-variables)
- [AWS](#aws)
  - [Deployment dependencies (manual deployments)](#deployment-dependencies-manual-deployments)
  - [Deployment environments](#deployment-environments)
  - [Deployment from Gitlab](#deployment-from-gitlab)

---

## Local installation

This project works with **Python 3.12**. Make sure you have this version installed to contribute to development.

To install all required Python packages for development and deployment, run the setup script:

```bash
source ./scripts/setup_dev_environment.sh
```

---

## 🌱 Environment variables

For local development, you may eventually need to define the following environment variables, depending on the future business logic of the Lambda.  
At this stage, **none are required**.

---

## ☁️ AWS

### 📦 Deployment dependencies (manual deployments)

To manually deploy to AWS, ensure the **AWS CDK** is installed.  
It must match the version specified in the `CDK_VERSION` variable of the `gitlab-ci.yml`.

> ℹ️ You must manually create the Kinéis API credentials in **AWS Secrets Manager**, under the ARN defined by `secret_manager_arn` (see `global_config.py`). The secret must include `client_id` and `client_secret` keys corresponding to the Kinéis API authentication credentials.

---

### Deployment environments

ATLAS deployment environments are defined in:

aopcs_lambda/target/aws/environments/atlas_environment.py

Each environment has a dedicated configuration file in the same folder.

👉 See the [ATLAS AWS deployment environments documentation](https://kerlink.atlassian.net/wiki/spaces/ATLAS/pages/1134460929/Atlas+AWS+deployment+environments) for more details.

---

### Deployment from GitLab

Manual deployments to **preproduction** or **production** can be triggered here:  
👉 [Launch GitLab pipeline](https://gitlab.klksi.fr/atlas/configuration-app/aopcs-lambda/-/pipelines/new)

Make sure to launch the pipeline from the `develop` branch.

---

### ✅ Pipeline arguments

- `ENVIRONMENT` (**required**): name of the target environment (in uppercase), e.g. `DEVELOPMENT`  
- `VERSION` (optional): Git tag to deploy (defaults to the current commit hash)  
- `CDK_VERSION` (optional): version of the CDK to use (must match `aws-cdk-lib`)

⚠️ **Do not manually set other variables** — this may break the pipeline.
