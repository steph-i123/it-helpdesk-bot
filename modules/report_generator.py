from modules.diagnostics import (
    ping_test, dns_lookup, flush_dns, check_default_gateway,
    check_dns_servers, check_network_interfaces, traceroute,
    check_open_ports, check_disk_space, check_uptime,
    check_memory_usage, check_cpu_usage, check_running_processes,
    check_os_info, check_battery, check_audio_devices,
    check_firewall_status, check_failed_logins,
    check_open_connections, check_suspicious_processes,
)


def generate(report_type):
    generators = {
        "isp": _isp_report,
        "device": _device_report,
        "network": _network_report,
        "security": _security_report,
        "gaming": _gaming_report,
        "remote": _remote_report,
    }
    fn = generators.get(report_type)
    if not fn:
        return [{"title": "Error", "data": "Unknown report type."}]
    return fn()


def _isp_report():
    return [
        {"title": "Ping Test (Google DNS 8.8.8.8)", "data": ping_test("8.8.8.8", 10)},
        {"title": "Ping Test (Cloudflare 1.1.1.1)", "data": ping_test("1.1.1.1", 10)},
        {"title": "DNS Resolution", "data": "\n".join([
            dns_lookup("google.com"),
            dns_lookup("cloudflare.com"),
            dns_lookup("amazon.com"),
        ])},
        {"title": "DNS Servers Configured", "data": check_dns_servers()},
        {"title": "Default Gateway", "data": check_default_gateway()},
        {"title": "Network Interfaces", "data": check_network_interfaces()},
        {"title": "Traceroute to 8.8.8.8", "data": traceroute("8.8.8.8")},
        {"title": "System Info", "data": check_os_info()},
    ]


def _device_report():
    return [
        {"title": "Operating System", "data": check_os_info()},
        {"title": "System Uptime", "data": check_uptime()},
        {"title": "Disk Space", "data": check_disk_space()},
        {"title": "Memory Usage", "data": check_memory_usage()},
        {"title": "CPU Usage", "data": check_cpu_usage()},
        {"title": "Top Processes (by CPU)", "data": check_running_processes("cpu")},
        {"title": "Top Processes (by Memory)", "data": check_running_processes("memory")},
        {"title": "Battery Status", "data": check_battery()},
        {"title": "Audio Devices", "data": check_audio_devices()},
    ]


def _network_report():
    return [
        {"title": "Network Interfaces", "data": check_network_interfaces()},
        {"title": "Default Gateway", "data": check_default_gateway()},
        {"title": "DNS Servers", "data": check_dns_servers()},
        {"title": "DNS Resolution Test", "data": "\n".join([
            dns_lookup("google.com"),
            dns_lookup("github.com"),
        ])},
        {"title": "Ping Test", "data": ping_test("8.8.8.8", 5)},
        {"title": "Traceroute", "data": traceroute("8.8.8.8")},
        {"title": "Open Ports (Listening)", "data": check_open_ports()},
        {"title": "Active Connections", "data": check_open_connections()},
    ]


def _security_report():
    return [
        {"title": "Firewall Status", "data": check_firewall_status()},
        {"title": "Failed Login Attempts", "data": check_failed_logins()},
        {"title": "Active Network Connections", "data": check_open_connections()},
        {"title": "Open Ports", "data": check_open_ports()},
        {"title": "Running Processes", "data": check_suspicious_processes()},
        {"title": "System Info", "data": check_os_info()},
    ]


def _gaming_report():
    return [
        {"title": "Ping to Google DNS (8.8.8.8)", "data": ping_test("8.8.8.8", 20)},
        {"title": "Ping to Cloudflare (1.1.1.1)", "data": ping_test("1.1.1.1", 20)},
        {"title": "Traceroute to Google DNS", "data": traceroute("8.8.8.8")},
        {"title": "DNS Resolution Speed", "data": "\n".join([
            dns_lookup("google.com"),
            dns_lookup("cloudflare.com"),
            dns_lookup("riot.com"),
            dns_lookup("steampowered.com"),
        ])},
        {"title": "Network Interfaces", "data": check_network_interfaces()},
        {"title": "Default Gateway", "data": check_default_gateway()},
        {"title": "CPU Usage", "data": check_cpu_usage()},
        {"title": "Memory Usage", "data": check_memory_usage()},
    ]


def _remote_report():
    return [
        {"title": "Internet Connectivity", "data": ping_test("8.8.8.8", 10)},
        {"title": "DNS Resolution", "data": "\n".join([
            dns_lookup("google.com"),
            dns_lookup("zoom.us"),
            dns_lookup("teams.microsoft.com"),
        ])},
        {"title": "Traceroute", "data": traceroute("8.8.8.8")},
        {"title": "Network Interfaces", "data": check_network_interfaces()},
        {"title": "Default Gateway", "data": check_default_gateway()},
        {"title": "System Resources", "data": "\n".join([
            "--- CPU ---", check_cpu_usage(),
            "", "--- Memory ---", check_memory_usage(),
            "", "--- Disk ---", check_disk_space(),
        ])},
        {"title": "System Info", "data": check_os_info()},
    ]
