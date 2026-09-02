resource "google_compute_network" "trusted_vpc" {
  name                    = "trusted"
  auto_create_subnetworks = false
}

resource "google_compute_network" "untrusted_vpc" {
  name                    = "untrusted"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "trusted_subnet" {
  name          = "trusted-subnet"
  ip_cidr_range = "10.10.3.0/24"
  region        = var.region
  network       = google_compute_network.trusted_vpc.id
}

resource "google_compute_subnetwork" "untrusted_subnet" {
  name          = "untrusted-subnet"
  ip_cidr_range = "10.10.2.0/24"
  region        = var.region
  network       = google_compute_network.untrusted_vpc.id
}

# Firewall Rule: Allow SSH and HTTPS from IAP in trusted VPC
resource "google_compute_firewall" "allow_iap_ssh_trusted" {
  name    = "allow-iap-ssh-trusted"
  network = google_compute_network.trusted_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22", "443", "80"]
  }

  source_ranges = ["35.235.240.0/20"]
}

# Firewall Rule: Allow all traffic internal to the trusted VPC
resource "google_compute_firewall" "allow_trusted_internal" {
  name    = "allow-trusted-internal"
  network = google_compute_network.trusted_vpc.name

  allow {
    protocol = "all"
  }

  source_ranges = ["10.10.0.0/16"]
}

# Firewall Rule: Allow SSH/HTTPS/SD-WAN traffic from outside in untrusted VPC (e.g. for Management/Overlay)
resource "google_compute_firewall" "allow_untrusted_external" {
  name    = "allow-untrusted-external"
  network = google_compute_network.untrusted_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22", "443", "80"]
  }

  allow {
    protocol = "udp"
    ports    = ["500", "4500", "2426"] # IPsec VPN & Velocloud VCMP
  }

  source_ranges = ["0.0.0.0/0"]
}

# --- Management VPC ---
resource "google_compute_network" "mgmt_vpc" {
  name                    = "paloalto-mgmt"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "mgmt_subnet" {
  name          = "mgmt-subnet"
  ip_cidr_range = "10.10.1.0/24"
  region        = var.region
  network       = google_compute_network.mgmt_vpc.id
}

resource "google_compute_firewall" "allow_mgmt_external" {
  name    = "allow-mgmt-external"
  network = google_compute_network.mgmt_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22", "443", "80"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# --- Untrusted-2 VPC ---
resource "google_compute_network" "untrusted_2_vpc" {
  name                    = "untrusted-2"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "untrusted_2_subnet" {
  name          = "untrusted-2-subnet"
  ip_cidr_range = "10.10.5.0/24"
  region        = var.region
  network       = google_compute_network.untrusted_2_vpc.id
}

resource "google_compute_firewall" "allow_untrusted_2_external" {
  name    = "allow-untrusted-2-external"
  network = google_compute_network.untrusted_2_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22", "443", "80"]
  }

  allow {
    protocol = "udp"
    ports    = ["500", "4500", "2426"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# --- HA2 VPC ---
resource "google_compute_network" "ha2_vpc" {
  name                    = "paloalto-ha2"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "ha2_subnet" {
  name          = "ha2-subnet"
  ip_cidr_range = "10.10.7.0/24"
  region        = var.region
  network       = google_compute_network.ha2_vpc.id
}

resource "google_compute_firewall" "allow_ha2_internal" {
  name    = "allow-ha2-internal"
  network = google_compute_network.ha2_vpc.name

  allow {
    protocol = "all"
  }

  source_ranges = ["10.10.7.0/24"]
}



