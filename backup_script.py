#!/usr/bin/env python3
import subprocess
import os
import sys
import datetime

SSH_KEY = os.path.expanduser("~/paloalto-key")
USER = "admin"

FIREWALLS = {
    "paloalto-ngfw": {"ip": "10.10.1.15", "suffix": ""},
    "paloalto-ngfw-2": {"ip": "10.10.1.14", "suffix": "_2"}
}

def run_ssh_commands(ip, commands, timeout=60):
    batch = "\n" + "\n".join(commands) + "\nexit\n"
    temp_cmd = f"/tmp/cmd_{ip}.txt"
    with open(temp_cmd, "w") as f:
        f.write(batch)
        
    ssh_cmd = [
        "ssh", "-i", SSH_KEY,
        "-o", "BatchMode=yes",
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"{USER}@{ip}"
    ]
    
    try:
        with open(temp_cmd, "r") as tf:
            res = subprocess.run(ssh_cmd, stdin=tf, capture_output=True, text=True, timeout=timeout)
        return res.stdout
    except Exception as e:
        print(f"Error connecting to {ip}: {e}", file=sys.stderr)
        return None
    finally:
        if os.path.exists(temp_cmd):
            os.remove(temp_cmd)

def parse_xml_output(output):
    if not output:
        return ""
    lines = output.splitlines()
    xml_start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("<response") or stripped.startswith("<config"):
            xml_start = i
            break
    if xml_start == -1:
        return ""
    xml_end = -1
    for i in range(xml_start, len(lines)):
        if lines[i].strip() == "[edit]":
            xml_end = i
            break
    if xml_end != -1:
        return "\n".join(lines[xml_start:xml_end]).strip()
    else:
        return "\n".join(lines[xml_start:]).strip()

def parse_text_output(output):
    if not output:
        return ""
    lines = output.splitlines()
    start_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if "configuration mode" in stripped or stripped == "[edit]" or "set cli" in stripped:
            continue
        if stripped.startswith("admin@") or stripped.startswith("#") or stripped == "configure" or stripped == "show":
            continue
        start_idx = i
        break
    if start_idx == -1:
        return ""
    end_idx = -1
    for i in range(start_idx, len(lines)):
        stripped = lines[i].strip()
        if stripped == "[edit]" or (stripped.startswith("admin@") and stripped.endswith("exit")):
            end_idx = i
            break
    if end_idx != -1:
        return "\n".join(lines[start_idx:end_idx]).strip()
    else:
        return "\n".join(lines[start_idx:]).strip()

def parse_set_output(output):
    if not output:
        return ""
    lines = output.splitlines()
    set_lines = [line for line in lines if line.strip().startswith("set ")]
    return "\n".join(set_lines).strip()

def backup_firewall(name, info, backup_dir):
    ip = info["ip"]
    suffix = info["suffix"]
    print(f"\n==========================================")
    print(f"Backing up {name} ({ip})...")
    print(f"==========================================")
    
    # 1. Fetch XML config
    print(f"Fetching XML config from {name}...")
    xml_raw = run_ssh_commands(ip, [
        "set cli pager off",
        "set cli config-output-format xml",
        "configure",
        "show",
        "exit",
        "exit"
    ])
    xml_clean = parse_xml_output(xml_raw)
    
    # 2. Fetch Set format config
    print(f"Fetching 'set' format config from {name}...")
    set_raw = run_ssh_commands(ip, [
        "set cli pager off",
        "set cli config-output-format set",
        "configure",
        "show",
        "exit",
        "exit"
    ])
    set_clean = parse_set_output(set_raw)

    # 3. Fetch Standard hierarchical config
    print(f"Fetching standard hierarchical config from {name}...")
    text_raw = run_ssh_commands(ip, [
        "set cli pager off",
        "set cli config-output-format default",
        "configure",
        "show",
        "exit",
        "exit"
    ])
    text_clean = parse_text_output(text_raw)
    
    # Save files to current directory and backup directory
    files_to_write = {
        f"paloalto_running_config{suffix}.xml": xml_clean,
        f"paloalto_running_config{suffix}.txt": text_clean,
        f"paloalto_running_config{suffix}_set.txt": set_clean,
    }
    
    for filename, content in files_to_write.items():
        if content:
            # write root
            with open(filename, "w") as f:
                f.write(content + "\n")
            print(f" Saved: {filename} ({len(content)} bytes)")
            
            # write timestamped backup
            backup_file_path = os.path.join(backup_dir, filename)
            with open(backup_file_path, "w") as f:
                f.write(content + "\n")
        else:
            print(f" Failed/Empty content for {filename}", file=sys.stderr)

def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Created backup directory: {backup_dir}")
    
    for name, info in FIREWALLS.items():
        backup_firewall(name, info, backup_dir)
        
    print("\nBackup process completed.")

if __name__ == "__main__":
    main()
