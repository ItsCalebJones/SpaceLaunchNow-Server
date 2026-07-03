terraform {
  required_version = ">= 0.13"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.56"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.16"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

provider "kubernetes" {
  host  = digitalocean_kubernetes_cluster.sln_k8s_prod.endpoint
  token = digitalocean_kubernetes_cluster.sln_k8s_prod.kube_config[0].token
  cluster_ca_certificate = base64decode(
    digitalocean_kubernetes_cluster.sln_k8s_prod.kube_config[0].cluster_ca_certificate
  )
}

resource "digitalocean_container_registry" "sln_registry" {
  name                   = "sln-prod-registry-01"
  region                 = "nyc3"
  subscription_tier_slug = "basic"
}


resource "digitalocean_container_registry_docker_credentials" "sln_registry_pull" {
  registry_name = digitalocean_container_registry.sln_registry.name
  write         = false
}

resource "kubernetes_secret" "registry_pull" {
  metadata {
    name = "docker-cfg"
  }

  data = {
    ".dockerconfigjson" = digitalocean_container_registry_docker_credentials.sln_registry_pull.docker_credentials
  }

  type = "kubernetes.io/dockerconfigjson"

  depends_on = [digitalocean_kubernetes_cluster.sln_k8s_prod]
}

resource "digitalocean_vpc" "sln_vpc" {
  name   = "sln-prod-vpc-01"
  region = var.region
}

resource "digitalocean_kubernetes_cluster" "sln_k8s_prod" {
  name   = "sln-prod-k8s-01"
  region = var.region
  # Floor version at create time. DO's auto_upgrade (below) moves the live
  # patch forward during the Sunday maintenance window, so this string goes
  # stale by design — ignore_changes (lifecycle) stops Terraform from trying
  # to "downgrade" back to it, which forces a full cluster replacement.
  version = "1.33.12-do.1"

  # assign to the created VPC
  vpc_uuid = digitalocean_vpc.sln_vpc.id

  # tag the cluster itself (and propagates to each node pool)
  tags         = var.tags
  auto_upgrade = true
  maintenance_policy {
    day        = "sunday"
    start_time = "04:00"
  }

  # main node-pool - optimized for production scaling during launch events
  node_pool {
    name       = "sln-prod-nodepool-main-01"
    size       = "s-4vcpu-8gb"
    node_count = 2 # Reduced from 3 to 2 for normal operations
    tags       = concat(var.tags, ["prod-4cpu", "scalable"])
    auto_scale = true
    min_nodes  = 2
    max_nodes  = 10
  }

  lifecycle {
    # These are all managed out-of-band; don't let Terraform fight them:
    #  - version: DO auto_upgrade bumps the patch during the maintenance window.
    #  - node_pool count/min/max: src/autoscaler/autoscaler.py PATCHes the
    #    "scalable"-tagged pool (this one) around launch/event windows.
    ignore_changes = [
      version,
      node_pool[0].node_count,
      node_pool[0].min_nodes,
      node_pool[0].max_nodes,
    ]
  }
}

# Consolidated platform pool — replaces the separate memory-02 (m-2vcpu-16gb)
# and system-03 (c-4) pools. Both were mis-typed for their actual workloads
# (memory pool ran CPU-bound at 27% mem; system pool ran at 6% CPU), so this
# folds them into two balanced s-4vcpu-8gb nodes (~65% mem each, HA spread).
# NOTE: deliberately NOT tagged "scalable" — src/autoscaler/autoscaler.py only
# manages the scalable-tagged pool (main-01); this pool uses DOKS native
# autoscaling within min/max instead.
resource "digitalocean_kubernetes_node_pool" "sln_k8s_prod_shared" {
  cluster_id = digitalocean_kubernetes_cluster.sln_k8s_prod.id
  name       = "sln-prod-nodepool-shared-04"
  size       = "s-4vcpu-8gb"
  node_count = 2
  tags = concat(
    var.tags,
    ["prod-shared"],
  )
  auto_scale = true
  min_nodes  = 1
  max_nodes  = 3

  labels = {
    "workload-type" = "shared-infrastructure"
  }
}

# Save kubeconfig to file
resource "local_file" "kubeconfig" {
  content  = digitalocean_kubernetes_cluster.sln_k8s_prod.kube_config[0].raw_config
  filename = "${path.module}/sln-prod-kubeconfig-01"

  depends_on = [digitalocean_kubernetes_cluster.sln_k8s_prod]
}

# export the raw kubeconfig so you can feed kubectl or the k8s provider
output "kubeconfig" {
  description = "Raw kubeconfig for the DO cluster"
  value       = digitalocean_kubernetes_cluster.sln_k8s_prod.kube_config[0].raw_config
  sensitive   = true
}

# VPC outputs
output "vpc_id" {
  description = "ID of the created VPC"
  value       = digitalocean_vpc.sln_vpc.id
}

output "vpc_ip_range" {
  description = "IP range of the VPC"
  value       = digitalocean_vpc.sln_vpc.ip_range
}

# Cluster information
output "cluster_id" {
  description = "ID of the Kubernetes cluster"
  value       = digitalocean_kubernetes_cluster.sln_k8s_prod.id
}

output "cluster_endpoint" {
  description = "Endpoint for the Kubernetes cluster"
  value       = digitalocean_kubernetes_cluster.sln_k8s_prod.endpoint
}

output "kubeconfig_file" {
  description = "Path to the saved kubeconfig file"
  value       = local_file.kubeconfig.filename
}
