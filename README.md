# Larodan Product Scraper

This script scrapes product information from the Larodan website, specifically from the monounsaturated fatty acids category.

## Features

- Scrapes product listings, handling pagination
- Extracts detailed product information
- Saves product images as PNG thumbnails
- Extracts UN Number from product MSDS PDFs (when available)
- Supports concurrent crawling for faster operation

## Requirements

Python 3.10 or higher is required. All necessary libraries are listed in `requirements.txt`.

## Installation

1. Clone this repository
2. Install the required libraries:

   ```
   pip install -r requirements.txt
   ```

## Usage

Run the script with:

```
python larodan_scraper.py https://www.larodan.com/products/category/monounsaturated-fa/ -c 5
```

The `-c` parameter sets the number of concurrent crawlers. Adjust as needed.

## Output

The script outputs a `products.json` file containing all scraped product information. Product images are saved in the `images` directory.

## Note

This script is for educational purposes only. Ensure you have permission before scraping any website, and be mindful of the load you put on the server.
Ahmed Ali (Lord Amdal )
