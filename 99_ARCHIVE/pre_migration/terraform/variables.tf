# Neuro-Sovereign Enterprise v5 – Terraform Variables

variable "aws_region" {
  description = "AWS region for NSE infrastructure"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Deployment environment (production, staging, development)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "environment must be one of: production, staging, development."
  }
}

variable "node_instance_types" {
  description = "EKS node instance types"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}
