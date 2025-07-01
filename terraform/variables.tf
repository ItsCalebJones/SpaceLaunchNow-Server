variable "do_token" {
  type        = string
  description = "DigitalOcean API token"
  sensitive   = true
}

variable "cloudflare_api_token" {
  type        = string
  description = "Cloudflare API token"
  sensitive   = true
}

variable "cloudflare_zone_id" {
  type        = string
  description = "Cloudflare zone ID for spacelaunchnow.app"
}

variable "region" {
  type        = string
  default     = "nyc1"
  description = "Which DO region to deploy into"
}

variable "tags" {
  type        = list(string)
  default     = ["sln-k8s", "production"]
  description = "Tags to apply to the cluster and all node pools"
}