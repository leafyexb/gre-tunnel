# GCP GRE Tunnel & Palo Alto NGFW / VeloCloud SD-WAN Integration

This repository contains Terraform infrastructure code, appliance configurations, and automation scripts for deploying high-availability Palo Alto Networks VM-Series Next-Generation Firewalls (NGFW) integrated with VMware VeloCloud SD-WAN Edges in Google Cloud Platform (GCP) via Generic Routing Encapsulation (GRE) tunnels and dynamic BGP peering.

---

## Architecture Overview

```
                          +-------------------------+
                          |   test-vpc (Workload)   |
                          |      10.10.6.0/24       |
                          +------------+------------+
                                       |
                                 [VPC Peering]
                                       |
+--------------------------------------v--------------------------------------+
|                           trusted-vpc (10.10.3.0/24)                        |
|                                                                             |
|      +---------------------------------------------------------------+      |
|      |               Internal TCP/UDP Load Balancer (ILB)            |      |
|      |                         VIP: 10.10.3.3                        |      |
|      +-------------------------------+-------------------------------+      |
|                                      |                                      |
|             +------------------------+------------------------+             |
|             |                                                 |             |
|   +---------v---------+                             +---------v---------+   |
|   |   paloalto-ngfw   |                             |  paloalto-ngfw-2  |   |
|   |  Trust: 10.10.3.10|                             |  Trust: 10.10.3.11|   |
|   +---------+---------+                             +---------+---------+   |
|             |   ^                                             |   ^         |
|   [GRE-1]   |   | [HA2 Sync: 10.10.7.0/24]                    |   | [GRE-2] |
|             v   +---------------------------------------------+   v         |
|   +-------------------+                             +-------------------+   |
|   |  velocloud-edge   |                             | velocloud-edge-2  |   |
|   |  Trust: 10.10.3.20|                             |  Trust: 10.10.3.21|   |
|   +---------+---------+                             +---------+---------+   |
+-------------|-----------------------------------------------------|---------+
              |                                                     |
    +---------v---------+                                 +---------v---------+
    |   untrusted-vpc   |                                 |  untrusted-2-vpc  |
    |   10.10.2.0/24    |                                 |   10.10.5.0/24    |
    |  WAN IP / Overlay |                                 |  WAN IP / Overlay |
    +-------------------+                                 +-------------------+
```

### Key Highlights
- **VPC Segmentation**: 6 dedicated VPC networks (`trusted`, `untrusted`, `untrusted-2`, `paloalto-mgmt`, `paloalto-ha2`, `test-vpc`) ensuring strict security and routing isolation.
- **GRE Tunnels**: Point-to-point GRE encapsulation over GCP internal network fabric between Palo Alto VM-Series firewalls and VeloCloud SD-WAN Edges.
- **Dynamic Routing**: eBGP sessions established across tunnel interfaces (`tunnel.1`, `tunnel.2`) exchanging routes with custom MED metrics and prefix filters.
- **Traffic Inspection & Load Balancing**: Internal Load Balancer distributing workload traffic to the Palo Alto NGFWs with customized health checking (`allow-hc`).

---

## Repository Structure

```
├── README.md                          # Project documentation and deployment guide
├── architecture.md                    # Detailed architecture and network specification
├── appliance_config.md                # Step-by-step PAN-OS and VeloCloud CLI guide
├── palo_ha_topology.jpg               # High-level architecture topology diagram
│
├── *.tf                               # Terraform infrastructure manifests
│   ├── provider.tf                    # GCP provider settings and version constraints
│   ├── variables.tf                   # Deployment variables and VM image definitions
│   ├── vpc.tf                         # VPCs, subnets, and security firewall rules
│   ├── paloalto.tf                    # Palo Alto NGFW VM instances and network interfaces
│   ├── velocloud.tf                   # VeloCloud SD-WAN Edge VM instances and metadata
│   ├── test_networks.tf               # Test workload VPC, test client VM, and ILB setup
│   ├── routes.tf                      # Static routes for untrusted VPC transit
│   └── outputs.tf                     # Exported instance IPs and management endpoints
│
├── paloalto_*_config.*                # Palo Alto PAN-OS running and restored configurations
│   ├── paloalto_running_config.xml    # Active XML running configuration (Firewall 1)
│   ├── paloalto_running_config_2.xml  # Active XML running configuration (Firewall 2)
│   ├── paloalto_running_config.txt    # Hierarchical text configuration (Firewall 1)
│   ├── paloalto_running_config_2.txt  # Hierarchical text configuration (Firewall 2)
│   ├── paloalto_running_config_set.txt# Set-command syntax configuration (Firewall 1)
│   ├── paloalto_running_config_2_set.txt# Set-command syntax configuration (Firewall 2)
│   ├── paloalto_clean_config.xml      # Base sanitized XML configuration template
│   └── paloalto_restored_config*.xml  # Validated restored configuration snapshots
│
└── *.py                               # Automation & operational scripts
    ├── configure_palo_2.py            # Automated PAN-OS provisioning script
    ├── download_palo_configs.py       # Configuration extraction utility via SSH
    ├── run_palo_backup.py             # Periodic configuration backup utility
    └── backup_script.py               # Firewall snapshot backup script
```

---

## Deployment Prerequisites

1. **Google Cloud SDK (`gcloud`)**: Authenticated with adequate permissions on the target GCP project.
2. **Terraform**: Version `>= 1.0.0` with the Google Cloud provider `~> 5.0`.
3. **SSH Keypair**: An SSH public key at `paloalto-key.pub` for instance bootstrapping.
4. **Appliance Licenses / Images**:
   - Palo Alto VM-Series (`vmseries-flex-bundle2-1104h1` or BYOL/PAYG equivalent)
   - VMware VeloCloud Edge (`vce-342-102-r342-20200610-ga-3f5ad3b9e2`)

---

## Quick Start

### 1. Initialize & Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review execution plan
terraform plan -var="project_id=<YOUR_PROJECT_ID>"

# Deploy the topology
terraform apply -var="project_id=<YOUR_PROJECT_ID>"
```

### 2. Configure Palo Alto Firewalls

Use the provided automation script or execute the configuration commands in `appliance_config.md`:

```bash
python3 configure_palo_2.py
```

### 3. Backup & Verify Configurations

```bash
# Download active running configuration snapshots in XML and set formats
python3 download_palo_configs.py
```
