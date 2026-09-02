#!/usr/bin/env python3
import os
import pty
import select
import subprocess
import time
import fcntl
import datetime
import sys

FIREWALLS = [
    {"name": "paloalto-ngfw", "ip": "10.10.1.15", "suffix": ""},
    {"name": "paloalto-ngfw-2", "ip": "10.10.1.14", "suffix": "_2"}
]

def clean_output(raw_out, fmt):
    if not raw_out:
        return ""
    lines = raw_out.splitlines()
    
    # Remove command echo lines and prompt lines
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "show" or stripped.startswith("admin@") and stripped.endswith("#"):
            continue
        if stripped.startswith("admin@") and stripped.endswith(">"):
            continue
        if "configuration mode" in stripped or stripped == "[edit]":
            continue
        cleaned.append(line)
        
    result = "\n".join(cleaned).strip()
    
    if fmt == "xml":
        # Extract everything from first tag (<response or <config) to closing tag
        first_tag = -1
        for i, l in enumerate(cleaned):
            if l.strip().startswith("<response") or l.strip().startswith("<config"):
                first_tag = i
                break
        if first_tag != -1:
            result = "\n".join(cleaned[first_tag:]).strip()
            
    elif fmt == "set":
        # Only keep 'set ' lines
        set_lines = [l for l in cleaned if l.strip().startswith("set ")]
        result = "\n".join(set_lines).strip()
        
    return result

def get_palo_configs(ip):
    master, slave = pty.openpty()
    key = os.path.expanduser('~/paloalto-key')
    cmd = ['ssh', '-i', key, '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=no', f'admin@{ip}']
    
    proc = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave, close_fds=True)
    os.close(slave)
    
    flags = fcntl.fcntl(master, fcntl.F_GETFL)
    fcntl.fcntl(master, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    def read_until_prompt(expect='#', timeout=30):
        output = ''
        start = time.time()
        while time.time() - start < timeout:
            r, _, _ = select.select([master], [], [], 0.1)
            if r:
                try:
                    chunk = os.read(master, 8192).decode('utf-8', errors='ignore')
                    output += chunk
                    lines = [l.strip() for l in output.strip().splitlines() if l.strip()]
                    if lines:
                        last = lines[-1]
                        if expect == '>' and (last.endswith('>') or '> ' in last):
                            return output
                        elif expect == '#' and (last.endswith('#') or '# ' in last):
                            return output
                except OSError:
                    break
        return output

    def exec_cmd(command, expect='>', timeout=30):
        os.write(master, (command + '\n').encode('utf-8'))
        time.sleep(0.1)
        return read_until_prompt(expect, timeout=timeout)

    print(f'Connecting and logging in to {ip}...')
    read_until_prompt('>', timeout=20)
    
    print(f'[{ip}] Disabling pager...')
    exec_cmd('set cli pager off', '>')
    
    print(f'[{ip}] Fetching XML format...')
    exec_cmd('set cli config-output-format xml', '>')
    exec_cmd('configure', '#')
    xml_raw = exec_cmd('show', '#', timeout=35)
    exec_cmd('exit', '>')
    
    print(f'[{ip}] Fetching Set format...')
    exec_cmd('set cli config-output-format set', '>')
    exec_cmd('configure', '#')
    set_raw = exec_cmd('show', '#', timeout=35)
    exec_cmd('exit', '>')
    
    print(f'[{ip}] Fetching Hierarchical text format...')
    exec_cmd('set cli config-output-format default', '>')
    exec_cmd('configure', '#')
    text_raw = exec_cmd('show', '#', timeout=35)
    exec_cmd('exit', '>')
    
    exec_cmd('exit', '>')
    os.close(master)
    proc.wait()
    
    xml_clean = clean_output(xml_raw, "xml")
    set_clean = clean_output(set_raw, "set")
    text_clean = clean_output(text_raw, "default")
    
    return xml_clean, set_clean, text_clean

def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Timestamped backup directory: {backup_dir}")
    
    for fw in FIREWALLS:
        name = fw["name"]
        ip = fw["ip"]
        suffix = fw["suffix"]
        
        print(f"\n==========================================")
        print(f"Backing up {name} ({ip})...")
        print(f"==========================================")
        
        xml_cfg, set_cfg, text_cfg = get_palo_configs(ip)
        
        files = {
            f"paloalto_running_config{suffix}.xml": xml_cfg,
            f"paloalto_running_config{suffix}.txt": text_cfg,
            f"paloalto_running_config{suffix}_set.txt": set_cfg,
        }
        
        for fname, content in files.items():
            if content:
                # Root workspace file
                with open(fname, "w") as f:
                    f.write(content + "\n")
                print(f" Saved: {fname} ({len(content)} bytes)")
                
                # Timestamped backup copy
                bpath = os.path.join(backup_dir, fname)
                with open(bpath, "w") as f:
                    f.write(content + "\n")
            else:
                print(f" Error: Empty content for {fname}", file=sys.stderr)
                
    print("\nAll firewall backups completed successfully!")

if __name__ == "__main__":
    main()
