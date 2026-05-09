import time
import urllib.parse
from collections import deque
import requests
from bs4 import BeautifulSoup

# Try importing playwright for JS-rendered fallback
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not installed. JS rendering fallback will not be available.")

def clean_html_content(soup):
    """
    Remove unnecessary tags (scripts, styles, navs, headers, footers) and extract visible text.
    """
    # Tags to remove completely
    for element in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "meta", "link", "form", "svg"]):
        element.extract()
        
    # Get text
    text = soup.get_text(separator="\n")
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    
    # Drop blank lines and UI noise
    noise = {"skip to content", "item added to your cart", "view cart", "check out", "continue shopping", "menu", "search", "close", "login", "create account", "cart"}
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk and len(chunk) > 1 and chunk.lower() not in noise)
    
    return text

def extract_with_playwright(url):
    """
    Uses Playwright to fully render the page and execute JavaScript.
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "", ""
        
    print(f"  [Fallback] Using Playwright to render: {url}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                # Go to page and wait until domcontentloaded (faster than load)
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                
                # Wait a bit for JS to populate DOM
                page.wait_for_timeout(2000)
                
                # Scroll down to trigger any lazy-loaded content
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)  # Wait for JS to render
            except Exception as e:
                print(f"  [Playwright] Navigation timeout or error, proceeding anyway. ({e})")
            
            content = page.content()
            title = page.title()
            browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            text = clean_html_content(soup)
            return text, title, soup
    except Exception as e:
        print(f"  [Playwright Error] Failed to launch or extract {url}: {e}")
        return "", "", None

def extract_links(soup, base_url, current_url):
    """
    Extracts valid internal links from the page.
    """
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Resolve relative URLs
        full_url = urllib.parse.urljoin(current_url, href)
        
        # Remove fragments (#)
        full_url = urllib.parse.urlunparse(urllib.parse.urlparse(full_url)._replace(fragment=""))
        
        # Check if it belongs to the base domain
        if full_url.startswith(base_url):
            lower_url = full_url.lower()
            # Filter out explicitly irrelevant URLs but keep products, collections, etc.
            invalid_keywords = ['/cart', '/checkout', '/account', '/login', '/search', '/policies']
            if any(kw in lower_url for kw in invalid_keywords):
                continue
                
            # Ignore common non-HTML files
            if any(lower_url.endswith(ext) for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.mp4', '.zip', '.gif', '.svg']):
                continue
                
            links.add(full_url)
    return links

def crawl_and_extract(base_url, max_pages=25):
    """
    Crawls the website and extracts content from each page.
    """
    visited = set()
    
    # Normalize base url
    parsed_base = urllib.parse.urlparse(base_url)
    base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
    
    # Seed the queue with the base URL and common paths requested by the user
    queue = deque([base_url])
    common_paths = ["/collections", "/products", "/pages", "/about", "/about-us", "/contact", "/contact-us"]
    for path in common_paths:
        queue.append(urllib.parse.urljoin(base_domain, path))
        
    all_content = []
    pages_scraped = 0
    
    print(f"Starting crawl at {base_url} (Max pages: {max_pages})")
    
    while queue and pages_scraped < max_pages:
        url = queue.popleft()
        
        # Normalize trailing slashes to avoid duplicates
        normalized_url = url.rstrip('/')
        if normalized_url in visited:
            continue
            
        visited.add(normalized_url)
        print(f"Scraping ({pages_scraped + 1}/{max_pages}): {url}")
        
        try:
            # 1. Try standard request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"  Skipped (Status {response.status_code})")
                continue
                
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
            
            text = clean_html_content(soup)
            
            # 2. Check if content is minimal (indicative of JS rendering) or if it's the base URL (to guarantee link discovery)
            if len(text) < 500 or url == base_url or url == base_url + "/":
                pw_text, pw_title, pw_soup = extract_with_playwright(url)
                if pw_text:
                    text = pw_text
                    if pw_title:
                        title = pw_title
                    if pw_soup:
                        soup = pw_soup
            
            # 3. Store valid content
            if len(text) >= 50:  # Minimum acceptable text length
                page_data = f"[Title: {title} | URL: {url}]\n{text}"
                all_content.append(page_data)
                pages_scraped += 1
                
                # Extract more links to crawl
                new_links = extract_links(soup, base_domain, url)
                for link in new_links:
                    if link not in visited and link not in queue:
                        queue.append(link)
            else:
                print(f"  Skipped (Insufficient content)")
                
        except Exception as e:
            print(f"  Error scraping {url}: {e}")
            
        # Small delay to avoid overloading the server
        time.sleep(0.5)
        
    combined_content = "\n\n" + ("="*50) + "\n\n".join(all_content)
    return combined_content, pages_scraped

if __name__ == "__main__":
    import sys
    # Ensure stdout handles utf-8 characters properly on Windows
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    target_url = "https://www.magppie.com"
    
    extracted_text, num_pages = crawl_and_extract(target_url, max_pages=25)
    
    print("\n" + "-"*40)
    print("--- Web Scraping Complete ---")
    print(f"Total pages successfully scraped: {num_pages}")
    print(f"Total characters extracted: {len(extracted_text)}")
    
    print("\n--- First 300 Characters ---")
    print(extracted_text[:300])
