#!/usr/bin/env python3
import subprocess
import time
import sys

# Configuration variables
VM_IP = "136.115.159.14"
SSH_KEY = "paloalto-key"
USER = "admin"

commands = [
    # A. Interface Management Profile & Interface IP
    "set network profiles interface-management-profile allow-hc ssh yes ping yes",
    "set network interface ethernet ethernet1/1 layer3 interface-management-profile allow-hc",
    "set network interface ethernet ethernet1/1 layer3 ip 10.10.3.11/24",
    
    # B. Loopback & Tunnel Interfaces
    "set network interface loopback units loopback.1 ip 10.10.3.3/32",
    "set network interface loopback units loopback.1 comment 'GCP ILB Health Check VIP'",
    "set network interface loopback units loopback.1 interface-management-profile allow-hc",
    
    "set network interface tunnel units tunnel.1 ip 169.254.30.6/29",
    "set network interface tunnel units tunnel.1 interface-management-profile allow-hc",
    
    "set network interface tunnel units tunnel.2 ip 169.254.31.6/29",
    "set network interface tunnel units tunnel.2 interface-management-profile allow-hc",
    
    # C. GRE Tunnels definition
    # Tunnel to Edge 1 (velo-1)
    "set network tunnel gre velo-1 local-address ip 10.10.3.11",
    "set network tunnel gre velo-1 local-address interface ethernet1/1",
    "set network tunnel gre velo-1 peer-address ip 10.10.3.20",
    "set network tunnel gre velo-1 tunnel-interface tunnel.1",
    "set network tunnel gre velo-1 keep-alive enable no",
    
    # Tunnel to Edge 2 (velo-2)
    "set network tunnel gre velo-2 local-address ip 10.10.3.11",
    "set network tunnel gre velo-2 local-address interface ethernet1/1",
    "set network tunnel gre velo-2 peer-address ip 10.10.3.21",
    "set network tunnel gre velo-2 tunnel-interface tunnel.2",
    "set network tunnel gre velo-2 keep-alive enable no",
    
    # D. Virtual Router interface assignments
    "set network virtual-router default interface ethernet1/1",
    "set network virtual-router default interface loopback.1",
    "set network virtual-router default interface tunnel.1",
    "set network virtual-router default interface tunnel.2",
    
    # E. Static routing & Host routes for BGP peers
    "set network virtual-router default routing-table ip static-route Route-to-Test-VPC destination 10.10.6.0/24 nexthop ip-address 10.10.3.1",
    "set network virtual-router default routing-table ip static-route Route-to-Health-Check-1 destination 35.191.0.0/16 nexthop ip-address 10.10.3.1",
    "set network virtual-router default routing-table ip static-route Route-to-Health-Check-2 destination 130.211.0.0/22 nexthop ip-address 10.10.3.1",
    "set network virtual-router default routing-table ip static-route default-route destination 0.0.0.0/0 nexthop ip-address 10.10.3.1 interface ethernet1/1",
    
    "set network virtual-router default routing-table ip static-route route-velo1 destination 169.254.30.5/32 interface tunnel.1",
    "set network virtual-router default routing-table ip static-route route-velo2 destination 169.254.31.5/32 interface tunnel.2",
    
    # F. BGP dynamic routing
    "set network virtual-router default protocol bgp enable yes",
    "set network virtual-router default protocol bgp router-id 169.254.30.6",
    "set network virtual-router default protocol bgp local-as 65001",
    "set network virtual-router default protocol bgp install-route yes",
    
    # BGP Peer Group 1 (to Edge 1)
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 enable yes",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 type ebgp remove-private-as yes",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 type ebgp import-nexthop original",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 type ebgp export-nexthop resolve",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 peer peer-velo1 enable yes",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 peer peer-velo1 peer-address ip 169.254.30.5",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 peer peer-velo1 peer-as 65003",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 peer peer-velo1 local-address ip 169.254.30.6/29 interface tunnel.1",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 peer peer-velo1 connection-options incoming-bgp-connection allow yes",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-1 peer peer-velo1 connection-options outgoing-bgp-connection allow yes",
    
    # BGP Peer Group 2 (to Edge 2)
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 enable yes",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 type ebgp remove-private-as yes",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 type ebgp import-nexthop original",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 type ebgp export-nexthop resolve",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 enable yes",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 peer-address ip 169.254.31.5",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 peer-as 65002",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 local-address ip 169.254.31.6/29 interface tunnel.2",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 connection-options incoming-bgp-connection allow yes",
    "set network virtual-router default protocol bgp peer-group Group-to-VeloCloud-2 peer peer-velo-2 connection-options outgoing-bgp-connection allow yes",
    
    # BGP Policies - Split
    "set network virtual-router default protocol bgp policy export rules Export-Test-VPC action allow update as-path none",
    "set network virtual-router default protocol bgp policy export rules Export-Test-VPC action allow update community none",
    "set network virtual-router default protocol bgp policy export rules Export-Test-VPC action allow update extended-community none",
    "set network virtual-router default protocol bgp policy export rules Export-Test-VPC match route-table unicast",
    "set network virtual-router default protocol bgp policy export rules Export-Test-VPC match address-prefix 10.10.6.0/24 exact yes",
    "set network virtual-router default protocol bgp policy export rules Export-Test-VPC used-by Group-to-VeloCloud-1",
    "set network virtual-router default protocol bgp policy export rules Export-Test-VPC used-by Group-to-VeloCloud-2",
    
    "set network virtual-router default protocol bgp policy import rules \"import from Velo\" action allow update as-path none",
    "set network virtual-router default protocol bgp policy import rules \"import from Velo\" action allow update community none",
    "set network virtual-router default protocol bgp policy import rules \"import from Velo\" action allow update extended-community none",
    "set network virtual-router default protocol bgp policy import rules \"import from Velo\" match route-table unicast",
    "set network virtual-router default protocol bgp policy import rules \"import from Velo\" used-by Group-to-VeloCloud-1",
    "set network virtual-router default protocol bgp policy import rules \"import from Velo\" used-by Group-to-VeloCloud-2",
    
    "set network virtual-router default protocol bgp redist-rules redist-static enable yes",
    "set network virtual-router default protocol bgp redist-rules redist-static address-family-identifier ipv4",
    "set network virtual-router default protocol bgp redist-rules redist-static set-origin incomplete",
    "set network virtual-router default protocol bgp redist-profile redist-static filter type static",
    "set network virtual-router default protocol bgp redist-profile redist-static priority 1",
    "set network virtual-router default protocol bgp redist-profile redist-static action redist",
    
    # ECMP Setup
    "set network virtual-router default ecmp algorithm ip-modulo",
    
    # G. Security policy and zone assignment
    "set zone Trust network layer3 ethernet1/1",
    "set zone Trust network layer3 loopback.1",
    "set zone Trust network layer3 tunnel.1",
    "set zone Trust network layer3 tunnel.2",
    
    # Rules
    "set rulebase security rules Allow-Test-Traffic from Trust",
    "set rulebase security rules Allow-Test-Traffic to Trust",
    "set rulebase security rules Allow-Test-Traffic source 10.10.6.0/24",
    "set rulebase security rules Allow-Test-Traffic destination 10.10.2.0/24",
    "set rulebase security rules Allow-Test-Traffic destination 10.10.5.0/24",
    "set rulebase security rules Allow-Test-Traffic application any service any action allow log-end yes",
    
    "set rulebase security rules GCP-ILB-HealthCheck-Allow from Trust",
    "set rulebase security rules GCP-ILB-HealthCheck-Allow to Trust",
    "set rulebase security rules GCP-ILB-HealthCheck-Allow source 35.191.0.0/16",
    "set rulebase security rules GCP-ILB-HealthCheck-Allow source 130.211.0.0/22",
    "set rulebase security rules GCP-ILB-HealthCheck-Allow destination 10.10.3.11/32",
    "set rulebase security rules GCP-ILB-HealthCheck-Allow destination 10.10.3.3/32",
    "set rulebase security rules GCP-ILB-HealthCheck-Allow application any service any action allow",
]

def main():
    print(f"Connecting to Palo Alto VM-2 ({VM_IP}) and applying configuration...")
    
    # Combine commands into one CLI session run
    config_commands = ["configure", "revert config"]
    for cmd in commands:
        config_commands.append(cmd)
    config_commands.append("commit")
    config_commands.append("exit")
    
    # Join commands with newline
    batch_command = "\n".join(config_commands)
    
    # Write to a temporary file locally and pipe it to SSH
    with open("temp_palo_commands.txt", "w") as f:
        f.write(batch_command)
        
    ssh_run = f"ssh -i {SSH_KEY} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no {USER}@{VM_IP} < temp_palo_commands.txt"
    print("Executing configuration commands on the firewall...")
    result = subprocess.run(ssh_run, shell=True, capture_output=True, text=True)
    
    # Clean up temp file
    subprocess.run(["rm", "-f", "temp_palo_commands.txt"])
    
    print(result.stdout)
    if result.returncode != 0:
        print(f"Configuration execution failed.\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
        
    print("Configuration applied and committed successfully!")

if __name__ == "__main__":
    main()
