output "velocloud_untrusted_public_ip" {
  value       = google_compute_instance.velocloud_edge.network_interface[1].access_config[0].nat_ip
  description = "Public IP of VeloCloud Edge on Untrusted VPC"
}

output "velocloud_untrusted_private_ip" {
  value       = google_compute_instance.velocloud_edge.network_interface[1].network_ip
  description = "Private IP of VeloCloud Edge on Untrusted VPC"
}

output "velocloud_trusted_ip" {
  value       = google_compute_instance.velocloud_edge.network_interface[2].network_ip
  description = "Internal IP of VeloCloud Edge on Trusted VPC"
}

output "paloalto_mgmt_public_ip" {
  value       = google_compute_instance.paloalto_ngfw.network_interface[1].access_config[0].nat_ip
  description = "Public IP of Palo Alto NGFW on Management VPC"
}

output "paloalto_mgmt_private_ip" {
  value       = google_compute_instance.paloalto_ngfw.network_interface[1].network_ip
  description = "Private IP of Palo Alto NGFW on Management VPC"
}

output "paloalto_trusted_ip" {
  value       = google_compute_instance.paloalto_ngfw.network_interface[0].network_ip
  description = "Internal IP of Palo Alto NGFW on Trusted VPC"
}

output "paloalto_2_mgmt_public_ip" {
  value       = google_compute_instance.paloalto_ngfw_2.network_interface[1].access_config[0].nat_ip
  description = "Public IP of Palo Alto NGFW 2 on Management VPC"
}

output "paloalto_2_mgmt_private_ip" {
  value       = google_compute_instance.paloalto_ngfw_2.network_interface[1].network_ip
  description = "Private IP of Palo Alto NGFW 2 on Management VPC"
}

output "paloalto_2_trusted_ip" {
  value       = google_compute_instance.paloalto_ngfw_2.network_interface[0].network_ip
  description = "Internal IP of Palo Alto NGFW 2 on Trusted VPC"
}

output "velocloud_2_untrusted_public_ip" {
  value       = google_compute_instance.velocloud_edge_2.network_interface[1].access_config[0].nat_ip
  description = "Public IP of VeloCloud Edge 2 on Untrusted-2 VPC"
}

output "velocloud_2_untrusted_private_ip" {
  value       = google_compute_instance.velocloud_edge_2.network_interface[1].network_ip
  description = "Private IP of VeloCloud Edge 2 on Untrusted-2 VPC"
}

output "velocloud_2_trusted_ip" {
  value       = google_compute_instance.velocloud_edge_2.network_interface[2].network_ip
  description = "Internal IP of VeloCloud Edge 2 on Trusted VPC"
}
