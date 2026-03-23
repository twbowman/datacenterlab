# Root module — dispatches to cloud-specific modules.
# Currently only Hetzner is implemented.

terraform {
  required_version = ">= 1.5"
}

module "hetzner" {
  source = "./hetzner"
  count  = var.cloud_provider == "hetzner" ? 1 : 0

  server_name      = var.server_name
  server_type      = var.server_type
  location         = var.location
  image            = var.image
  ssh_public_key_path  = var.ssh_public_key_path
  ssh_private_key_path = var.ssh_private_key_path
}
