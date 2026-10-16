import os
import json
import feedparser
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "sent_history.json"

# 监控源配置：官方 RSS 及稳定镜像源
FEEDS = {
    "OpenAI News": "https://openai.com/news/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Anthropic News (Mirror)": "https://rsshub.bestblogs.dev/anthropic/news",
    "Hugging Face Blog": "https://huggingface.co/blog/feed.xml"
}

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False, indent=2)

def send_telegram_message(title, link, source):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = (
        f"🚨 *AI Breaking News* | {source}\n\n"
        f"📌 *{title}*\n\n"
        f"🔗 [点击阅读全文]({link})"
    )
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def main():
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

    history = load_history()
    new_sent_count = 0

    for source_name, feed_url in FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            # 取最近的 5 条检查
            for entry in feed.entries[:5]:
                post_id = entry.get("id") or entry.get("link")
                if post_id and post_id not in history:
                    title = entry.get("title", "No Title").strip()
                    link = entry.get("link", "").strip()
                    
                    if send_telegram_message(title, link, source_name):
                        history.add(post_id)
                        new_sent_count += 1
                        print(f"Sent: [{source_name}] {title}")
        except Exception as e:
            print(f"Failed to fetch {source_name}: {e}")

    if new_sent_count > 0:
        save_history(history)
        print(f"Total new messages sent: {new_sent_count}")
    else:
        print("No new updates found.")

if __name__ == "__main__":
    main()
