locals {
  name_prefix  = "${var.project_name}-${var.environment}"
  project_root = abspath("${path.module}/../../..")

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = "data-engineering"
  }
}
