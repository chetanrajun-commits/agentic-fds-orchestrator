provider "aws" {
  region = var.aws_region
}

# --- Networking ------------------------------------------------------------

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "fds-vpc-${var.environment_tier}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
  enable_dns_hostnames = true

  tags = var.finops_cost_center_tags
}

# --- Compute: EKS ----------------------------------------------------------

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "fds-mesh-${var.environment_tier}"
  cluster_version = "1.29"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    fds-workers = {
      min_size       = 2
      max_size       = 10
      desired_size   = 3
      instance_types = ["m6i.xlarge"]
      tags           = var.finops_cost_center_tags
    }
  }

  tags = var.finops_cost_center_tags
}

# --- Namespace-level resource quotas --------------------------------------
# These mirror the ceilings enforced by `fds-policy-pack-v1` on the manifest
# side. Defense in depth: policy in CI, enforcement at the cluster.

resource "kubernetes_namespace" "engagement" {
  for_each = var.engagement_ceilings

  metadata {
    name = each.key
    labels = {
      "tenant"      = each.key
      "environment" = var.environment_tier
      "managed-by"  = "agentic-fds"
    }
  }

  depends_on = [module.eks]
}

resource "kubernetes_resource_quota" "engagement_quota" {
  for_each = var.engagement_ceilings

  metadata {
    name      = "${each.key}-quota"
    namespace = kubernetes_namespace.engagement[each.key].metadata[0].name
  }

  spec {
    hard = {
      "requests.cpu"    = each.value.cpu_limit
      "requests.memory" = each.value.memory_limit
      "pods"            = each.value.max_replicas * 5
    }
  }
}
