resource "google_compute_instance" "velocloud_edge" {
  name           = "velocloud-edge"
  machine_type   = var.velocloud_machine_type
  zone           = var.zone
  can_ip_forward            = true
  allow_stopping_for_update = true

  tags = ["mgmt-access", "nva-appliance"]

  # nic0: Mgmt
  network_interface {
    subnetwork = google_compute_subnetwork.mgmt_subnet.id
    access_config {
      // Ephemeral public IP for management outbound access to VCO
    }
  }

  # nic1: GE2 - WAN (Public)
  network_interface {
    subnetwork = google_compute_subnetwork.untrusted_subnet.id
    network_ip = "10.10.2.11"
    access_config {
      // Ephemeral public IP for SD-WAN overlay
    }
  }

  # nic2: GE3 - LAN (GRE Transit)
  network_interface {
    subnetwork = google_compute_subnetwork.trusted_subnet.id
    network_ip = "10.10.3.20"
    // No external IP
  }

  boot_disk {
    initialize_params {
      image = var.velocloud_image
      type  = "pd-ssd"
      size  = 66 # VeloCloud virtual edge standard disk size is 66 GB
    }
  }

  service_account {
    email  = "velocloud@test-terraform-nsi.iam.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }

  metadata = {
    # VeloCloud Edge uses cloud-init user-data to activate itself to a VeloCloud Orchestrator.
    # Populate these placeholder values with actual activation parameters if deploying in a real environment.
    user-data = <<EOF
#cloud-config
velocloud:
  vce:
    vco: "veco58-kiad1.velocloud.net"
    activation_code: "UARN-FAVZ-RQBD-FC7T"
EOF
    serial-port-enable = "true"
  }
}

resource "google_compute_instance" "velocloud_edge_2" {
  name           = "velocloud-edge-2"
  machine_type   = var.velocloud_machine_type
  zone           = var.zone
  can_ip_forward             = true
  allow_stopping_for_update = true

  tags = ["mgmt-access", "nva-appliance"]

  # nic0: Mgmt
  network_interface {
    subnetwork = google_compute_subnetwork.mgmt_subnet.id
    access_config {
      // Ephemeral public IP for management outbound access to VCO
    }
  }

  # nic1: GE2 - WAN (Public)
  network_interface {
    subnetwork = google_compute_subnetwork.untrusted_2_subnet.id
    network_ip = "10.10.5.3"
    access_config {
      // Ephemeral public IP for SD-WAN overlay
    }
  }

  # nic2: GE3 - LAN (GRE Transit)
  network_interface {
    subnetwork = google_compute_subnetwork.trusted_subnet.id
    network_ip = "10.10.3.21"
    // No external IP
  }

  boot_disk {
    initialize_params {
      image = var.velocloud_image
      type  = "pd-ssd"
      size  = 66
    }
  }

  service_account {
    email  = "velocloud@test-terraform-nsi.iam.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }

  metadata = {
    user-data = <<EOF
#cloud-config
velocloud:
  vce:
    vco: "veco58-kiad1.velocloud.net"
    activation_code: "GNPV-WSRM-M2TB-RURF"
EOF
    serial-port-enable = "true"
  }
}
