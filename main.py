import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO)

class WebCrawler:
    def __init__(self):
        self.index = defaultdict(list)
        self.visited = set()

    def crawl(self, url, base_url=None):
        if url in self.visited:
            logging.debug(f"Skipping already visited URL: {url}")
            return
            
        logging.info(f"Crawling URL: {url}")
        self.visited.add(url)

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            soup = BeautifulSoup(response.text, 'html.parser')
            self.index[url] = soup.get_text()
            logging.debug(f"Successfully indexed content from {url}")

            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    href = urljoin(base_url or url, href)
                    if href.startswith(base_url or url):
                        logging.debug(f"Found internal link: {href}")
                        self.crawl(href, base_url=base_url or url)
                    else:
                        logging.debug(f"Skipping external link: {href}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error crawling {url}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error while crawling {url}: {e}")

    def search(self, keyword):
        results = []
        for url, text in self.index.items():
            if keyword.lower() in text.lower():
                results.append(url)
        return results

    def print_results(self, results):
        if results:
            print("Search results:")
            for result in results:
                print(f"- {result}")
        else:
            print("No results found.")

def main():
    crawler = WebCrawler()
    start_url = "https://example.com"
    crawler.crawl(start_url)

    keyword = "test"
    results = crawler.search(keyword)
    crawler.print_results(results)

import unittest
from unittest.mock import patch, MagicMock
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urljoin, urlparse

class WebCrawlerTests(unittest.TestCase):
    def setUp(self):
        self.crawler = WebCrawler()
        
    def test_init(self):
        """Test crawler initialization"""
        self.assertIsInstance(self.crawler.index, defaultdict)
        self.assertIsInstance(self.crawler.visited, set)
        self.assertEqual(len(self.crawler.visited), 0)
        self.assertEqual(len(self.crawler.index), 0)

    @patch('requests.get')
    def test_crawl_success(self, mock_get):
        """Test successful crawling with internal and external links"""
        sample_html = """
        <html><body>
            <h1>Welcome!</h1>
            <a href="/about">About Us</a>
            <a href="https://www.external.com">External Link</a>
            <a href="/contact">Contact</a>
            <a href="#section">Section Link</a>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_get.return_value = mock_response

        self.crawler.crawl("https://example.com")

        # Assert internal links were added
        self.assertIn("https://example.com/about", self.crawler.visited)
        self.assertIn("https://example.com/contact", self.crawler.visited)
        # Assert external links were not crawled
        self.assertNotIn("https://www.external.com", self.crawler.visited)
        # Assert anchor links were not crawled
        self.assertNotIn("https://example.com/#section", self.crawler.visited)

    @patch('requests.get')
    def test_crawl_nested_pages(self, mock_get):
        """Test crawling nested pages"""
        main_html = '<a href="/page1">Page 1</a>'
        page1_html = '<a href="/page2">Page 2</a>'
        page2_html = '<a href="/page3">Page 3</a>'

        def mock_get_response(*args, **kwargs):
            url = args[0]
            mock_resp = MagicMock()
            if url == "https://example.com":
                mock_resp.text = main_html
            elif url == "https://example.com/page1":
                mock_resp.text = page1_html
            elif url == "https://example.com/page2":
                mock_resp.text = page2_html
            return mock_resp

        mock_get.side_effect = mock_get_response
        self.crawler.crawl("https://example.com")

        for page in ["/page1", "/page2", "/page3"]:
            self.assertIn(f"https://example.com{page}", self.crawler.visited)

    @patch('requests.get')
    def test_crawl_error_handling(self, mock_get):
        """Test various error scenarios during crawling"""
        mock_get.side_effect = requests.exceptions.RequestException("Network Error")
        
        # Capture logging output
        with self.assertLogs(level='INFO') as log:
            self.crawler.crawl("https://example.com")
            
        self.assertIn("https://example.com", self.crawler.visited)
        self.assertEqual(len(self.crawler.index), 0)

    def test_search_case_insensitive(self):
        """Test case-insensitive search functionality"""
        self.crawler.index = {
            "page1": "This has the KEYWORD",
            "page2": "This has the keyword",
            "page3": "No match here"
        }

        results = self.crawler.search("keyword")
        self.assertEqual(len(results), 2)
        self.assertIn("page1", results)
        self.assertIn("page2", results)
        self.assertNotIn("page3", results)

    def test_search_empty_index(self):
        """Test search with empty index"""
        results = self.crawler.search("keyword")
        self.assertEqual(results, [])

    def test_search_special_characters(self):
        """Test search with special characters"""
        self.crawler.index = {
            "page1": "Text with $ special & characters",
            "page2": "Normal text"
        }
        
        results = self.crawler.search("$ special &")
        self.assertEqual(len(results), 1)
        self.assertIn("page1", results)

    @patch('builtins.print')
    def test_print_results(self, mock_print):
        """Test printing search results"""
        # Test with results
        results = ["https://example.com/page1", "https://example.com/page2"]
        self.crawler.print_results(results)
        mock_print.assert_any_call("Search results:")
        for result in results:
            mock_print.assert_any_call(f"- {result}")

        # Test without results
        mock_print.reset_mock()
        self.crawler.print_results([])
        mock_print.assert_called_once_with("No results found.")

if __name__ == "__main__":
    unittest.main()  # Run unit tests
    main()  # Run your main application logic 