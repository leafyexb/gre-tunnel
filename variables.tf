variable "project_id" {
  type        = string
  description = "The GCP project ID to deploy resources into"
  default     = ""
}

variable "region" {
  type        = string
  description = "The GCP region to deploy resources into"
  default     = "us-central1"
}

variable "zone" {
  type        = string
  description = "The GCP zone to deploy resources into"
  default     = "us-central1-a"
}

variable "paloalto_image" {
  type        = string
  description = "The image URI or name for the Palo Alto VM-series instance"
  default     = "projects/paloaltonetworksgcp-public/global/images/vmseries-flex-bundle2-1104h1"
}

variable "velocloud_image" {
  type        = string
  description = "The image URI or name for the VeloCloud SD-WAN Edge instance"
  default     = "projects/vmware-sdwan-public/global/images/vce-342-102-r342-20200610-ga-3f5ad3b9e2"
}

variable "paloalto_machine_type" {
  type        = string
  description = "The machine type for the Palo Alto NGFW VM"
  default     = "n1-standard-4"
}

variable "velocloud_machine_type" {
  type        = string
  description = "The machine type for the VeloCloud SD-WAN Edge VM"
  default     = "e2-standard-4"
}
