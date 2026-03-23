# Outputs — normalized across cloud providers.

output "server_ip" {
  description = "Public IP of the lab server"
  value       = var.cloud_provider == "hetzner" ? module.hetzner[0].server_ip : "not implemented"
}

output "ssh_command" {
  description = "SSH command to connect to the lab server"
  value       = "ssh -i ${var.ssh_private_key_path} root@${var.cloud_provider == "hetzner" ? module.hetzner[0].server_ip : "unknown"}"
}

output "env_file_content" {
  description = "Content for .env file (paste into .env)"
  value       = <<-EOT
    LAB_HOST=${var.cloud_provider == "hetzner" ? module.hetzner[0].server_ip : "unknown"}
    LAB_USER=root
    LAB_SSH_KEY=${var.ssh_private_key_path}
    LAB_PORT=22
    LAB_REMOTE_DIR=/opt/containerlab
    LAB_VENDOR=srlinux
  EOT
}
