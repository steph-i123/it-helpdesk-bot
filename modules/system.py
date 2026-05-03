import subprocess

def handle_system_command(user_input):
    responses = []
    lower_input = user_input.lower()

    if "temp" in lower_input and "clear" in lower_input:
        try:
            result = subprocess.run("rm -rf /tmp/*", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                responses.append("🧹 Temp files cleared successfully.")
            else:
                responses.append(f"⚠️ Failed to clear temp files:\n{result.stderr}")
        except Exception as e:
            responses.append(f"❌ Error: {str(e)}")

    elif "disk" in lower_input:
        try:
            result = subprocess.run("df -h", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                responses.append("💾 Disk Space:\n" + "\n".join(lines[:5]))
            else:
                responses.append(f"⚠️ Failed to check disk:\n{result.stderr}")
        except Exception as e:
            responses.append(f"❌ Error: {str(e)}")

    elif "uptime" in lower_input:
        try:
            result = subprocess.run("uptime", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                responses.append(f"🕒 Uptime: {result.stdout.strip()}")
            else:
                responses.append(f"⚠️ Failed to get uptime:\n{result.stderr}")
        except Exception as e:
            responses.append(f"❌ Error: {str(e)}")

    return responses



