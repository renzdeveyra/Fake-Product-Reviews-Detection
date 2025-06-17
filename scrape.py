from lxml import html
import json
import os
from time import sleep
from dateutil import parser as dateparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

BROWSERS = ['chrome', 'firefox', 'edge']

def get_review_url(url):
    if '/dp/' in url:
        asin = url.split('/dp/')[1].split('/')[0]
        return f"https://www.amazon.com/product-reviews/{asin}?ie=UTF8&reviewerType=all_reviews&sortBy=recent", asin
    elif '/product-reviews/' in url:
        asin = url.split('/product-reviews/')[1].split('?')[0]
        return f"https://www.amazon.com/product-reviews/{asin}?ie=UTF8&reviewerType=all_reviews&sortBy=recent", asin
    else:
        raise ValueError("URL must contain /dp/ASIN or /product-reviews/ASIN")


def launch_browser():
    for browser in BROWSERS:
        profile_path = os.path.join(os.getcwd(), f"{browser}_profile")
        try:
            if browser == 'chrome':
                options = webdriver.ChromeOptions()
                options.add_argument(f"--user-data-dir={profile_path}")
                options.add_argument("--profile-directory=Default")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--start-maximized")
                driver = webdriver.Chrome(options=options)
                print("✅ Launched Chrome")
                return driver

            elif browser == 'firefox':
                options = webdriver.FirefoxOptions()
                options.set_preference("dom.webnotifications.enabled", False)
                driver = webdriver.Firefox(options=options)
                print("✅ Launched Firefox")
                return driver

            elif browser == 'edge':
                options = webdriver.EdgeOptions()
                options.add_argument(f"--user-data-dir={profile_path}")
                options.add_argument("--profile-directory=Default")
                driver = webdriver.Edge(options=options)
                print("✅ Launched Edge")
                return driver

        except WebDriverException as e:
            print(f"❌ {browser.title()} failed to launch: {e}")
    
    raise RuntimeError("🚫 No supported browser could be launched. Make sure drivers are installed.")


def scrape_top_reviews(base_url, asin):
    print("Scraping top reviews for:", asin)

    XPATH_REVIEWS = '//div[contains(@id,"customer_review-")]'
    XPATH_TITLE = (
        './/a[@data-hook="review-title"]//span[contains(@class, "cr-original-review-content")]/text() | '
        './/a[@data-hook="review-title"]//span[not(@*)]/text()'
    )
    XPATH_RATING = './/i/span/text()'
    XPATH_DATE = './/span[contains(@data-hook,"review-date")]/text()'
    XPATH_AUTHOR = './/span[contains(@class,"a-profile-name")]/text()'
    XPATH_REVIEW_TEXT = (
        './/span[@data-hook="review-body"]//text() | '
        './/span[contains(@class,"cr-original-review-content")]/text() | '
        './/span[contains(@class,"cr-translated-review-content")]/text()'
    )
    XPATH_VERIFIED_PURCHASE = './/span[contains(@data-hook,"avp-badge")]/text()'

    all_reviews = []
    driver = launch_browser()
    driver.get(base_url)

    for page in range(1, 6):
        print(f"📄 Fetching page {page}...")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, XPATH_REVIEWS))
            )
        except Exception as e:
            print(f"[Page {page}] Timeout waiting for reviews:", e)

        source = driver.page_source
        parser = html.fromstring(source)
        reviews = parser.xpath(XPATH_REVIEWS)

        for review in reviews:
            try:
                review_author = ''.join(review.xpath(XPATH_AUTHOR)).strip()
                if review_author and len(review_author) % 2 == 0:
                    half = len(review_author) // 2
                    if review_author[:half] == review_author[half:]:
                        review_author = review_author[:half]

                review_rating = ''.join(review.xpath(XPATH_RATING)).replace(' out of 5 stars', '').strip()
                if review_rating and len(review_rating) % 2 == 0:
                    half = len(review_rating) // 2
                    if review_rating[:half] == review_rating[half:]:
                        review_rating = review_rating[:half]

                review_header = ' '.join([t.strip() for t in review.xpath(XPATH_TITLE) if t.strip()])
                review_posted_date = ''.join(review.xpath(XPATH_DATE)).strip()
                review_text = ' '.join([t.strip() for t in review.xpath(XPATH_REVIEW_TEXT) if t.strip()])

                verified_purchase_list = review.xpath(XPATH_VERIFIED_PURCHASE)
                verified_purchase = verified_purchase_list[0].strip() if verified_purchase_list else "Not Verified"

                if 'on ' in review_posted_date:
                    review_posted_date = dateparser.parse(review_posted_date.split('on ')[1]).strftime('%d %b %Y')
                else:
                    review_posted_date = dateparser.parse(review_posted_date).strftime('%d %b %Y')

                all_reviews.append({
                    'review_author': review_author,
                    'review_rating': review_rating,
                    'review_header': review_header,
                    'review_text': review_text,
                    'review_posted_date': review_posted_date,
                    'verified_purchase': verified_purchase,
                })
            except Exception as e:
                print("Skipping review due to error:", e)

        driver.save_screenshot(f"debug_page_{page}.png")

        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//li[@class="a-last"]/a'))
            )
            driver.execute_script("arguments[0].scrollIntoView();", next_button)
            sleep(1)
            next_button.click()
            sleep(3)
        except Exception as e:
            print("⚠️ Could not click Next button. Might be end of pages.")
            break

    driver.quit()
    return all_reviews


def is_logged_in(driver):
    driver.get("https://www.amazon.com/gp/profile")
    sleep(3)
    return "Sign-In" not in driver.title and "Amazon Sign In" not in driver.title


def login_amazon_if_needed():
    print("\n🔐 Opening browser for manual Amazon login...")
    driver = launch_browser()
    driver.get("https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2Fsign%2Fs%3Fk%3Dsign%2Bin%26ref_%3Dnav_custrec_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")

    print("👉 Please log in manually in the browser that just opened.")
    print("⚠️ Do NOT close the browser until prompted.")
    input("✅ Press ENTER here AFTER you've logged in and you can see your account name...")

    try:
        if is_logged_in(driver):
            print("✅ Login successful. Proceeding...")
        else:
            print("⚠️ Still not logged in. You may need to try again.")
            input("Press ENTER to close browser and abort.")
            driver.quit()
            raise RuntimeError("Login not detected. Exiting.")
    finally:
        driver.quit()


if __name__ == "__main__":
    for b in BROWSERS:
        os.makedirs(os.path.join(os.getcwd(), f"{b}_profile"), exist_ok=True)

    login_amazon_if_needed()

    with open("urls.txt", 'r') as urllist:
        os.makedirs('scraped_reviews', exist_ok=True)

        for url in urllist.readlines():
            url = url.strip()
            if not url:
                continue

            try:
                review_url, asin = get_review_url(url)
                reviews = scrape_top_reviews(review_url, asin)

                with open(f'scraped_reviews/{asin}_top_reviews.json', 'w', encoding='utf-8') as f:
                    json.dump(reviews, f, indent=4, ensure_ascii=False)

                print(f"✅ Saved: scraped_reviews/{asin}_top_reviews.json")
            except Exception as e:
                print(f"❌ Error scraping {url}:", e)
