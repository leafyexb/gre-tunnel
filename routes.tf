resource "google_compute_route" "untrusted_2_to_trusted_route" {
  name        = "untrusted-2-to-trusted-route"
  dest_range  = "10.10.0.0/16"
  network     = google_compute_network.untrusted_2_vpc.name
  next_hop_ip = google_compute_instance.velocloud_edge_2.network_interface[1].network_ip
  priority    = 100
}

resource "google_compute_route" "untrusted_to_trusted_route" {
  name        = "untrusted-to-trusted-route"
  dest_range  = "10.10.0.0/16"
  network     = google_compute_network.untrusted_vpc.name
  next_hop_ip = google_compute_instance.velocloud_edge.network_interface[1].network_ip
  priority    = 100
}


