# Remote state backend — DigitalOcean Spaces (S3-compatible).
#
# Why Spaces: same cloud/console/billing as the infra this state manages, and
# native S3 state locking (no DynamoDB needed on Terraform >= 1.10).
#
# ONE-TIME SETUP before `terraform init -migrate-state`:
#   1. Create a PRIVATE Space named below, region nyc3 (DO console -> Spaces).
#      Create it by hand, NOT via this Terraform — a state bucket must not live
#      in the state it stores. Enable encryption on the Space.
#   2. Create a Spaces access key (DO console -> API -> Spaces Keys).
#   3. Export creds — the backend block CANNOT read Terraform variables:
#        export AWS_ACCESS_KEY_ID=<spaces-key>
#        export AWS_SECRET_ACCESS_KEY=<spaces-secret>
#   4. terraform init -migrate-state
#      Terraform detects local -> s3 and offers to copy the existing state up.
#      Confirm "yes", verify `terraform plan` is clean, then the local
#      terraform.tfstate is just a backup (already gitignored).
terraform {
  backend "s3" {
    bucket = "sln-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1" # dummy placeholder; the real region is in the endpoint below.

    endpoints = {
      s3 = "https://nyc3.digitaloceanspaces.com"
    }

    # DO Spaces is S3-compatible but not AWS — skip the AWS-only preflight calls.
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_s3_checksum            = true # Spaces rejects the AWS SDK's newer default checksum trailers

    use_lockfile = true # native S3 state locking (Terraform >= 1.10)
  }
}
