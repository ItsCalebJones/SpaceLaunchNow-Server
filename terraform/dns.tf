# This file should be applied AFTER the Ansible deployment creates the nginx-ingress
# Run this as a separate Terraform apply after the load balancer is created

# Get load balancer IP from nginx-ingress service
data "kubernetes_service" "nginx_ingress" {
  metadata {
    name      = "nginx-ingress-ingress-nginx-controller"
    namespace = "nginx-ingress"
  }
}

# DNS record for spacelaunchnow.app pointing to load balancer
resource "cloudflare_record" "spacelaunchnow_app" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  content = data.kubernetes_service.nginx_ingress.status.0.load_balancer.0.ingress.0.ip
  type    = "A"
  ttl     = 1
  proxied = true
   
  depends_on = [data.kubernetes_service.nginx_ingress]
}

# Wildcard DNS record for *spacelaunchnow.app pointing to load balancer
resource "cloudflare_record" "wildcard_spacelaunchnow_app" {
  zone_id = var.cloudflare_zone_id
  name    = "*"
  content = data.kubernetes_service.nginx_ingress.status.0.load_balancer.0.ingress.0.ip
  type    = "A"
  ttl     = 1
  proxied = true
  
  depends_on = [data.kubernetes_service.nginx_ingress]
}

# Outputs
output "load_balancer_ip" {
  description = "IP address of the Kubernetes load balancer"
  value       = data.kubernetes_service.nginx_ingress.status.0.load_balancer.0.ingress.0.ip
}

output "dns_record_fqdn" {
  description = "FQDN of the created DNS record"
  value       = cloudflare_record.spacelaunchnow_app.hostname
}

output "dns_record_ip" {
  description = "IP address the DNS record points to"
  value       = cloudflare_record.spacelaunchnow_app.content
}

output "wildcard_dns_record_fqdn" {
  description = "FQDN of the wildcard DNS record"
  value       = cloudflare_record.wildcard_spacelaunchnow_app.hostname
}

output "wildcard_dns_record_ip" {
  description = "IP address the wildcard DNS record points to"
  value       = cloudflare_record.wildcard_spacelaunchnow_app.content
}
