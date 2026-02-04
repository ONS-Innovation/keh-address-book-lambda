# GitHub Repository Address Book Lambda

A weekly AWS Lambda function to retrieve all ONS Digital GitHub usernames and ONS verified emails from GitHub GraphQL API.

This allows [Digital Landscape's](https://github.com/ONSdigital/keh-digital-landscape) Address book page to translate between usernames and email addresses for easy identification of different repo owners in the ONS.

## Table of Contents

- [GitHub Repository Address Book Lambda](#github-repository-address-book-lambda)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Makefile](#makefile)
  - [Documentation](#documentation)
  - [Development](#development)
  - [Running the Project](#running-the-project)
    - [Outside of a Container (Recommended) (Development only)](#outside-of-a-container-recommended-development-only)
    - [Containerised](#containerised)
    - [Output Files](#output-files)
  - [Deployment](#deployment)
    - [Deployments with Concourse](#deployments-with-concourse)
      - [Allowlisting your IP](#allowlisting-your-ip)
      - [Setting up a pipeline](#setting-up-a-pipeline)
      - [Prod deployment](#prod-deployment)
      - [Triggering a pipeline](#triggering-a-pipeline)
      - [Destroying a pipeline](#destroying-a-pipeline)
    - [Manual Deployment](#manual-deployment)
      - [Overview](#overview)
      - [Deployment Prerequisites](#deployment-prerequisites)
      - [Storing the Container on AWS Elastic Container Registry (ECR)](#storing-the-container-on-aws-elastic-container-registry-ecr)
      - [Deploying the Lambda](#deploying-the-lambda)
      - [Destroying / Removing the Lambda](#destroying--removing-the-lambda)
  - [Linting and Testing](#linting-and-testing)
    - [GitHub Actions](#github-actions)
    - [Linters Used](#linters-used)
    - [Running Linting and Tests Locally](#running-linting-and-tests-locally)
  - [FAQs and troubleshooting tips](#faqs-and-troubleshooting-tips)
    - [Why do I get an S3 permissions error when writing outputs?](#why-do-i-get-an-s3-permissions-error-when-writing-outputs)
    - [Why are some users missing email addresses in the outputs?](#why-are-some-users-missing-email-addresses-in-the-outputs)
    - [How do I run locally and see logs?](#how-do-i-run-locally-and-see-logs)
    - [MkDocs won’t serve or pages 404 locally.](#mkdocs-wont-serve-or-pages-404-locally)
    - [Where are the outputs written?](#where-are-the-outputs-written)

## Prerequisites

- A Docker Daemon (Colima is recommended)
  - [Colima](https://github.com/abiosoft/colima)
- Terraform (For deployment)
  - [Terraform](https://www.terraform.io/)
- Python >3.12
  - [Python](https://www.python.org/)
- Make
  - [GNU make](https://www.gnu.org/software/make/manual/make.html#Overview)

## Makefile

This repository makes use of a Makefile to execute common commands. To view all commands, execute `make all`.

```bash
make all
```

## Documentation

This project uses [MkDocs](https://www.mkdocs.org/) for documentation. The documentation is located in the `docs` directory. To view the documentation locally, you can run the following commands:

1. Install MkDocs and its dependencies:

   ```bash
   make install-docs
   ```

2. Serve the documentation locally:

   ```bash
   make docs-serve
   ```

3. Open your web browser and navigate to `http://localhost:8000`.

Optional:

- Build static site: `make docs-build`
- Deploy to GitHub Pages manually: `make docs-deploy` (CI also deploys on pushes to `main`)
- [Deply Mkdocs Action](./.github/workflows/deploy_mkdocs.yml)

## Development

To work on this project, you need to:

1. Create a virtual environment and activate it.

   Create:

   ```python
   python3 -m venv venv
   ```

   Activate:

   ```python
   source venv/bin/activate
   ```

2. Install dependencies

   Production dependencies only:

   ```bash
   make install
   ```

   Dependencies including dev dependencies (used for Linting and Testing)

   ```bash
   make install-dev
   ```

To run the project during development, we recommend you [run the project outside of a container](#outside-of-a-container-development-only)

## Running the Project

### Outside of a Container (Recommended) (Development only)

To run the Lambda function outside of a container, we need to execute the `lambda_handler()` function.

1. Uncomment the following at the bottom of `lambda_function.py` (in `./src/` folder).

   ```python
   ...
   # if __name__ == "__main__":
   #     try:
   #         lambda_handler(event={}, context=None)
   #     except Exception as e:
   #         print(f"Error running lambda_handler locally: {e}")
   ...
   ```

   **Please Note:** If uncommenting the above in `lambda_function.py`, make sure you re-comment the code _before_ pushing back to GitHub.

2. Export the required environment variables:

   ```bash
   export AWS_ACCESS_KEY_ID=<access_key_id>
   export AWS_SECRET_ACCESS_KEY=<secret_access_key>
   export AWS_REGION=eu-west-2
   export AWS_SECRET_NAME=<secret_name>
   export S3_BUCKET_NAME=<bucket_name>
   export GITHUB_ORG=<org>
   export GITHUB_APP_CLIENT_ID=<client_id>
   export GITHUB_APP_ID=<app_id>
   export GITHUB_APP_CLIENT_SECRET=<app_client_secret>

   ```

3. Run the script.

   ```bash
   poetry run python3 src/lambda_function.py
   ```

### Containerised

To run the project, a Docker Daemon is required to containerise and execute the project. We recommend using [Colima](https://github.com/abiosoft/colima).

Before the doing the following, make sure your Daemon is running. If using Colima, run `colima start` to check this.

1. Containerise the project.

   ```bash
   docker build -t address-book-lambda .
   ```

2. Check the image exists (Optional).

   ```bash
   docker images
   ```

   Example Output:

   ```bash
   REPOSITORY                         TAG       IMAGE ID       CREATED          SIZE
   address-book-lambda                latest    b4a1e32ce51b   12 minutes ago   840MB
   ```

3. Run the image.

   ```bash
   docker run --platform linux/amd64 -p 9000:8080 \
   -e AWS_ACCESS_KEY_ID=<access_key_id> \
   -e AWS_SECRET_ACCESS_KEY=<secret_access_key> \
   -e AWS_REGION=<region> \
   -e AWS_SECRET_NAME=<secret_name> \
   -e GITHUB_ORG=<org> \
   -e GITHUB_APP_ID=<app_id> \
   -e GITHUB_APP_CLIENT_ID=<client_id> \
   -e S3_BUCKET_NAME=<bucket_name>\
   -e GITHUB_APP_CLIENT_SECRET=<app_client_secret>
   address-book-lambda
   ```

   When running the container, you are required to pass some environment variables:

   | Variable                 | Description                                                                               |
   | ------------------------ | ----------------------------------------------------------------------------------------- |
   | GITHUB_ORG               | The organisation you would like to run the tool in.                                       |
   | GITHUB_APP_CLIENT_ID     | The Client ID for the GitHub App which the tool uses to authenticate with the GitHub API. |
   | GITHUB_APP_ID            | Numeric ID of the GitHub App used for authentication.                                     |
   | GITHUB_APP_CLIENT_SECRET | Client secret for the GitHub App OAuth authentication.                                    |
   | AWS_REGION               | The AWS Region which the Secret Manager Secret is in.                                     |
   | AWS_SECRET_NAME          | Name of the AWS Secrets Manager secret to retrieve.                                       |
   | S3_BUCKET_NAME           | The name of the S3 bucket the Lambda writes AddressBook JSON files to.                    |
   | AWS_ACCESS_KEY_ID        | AWS access key ID for the configured IAM credentials                                      |
   | AWS_SECRET_ACCESS_KEY    | AWS secret access key for the configured IAM credentials                                  |

   Once the container is running, a local endpoint is created at `localhost:9000/2015-03-31/functions/function/invocations`.

4. Check the container is running (Optional).

   ```bash
   docker ps
   ```

   Example Output:

   ```bash
   CONTAINER ID   IMAGE                              COMMAND                  CREATED         STATUS         PORTS                                       NAMES
   ca890d30e24d   address-book-lambda                "/lambda-entrypoint.…"   5 seconds ago   Up 4 seconds   0.0.0.0:9000->8080/tcp, :::9000->8080/tcp   recursing_bartik
   ```

5. Post to the endpoint (`localhost:9000/2015-03-31/functions/function/invocations`).

   ```bash
   curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
   ```

   This will run the Lambda function and, once complete, will return a success message.

6. After testing stop the container.

   ```bash
   docker stop <container_id>
   ```

   ### Output Files

   When the Lambda runs successfully, it writes three JSON files into your configured S3 bucket under the `AddressBook/` prefix:
   - AddressBook/addressBookUsernameKey.json: username -> list of verified org emails
     Example: `{ "alice": ["alice@org.com", "alice2@org.com"], "bob": ["bob@org.com"] }`
   - AddressBook/addressBookEmailKey.json: email -> username
     Example: `{ "alice@org.com": "alice", "bob@org.com": "bob" }`
   - AddressBook/addressBookIDKey.json: username -> GitHub account ID
     Example: `{ "alice": 101, "bob": 202 }`

   Note: The `AddressBook/` path is an S3 key prefix used to group these files in the bucket.

## Deployment

### Deployments with Concourse

#### Allowlisting your IP

To setup the deployment pipeline with concourse, you must first allowlist your IP address on the Concourse
server. IP addresses are flushed everyday at 00:00 so this must be done at the beginning of every working day
whenever the deployment pipeline needs to be used. Follow the instructions on the Confluence page (SDP Homepage > SDP Concourse > Concourse Login) to
login. All our pipelines run on sdp-pipeline-prod, whereas sdp-pipeline-dev is the account used for
changes to Concourse instance itself. Make sure to export all necessary environment variables from sdp-pipeline-prod (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN).

#### Setting up a pipeline

When setting up our pipelines, we use ecs-infra-user on sdp-dev to be able to interact with our infrastructure on AWS. The credentials for this are stored on
AWS Secrets Manager so you do not need to set up anything yourself.

To set the pipeline, run the following script:

```bash
chmod u+x ./concourse/scripts/set_pipeline.sh
./concourse/scripts/set_pipeline.sh
```

Note that you only have to run chmod the first time running the script in order to give permissions.
This script will set the branch and pipeline name to whatever branch you are currently on. It will also set the image tag on ECR to 7 characters of the current branch name if running on a branch other than main. For main, the ECR tag will be the latest release tag on the repository that has semantic versioning(vX.Y.Z).

The pipeline name itself will usually follow a pattern as follows: `digital-landscape-<branch-name>` for any non-main branch and `digital-landscape` for the main/master branch.

#### Prod deployment

To deploy to prod, it is required that a Github Release is made on Github. The release is required to follow semantic versioning of vX.Y.Z.

A manual trigger is to be made on the pipeline name `digital-landscape > deploy-after-github-release` job through the Concourse CI UI. This will create a github-create-tag resource that is required on the `digital-landscape > build-and-push-prod` job. Then the prod deployment job is also through a manual trigger ensuring that prod is only deployed using the latest GitHub release tag in the form of vX.Y.Z and is manually controlled.

#### Triggering a pipeline

Once the pipeline has been set, you can manually trigger a dev build on the Concourse UI, or run the following command for non-main branch deployment:

```bash
fly -t aws-sdp trigger-job -j digital-landscape-<branch-name>/build-and-push-dev
```

and for main branch deployment:

```bash
fly -t aws-sdp trigger-job -j digital-landscape/build-and-push-dev
```

#### Destroying a pipeline

To destroy the pipeline, run the following command:

```bash
fly -t aws-sdp destroy-pipeline -p digital-landscape-<branch-name>
```

**It is unlikely that you will need to destroy a pipeline, but the command is here if needed.**

**Note:** This will not destroy any resources created by Terraform. You must manually destroy these resources using Terraform.

### Manual Deployment

#### Overview

This repository is designed to be hosted on AWS Lambda using a container image as the Lambda's definition.

There are 2 parts to deployment:

1. Updating the ECR Image.
2. Updating the Lambda.

#### Deployment Prerequisites

Before following the instructions below, we assume that:

- An ECR repository exists on AWS that aligns with the Lambda's naming convention, `{env_name}-{lambda_name}` (these can be set within the `.tfvars` file. See [example_tfvars.txt](./terraform/service/env/dev/example_tfvars.txt)).
- The AWS account contains underlying infrastructure to deploy on top of. This infrastructure is defined within [sdp-infrastructure](https://github.com/ONS-Innovation/sdp-infrastructure) on GitHub.
- An AWS IAM user has been setup with appropriate permissions.

Additionally, we recommend that you keep the container versioning in sync with GitHub releases. Internal documentation for this is available on Confluence ([GitHub Releases and AWS ECR Versions](https://confluence.ons.gov.uk/display/KEH/GitHub+Releases+and+AWS+ECR+Versions)). We follow Semantic Versioning ([Learn More](https://semver.org/spec/v2.0.0.html)).

#### Storing the Container on AWS Elastic Container Registry (ECR)

When changes are made to the repository's source code, the code must be containerised and pushed to AWS for the lambda to use.

The following instructions deploy to an ECR repository called `sdp-dev-address-book-lambda`. Please change this to `<env_name>-<lambda_name>` based on your AWS instance.

All of the commands (steps 2-5) are available for your environment within the AWS GUI. Navigate to ECR > {repository_name} > View push commands.

1. Export AWS credential into the environment. This makes it easier to ensure you are using the correct credentials.

   ```bash
   export AWS_ACCESS_KEY_ID="<aws_access_key_id>"
   export AWS_SECRET_ACCESS_KEY="<aws_secret_access_key>"
   ```

2. Login to AWS.

   ```bash
   aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.eu-west-2.amazonaws.com
   ```

3. Ensuring you're at the root of the repository, build a docker image of the project.

   ```bash
   docker build -t sdp-dev-address-book-lambda .
   ```

   **Please Note:** Change `sdp-dev-address-book-lambda` within the above command to `<env_name>-<lambda_name>`.

4. Tag the docker image to push to AWS, using the correct versioning mentioned in [prerequisites](#deployment-prerequisites).

   ```bash
   docker tag sdp-dev-address-book-lambda:latest <aws_account_id>.dkr.ecr.eu-west-2.amazonaws.com/sdp-dev-address-book-lambda:<semantic_version>
   ```

   **Please Note:** Change `sdp-dev-address-book-lambda` within the above command to `<env_name>-<lambda_name>`.

5. Push the image to ECR.

   ```bash
   docker push <aws_account_id>.dkr.ecr.eu-west-2.amazonaws.com/sdp-dev-address-book-lambda:<semantic_version>
   ```

Once pushed, you should be able to see your new image version within the ECR repository.

#### Deploying the Lambda

Once AWS ECR has the new container image, we need to update the Lambda's configuration to use it. To do this, use the repository's provided [Terraform](./terraform/).

Within the terraform directory, there is a [service](./terraform/service/) subdirectory which contains the terraform to setup the lambda on AWS.

1. Change directory to the service terraform.

   ```bash
   cd terraform/service
   ```

2. Fill out the appropriate environment variables file
   - `env/dev/dev.tfvars` for sdp-dev.
   - `env/prod/prod.tfvars` for sdp-prod.

   These files can be created based on [`example_tfvars.txt`](./terraform/service/env/dev/example_tfvars.txt).

   **It is crucial that the completed `.tfvars` file does not get committed to GitHub.**

3. Initialise the terraform using the appropriate `.tfbackend` file for the environment (`env/dev/backend-dev.tfbackend` or `env/prod/backend-prod.tfbackend`).

   ```bash
   terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure
   ```

   **Please Note:** This step requires an AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to be loaded into the environment if not already in place. This can be done using:

   ```bash
   export AWS_ACCESS_KEY_ID="<aws_access_key_id>"
   export AWS_SECRET_ACCESS_KEY="<aws_secret_access_key>"
   ```

4. Refresh the local state to ensure it is in sync with the backend, using the appropriate `.tfvars` file for the environment (`env/dev/dev.tfvars` or `env/prod/prod.tfvars`).

   ```bash
   terraform refresh -var-file=env/dev/dev.tfvars
   ```

5. Plan the changes, using the appropriate `.tfvars` file.

   i.e. for dev use

   ```bash
   terraform plan -var-file=env/dev/dev.tfvars
   ```

6. Apply the changes, using the appropriate `.tfvars` file.

   i.e. for dev use

   ```bash
   terraform apply -var-file=env/dev/dev.tfvars
   ```

Once applied successfully, the Lambda and EventBridge Schedule will be created.

#### Destroying / Removing the Lambda

To delete the service resources, run the following:

```bash
cd terraform/service
terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure
terraform refresh -var-file=env/dev/dev.tfvars
terraform destroy -var-file=env/dev/dev.tfvars
```

**Please Note:** Make sure to use the correct `.tfbackend` and `.tfvars` files for your environment.

## Linting and Testing

### GitHub Actions

This file contains 2 GitHub Actions to automatically lint and test code on pull request creation and pushing to the main branch.

- [`ci.yml`](./.github/workflows/ci.yml)
- [`mega-linter.yml`](./.github/workflows/mega-linter.yml)

### Linters Used

This repository uses the following linting and formatting tools:

Python:

- Black: code formatter (used for formatting and format checks)
- Ruff: Python linter (also used for autofixes and import sorting)
- Mypy: static type checker (configured via `mypy.ini`)

Other Languages:

- MegaLinter: runs a broad set of linters.

Configuration notes:

- Mypy reads settings from `mypy.ini`.

### Running Linting and Tests Locally

To lint and test locally, you need to:

1. Install dev dependencies

   ```bash
   make install-dev
   ```

2. Run all the linters

   ```bash
   make lint
   ```

3. Run all the formatting

   ```bash
   make format
   ```

4. Run all the tests

   ```bash
   make test
   ```

5. Run Megalinter

   ```bash
   make megalint
   ```

**Please Note:** This requires a docker daemon to be running. We recommend using [Colima](https://github.com/abiosoft/colima) if using MacOS or Linux. A docker daemon is required because Megalinter is ran from a docker image.

## FAQs and troubleshooting tips

### Why do I get an S3 permissions error when writing outputs?

- Ensure the Lambda execution role has `s3:PutObject` permission on the target bucket and the `AddressBook/` prefix.

### Why are some users missing email addresses in the outputs?

- Only verified organisation emails are included. Users without a verified org email will not appear in `addressBookUsernameKey.json` or `addressBookEmailKey.json`.

### How do I run locally and see logs?

- Export the required environment variables (see above) and run the handler locally.

### MkDocs won’t serve or pages 404 locally.

- Run `make install-docs` first, then `make docs-serve`. Verify `mkdocs.yml` nav matches files under `docs/`.

### Where are the outputs written?

- To your configured S3 bucket under the `AddressBook/` prefix as three JSON files.

For more Q&A: see the dedicated [FAQ](faq.md).
