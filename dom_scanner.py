#!/usr/bin/env python3
"""
DOM-focused scanner - Paste your HTML/DOM and search for text.
"""

from comprehensive_iframe_scanner import ComprehensiveIframeScanner
from bs4 import BeautifulSoup

def _compute_xpath(el):
    parts = []
    while el is not None and getattr(el, 'name', None) is not None:
        tag = el.name
        parent = el.parent
        if parent is None or getattr(parent, 'find_all', None) is None:
            parts.append(f"/{tag}")
            break
        same_tag_siblings = [sib for sib in parent.find_all(tag, recursive=False)]
        if len(same_tag_siblings) == 1:
            parts.append(f"/{tag}")
        else:
            index = 1
            for sib in same_tag_siblings:
                if sib is el:
                    break
                index += 1
            parts.append(f"/{tag}[{index}]")
        el = parent
    return ''.join(reversed(parts)) or '/'

def find_iframe_xpaths_in_dom(html_source: str, search_text: str):
    matches = []
    soup = BeautifulSoup(html_source, 'html.parser')
    iframes = soup.find_all(['iframe', 'frame'])
    search_lower = search_text.lower()
    for iframe in iframes:
        attrs_text = ' '.join([str(v) for v in iframe.attrs.values()])
        hit = False
        if search_lower in attrs_text.lower():
            hit = True
        srcdoc = iframe.get('srcdoc')
        if not hit and srcdoc:
            try:
                inner = BeautifulSoup(srcdoc, 'html.parser')
                if search_lower in inner.get_text(separator=' ').lower():
                    hit = True
            except Exception:
                pass
        if hit:
            matches.append(_compute_xpath(iframe))
    return matches

def scan_dom():
    """Simple DOM scanning interface."""
    print("🔍 DOM/HTML IFRAME SCANNER")
    print("="*40)
    print("✨ Paste your HTML/DOM source")
    print("✨ Automatically finds all iframes")
    print("✨ Searches everywhere for your text")
    print("="*40)
    
    # Get HTML source
    print("\n📄 Paste your HTML/DOM source below:")
    print("   (Press Ctrl+Z and Enter on Windows, or Ctrl+D on Mac/Linux when done)")
    print("-"*40)
    
    try:
        # Read multiple lines until EOF
        lines = []
        while True:
            try:
                line = input()
                lines.append(line)
            except EOFError:
                break
        
        html_source = '\n'.join(lines).strip()
        
        if not html_source:
            print("❌ No HTML source provided!")
            return
        
        print(f"\n✅ HTML source received ({len(html_source)} characters)")
        
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return
    
    # Get search text
    search_text = input("\n🔎 Enter text to search for: ").strip()
    if not search_text:
        print("❌ Search text is required!")
        return
    
    print(f"\n🚀 Starting DOM scan...")
    print(f"   HTML Size: {len(html_source)} characters")
    print(f"   Searching for: '{search_text}'")
    print("-"*40)
    
    # Create scanner
    scanner = ComprehensiveIframeScanner(headless=False, timeout=15)
    
    try:
        # Run scan on DOM
        report = scanner.scan_page(html_source=html_source, search_text=search_text)
        
        # Print results
        scanner.print_report(report)
        
        # DOM-only fallback to extract iframe XPaths from provided HTML (no browser access)
        print("\n🧭 DOM-only iframe XPath matches (from provided HTML, attributes/srcdoc only):")
        iframe_xpaths = find_iframe_xpaths_in_dom(html_source, search_text)
        if iframe_xpaths:
            for i, xp in enumerate(iframe_xpaths, 1):
                print(f"   {i}. {xp}")
        else:
            print("   None found in iframe attributes/srcdoc.")
        
        # Summary
        total_iframes = report['scan_summary']['total_iframes_found']
        total_matches = report['search_results']['total_locations_found'] if report['search_results'] else 0
        
        print(f"\n🎉 DOM SCAN COMPLETE!")
        print(f"   Found {total_iframes} iframe(s)")
        print(f"   Found '{search_text}' in {total_matches} location(s)")
        
        if total_matches > 0:
            print(f"✅ SUCCESS: Text found in DOM!")
            
            # Show quick summary of where found
            if report['search_results']['locations']:
                print(f"\n📍 Found in these locations:")
                for i, location in enumerate(report['search_results']['locations'][:5], 1):  # Show first 5
                    path = ' → '.join(location['location_path'])
                    print(f"   {i}. {path}")
                
                if len(report['search_results']['locations']) > 5:
                    print(f"   ... and {len(report['search_results']['locations']) - 5} more")
        else:
            print(f"❌ Text '{search_text}' not found in the provided DOM")
            print(f"💡 Try:")
            print(f"   • Check spelling")
            print(f"   • Try partial text (e.g., just 'WMS' or 'NWFR')")
            print(f"   • Check if text might be in attributes")
        
    except Exception as e:
        print(f"❌ Error during DOM scan: {e}")
    
    finally:
        scanner.close()

if __name__ == "__main__":
    scan_dom()
