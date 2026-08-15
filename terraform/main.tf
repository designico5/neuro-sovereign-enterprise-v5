# Neuro-Sovereign Enterprise v5 – Terraform IaC
# Provisions cloud infrastructure for NSE deployment.
# Provider: AWS (EKS + ElastiCache Redis + S3 state bucket)
# Usage:
#   cd terraform && terraform init && terraform plan && terraform apply

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state backend – create the bucket + DynamoDB table manually first:
  #   aws s3api create-bucket --bucket nse-tfstate --region eu-central-1
  #   aws dynamodb create-table --table-name nse-tf-locks \
  #     --attribute-definitions AttributeName=LockID,AttributeType=S \
  #     --key-schema AttributeName=LockID,KeyType=HASH \
  #     --billing-mode PAY_PER_REQUEST
  backend "s3" {
    bucket         = "nse-tfstate"
    key            = "nse/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true
    dynamodb_table = "nse-tf-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# ============================================================
# VPC – isolated network for NSE
# ============================================================
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "nse-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment == "production" ? false : true
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = var.environment
    Project     = "neuro-sovereign-enterprise"
  }
}

# ============================================================
# EKS – Kubernetes cluster for NSE workloads
# ============================================================
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "nse-cluster"
  cluster_version = "1.30"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Cluster endpoint is private for production, public for dev
  cluster_endpoint_public_access = var.environment != "production"

  eks_managed_node_groups = {
    nse_nodes = {
      min_size       = var.environment == "production" ? 3 : 1
      max_size       = 5
      desired_size   = var.environment == "production" ? 3 : 2
      instance_types = var.node_instance_types

      # Security-hardened node group
      disk_size      = 50
      disk_encrypted = true

      labels = {
        "app.kubernetes.io/name" = "neurosovereign"
      }

      tags = {
        Environment = var.environment
      }
    }
  }

  # Enforce encryption at rest
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }

  tags = {
    Environment = var.environment
    Project     = "neuro-sovereign-enterprise"
  }
}

# KMS key for EKS secrets encryption
resource "aws_kms_key" "eks" {
  description             = "EKS secret encryption key for NSE"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# ============================================================
# ElastiCache Redis – state cache for NSE
# ============================================================
resource "aws_elasticache_subnet_group" "nse" {
  name       = "nse-redis-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "redis" {
  name        = "nse-redis-sg"
  description = "Allow Redis access from EKS nodes"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "Redis from EKS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elasticache_replication_group" "nse" {
  replication_group_id       = "nse-redis"
  description                = "Redis cluster for NSE state caching"
  node_type                  = var.redis_node_type
  num_cache_clusters         = var.environment == "production" ? 3 : 1
  subnet_group_name          = aws_elasticache_subnet_group.nse.name
  security_group_ids         = [aws_security_group.redis.id]
  automatic_failover_enabled = var.environment == "production"
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  multi_az_enabled           = var.environment == "production"

  tags = {
    Environment = var.environment
    Project     = "neuro-sovereign-enterprise"
  }
}

# ============================================================
# S3 – persistent state / ledger backup
# ============================================================
resource "aws_s3_bucket" "nse_state" {
  bucket = "nse-state-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
    Project     = "neuro-sovereign-enterprise"
  }
}

resource "aws_s3_bucket_versioning" "nse_state" {
  bucket = aws_s3_bucket.nse_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "nse_state" {
  bucket = aws_s3_bucket.nse_state.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "nse_state" {
  bucket                  = aws_s3_bucket.nse_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_caller_identity" "current" {}
