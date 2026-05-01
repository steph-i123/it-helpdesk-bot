import os
import platform
import socket
import difflib
import subprocess
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
import openai

from modules import (
    network, device, active_directory, cloud,
    printer, qol, security, software, system
)

load_dotenv()

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
chat_history = []

INTENT_ROUTER = {
    "network": network.handle_network_command,
    "device": device.handle_device_command,
    "ad": active_directory.handle_ad_command,
    "cloud": cloud.handle_cloud_command,
    "printer": printer.handle_printer_command,
    "qol": qol.handle_qol_command,
    "security": security.handle_security_command,
    "software": software.handle_software_command,
    "system": system.handle_system_command,
}

# Intent keywords mapping to categories
INTENT_KEYWORDS = {
    "flush dns": "network",
    "reset adapter": "network",
    "check internet": "network",
    "wifi": "network",
    "printer": "printer",
    "print": "printer",
    "account locked": "ad",
    "reset password": "ad",
    "create user": "ad",
    "cloud backup": "cloud",
    "cloud storage": "cloud",
    "slow": "qol",
    "clear temp": "qol",
    "security": "security",
    "antivirus": "security",
    "install software": "software",
    "uninstall": "software",
    "disk space": "system",
    "uptime": "system",
    "temp files": "system"
}


def detect_intent(user_input):
    lower_input = user_input.lower()
    for keyword, group in INTENT_KEYWORDS.items():
        if keyword in lower_input:
            return group
    return None


def format_module_response(response, group):
    if response is None:
        return None

    if isinstance(response, dict):
        output = response.get("output", response.get("steps", []))
        summary = response.get("summary", "")
        if isinstance(output, list):
            output_text = "\n".join(str(item) for item in output)
        else:
            output_text = str(output)

        formatted = (
            f"**What I found:** Ran {group} diagnostics on your system.\n"
            f"**What it means:** {summary}\n"
            f"**What I can fix:** {output_text}\n"
            f"**Next step:** Let me know if you need further help or want me to generate a report."
        )
        return {"type": "chatgpt", "response": formatted}

    if isinstance(response, list):
        combined = "\n".join(str(item) for item in response)
        if not combined.strip():
            return {"type": "chatgpt", "response": f"I ran the {group} check but didn't get output. This may require a different approach on your system."}
        formatted = (
            f"**What I found:** Ran {group} diagnostics.\n"
            f"**What it means:** Here are the results:\n{combined}\n"
            f"**What I can fix:** I can re-run or try alternative diagnostics.\n"
            f"**Next step:** Let me know if anything looks wrong or if you need more help."
        )
        return {"type": "chatgpt", "response": formatted}

    return {"type": "chatgpt", "response": str(response)}


def generate_response(user_input):
    group = detect_intent(user_input)
    if group and group in INTENT_ROUTER:
        handler = INTENT_ROUTER[group]
        result = handler(user_input)
        formatted = format_module_response(result, group)
        if formatted:
            return formatted

    try:
        completion = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    "You are PingPal, a calm, intelligent, professional AI IT assistant. "
                    "When diagnosing issues, always structure your response using this format:\n\n"
                    "**What I found:** [describe the issue]\n"
                    "**What it means:** [explain in simple terms]\n"
                    "**What I can fix:** [what you can do]\n"
                    "**Next step:** [what the user should do]\n\n"
                    "For general questions or greetings, respond naturally and helpfully. "
                    "Be friendly, trustworthy, and easy to understand for non-technical users."
                )},
                {"role": "user", "content": user_input}
            ]
        )
        return {"type": "chatgpt", "response": completion.choices[0].message.content}

    except Exception as e:
        return {"type": "error", "response": f"❌ Error accessing smart assistant: {str(e)}"}


@app.route("/")
def home():
    return render_template("chat.html")


@app.route("/preview")
def product_preview():
    return send_from_directory("preview", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    chat_history.append({"user": user_message})

    try:
        response = generate_response(user_message)

        # If it's a dict with "type"
        if isinstance(response, dict):
            if response.get("type") == "steps":
                combined = "\n".join(response["steps"]) + f"\n\n{response['summary']}"
                chat_history.append({"bot": combined})
                return jsonify({"response": combined})
            elif response.get("type") == "chatgpt":
                chat_history.append({"bot": response["response"]})
                return jsonify({"response": response["response"]})
            elif response.get("type") == "error":
                chat_history.append({"bot": response["response"]})
                return jsonify({"response": response["response"]})

        # If it's a list (from system, qol, etc.)
        elif isinstance(response, list):
            combined = "\n".join(response)
            chat_history.append({"bot": combined})
            return jsonify({"response": combined})

        else:
            return jsonify({"response": "⚠️ Unexpected response format."})

    except Exception as e:
        error_msg = f"❌ Internal error: {str(e)}"
        chat_history.append({"bot": error_msg})
        return jsonify({"response": error_msg})


if __name__ == "__main__":
    app.run(debug=True)

