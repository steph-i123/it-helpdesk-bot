import os
from openai import OpenAI
from dotenv import load_dotenv

from modules.diagnostics import (
    ping_test, dns_lookup, flush_dns, check_default_gateway,
    check_dns_servers, check_network_interfaces, traceroute,
    check_open_ports, check_disk_space, check_uptime,
    check_memory_usage, check_cpu_usage, check_running_processes,
    check_os_info, check_battery, check_audio_devices,
    check_firewall_status, check_failed_logins,
    check_open_connections, check_suspicious_processes,
)

load_dotenv()

REPORT_NAMES = {
    "isp": "ISP Report",
    "device": "Device Health Report",
    "network": "Network Diagnostics",
    "security": "Security Check",
    "gaming": "Gaming Latency Report",
    "remote": "Remote Work Report",
}


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
        return {"summary": "Unknown report type.", "sections": [{"title": "Error", "data": "", "explanation": "This report type does not exist."}]}

    sections = fn()
    summary, sections = _ai_summarize(report_type, sections)
    return {"summary": summary, "sections": sections}


def _ai_summarize(report_type, sections):
    report_name = REPORT_NAMES.get(report_type, "Report")

    section_text = ""
    for s in sections:
        section_text += f"\n--- {s['title']} ---\n{s['data']}\n"

    prompt = f"""You are PingPal, a friendly AI IT assistant. A user just generated a "{report_name}". Below are the raw diagnostic results from their system.

Your job is to translate this into plain English that a non-technical person can understand.

Provide TWO things:

1. **OVERALL SUMMARY** (2-4 sentences): A friendly overview of what the report found. Is everything looking good? Are there any concerns? What should they do? Write like you're talking to a friend.

2. **SECTION EXPLANATIONS**: For EACH section below, write a 1-2 sentence explanation in plain English. What does this data mean? Is it good or bad? Should they worry?

Format your response EXACTLY like this (use these exact markers):

OVERALL_SUMMARY:
[your overall summary here]

SECTION: [exact section title]
[your plain English explanation]

SECTION: [exact section title]
[your plain English explanation]

... repeat for every section ...

Here are the raw diagnostic results:
{section_text}"""

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "placeholder":
            return _fallback_summary(sections)

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        ai_text = response.choices[0].message.content or ""
        return _parse_ai_response(ai_text, sections)
    except Exception:
        return _fallback_summary(sections)


def _parse_ai_response(ai_text, sections):
    summary = ""
    explanations = {}

    lines = ai_text.split("\n")
    current_key = None
    current_lines = []

    for line in lines:
        if line.strip().startswith("OVERALL_SUMMARY:"):
            if current_key and current_lines:
                explanations[current_key] = " ".join(current_lines).strip()
            current_key = "__summary__"
            current_lines = []
            rest = line.strip().replace("OVERALL_SUMMARY:", "").strip()
            if rest:
                current_lines.append(rest)
        elif line.strip().startswith("SECTION:"):
            if current_key == "__summary__" and current_lines:
                summary = " ".join(current_lines).strip()
            elif current_key and current_lines:
                explanations[current_key] = " ".join(current_lines).strip()
            section_name = line.strip().replace("SECTION:", "").strip()
            current_key = section_name
            current_lines = []
        else:
            if line.strip():
                current_lines.append(line.strip())

    if current_key == "__summary__" and current_lines:
        summary = " ".join(current_lines).strip()
    elif current_key and current_lines:
        explanations[current_key] = " ".join(current_lines).strip()

    for s in sections:
        matched = explanations.get(s["title"], "")
        if not matched:
            for key, val in explanations.items():
                if key.lower() in s["title"].lower() or s["title"].lower() in key.lower():
                    matched = val
                    break
        s["explanation"] = matched or "PingPal checked this for you."

    if not summary:
        summary = "PingPal has finished running your diagnostics. Check each section below for details."

    return summary, sections


def _fallback_summary(sections):
    for s in sections:
        s["explanation"] = ""
    return "PingPal ran your diagnostics. The raw results are shown below.", sections


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
