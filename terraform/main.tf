locals {
  nodes = {
    db = {
      ip = "192.168.56.10"
    }
    app = {
      ip = "192.168.56.11"
    }
    nginx = {
      ip = "192.168.56.12"
    }
  }

  ssh_authorized_key = trimspace(file(pathexpand(var.ssh_public_key_path)))
}

resource "libvirt_network" "lab" {
  name      = "mywebapp-net"
  mode      = "nat"
  domain    = var.network_domain
  addresses = [var.network_cidr]

  dhcp {
    enabled = true
  }
}

resource "libvirt_volume" "base" {
  name   = "mywebapp-base.qcow2"
  pool   = var.libvirt_pool
  source = var.base_image_url
  format = "qcow2"
}

resource "libvirt_volume" "node" {
  for_each        = local.nodes
  name            = "${each.key}.qcow2"
  pool            = var.libvirt_pool
  base_volume_id  = libvirt_volume.base.id
  size            = var.disk_size_gb * 1024 * 1024 * 1024
}

resource "libvirt_cloudinit_disk" "node" {
  for_each = local.nodes
  name     = "${each.key}-cloudinit.iso"
  pool     = var.libvirt_pool

  user_data = templatefile("${path.module}/cloud-init/user-data.yaml", {
    hostname           = each.key
    ssh_authorized_key = local.ssh_authorized_key
  })
}

resource "libvirt_domain" "node" {
  for_each = local.nodes

  name   = each.key
  memory = var.vm_memory_mb
  vcpu   = var.vm_vcpu

  cloudinit = libvirt_cloudinit_disk.node[each.key].id

  network_interface {
    network_id = libvirt_network.lab.id
    addresses  = [each.value.ip]
  }

  disk {
    volume_id = libvirt_volume.node[each.key].id
  }

  console {
    type        = "pty"
    target_type = "serial"
    target_port = "0"
  }

  graphics {
    type        = "spice"
    listen_type = "address"
    autoport    = true
  }
}
