variable "aws_region" {
  type        = string
  description = "AWS region for the FDS mesh."
  default     = "us-east-1"
}

variable "environment_tier" {
  type        = string
  description = "Environment tier (dev, staging, prod)."
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment_tier)
    error_message = "environment_tier must be one of: dev, staging, prod."
  }
}

variable "finops_cost_center_tags" {
  type        = map(string)
  description = "Tags applied to all resources for FinOps chargeback."
  default = {
    CostCenter = "fds-platform"
    Owner      = "chetan"
    Project    = "agentic-fds"
  }
}

variable "engagement_ceilings" {
  type = map(object({
    cpu_limit    = string
    memory_limit = string
    max_replicas = number
  }))
  description = "Per-engagement resource ceilings enforced at the namespace level."
  default = {
    "fds-acme-prod" = {
      cpu_limit    = "4"
      memory_limit = "8Gi"
      max_replicas = 6
    }
  }
}
