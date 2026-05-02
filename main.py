import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
from openai import OpenAI

from modules.diagnostics import TOOL_DEFINITIONS, execute_tool

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

sessions = {}

SYSTEM_PROMPT = """You are PingPal, a friendly and intelligent AI IT assistant built for regular people — not tech experts.

YOUR PERSONALITY:
- You are warm, patient, and conversational. You sound like a helpful friend who happens to be great with technology.
- Never sound robotic or overly formal. Use casual, clear language.
- When someone describes a problem, respond like a real person would: acknowledge their frustration, then get to work.
- You can use light humor when appropriate, but always stay helpful and professional.

HOW YOU WORK:
- Users will describe their tech problems in everyday language. They might say "my internet is being weird" instead of "I'm experiencing packet loss." You understand both.
- When you hear a problem, THINK about what could be causing it. Then use your diagnostic tools to investigate.
- You can and should run multiple diagnostics to build a complete picture before giving your answer.
- If the problem isn't clear, ASK a follow-up question. This is good — it shows you care and makes the conversation feel natural. For example: "Is this happening on Wi-Fi or when you're plugged in with a cable?" or "When did this start — has it always been like this or did it just start recently?"
- Only ask ONE question at a time. Don't overwhelm the user.

YOUR DIAGNOSIS FORMAT:
When you've figured out what's going on, structure your response like this:

**What I found:** [What your diagnostics revealed — keep it simple]
**What it means:** [Explain in plain English what this means for the user]
**What I can fix:** [What you did or can do right now]
**Next step:** [What the user should do next, or offer to do more]

You don't have to use this format for every message — only when you have actual diagnostic results. For follow-up questions, greetings, or simple answers, just talk naturally.

WHAT YOU CAN DO:
- You have real diagnostic tools that run on the user's system. Use them! Don't guess when you can check.
- You can check internet connectivity, DNS, network interfaces, gateways, run traceroutes
- You can check disk space, memory, CPU, running processes, system uptime
- You can find large files, clear temp files
- You can check printers, restart print services, clear print queues
- You can check audio devices, USB devices, battery, OS info
- You can check firewall status, failed logins, suspicious processes, open connections
- When you need to fix something, run the appropriate tool. When you need to guide a physical action (like restarting a router), walk the user through it step by step.

IMPORTANT RULES:
- Always run diagnostics BEFORE giving a diagnosis. Don't guess.
- If a tool returns an error or unhelpful output, explain that simply and try an alternative approach.
- Never tell the user to "open terminal" or "run a command." YOU run the commands for them.
- If you can't fix something with your tools, be honest about it and explain what the user should do next (call ISP, take to repair shop, etc.)
- Keep your responses concise. Don't write essays. Users want answers, not lectures.
- Remember the conversation — don't ask the same question twice or repeat diagnostics unnecessarily."""


def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return sessions[session_id]


def process_message(session_id, user_message):
    messages = get_session(session_id)
    messages.append({"role": "user", "content": user_message})

    max_tool_rounds = 6
    for _ in range(max_tool_rounds):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" or choice.message.tool_calls:
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                except json.JSONDecodeError:
                    fn_args = {}

                result = execute_tool(fn_name, fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })
        else:
            assistant_msg = choice.message.content or ""
            messages.append({"role": "assistant", "content": assistant_msg})

            if len(messages) > 40:
                system_msg = messages[0]
                messages[:] = [system_msg] + messages[-30:]

            return assistant_msg

    final = response.choices[0].message.content or "I ran several checks but need a moment to process. Could you describe the issue one more time?"
    messages.append({"role": "assistant", "content": final})
    return final


@app.route("/")
def home():
    return render_template("chat.html")


@app.route("/preview")
def product_preview():
    return send_from_directory("preview", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "")
    session_id = data.get("session_id", "default")

    if not user_message.strip():
        return jsonify({"response": "I didn't catch that. Could you describe your issue?"})

    try:
        response = process_message(session_id, user_message)
        return jsonify({"response": response})
    except Exception as e:
        error_str = str(e)
        if "api_key" in error_str.lower() or "auth" in error_str.lower():
            return jsonify({"response": "I'm having trouble connecting to my brain right now. Please make sure the API key is configured correctly."})
        return jsonify({"response": f"Something went wrong on my end. Here's what I know: {error_str}"})


@app.route("/chat/clear", methods=["POST"])
def clear_chat():
    data = request.json or {}
    session_id = data.get("session_id", "default")
    if session_id in sessions:
        del sessions[session_id]
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
