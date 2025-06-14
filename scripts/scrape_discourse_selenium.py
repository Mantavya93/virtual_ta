import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load email and password from .env
load_dotenv()
EMAIL = os.getenv("DISCOURSE_EMAIL")
PASSWORD = os.getenv("DISCOURSE_PASSWORD")

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_URL = f"{BASE_URL}/c/courses/tds-kb/34"

def login_and_get_driver():
    options = Options()
    options.add_argument("--headless")  # Remove this line if you want to see the browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(f"{BASE_URL}/login")
    time.sleep(3)

    # Enter email
    username_input = driver.find_element(By.ID, "login-account-name")
    username_input.send_keys(EMAIL)

    # Enter password
    password_input = driver.find_element(By.ID, "login-account-password")
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)

    time.sleep(5)  # Wait for login to complete
    return driver

def get_topic_links(driver):
    driver.get(CATEGORY_URL)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = soup.select('a.title.raw-link.raw-topic-link')
    topic_urls = [BASE_URL + link['href'] for link in links if link['href'].startswith('/t/')]
    return list(set(topic_urls))

def get_topic_content(driver, url):
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    posts = soup.select('.cooked')
    return "\n\n".join(post.get_text(separator="\n") for post in posts)

def main():
    driver = login_and_get_driver()
    print("🔍 Logged in successfully, scraping topics...")

    topic_urls = get_topic_links(driver)
    discussions = []

    for url in topic_urls:
        print(f"🔎 {url}")
        try:
            content = get_topic_content(driver, url)
            if content:
                discussions.append({"url": url, "content": content})
        except Exception as e:
            print(f"⚠️ Error fetching {url}: {e}")
        time.sleep(1)

    driver.quit()

    output_path = Path("data/discourse_content.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(discussions, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(discussions)} discussions to {output_path}")

if __name__ == "__main__":
    main()
