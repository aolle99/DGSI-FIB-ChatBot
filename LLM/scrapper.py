import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import html2text
from concurrent.futures import ThreadPoolExecutor

start_url = "https://www.fib.upc.edu/en/"
visited_urls = set()
output_folder = "./downloaded_pages"
markdown_folder = "./markdown_pages"
pdf_folder = "./pdf_pages"
os.makedirs(output_folder, exist_ok=True)
os.makedirs(markdown_folder, exist_ok=True)
os.makedirs(pdf_folder, exist_ok=True)

def save_page(url, content):
    if not url.startswith(start_url):
        return

    parsed_url = urlparse(url)
    path = parsed_url.path.strip("/")
    if not path:
        path = "index"
    else:
        path = os.path.join(*path.split("/"))

    html_filepath = os.path.join(output_folder, f"{path}.html")
    md_filepath = os.path.join(markdown_folder, f"{path}.md")

    os.makedirs(os.path.dirname(html_filepath), exist_ok=True)
    os.makedirs(os.path.dirname(md_filepath), exist_ok=True)

    soup = BeautifulSoup(content, "html.parser")
    for link in soup.find_all("a", href=True):
        link_url = urljoin(url, link["href"])
        link_parsed_url = urlparse(link_url)
        link_path = link_parsed_url.path.strip("/")
        if not link_path:
            link_path = "index"
        else:
            link_path = os.path.join(*link_path.split("/"))
        link["href"] = f"{link_path}.md"

    updated_content = str(soup)

    with open(html_filepath, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"Saved HTML: {html_filepath}")

    markdown_content = html2text.html2text(updated_content)
    with open(md_filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"Saved Markdown: {md_filepath}")

def save_pdf(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        pdf_filepath = os.path.join(pdf_folder, filename)
        os.makedirs(os.path.dirname(pdf_filepath), exist_ok=True)
        
        with open(pdf_filepath, 'wb') as f:
            f.write(response.content)
        print(f"Saved PDF: {pdf_filepath}")
        return True
    except requests.RequestException as e:
        print(f"Failed to download PDF {url}: {e}")
        return False

def fetch_and_save(url):
    # Check if URL points to a PDF
    if url.lower().endswith('.pdf'):
        save_pdf(url)
    else:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            save_page(url, response.text)
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")

def crawl(url):
    if url in visited_urls or not url.startswith(start_url):
        return
    print(f"Crawling: {url}")
    visited_urls.add(url)

    # Check if URL is a PDF
    if url.lower().endswith('.pdf'):
        save_pdf(url)
        return

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return

    save_page(url, response.text)

    soup = BeautifulSoup(response.text, "html.parser")
    links_to_crawl = []

    for link in soup.find_all("a", href=True):
        full_url = urljoin(url, link["href"])
        if full_url not in visited_urls:
            links_to_crawl.append(full_url)

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        executor.map(crawl, links_to_crawl)

crawl(start_url)