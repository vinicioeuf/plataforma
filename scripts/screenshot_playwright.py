from playwright.sync_api import sync_playwright
import os

OUTPUT_DIR = 'screens'
os.makedirs(OUTPUT_DIR, exist_ok=True)

urls = {
    'home': 'http://127.0.0.1:8000/',
    'dashboard': 'http://127.0.0.1:8000/dashboard'
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1365, 'height': 768})
    for name, url in urls.items():
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            path = os.path.join(OUTPUT_DIR, f'{name}.png')
            page.screenshot(path=path, full_page=True)
            print(f'Screenshot saved: {path}')
        except Exception as e:
            print(f'Failed to capture {url}: {e}')
    browser.close()
