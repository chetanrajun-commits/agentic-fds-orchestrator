output "vpc_id" {
  description = "VPC ID for the FDS mesh."
  value       = module.vpc.vpc_id
}

output "eks_cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint."
  value       = module.eks.cluster_endpoint
}

output "engagement_namespaces" {
  description = "Namespaces provisioned for each engagement."
  value       = [for ns in kubernetes_namespace.engagement : ns.metadata[0].name]
}
