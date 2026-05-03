import subprocess
import platform
import os
import shutil
import socket
import json


def _run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout.strip() or r.stderr.strip() or "Command completed with no output.")
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Error: {e}"


def _is_linux():
    return platform.system() == "Linux"


def _is_mac():
    return platform.system() == "Darwin"


def _is_windows():
    return platform.system() == "Windows"


# ---------- NETWORK ----------

def ping_test(host="8.8.8.8", count=4):
    flag = "-n" if _is_windows() else "-c"
    return _run(f"ping {flag} {count} {host}")


def dns_lookup(domain="google.com"):
    try:
        ip = socket.gethostbyname(domain)
        return f"DNS resolution successful: {domain} -> {ip}"
    except socket.gaierror as e:
        return f"DNS resolution failed for {domain}: {e}"


def flush_dns():
    if _is_mac():
        return _run("sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder 2>/dev/null; echo 'DNS cache flushed.'")
    elif _is_linux():
        result = _run("which systemd-resolve resolvectl 2>/dev/null")
        if "resolvectl" in result:
            return _run("resolvectl flush-caches && echo 'DNS cache flushed via resolvectl.'")
        elif "systemd-resolve" in result:
            return _run("systemd-resolve --flush-caches && echo 'DNS cache flushed via systemd-resolve.'")
        else:
            return _run("nscd -i hosts 2>/dev/null; echo 'Attempted DNS cache flush. If nscd is not installed, DNS cache may be managed by your resolver.'")
    elif _is_windows():
        return _run("ipconfig /flushdns")
    return "Unsupported OS for DNS flush."


def check_default_gateway():
    if _is_windows():
        return _run("ipconfig | findstr /i \"Default Gateway\"")
    else:
        return _run("ip route show default 2>/dev/null || netstat -rn 2>/dev/null | head -5")


def check_dns_servers():
    if _is_windows():
        return _run("ipconfig /all | findstr /i \"DNS Servers\"")
    elif _is_linux():
        result = _run("cat /etc/resolv.conf 2>/dev/null | grep nameserver")
        if not result or "Error" in result:
            result = _run("resolvectl status 2>/dev/null | head -20")
        return result
    else:
        return _run("scutil --dns 2>/dev/null | head -20")


def check_network_interfaces():
    if _is_windows():
        return _run("ipconfig")
    else:
        result = _run("ip addr show 2>/dev/null")
        if "Error" in result or not result:
            result = _run("ifconfig 2>/dev/null")
        return result


def traceroute(host="8.8.8.8"):
    if _is_windows():
        return _run(f"tracert -d -h 15 {host}", timeout=30)
    else:
        cmd = f"traceroute -n -m 15 {host} 2>/dev/null || tracepath {host} 2>/dev/null"
        return _run(cmd, timeout=30)


def check_open_ports():
    if _is_windows():
        return _run("netstat -an | findstr LISTENING | head -20")
    else:
        return _run("ss -tlnp 2>/dev/null | head -20 || netstat -tlnp 2>/dev/null | head -20")


# ---------- SYSTEM ----------

def check_disk_space():
    if _is_windows():
        return _run("wmic logicaldisk get size,freespace,caption")
    else:
        return _run("df -h")


def check_uptime():
    if _is_windows():
        return _run("systeminfo | findstr /i \"Boot Time\"")
    else:
        return _run("uptime")


def check_memory_usage():
    if _is_windows():
        return _run("systeminfo | findstr /i \"Memory\"")
    else:
        return _run("free -h 2>/dev/null || vm_stat 2>/dev/null")


def check_cpu_usage():
    if _is_windows():
        return _run("wmic cpu get loadpercentage")
    elif _is_linux():
        return _run("top -bn1 | head -5")
    else:
        return _run("top -l 1 | head -5")


def list_large_files(path="/", min_size_mb=100):
    if _is_windows():
        return _run(f'forfiles /P {path} /S /M * /C "cmd /c if @fsize GEQ {min_size_mb * 1024 * 1024} echo @path @fsize"', timeout=30)
    else:
        return _run(f"find {path} -xdev -type f -size +{min_size_mb}M -exec ls -lh {{}} \\; 2>/dev/null | sort -k5 -hr | head -15", timeout=30)


def clear_temp_files():
    cleaned = []
    if _is_windows():
        cleaned.append(_run("del /q/f/s %TEMP%\\* 2>nul"))
    else:
        tmp = "/tmp"
        try:
            before = _run(f"du -sh {tmp} 2>/dev/null")
            _run(f"find {tmp} -type f -atime +2 -delete 2>/dev/null")
            after = _run(f"du -sh {tmp} 2>/dev/null")
            cleaned.append(f"Temp cleanup: before={before}, after={after}")
        except Exception as e:
            cleaned.append(f"Error cleaning temp: {e}")
    return "\n".join(cleaned)


def check_running_processes(sort_by="cpu"):
    if _is_windows():
        return _run("tasklist /FO TABLE | head -30")
    elif _is_linux():
        if sort_by == "memory":
            return _run("ps aux --sort=-%mem | head -15")
        return _run("ps aux --sort=-%cpu | head -15")
    else:
        return _run("ps aux -r | head -15")


# ---------- DEVICE ----------

def check_os_info():
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "hostname": socket.gethostname(),
    }
    return json.dumps(info, indent=2)


def check_battery():
    if _is_linux():
        result = _run("cat /sys/class/power_supply/BAT0/capacity 2>/dev/null")
        if result and "Error" not in result and "No such" not in result:
            return f"Battery level: {result}%"
        return "No battery detected (desktop or VM)."
    elif _is_mac():
        return _run("pmset -g batt 2>/dev/null")
    elif _is_windows():
        return _run("WMIC PATH Win32_Battery Get EstimatedChargeRemaining")
    return "Battery check not supported."


def check_display_info():
    if _is_linux():
        return _run("xrandr --query 2>/dev/null || echo 'No display detected (headless/server).'")
    elif _is_mac():
        return _run("system_profiler SPDisplaysDataType 2>/dev/null | head -20")
    return "Display info not available on this OS."


def check_audio_devices():
    if _is_linux():
        result = _run("pactl list sinks short 2>/dev/null || aplay -l 2>/dev/null")
        return result if result else "No audio devices found."
    elif _is_mac():
        return _run("system_profiler SPAudioDataType 2>/dev/null | head -20")
    return "Audio device check not available on this OS."


def check_usb_devices():
    if _is_linux():
        return _run("lsusb 2>/dev/null || echo 'lsusb not available.'")
    elif _is_mac():
        return _run("system_profiler SPUSBDataType 2>/dev/null | head -25")
    return "USB device check not available on this OS."


# ---------- PRINTER ----------

def list_printers():
    if _is_linux() or _is_mac():
        return _run("lpstat -p 2>/dev/null || echo 'No CUPS printers found. CUPS may not be installed.'")
    elif _is_windows():
        return _run("wmic printer get name,status")
    return "Printer listing not supported."


def check_print_service():
    if _is_linux():
        return _run("systemctl status cups 2>/dev/null || service cups status 2>/dev/null || echo 'CUPS service not found.'")
    elif _is_mac():
        return _run("launchctl list | grep cups 2>/dev/null; cupsctl 2>/dev/null")
    elif _is_windows():
        return _run("sc query spooler")
    return "Print service check not supported."


def restart_print_service():
    if _is_linux():
        return _run("sudo systemctl restart cups 2>/dev/null || sudo service cups restart 2>/dev/null; echo 'Print service restart attempted.'")
    elif _is_mac():
        return _run("sudo launchctl stop org.cups.cupsd && sudo launchctl start org.cups.cupsd; echo 'CUPS restarted.'")
    elif _is_windows():
        return _run("net stop spooler && net start spooler")
    return "Print service restart not supported."


def clear_print_queue():
    if _is_linux() or _is_mac():
        return _run("cancel -a 2>/dev/null; echo 'Print queue cleared.'")
    elif _is_windows():
        return _run("net stop spooler && del /Q /F /S \"%systemroot%\\System32\\spool\\PRINTERS\\*\" && net start spooler")
    return "Print queue clear not supported."


# ---------- SECURITY ----------

def check_firewall_status():
    if _is_linux():
        result = _run("sudo ufw status 2>/dev/null || sudo iptables -L -n 2>/dev/null | head -15")
        return result
    elif _is_mac():
        return _run("sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null")
    elif _is_windows():
        return _run("netsh advfirewall show allprofiles state")
    return "Firewall check not supported."


def check_failed_logins():
    if _is_linux():
        return _run("journalctl -u sshd --no-pager -n 20 2>/dev/null | grep -i 'fail\\|invalid' || lastb -n 10 2>/dev/null || echo 'No failed login data available.'")
    elif _is_mac():
        return _run("log show --predicate 'eventMessage contains \"authentication failure\"' --last 1h 2>/dev/null | tail -10")
    return "Failed login check not available on this OS."


def check_open_connections():
    if _is_windows():
        return _run("netstat -an | findstr ESTABLISHED | head -20")
    else:
        return _run("ss -tnp 2>/dev/null | head -20 || netstat -tnp 2>/dev/null | head -20")


def check_suspicious_processes():
    if _is_windows():
        return _run("tasklist /FO TABLE /V | head -30")
    else:
        return _run("ps aux --sort=-%cpu | head -20")


# ---------- TOOL DEFINITIONS FOR OPENAI FUNCTION CALLING ----------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "ping_test",
            "description": "Ping a host to check if it's reachable and measure latency/packet loss. Use this to test internet connectivity or check if a specific server is up.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Host or IP to ping. Default: 8.8.8.8 (Google DNS)"},
                    "count": {"type": "integer", "description": "Number of ping packets. Default: 4"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dns_lookup",
            "description": "Check if DNS is working by resolving a domain name to an IP address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Domain to look up. Default: google.com"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "flush_dns",
            "description": "Clear the DNS cache. Fixes issues where websites won't load even though internet works. Safe to run.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_default_gateway",
            "description": "Show the default gateway/router IP. Helps diagnose if the device can reach the router.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_dns_servers",
            "description": "Show which DNS servers are configured on this system.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_network_interfaces",
            "description": "Show all network interfaces (Wi-Fi, Ethernet, etc.) and their IP addresses.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "traceroute",
            "description": "Trace the network path to a host. Shows where packets travel and where they might get stuck.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Host to trace. Default: 8.8.8.8"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_open_ports",
            "description": "List ports that are currently listening for connections on this machine.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_disk_space",
            "description": "Show disk/storage usage on all drives. Checks if the disk is full.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_uptime",
            "description": "Show how long the system has been running since last reboot.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_memory_usage",
            "description": "Show RAM/memory usage. Helps diagnose if the system is running out of memory.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_cpu_usage",
            "description": "Show CPU usage and top processes. Helps diagnose if something is using too much processing power.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_large_files",
            "description": "Find the largest files on the system. Useful when disk space is low.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to search. Default: /"},
                    "min_size_mb": {"type": "integer", "description": "Minimum file size in MB. Default: 100"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_temp_files",
            "description": "Safely clean up old temporary files to free disk space.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_running_processes",
            "description": "List running processes sorted by resource usage. Helps find what's slowing the system down.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sort_by": {"type": "string", "enum": ["cpu", "memory"], "description": "Sort by cpu or memory usage. Default: cpu"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_os_info",
            "description": "Get operating system details: OS type, version, architecture, hostname.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_battery",
            "description": "Check battery level and status (laptop/mobile only).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_audio_devices",
            "description": "List audio output devices. Helps troubleshoot sound issues.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_usb_devices",
            "description": "List connected USB devices.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_printers",
            "description": "List installed printers and their status.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_print_service",
            "description": "Check if the print service (CUPS/Spooler) is running.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_print_service",
            "description": "Restart the print service. Fixes most printer connection issues.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_print_queue",
            "description": "Clear all stuck print jobs from the queue.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_firewall_status",
            "description": "Check if the firewall is enabled and show its current rules.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_failed_logins",
            "description": "Check for recent failed login attempts. Helps detect unauthorized access.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_open_connections",
            "description": "Show active network connections. Helps detect suspicious outbound traffic.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_suspicious_processes",
            "description": "List all running processes with details. Helps spot unfamiliar or suspicious programs.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
]

TOOL_MAP = {
    "ping_test": ping_test,
    "dns_lookup": dns_lookup,
    "flush_dns": flush_dns,
    "check_default_gateway": check_default_gateway,
    "check_dns_servers": check_dns_servers,
    "check_network_interfaces": check_network_interfaces,
    "traceroute": traceroute,
    "check_open_ports": check_open_ports,
    "check_disk_space": check_disk_space,
    "check_uptime": check_uptime,
    "check_memory_usage": check_memory_usage,
    "check_cpu_usage": check_cpu_usage,
    "list_large_files": list_large_files,
    "clear_temp_files": clear_temp_files,
    "check_running_processes": check_running_processes,
    "check_os_info": check_os_info,
    "check_battery": check_battery,
    "check_audio_devices": check_audio_devices,
    "check_usb_devices": check_usb_devices,
    "list_printers": list_printers,
    "check_print_service": check_print_service,
    "restart_print_service": restart_print_service,
    "clear_print_queue": clear_print_queue,
    "check_firewall_status": check_firewall_status,
    "check_failed_logins": check_failed_logins,
    "check_open_connections": check_open_connections,
    "check_suspicious_processes": check_suspicious_processes,
}


def execute_tool(name, arguments=None):
    if name not in TOOL_MAP:
        return f"Unknown tool: {name}"
    fn = TOOL_MAP[name]
    args = arguments or {}
    try:
        return fn(**args)
    except Exception as e:
        return f"Error running {name}: {e}"
