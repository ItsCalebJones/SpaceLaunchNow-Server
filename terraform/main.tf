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
  host                   = digitalocean_kubernetes_cluster.sln_k8s_prod.endpoint
  token                  = digitalocean_kubernetes_cluster.sln_k8s_prod.kube_config[0].token
  cluster_ca_certificate = base64decode(
    digitalocean_kubernetes_cluster.sln_k8s_prod.kube_config[0].cluster_ca_certificate
  )
}

resource "digitalocean_container_registry" "sln_registry" {
  name     = "sln-prod-registry-01"
  region   = "nyc3"
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
  name     = "sln-prod-vpc-01"
  region   = var.region
}

resource "digitalocean_kubernetes_cluster" "sln_k8s_prod" {
  name    = "sln-prod-k8s-01"
  region  = var.region
  version = "1.33.1-do.0"

  # assign to the created VPC
  vpc_uuid = digitalocean_vpc.sln_vpc.id

  # tag the cluster itself (and propagates to each node pool)
  tags = var.tags
  auto_upgrade = true
  maintenance_policy {
    day        = "sunday"
    start_time = "04:00"
  }

  # first node-pool
  node_pool {
    name       = "sln-prod-nodepool-main-01"
    size       = "s-4vcpu-8gb"
    node_count = 3
    tags       = concat(var.tags, ["prod-4cpu", "scalable"])
    auto_scale = true
    min_nodes = 1
    max_nodes = 10
  }
}

resource "digitalocean_kubernetes_node_pool" "sln_k8s_prod_memory" {
  cluster_id = digitalocean_kubernetes_cluster.sln_k8s_prod.id
  name       = "sln-prod-nodepool-memory-02"
  size       = "m-2vcpu-16gb"
  node_count = 1
  tags       = concat(
    var.tags,
    ["prod-memory"],
  )
  auto_scale = true
  min_nodes = 1
  max_nodes = 2
  
  # Add node labels for workload scheduling
  labels = {
    "workload-type" = "memory-intensive"
  }
}

resource "digitalocean_kubernetes_node_pool" "sln_k8s_prod_cpu" {
  cluster_id = digitalocean_kubernetes_cluster.sln_k8s_prod.id
  name       = "sln-prod-nodepool-compute-03"
  size       = "c-4"
  node_count = 1
  tags       = concat(
    var.tags,
    ["prod-cpu-optimized", "scalable"],
  )
  auto_scale = true
  min_nodes = 0
  max_nodes = 5
  
  # Add node labels for workload scheduling
  labels = {
    "workload-type" = "cpu-intensive"
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
