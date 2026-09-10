# Neuro-Sovereign Enterprise v5 – Terraform Outputs

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_ca_certificate" {
  description = "EKS cluster CA certificate (base64)"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.nse.primary_endpoint_address
  sensitive   = true
}

output "state_bucket" {
  description = "S3 bucket for persistent NSE state"
  value       = aws_s3_bucket.nse_state.id
}

output "vpc_id" {
  description = "VPC ID for NSE network"
  value       = module.vpc.vpc_id
}

output "kubeconfig_command" {
  description = "Command to update local kubeconfig"
  value       = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.aws_region}"
}
