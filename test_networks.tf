

resource "google_compute_firewall" "allow_http_untrusted" {
  name    = "allow-http-untrusted"
  network = google_compute_network.untrusted_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
}



resource "google_compute_firewall" "allow_http_untrusted_2" {
  name    = "allow-http-untrusted-2"
  network = google_compute_network.untrusted_2_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
}

# --- Test VPC and Peering ---
resource "google_compute_network" "test_vpc" {
  name                    = "test-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "test_subnet" {
  name          = "test-subnet"
  ip_cidr_range = "10.10.6.0/24"
  region        = var.region
  network       = google_compute_network.test_vpc.id
}

resource "google_compute_network_peering" "trusted_to_test" {
  name                 = "trusted-to-test"
  network              = google_compute_network.trusted_vpc.id
  peer_network         = google_compute_network.test_vpc.id
  export_custom_routes = true
  import_custom_routes = true
}

resource "google_compute_network_peering" "test_to_trusted" {
  name                 = "test-to-trusted"
  network              = google_compute_network.test_vpc.id
  peer_network         = google_compute_network.trusted_vpc.id
  export_custom_routes = true
  import_custom_routes = true
}

# --- Test Client (Test VPC) ---
resource "google_compute_instance" "test_client" {
  name         = "test-client"
  machine_type = "e2-micro"
  zone         = var.zone

  network_interface {
    subnetwork = google_compute_subnetwork.test_subnet.id
    // No external IP
  }

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 10
    }
  }

  service_account {
    scopes = ["cloud-platform"]
  }
}

# --- Internal Load Balancer (ILB) in Trusted VPC ---
resource "google_compute_instance_group" "paloalto_group_primary" {
  name        = "paloalto-group-primary"
  zone        = var.zone
  description = "Unmanaged instance group for primary Palo Alto NGFW"
  network     = google_compute_network.trusted_vpc.id
  instances   = [
    google_compute_instance.paloalto_ngfw.self_link
  ]
}

resource "google_compute_instance_group" "paloalto_group_secondary" {
  name        = "paloalto-group-secondary"
  zone        = var.zone
  description = "Unmanaged instance group for failover Palo Alto NGFW"
  network     = google_compute_network.trusted_vpc.id
  instances   = [
    google_compute_instance.paloalto_ngfw_2.self_link
  ]
}

resource "google_compute_region_health_check" "paloalto_ilb_health_check" {
  name               = "paloalto-ilb-health-check"
  region             = var.region
  check_interval_sec = 5
  timeout_sec        = 5

  tcp_health_check {
    port = 22 # Checking SSH port 22 on ethernet1/1
  }
}

resource "google_compute_region_backend_service" "paloalto_ilb_backend" {
  name                  = "paloalto-ilb-backend"
  region                = var.region
  load_balancing_scheme = "INTERNAL"
  protocol              = "UNSPECIFIED"

  backend {
    group    = google_compute_instance_group.paloalto_group_primary.id
    failover = false
  }

  backend {
    group    = google_compute_instance_group.paloalto_group_secondary.id
    failover = true
  }

  failover_policy {
    disable_connection_drain_on_failover = false
    drop_traffic_if_unhealthy            = true
    failover_ratio                       = 0.0 # Fail over when 0% of instances in primary group are healthy
  }

  health_checks = [google_compute_region_health_check.paloalto_ilb_health_check.id]
}

resource "google_compute_forwarding_rule" "paloalto_ilb_forwarding_rule" {
  name                  = "paloalto-ilb-forwarding-rule"
  region                = var.region
  network               = google_compute_network.trusted_vpc.id
  subnetwork            = google_compute_subnetwork.trusted_subnet.id
  load_balancing_scheme = "INTERNAL"
  backend_service       = google_compute_region_backend_service.paloalto_ilb_backend.id
  all_ports             = true
  ip_protocol           = "TCP"
  allow_global_access   = true
}

# --- Static Route in Test VPC pointing to ILB ---
resource "google_compute_route" "trusted_default_route_to_ilb" {
  name         = "trusted-default-route-to-ilb"
  dest_range   = "0.0.0.0/0"
  network      = google_compute_network.trusted_vpc.name
  next_hop_ilb = google_compute_forwarding_rule.paloalto_ilb_forwarding_rule.id
  priority     = 100
}

# --- Firewall Rule: Allow GCP Health Checks to Trusted VPC ---
resource "google_compute_firewall" "allow_health_checks_trusted" {
  name    = "allow-health-checks-trusted"
  network = google_compute_network.trusted_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
}

# --- Firewall Rule: Allow SSH from IAP in Test VPC ---
resource "google_compute_firewall" "allow_iap_ssh_test" {
  name    = "allow-iap-ssh-test"
  network = google_compute_network.test_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
}

# --- Firewall Rule: Allow HTTP internal transit in Test VPC ---
resource "google_compute_firewall" "allow_http_test" {
  name    = "allow-http-test"
  network = google_compute_network.test_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
}
