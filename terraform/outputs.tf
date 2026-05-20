output "vm_ips" {
  description = "Static IPs assigned to each VM."
  value = {
    for name, node in local.nodes : name => node.ip
  }
}
