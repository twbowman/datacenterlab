output "server_ip" {
  description = "Public IPv4 address of the lab server"
  value       = hcloud_server.lab.ipv4_address
}

output "server_id" {
  description = "Hetzner server ID"
  value       = hcloud_server.lab.id
}

output "server_status" {
  description = "Server status"
  value       = hcloud_server.lab.status
}
