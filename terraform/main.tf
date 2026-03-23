# Root module — dispatches to cloud-specific modules.
# Currently only Hetzner is implemented.

terraform {
  required_version = ">= 1.5"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
}

# Token via HCLOUD_TOKEN env var — never in tfvars.
provider "hcloud" {}

# Read SSH keys at the root level where file() can access them
locals {
  ssh_public_key  = file(pathexpand(var.ssh_public_key_path))
  ssh_private_key = file(pathexpand(var.ssh_private_key_path))
}

module "hetzner" {
  source = "./hetzner"
  count  = var.cloud_provider == "hetzner" ? 1 : 0

  server_name             = var.server_name
  server_type             = var.server_type
  location                = var.location
  image                   = var.image
  ssh_public_key_content  = local.ssh_public_key
  ssh_private_key_content = local.ssh_private_key
}
