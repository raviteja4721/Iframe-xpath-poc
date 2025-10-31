#!/usr/bin/env python3
"""
Comprehensive Iframe Scanner and Text Finder

This tool automatically:
1. Discovers and maps all iframes on a page
2. Shows iframe hierarchy and details
3. Searches for any text across all iframes using multiple strategies
4. No need to specify locator strategies - tries everything automatically
"""

import time
import logging
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dataclasses import dataclass

@dataclass
class IframeInfo:
    """Information about discovered iframes."""
    index: int
    id: str
    name: str
    src: str
    title: str
    class_name: str
    xpath: str
    hierarchy_path: List[str]
    is_accessible: bool
    error_message: str = ""
    content_preview: str = ""
    text_found: List[Dict] = None

    def __post_init__(self):
        if self.text_found is None:
            self.text_found = []

class ComprehensiveIframeScanner:
    """
    Comprehensive iframe discovery and text search tool.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 15):
        self.timeout = timeout
        self.driver = None
        self.wait = None
        self.discovered_iframes = []
        self.search_results = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup WebDriver
        self._setup_driver(headless)
    
    def _setup_driver(self, headless: bool):
        """Setup Chrome WebDriver."""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, self.timeout)
            self.logger.info("✅ WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize WebDriver: {str(e)}")
            raise
    
    def scan_page(self, url: str = None, html_source: str = None, search_text: str = None) -> Dict[str, Any]:
        """
        Comprehensive page scan - discover iframes and optionally search for text.
        
        Args:
            url (str, optional): URL to scan
            html_source (str, optional): HTML/DOM source to analyze
            search_text (str, optional): Text to search for across all iframes
            
        Returns:
            Dict containing all discovered iframes and search results
        """
        try:
            if url:
                self.logger.info(f"🔍 Starting comprehensive scan of URL: {url}")
                # Load the page
                self.driver.get(url)
                self.logger.info("📄 Page loaded, waiting for content...")
                time.sleep(3)
            elif html_source:
                self.logger.info(f"🔍 Starting comprehensive scan of provided DOM/HTML source")
                # Load HTML source directly
                self._load_html_source(html_source)
                self.logger.info("📄 HTML source loaded")
            else:
                raise ValueError("Either URL or HTML source must be provided")
            
            # Discover all iframes
            self.logger.info("🖼️  Discovering iframes...")
            self._discover_all_iframes()
            
            # Search for text if provided
            if search_text:
                self.logger.info(f"🔎 Searching for text: '{search_text}'")
                self._search_text_everywhere(search_text)
            
            # Generate comprehensive report
            report = self._generate_report(search_text)
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error during scan: {str(e)}")
            raise
        finally:
            self._return_to_main_context()
    
    def _load_html_source(self, html_source: str):
        """Load HTML source directly into the browser."""
        try:
            # Create a data URL with the HTML content
            data_url = f"data:text/html;charset=utf-8,{html_source}"
            self.driver.get(data_url)
            self.logger.info("✅ HTML source loaded successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to load HTML source: {str(e)}")
            raise
    
    def _discover_all_iframes(self, current_path: List[str] = None, depth: int = 0):
        """Recursively discover all iframes on the page."""
        if current_path is None:
            current_path = ["main_page"]
        
        if depth > 10:  # Prevent infinite recursion
            self.logger.warning(f"⚠️  Maximum iframe depth reached: {depth}")
            return
        
        try:
            # Find all iframe and frame elements
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            frames = self.driver.find_elements(By.TAG_NAME, "frame")
            all_frames = iframes + frames
            
            self.logger.info(f"📊 Found {len(all_frames)} iframe(s) at depth {depth}")
            
            for i, frame in enumerate(all_frames):
                frame_info = self._extract_iframe_info(frame, i, current_path, depth)
                self.discovered_iframes.append(frame_info)
                
                # Try to access the iframe content
                if frame_info.is_accessible:
                    try:
                        self.logger.info(f"🔍 Accessing iframe: {' → '.join(frame_info.hierarchy_path)}")
                        
                        # Switch to iframe
                        self.driver.switch_to.frame(frame)
                        
                        # Get content preview
                        frame_info.content_preview = self._get_content_preview()
                        
                        # Recursively check for nested iframes
                        nested_path = current_path + [frame_info.xpath.split('/')[-1]]
                        self._discover_all_iframes(nested_path, depth + 1)
                        
                    except Exception as e:
                        frame_info.is_accessible = False
                        frame_info.error_message = str(e)
                        self.logger.warning(f"⚠️  Cannot access iframe {i}: {str(e)}")
                    
                    finally:
                        # Always switch back to parent
                        self.driver.switch_to.parent_frame()
        
        except Exception as e:
            self.logger.error(f"❌ Error discovering iframes at depth {depth}: {str(e)}")
    
    def _extract_iframe_info(self, frame, index: int, current_path: List[str], depth: int) -> IframeInfo:
        """Extract comprehensive information about an iframe."""
        try:
            # Get all available attributes
            frame_id = frame.get_attribute("id") or ""
            frame_name = frame.get_attribute("name") or ""
            frame_src = frame.get_attribute("src") or ""
            frame_title = frame.get_attribute("title") or ""
            frame_class = frame.get_attribute("class") or ""
            
            # Generate XPath
            xpath = self._generate_element_xpath(frame)
            
            # Create hierarchy path
            hierarchy_path = current_path + [self._get_frame_identifier(frame, index)]
            
            # Check if frame is accessible (basic check)
            is_accessible = True
            try:
                # Try to get the frame's tag name as a basic accessibility test
                frame.tag_name
            except:
                is_accessible = False
            
            return IframeInfo(
                index=index,
                id=frame_id,
                name=frame_name,
                src=frame_src,
                title=frame_title,
                class_name=frame_class,
                xpath=xpath,
                hierarchy_path=hierarchy_path,
                is_accessible=is_accessible
            )
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error extracting iframe info: {str(e)}")
            return IframeInfo(
                index=index,
                id="",
                name="",
                src="",
                title="",
                class_name="",
                xpath="",
                hierarchy_path=current_path + [f"iframe_{index}"],
                is_accessible=False,
                error_message=str(e)
            )
    
    def _get_frame_identifier(self, frame, index: int) -> str:
        """Get a human-readable identifier for the frame."""
        frame_id = frame.get_attribute("id")
        if frame_id:
            return f"id='{frame_id}'"
        
        frame_name = frame.get_attribute("name")
        if frame_name:
            return f"name='{frame_name}'"
        
        frame_src = frame.get_attribute("src")
        if frame_src:
            src_name = frame_src.split('/')[-1][:20]
            return f"src='{src_name}'"
        
        return f"iframe_{index}"
    
    def _generate_element_xpath(self, element) -> str:
        """Generate XPath for an element."""
        try:
            xpath = self.driver.execute_script("""
                function getElementXPath(element) {
                    if (element.id !== '') {
                        return "//*[@id='" + element.id + "']";
                    }
                    if (element === document.body) {
                        return '/html/body';
                    }
                    var ix = 0;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element) {
                            return getElementXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                }
                return getElementXPath(arguments[0]);
            """, element)
            return xpath or "//iframe"
        except:
            return "//iframe"
    
    def _get_content_preview(self) -> str:
        """Get a preview of the current frame's content."""
        try:
            # Get page title
            title = self.driver.title
            
            # Get some text content
            body = self.driver.find_element(By.TAG_NAME, "body")
            text_content = body.text[:200]  # First 200 characters
            
            # Clean up the text
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            preview = ' | '.join(lines[:3])  # First 3 non-empty lines
            
            if title:
                return f"Title: {title} | Content: {preview}"
            else:
                return f"Content: {preview}"
                
        except Exception as e:
            return f"Error getting preview: {str(e)}"
    
    def _search_text_everywhere(self, search_text: str):
        """Search for text in main page and all accessible iframes."""
        self.search_results = {
            'search_text': search_text,
            'total_locations_found': 0,
            'locations': []
        }
        
        # Search in main page first
        self._return_to_main_context()
        self.logger.info("🔍 Searching in main page...")
        main_results = self._search_in_current_context(search_text, ["main_page"])
        
        if main_results:
            self.search_results['locations'].extend(main_results)
            self.search_results['total_locations_found'] += len(main_results)
        
        # Search in each accessible iframe
        for iframe_info in self.discovered_iframes:
            if iframe_info.is_accessible:
                try:
                    self.logger.info(f"🔍 Searching in iframe: {' → '.join(iframe_info.hierarchy_path)}")
                    
                    # Navigate to the iframe
                    self._navigate_to_iframe(iframe_info)
                    
                    # Search in this iframe
                    iframe_results = self._search_in_current_context(search_text, iframe_info.hierarchy_path)
                    
                    if iframe_results:
                        iframe_info.text_found = iframe_results
                        self.search_results['locations'].extend(iframe_results)
                        self.search_results['total_locations_found'] += len(iframe_results)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Error searching in iframe {iframe_info.hierarchy_path}: {str(e)}")
                
                finally:
                    self._return_to_main_context()
    
    def _search_in_current_context(self, search_text: str, location_path: List[str]) -> List[Dict]:
        """Search for text in the current context using multiple strategies."""
        found_elements = []
        
        # Multiple search strategies - no need for user to specify!
        search_strategies = [
            # Exact text match
            f"//*[text()='{search_text}']",
            # Contains text
            f"//*[contains(text(), '{search_text}')]",
            # Partial matches for each word
            f"//*[contains(text(), '{search_text.split()[0] if search_text.split() else search_text}')]",
            # Case insensitive
            f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_text.lower()}')]",
            # In attributes
            f"//*[@title[contains(., '{search_text}')] or @alt[contains(., '{search_text}')] or @placeholder[contains(., '{search_text}')]]",
            # In any text content (including nested)
            f"//*[contains(., '{search_text}')]"
        ]
        
        for i, xpath in enumerate(search_strategies):
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                
                for element in elements:
                    try:
                        # Get element details
                        tag_name = element.tag_name
                        element_text = element.text[:100]  # First 100 chars
                        element_xpath = self._generate_element_xpath(element)
                        
                        # Check if this element is already found
                        already_found = any(
                            found['element_xpath'] == element_xpath 
                            for found in found_elements
                        )
                        
                        if not already_found:
                            found_elements.append({
                                'location_path': location_path,
                                'strategy_used': f"Strategy {i+1}",
                                'xpath_used': xpath,
                                'element_xpath': element_xpath,
                                'tag_name': tag_name,
                                'element_text': element_text,
                                'found_text': search_text
                            })
                    
                    except Exception as e:
                        continue  # Skip problematic elements
                        
            except Exception as e:
                continue  # Skip problematic strategies
        
        return found_elements
    
    def _navigate_to_iframe(self, iframe_info: IframeInfo):
        """Navigate to a specific iframe."""
        self._return_to_main_context()
        
        # Find the iframe again (it might have changed)
        try:
            if iframe_info.id:
                iframe = self.driver.find_element(By.ID, iframe_info.id)
            elif iframe_info.name:
                iframe = self.driver.find_element(By.NAME, iframe_info.name)
            else:
                # Use XPath as fallback
                iframe = self.driver.find_element(By.XPATH, iframe_info.xpath)
            
            self.driver.switch_to.frame(iframe)
            
        except Exception as e:
            raise Exception(f"Cannot navigate to iframe: {str(e)}")
    
    def _return_to_main_context(self):
        """Return to main page context."""
        try:
            self.driver.switch_to.default_content()
        except:
            pass
    
    def _generate_report(self, search_text: str = None) -> Dict[str, Any]:
        """Generate comprehensive report of findings."""
        report = {
            'scan_summary': {
                'total_iframes_found': len(self.discovered_iframes),
                'accessible_iframes': len([f for f in self.discovered_iframes if f.is_accessible]),
                'inaccessible_iframes': len([f for f in self.discovered_iframes if not f.is_accessible]),
            },
            'iframe_details': [],
            'search_results': self.search_results if search_text else None
        }
        
        # Add iframe details
        for iframe in self.discovered_iframes:
            iframe_detail = {
                'hierarchy_path': ' → '.join(iframe.hierarchy_path),
                'id': iframe.id,
                'name': iframe.name,
                'src': iframe.src,
                'title': iframe.title,
                'class': iframe.class_name,
                'xpath': iframe.xpath,
                'is_accessible': iframe.is_accessible,
                'error_message': iframe.error_message,
                'content_preview': iframe.content_preview,
                'text_found_count': len(iframe.text_found) if iframe.text_found else 0
            }
            report['iframe_details'].append(iframe_detail)
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """Print a formatted report to console."""
        print("\n" + "="*80)
        print("🔍 COMPREHENSIVE IFRAME SCAN REPORT")
        print("="*80)
        
        # Summary
        summary = report['scan_summary']
        print(f"\n📊 SCAN SUMMARY:")
        print(f"   Total iframes found: {summary['total_iframes_found']}")
        print(f"   Accessible iframes: {summary['accessible_iframes']}")
        print(f"   Inaccessible iframes: {summary['inaccessible_iframes']}")
        
        # Search results summary
        if report['search_results']:
            search = report['search_results']
            print(f"\n🔎 SEARCH RESULTS for '{search['search_text']}':")
            print(f"   Total matches found: {search['total_locations_found']}")
        
        # Iframe details
        print(f"\n🖼️  IFRAME DETAILS:")
        print("-" * 60)
        
        if not report['iframe_details']:
            print("   No iframes found on this page.")
        else:
            for i, iframe in enumerate(report['iframe_details'], 1):
                status = "✅ Accessible" if iframe['is_accessible'] else "❌ Blocked"
                
                print(f"\n   #{i}. {iframe['hierarchy_path']}")
                print(f"       Status: {status}")
                
                if iframe['id']:
                    print(f"       ID: {iframe['id']}")
                if iframe['name']:
                    print(f"       Name: {iframe['name']}")
                if iframe['src']:
                    print(f"       Source: {iframe['src']}")
                if iframe['title']:
                    print(f"       Title: {iframe['title']}")
                
                if iframe['content_preview']:
                    print(f"       Preview: {iframe['content_preview']}")
                
                if iframe['text_found_count'] > 0:
                    print(f"       🎯 Found {iframe['text_found_count']} text match(es)!")
                
                if iframe['error_message']:
                    print(f"       Error: {iframe['error_message']}")
        
        # Detailed search results
        if report['search_results'] and report['search_results']['locations']:
            print(f"\n🎯 DETAILED SEARCH RESULTS:")
            print("-" * 60)
            
            for i, result in enumerate(report['search_results']['locations'], 1):
                print(f"\n   Match #{i}:")
                print(f"       Location: {' → '.join(result['location_path'])}")
                print(f"       Element: <{result['tag_name']}>")
                print(f"       Text: {result['element_text']}")
                print(f"       XPath: {result['element_xpath']}")
        
        print("\n" + "="*80)
    
    def close(self):
        """Clean up resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("✅ WebDriver closed successfully")
        except Exception as e:
            self.logger.error(f"❌ Error closing WebDriver: {str(e)}")

def main():
    """Example usage."""
    print("🔍 Comprehensive Iframe Scanner")
    print("="*50)
    
    url = input("Enter URL to scan: ").strip()
    if not url:
        print("❌ Please provide a URL")
        return
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    search_text = input("Enter text to search for (or press Enter to skip): ").strip()
    
    scanner = ComprehensiveIframeScanner(headless=True, timeout=20)
    
    try:
        # Perform comprehensive scan
        report = scanner.scan_page(url, search_text if search_text else None)
        
        # Print formatted report
        scanner.print_report(report)
        
    except Exception as e:
        print(f"❌ Error during scan: {e}")
    
    finally:
        scanner.close()

if __name__ == "__main__":
    main()
