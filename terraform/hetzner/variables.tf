variable "server_name" {
  type = string
}

variable "server_type" {
  type = string
}

variable "location" {
  type = string
}

variable "image" {
  type = string
}

variable "ssh_public_key_content" {
  description = "SSH public key content (not path)"
  type        = string
}

variable "ssh_private_key_content" {
  description = "SSH private key content (not path)"
  type        = string
  sensitive   = true
}
