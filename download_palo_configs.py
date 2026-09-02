#!/usr/bin/env python3
import subprocess
import sys
import os

SSH_KEY = "paloalto-key"
USER = "admin"

def get_instance_ips():
    # Run gcloud to get instances and their public/private IPs
    print("Retrieving firewall external IPs using gcloud...")
    res = subprocess.run(
        ["gcloud", "compute", "instances", "list", "--format=value(name,status,networkInterfaces[1].accessConfigs[0].natIP)"],
        capture_output=True, text=True, check=True
    )
    ips = {}
    for line in res.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 3:
            name, status, ext_ip = parts[0], parts[1], parts[2]
            if status == "RUNNING" and "paloalto" in name:
                ips[name] = ext_ip
    return ips

def fetch_combined_output(ip):
    # Fetch both formats in a single session to avoid firewall SSH rate-limiting
    commands = [
        "set cli pager off",
        "set cli config-output-format xml",
        "configure",
        "show",
        "exit",
        "set cli config-output-format default",
        "configure",
        "show",
        "exit",
        "exit"
    ]
    batch_command = "\n" + "\n".join(commands) + "\n"
    temp_file = f"temp_cmd_{ip}.txt"
    with open(temp_file, "w") as f:
        f.write(batch_command)
        
    ssh_cmd = [
        "ssh", "-i", SSH_KEY,
        "-o", "ProxyCommand=none",
        "-o", "BatchMode=yes",
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"{USER}@{ip}"
    ]
    
    print(f"Fetching configuration from {ip}...")
    try:
        with open(temp_file, "r") as tf:
            res = subprocess.run(ssh_cmd, stdin=tf, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        print(f"Timeout expired while fetching configuration from {ip}")
        res = None
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
    if not res or res.returncode != 0:
        err = res.stderr if res else "No response"
        print(f"Failed to fetch configuration from {ip}: {err}", file=sys.stderr)
        return None
        
    return res.stdout

def parse_combined_output(output):
    if not output:
        return "", ""
        
    lines = output.splitlines()
    
    # 1. Parse XML config
    xml_start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("<response") or stripped.startswith("<config"):
            xml_start = i
            break
            
    xml_config = ""
    remaining_lines = lines
    if xml_start != -1:
        xml_end = -1
        for i in range(xml_start, len(lines)):
            if lines[i].strip() == "[edit]":
                xml_end = i
                break
        if xml_end != -1:
            xml_config = "\n".join(lines[xml_start:xml_end])
            remaining_lines = lines[xml_end+1:]
        else:
            xml_config = "\n".join(lines[xml_start:])
            remaining_lines = []

    # 2. Parse Default config block in remaining lines
    # We find the first non-empty line that isn't a prompt or transition message
    default_start = -1
    for i, line in enumerate(remaining_lines):
        stripped = line.strip()
        if not stripped:
            continue
        if "configuration mode" in stripped or stripped == "[edit]":
            continue
        # The first line that is actual config content
        default_start = i
        break
            
    default_config = ""
    if default_start != -1:
        default_end = -1
        for i in range(default_start, len(remaining_lines)):
            if remaining_lines[i].strip() == "[edit]":
                default_end = i
                break
        if default_end != -1:
            default_config = "\n".join(remaining_lines[default_start:default_end])
        else:
            default_config = "\n".join(remaining_lines[default_start:])
            
    return xml_config, default_config

def main():
    ips = get_instance_ips()
    if not ips:
        print("No running Palo Alto firewalls found.")
        sys.exit(1)
        
    for name, ip in ips.items():
        print(f"Found running firewall {name} at IP {ip}")
        suffix = "" if name == "paloalto-ngfw" else "_2"
        
        raw_output = fetch_combined_output(ip)
        if raw_output:
            xml_config, default_config = parse_combined_output(raw_output)
            
            if xml_config:
                xml_filename = f"paloalto_running_config{suffix}.xml"
                with open(xml_filename, "w") as f:
                    f.write(xml_config)
                    f.write("\n")
                print(f"Saved {xml_filename}")
            else:
                print(f"Warning: Could not parse XML configuration for {name}")
                
            if default_config:
                default_filename = f"paloalto_running_config{suffix}.txt"
                with open(default_filename, "w") as f:
                    f.write(default_config)
                    f.write("\n")
                print(f"Saved {default_filename}")
            else:
                print(f"Warning: Could not parse default block configuration for {name}")

if __name__ == "__main__":
    main()
