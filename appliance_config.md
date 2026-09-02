# Appliance Configuration Guide: GRE Tunnel Establishment

Since VM configuration settings (such as establishing internal GRE tunnels) are applied within each virtual appliance's operating system (PAN-OS for Palo Alto, and the VeloCloud Orchestrator for SD-WAN), follow these configuration steps after provisioning the GCP infrastructure.

---

## 1. Palo Alto VM-Series (PAN-OS) Configuration

Access the Palo Alto management console (via HTTPS or SSH using the IP output by `paloalto_mgmt_ip`).

### A. Configure the Tunnel Interface
Create a logical tunnel interface and assign it the tunnel IP address:
```text
configure
set network interface tunnel units tunnel.1 ip 172.16.1.2/30
```

### B. Define the GRE Tunnel
Configure the GRE tunnel endpoints, binding the local Trust IP and VeloCloud's Trust IP as the peer:
```text
set network tunnel gre GRE-to-VeloCloud local-address ip 10.10.3.10
set network tunnel gre GRE-to-VeloCloud peer-address ip 10.10.3.20
set network tunnel gre GRE-to-VeloCloud tunnel-interface tunnel.1
```

### C. Configure BGP Routing
Attach the tunnel interface to the virtual router, enable BGP, and configure peering with the VeloCloud Edge (AS 65002):
```text
set network virtual-router default interface [ ethernet1/1 ethernet1/2 tunnel.1 ]
set network virtual-router default protocol bgp enable yes
set network virtual-router default protocol bgp router-id 172.16.1.2
set network virtual-router default protocol bgp local-as 65001

# Create BGP Peer Group and Peer connection
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud enable yes
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud peer Peer-VeloCloud enable yes
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud peer Peer-VeloCloud peer-address ip 172.16.1.1
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud peer Peer-VeloCloud peer-as 65002
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud peer Peer-VeloCloud local-address ip 172.16.1.2/30 interface tunnel.1
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud peer Peer-VeloCloud connection-options incoming-connection accept yes
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud peer Peer-VeloCloud connection-options outgoing-connection start yes

# Commit changes
commit
```

---

## 2. VeloCloud SD-WAN Edge Configuration

VeloCloud Edges are managed centrally via the VeloCloud Orchestrator (VCO). 

### A. Create a Non-VeloCloud Site (Generic GRE)
1. Log in to the VeloCloud Orchestrator.
2. Navigate to **Configure > Network Services** or **Configure > Profiles > Device > Non-VeloCloud Sites**.
3. Click **New Non-VeloCloud Site**.
4. Configure the parameters:
   - **Name**: `PaloAlto-Hub`
   - **Type**: `Generic GRE` (or Generic IPsec/GRE depending on VCO version)
   - **Primary VPN Gateway (IP Address)**: `10.10.3.10` (Palo Alto Trust IP)
5. Save the configuration.

### B. Configure Interface and Tunnel IP
In the site settings, configure the tunnel subnet matching the Palo Alto side:
- **Local IP**: `172.16.1.1/30`
- **Remote Peer IP**: `172.16.1.2/30`

### C. Configure BGP Peering & Advertise Routes
To exchange routes dynamically with Palo Alto:
1. In the Non-VeloCloud Site configuration, enable the **BGP** checkbox.
2. Set the following parameters:
   - **Local AS**: `65002` (VeloCloud AS)
   - **Neighbor IP**: `172.16.1.2` (Palo Alto Tunnel IP)
   - **Neighbor AS**: `65001` (Palo Alto AS)
3. Configure the profile to advertise local LAN prefixes (such as `10.10.4.0/24`) to the peer and learn the default route `0.0.0.0/0` advertised by Palo Alto.
4. Save and apply the configuration.

---

## 3. Palo Alto VM-2 (PAN-OS) Configuration (Passive/Secondary)

Access the second Palo Alto management console (via SSH using `136.115.159.14` or internally using the private management IP `10.10.1.11`).

### A. Configure the Interface Management Profile
Enable SSH and Ping on the data interface (`ethernet1/1`) so that GCP regional health check probes on port 22 can verify the appliance state:
```text
configure
set network profiles interface-management-profile allow-hc ssh yes ping yes
set network interface ethernet ethernet1/1 layer3 interface-management-profile allow-hc
```

### B. Configure Loopback & Tunnel Interfaces
Assign the shared Load Balancer VIP to `loopback.1` and define the second BGP peer IP on `tunnel.2`:
```text
set network interface loopback units loopback.1 ip 10.10.3.3/32
set network interface tunnel units tunnel.2 ip 169.254.31.6/30
```

### C. Configure GRE Tunnel
Define the GRE tunnel endpoints, binding the local VM-2 IP (`10.10.3.11`) and VeloCloud Edge 2 IP (`10.10.3.21`) as the peer:
```text
set network tunnel gre velo-2 local-address ip 10.10.3.11/24
set network tunnel gre velo-2 local-address interface ethernet1/1
set network tunnel gre velo-2 peer-address ip 10.10.3.21
set network tunnel gre velo-2 tunnel-interface tunnel.2
```

### D. Configure Static Routing & Virtual Router
Bind interfaces to the default virtual router and add routes for health checks, test client VPC transit, and the default gateway:
```text
set network virtual-router default interface ethernet1/1
set network virtual-router default interface loopback.1
set network virtual-router default interface tunnel.2
set network virtual-router default routing-table ip static-route Route-to-Test-VPC destination 10.10.6.0/24 nexthop ip-address 10.10.3.1
set network virtual-router default routing-table ip static-route Route-to-Health-Check-1 destination 35.191.0.0/16 nexthop ip-address 10.10.3.1
set network virtual-router default routing-table ip static-route Route-to-Health-Check-2 destination 130.211.0.0/22 nexthop ip-address 10.10.3.1
set network virtual-router default routing-table ip static-route default-route destination 0.0.0.0/0 nexthop ip-address 10.10.3.1 interface ethernet1/1
```

### E. Configure BGP Peering
Enable BGP and define the peer connection targeting VeloCloud Edge 2 (AS 65002, Peer IP `169.254.31.5`):
```text
set network virtual-router default protocol bgp enable yes
set network virtual-router default protocol bgp router-id 169.254.31.6
set network virtual-router default protocol bgp local-as 65001
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 enable yes
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 enable yes
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 peer-address ip 169.254.31.5
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 peer-as 65002
set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 local-address ip 169.254.31.6/30 interface tunnel.2
```

### F. Bind Zones & Configure Security Policies
Place the interfaces in the `Trust` zone and explicitly allow GCP health checks:
```text
set zone Trust network layer3 ethernet1/1
set zone Trust network layer3 loopback.1
set zone Trust network layer3 tunnel.2
set rulebase security rules GCP-ILB-HealthCheck-Allow from Trust to Trust source 35.191.0.0/16
set rulebase security rules GCP-ILB-HealthCheck-Allow from Trust to Trust source 130.211.0.0/22
set rulebase security rules GCP-ILB-HealthCheck-Allow from Trust to Trust destination 10.10.3.11/32
set rulebase security rules GCP-ILB-HealthCheck-Allow from Trust to Trust destination 10.10.3.3/32
set rulebase security rules GCP-ILB-HealthCheck-Allow service any application any action allow
```

### G. Commit Changes
Apply and save all configurations to the active plane:
```text
commit
exit
```

