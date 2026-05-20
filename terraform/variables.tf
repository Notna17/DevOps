variable "libvirt_uri" {
  description = "Libvirt connection URI."
  type        = string
  default     = "qemu:///system"
}

variable "libvirt_pool" {
  description = "Libvirt storage pool to use."
  type        = string
  default     = "default"
}

variable "network_cidr" {
  description = "CIDR for the lab network."
  type        = string
  default     = "192.168.56.0/24"
}

variable "network_domain" {
  description = "DNS domain for the libvirt network."
  type        = string
  default     = "mywebapp.local"
}

variable "base_image_url" {
  description = "Cloud image URL used as a base volume."
  type        = string
  default     = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
}

variable "ssh_public_key_path" {
  description = "Path to the public SSH key injected via cloud-init."
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "vm_memory_mb" {
  description = "Memory for each VM in MB."
  type        = number
  default     = 2048
}

variable "vm_vcpu" {
  description = "vCPU count for each VM."
  type        = number
  default     = 2
}

variable "disk_size_gb" {
  description = "Disk size for each VM in GB."
  type        = number
  default     = 12
}
