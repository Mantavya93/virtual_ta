import os
import json
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urljoin

load_dotenv()

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in/"
CATEGORY_URL = urljoin(BASE_URL, "c/courses/tds-kb/34")  # TDS forum
LOGIN_URL = urljoin(BASE_URL, "session")

EMAIL = os.getenv("DISCOURSE_EMAIL")
PASSWORD = os.getenv("DISCOURSE_PASSWORD")

session = requests.Session()


def login():
    resp = session.get(LOGIN_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    csrf_token = soup.find("input", {"name": "csrf"}).get("value")

    payload = {
        "login": EMAIL,
        "password": PASSWORD,
        "authenticity_token": csrf_token
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    login_resp = session.post(LOGIN_URL, data=payload, headers=headers)
    if login_resp.status_code == 200 and "Incorrect" not in login_resp.text:
        print("✅ Logged in to Discourse")
    else:
        raise Exception("❌ Login failed")


def get_topic_urls(category_url):
    topic_urls = set()
    page = 0

    while True:
        paginated_url = f"{category_url}?page={page}"
        resp = session.get(paginated_url)
        soup = BeautifulSoup(resp.text, "html.parser")

        topic_links = soup.select("a.title.raw-link.raw-topic-link")
        if not topic_links:
            break  # no more topics

        for link in topic_links:
            href = link.get("href")
            if href:
                topic_urls.add(urljoin(BASE_URL, href))
        
        print(f"🔗 Found {len(topic_links)} topics on page {page}")
        page += 1
        time.sleep(1)

    return list(topic_urls)


def scrape_topic(url):
    resp = session.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    title = soup.find("title").text.strip()
    posts = soup.select("div.topic-body .cooked")

    content = []
    for post in posts:
        text = post.get_text(separator="\n").strip()
        content.append(text)

    return {
        "url": url,
        "title": title,
        "content": "\n\n".join(content)
    }


def main():
    login()

    print("🔍 Collecting topic URLs...")
    topic_urls = get_topic_urls(CATEGORY_URL)
    print(f"📚 Found {len(topic_urls)} topics")

    data = []

    for idx, topic_url in enumerate(topic_urls):
        try:
            print(f"📄 Scraping ({idx+1}/{len(topic_urls)}): {topic_url}")
            post_data = scrape_topic(topic_url)
            data.append(post_data)
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Error scraping {topic_url}: {e}")

    with open("data/discourse_forum.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Scraping complete. Saved to data/discourse_forum.json")


if __name__ == "__main__":
    main()
