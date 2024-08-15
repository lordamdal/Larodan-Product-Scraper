import argparse
import json
import concurrent.futures
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os
import time
from PIL import Image
from io import BytesIO
from tqdm import tqdm
import random
import sys

def matrix_print(text):
    for line in text.split('\n'):
        for char in line:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(random.uniform(0.01, 0.1))
        sys.stdout.write('\n')
        sys.stdout.flush()
        time.sleep(0.1)

class LarodanScraper:
    def __init__(self, base_url, concurrency):
        self.base_url = base_url
        self.concurrency = concurrency
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_product_urls(self):
        urls = []
        page = 1
        while True:
            page_url = f"{self.base_url}page/{page}/"
            response = self.session.get(page_url)
            if response.status_code != 200:
                print(f"Failed to fetch page {page}")
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            product_links = soup.find_all('a', class_='woocommerce-LoopProduct-link')
            
            if not product_links:
                break
            
            urls.extend([urljoin(self.base_url, link['href']) for link in product_links])
            page += 1
            time.sleep(1)  # Add a delay to avoid overwhelming the server
        
        return urls

    def crawl_product(self, url):
        response = self.session.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch product page: {url}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        product_data = {
            "id": "",
            "name": "",
            "CAS": "",
            "structure": "",
            "smiles": "",
            "description": "",
            "molecular_weight": "",
            "url": url,
            "image_path": "",
            "img": "",
            "pdf_msds": "",
            "synonyms": [],
            "packaging": {}
        }
        
        # Extract product name
        name_elem = soup.find('h1', class_='product_title')
        product_data["name"] = name_elem.text.strip() if name_elem else ""

        # Extract product ID
        id_elem = soup.find('span', class_='sku')
        product_data["id"] = id_elem.text.strip() if id_elem else ""

        # Extract CAS number
        cas_elem = soup.find('div', class_='product-prop', string=lambda text: 'CAS number:' in text if text else False)
        if cas_elem:
            product_data["CAS"] = cas_elem.text.split(':')[-1].strip()

        # Extract structure and molecular weight
        info_columns = soup.find('div', class_='product-info-columns')
        if info_columns:
            for prop in info_columns.find_all('div', class_='product-prop'):
                label = prop.find('span', class_='prop-label')
                if label:
                    if 'Molecular formula:' in label.text:
                        product_data["structure"] = prop.text.split(':')[-1].strip()
                    elif 'Molecular weight:' in label.text:
                        product_data["molecular_weight"] = prop.text.split(':')[-1].strip()
                    elif 'Smiles:' in label.text:
                        product_data["smiles"] = prop.text.split(':')[-1].strip()

        # Extract synonyms
        synonyms_elem = soup.find('div', class_='product-prop-synonyms')
        if synonyms_elem:
            product_data["synonyms"] = [s.strip() for s in synonyms_elem.text.split(':')[-1].split(',')]

        # Extract description
        desc_elem = soup.find('div', class_='woocommerce-product-details__short-description')
        product_data["description"] = desc_elem.text.strip() if desc_elem else ""

        # Extract image URL
        img_elem = soup.find('div', class_='prod-structure')
        if img_elem:
            img_tag = img_elem.find('img')
            if img_tag and 'src' in img_tag.attrs:
                product_data["img"] = img_tag['src']
                image_filename = self.process_image(product_data["img"], product_data["id"])
                if image_filename:
                    product_data["image_path"] = os.path.join('images', image_filename)

        # Extract PDF MSDS link
        pdf_link = soup.find('a', href=lambda href: href and href.endswith('.pdf'))
        if pdf_link:
            product_data["pdf_msds"] = urljoin(url, pdf_link['href'])

        # Extract packaging information
        variations_table = soup.find('table', class_='product-variations-table')
        if variations_table:
            for row in variations_table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 3:
                    package_size = cols[1].text.split('-')[-1].strip()
                    price = cols[2].text.strip()
                    product_data["packaging"][package_size] = price

        return product_data

    def process_image(self, img_url, product_id):
        try:
            response = self.session.get(img_url)
            img = Image.open(BytesIO(response.content))
            img.thumbnail((100, 100))  # Resize to thumbnail
            
            img_dir = 'images'
            os.makedirs(img_dir, exist_ok=True)
            
            img_filename = f"{product_id}.png"
            img_path = os.path.join(img_dir, img_filename)
            img.save(img_path, 'PNG', optimize=True)
            
            return img_filename
        except Exception as e:
            print(f"Error processing image for product {product_id}: {e}")
            return None

    def run(self):
        product_urls = self.get_product_urls()
        
        print(f"Found {len(product_urls)} products to scrape.")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            products = list(tqdm(executor.map(self.crawl_product, product_urls), 
                                 total=len(product_urls), 
                                 desc="Scraping products", 
                                 unit="product"))
        
        products = [p for p in products if p and any(p.values())]
        
        print(f"Successfully scraped {len(products)} products.")
        print("Saving results to products.json...")
        
        with open('products.json', 'w') as f:
            json.dump(products, f, indent=2)
        
        print("Scraping completed successfully!")

def main():
    parser = argparse.ArgumentParser(description='Larodan Product Scraper')
    parser.add_argument('url', help='URL of the product listing page')
    parser.add_argument('-c', type=int, default=1, help='Number of concurrent crawlers')
    args = parser.parse_args()

    matrix_print("AMDAL WEB SCRAPER")
    time.sleep(1)  # Pause for effect after the matrix message

    print("\nInitializing scraper...")
    scraper = LarodanScraper(args.url, args.c)
    
    print("Starting scraping process...")
    scraper.run()

if __name__ == '__main__':
    main()