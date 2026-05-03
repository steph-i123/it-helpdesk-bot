import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

ARTICLES = {
    "what-is-dns": {
        "title": "What is DNS?",
        "icon": "📡",
        "category": "Internet & Wi-Fi",
        "short": "DNS translates website names into addresses your computer can find.",
        "prompt": "Explain what DNS is to someone who knows nothing about technology. Cover: what it does, why it matters, what happens when it breaks, how to fix common DNS issues (in simple steps a non-tech person can follow), and when to call their ISP. Keep it friendly and conversational. Use simple analogies.",
    },
    "wifi-drops": {
        "title": "Why does Wi-Fi drop?",
        "icon": "🌐",
        "category": "Internet & Wi-Fi",
        "short": "Wi-Fi can drop because of distance, interference, or router issues.",
        "prompt": "Explain why Wi-Fi drops to a non-technical person. Cover: common reasons (distance, walls, interference, too many devices, old router), simple fixes they can try themselves (moving closer, restarting router, changing channel), and when the problem is their ISP vs their router. Keep it friendly.",
    },
    "modem-vs-router": {
        "title": "Modem vs Router",
        "icon": "🔌",
        "category": "Internet & Wi-Fi",
        "short": "Your modem connects to the internet. Your router shares that connection.",
        "prompt": "Explain the difference between a modem and a router to someone non-technical. Use a simple analogy. Cover: what each one does, combo devices, when you need to restart which one, and common problems with each. Keep it friendly and simple.",
    },
    "packet-loss": {
        "title": "What is packet loss?",
        "icon": "📊",
        "category": "Internet & Wi-Fi",
        "short": "Packet loss means some data never arrives, causing lag and buffering.",
        "prompt": "Explain packet loss to a non-technical person. Use a simple analogy (like sending letters and some getting lost). Cover: what causes it, how it affects everyday use (video calls, gaming, streaming), how to tell if you have it, and what to do about it. Keep it friendly.",
    },
    "slow-computer": {
        "title": "Why is my computer slow?",
        "icon": "🐌",
        "category": "Computer Performance",
        "short": "Low disk space, too many apps, not enough RAM, or malware.",
        "prompt": "Explain to a non-technical person why their computer might be slow. Cover the most common reasons: too many programs running, low disk space, not enough RAM, malware, old hardware. For each reason, give a simple fix they can try. Keep it friendly and encouraging.",
    },
    "disk-space": {
        "title": "What eats disk space?",
        "icon": "💾",
        "category": "Computer Performance",
        "short": "Downloads, old files, temp files, and app caches pile up over time.",
        "prompt": "Explain to a non-technical person what uses up their disk space and how to free it up. Cover: downloads folder, temp files, app caches, old programs, large media files. Give simple steps to clean up. Mention that PingPal can help find large files. Keep it friendly.",
    },
    "ram-vs-storage": {
        "title": "RAM vs Storage",
        "icon": "🧠",
        "category": "Computer Performance",
        "short": "RAM is short-term memory for running apps. Storage is for saving files.",
        "prompt": "Explain RAM vs storage to a non-technical person using a desk analogy (RAM = desk space for working, storage = filing cabinet for keeping things). Cover: why both matter, signs you need more of each, and what you can do about it. Keep it simple and friendly.",
    },
    "cpu-usage": {
        "title": "What is CPU usage?",
        "icon": "⚡",
        "category": "Computer Performance",
        "short": "CPU is your computer's brain. At 100%, everything slows down.",
        "prompt": "Explain CPU usage to a non-technical person. What the CPU does (the brain that processes everything), what high CPU usage means, why it makes things slow, how to find what's using it, and simple fixes. Keep it friendly and conversational.",
    },
    "gaming-lag": {
        "title": "Why am I lagging?",
        "icon": "🎮",
        "category": "Gaming",
        "short": "High ping, packet loss, or a busy network cause gaming lag.",
        "prompt": "Explain gaming lag to a non-technical gamer. Cover: what ping is and why lower is better, what packet loss does to gameplay, the difference between lag and low FPS, why Wi-Fi is worse than wired for gaming, and simple things they can do to reduce lag. Keep it fun and relatable.",
    },
    "ping-jitter-nat": {
        "title": "Ping, jitter & NAT",
        "icon": "📶",
        "category": "Gaming",
        "short": "Ping is delay, jitter is inconsistency, NAT type affects matchmaking.",
        "prompt": "Explain ping, jitter, and NAT type to a gamer who doesn't understand networking. Use gaming examples. Cover: what good/bad ping looks like, why jitter causes rubber-banding, what NAT types mean for matchmaking, and how to improve each. Keep it fun.",
    },
    "virus-check": {
        "title": "Do I have a virus?",
        "icon": "🛡️",
        "category": "Security & Privacy",
        "short": "Signs include slowness, pop-ups, unknown programs, and high CPU usage.",
        "prompt": "Explain to a non-technical person how to tell if their computer has a virus. Cover: common signs (slowness, pop-ups, unknown programs, browser redirects), what to do if they suspect one, how to stay safe (don't click random links, keep software updated, use built-in security). Keep it reassuring, not scary.",
    },
    "firewall": {
        "title": "What is a firewall?",
        "icon": "🔥",
        "category": "Security & Privacy",
        "short": "A firewall controls what can enter or leave your network.",
        "prompt": "Explain firewalls to a non-technical person. Use a simple analogy (like a security guard at a building). Cover: what it does, why it matters, when it might block something you want, and whether they need to do anything about it. Keep it simple and reassuring.",
    },
    "printer-help": {
        "title": "Printer won't print",
        "icon": "🖨️",
        "category": "Printers & Devices",
        "short": "Usually a stuck print queue, offline status, or driver issue.",
        "prompt": "Explain to a non-technical person why their printer might not be working and how to fix it. Cover: checking if it's turned on and connected, clearing the print queue, restarting the print service, checking if it shows as offline, and reinstalling the printer. Give step-by-step instructions in plain English.",
    },
    "no-sound": {
        "title": "No sound",
        "icon": "🔊",
        "category": "Printers & Devices",
        "short": "Check output device, volume, mute, and audio drivers.",
        "prompt": "Explain to a non-technical person how to fix sound issues on their computer. Cover: checking volume isn't muted, selecting the right output device, checking headphone connections, restarting the audio service, and when it might be a hardware problem. Keep it friendly and step-by-step.",
    },
}


def get_all_articles():
    return {slug: {"title": a["title"], "icon": a["icon"], "category": a["category"], "short": a["short"]} for slug, a in ARTICLES.items()}


def get_article_meta(slug):
    a = ARTICLES.get(slug)
    if not a:
        return None
    return {"title": a["title"], "icon": a["icon"], "category": a["category"], "short": a["short"]}


def generate_article(slug):
    a = ARTICLES.get(slug)
    if not a:
        return None

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "placeholder":
            return {"title": a["title"], "content": a["short"] + "\n\nFull article unavailable — API key not configured."}

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    "You are PingPal, a friendly AI IT assistant writing knowledge base articles for non-technical people. "
                    "Write in a warm, conversational tone — like explaining to a friend. "
                    "Use short paragraphs, bullet points, and simple analogies. "
                    "Bold key terms with **term**. "
                    "End with a short 'Still stuck?' section mentioning they can ask PingPal to diagnose it for them."
                )},
                {"role": "user", "content": a["prompt"]},
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content or a["short"]
        return {"title": a["title"], "content": content}
    except Exception as e:
        return {"title": a["title"], "content": a["short"] + f"\n\nCouldn't generate full article: {e}"}
