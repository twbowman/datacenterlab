variable "cloud_provider" {
  description = "Cloud provider to deploy lab server (hetzner, aws, gcp — only hetzner implemented)"
  type        = string
  default     = "hetzner"

  validation {
    condition     = contains(["hetzner"], var.cloud_provider)
    error_message = "Only 'hetzner' is currently supported."
  }
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key for server access"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "ssh_private_key_path" {
  description = "Path to SSH private key (used for provisioning)"
  type        = string
  default     = "~/.ssh/id_ed25519"
}

variable "server_name" {
  description = "Name for the lab server"
  type        = string
  default     = "dclab"
}

variable "server_type" {
  description = "Server size (Hetzner: cpx32=4vCPU/8GB, cpx42=8vCPU/16GB, cx32=4vCPU/8GB shared)"
  type        = string
  default     = "cpx32"
}

variable "location" {
  description = "Server location (Hetzner: fsn1, nbg1, hel1, ash, hil)"
  type        = string
  default     = "nbg1"
}

variable "image" {
  description = "OS image"
  type        = string
  default     = "ubuntu-24.04"
}
