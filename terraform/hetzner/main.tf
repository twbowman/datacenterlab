terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
}

# ─────────────────────────────────────────────────────────────
# SSH Key
# ─────────────────────────────────────────────────────────────

resource "hcloud_ssh_key" "lab" {
  name       = "${var.server_name}-key"
  public_key = var.ssh_public_key_content
}

# ─────────────────────────────────────────────────────────────
# Firewall — SSH + gNMI + monitoring
# ─────────────────────────────────────────────────────────────

resource "hcloud_firewall" "lab" {
  name = "${var.server_name}-fw"

  # SSH
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # gNMI (SR Linux default)
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "57400"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # gNMI (gNMIc collector)
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "9273"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # Grafana
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "3000"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # Prometheus
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "9090"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # Allow all outbound
  rule {
    direction       = "out"
    protocol        = "tcp"
    port            = "1-65535"
    destination_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction       = "out"
    protocol        = "udp"
    port            = "1-65535"
    destination_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction       = "out"
    protocol        = "icmp"
    destination_ips = ["0.0.0.0/0", "::/0"]
  }
}

# ─────────────────────────────────────────────────────────────
# Server
# ─────────────────────────────────────────────────────────────

resource "hcloud_server" "lab" {
  name        = var.server_name
  server_type = var.server_type
  location    = var.location
  image       = var.image
  ssh_keys    = [hcloud_ssh_key.lab.id]

  firewall_ids = [hcloud_firewall.lab.id]

  labels = {
    purpose = "containerlab"
    project = "dc-fabric"
  }

  # Wait for SSH to become available, then run remote-setup.sh
  connection {
    type        = "ssh"
    user        = "root"
    private_key = var.ssh_private_key_content
    host        = self.ipv4_address
    timeout     = "2m"
  }

  provisioner "file" {
    source      = "${path.module}/../../scripts/remote-setup.sh"
    destination = "/tmp/remote-setup.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /tmp/remote-setup.sh",
      "/tmp/remote-setup.sh",
    ]
  }
}
