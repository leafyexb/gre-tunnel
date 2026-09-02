resource "google_compute_instance" "paloalto_ngfw" {
  name           = "paloalto-ngfw"
  machine_type   = var.paloalto_machine_type
  zone           = var.zone
  can_ip_forward             = true
  allow_stopping_for_update = true

  tags = ["mgmt-access", "nva-appliance"]

  # nic0: Trust (LAN) Interface
  network_interface {
    subnetwork = google_compute_subnetwork.trusted_subnet.id
    network_ip = "10.10.3.10"
    // No public IP
  }

  # nic1: Management Interface
  network_interface {
    subnetwork = google_compute_subnetwork.mgmt_subnet.id
    access_config {
      // Ephemeral public IP for internet and management access
    }
  }

  # nic2: HA2 (Data Link) Interface
  network_interface {
    subnetwork = google_compute_subnetwork.ha2_subnet.id
    network_ip = "10.10.7.10"
  }


  boot_disk {
    initialize_params {
      image = var.paloalto_image
      type  = "pd-ssd"
      size  = 60
    }
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  metadata = {
    mgmt-interface-swap = "enable"
    serial-port-enable  = "true"
    ssh-keys            = "admin:${file("${path.module}/paloalto-key.pub")}"
  }
}

resource "google_compute_instance" "paloalto_ngfw_2" {
  name           = "paloalto-ngfw-2"
  machine_type   = var.paloalto_machine_type
  zone           = var.zone
  can_ip_forward             = true
  allow_stopping_for_update = true

  tags = ["mgmt-access", "nva-appliance"]

  # nic0: Trust (LAN) Interface
  network_interface {
    subnetwork = google_compute_subnetwork.trusted_subnet.id
    network_ip = "10.10.3.11"
    // No public IP
  }

  # nic1: Management Interface
  network_interface {
    subnetwork = google_compute_subnetwork.mgmt_subnet.id
    access_config {
      // Ephemeral public IP for internet and management access
    }
  }

  # nic2: HA2 (Data Link) Interface
  network_interface {
    subnetwork = google_compute_subnetwork.ha2_subnet.id
    network_ip = "10.10.7.11"
  }


  boot_disk {
    initialize_params {
      image = var.paloalto_image
      type  = "pd-ssd"
      size  = 60
    }
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  metadata = {
    mgmt-interface-swap = "enable"
    serial-port-enable  = "true"
    ssh-keys            = "admin:${file("${path.module}/paloalto-key.pub")}"
  }
}

