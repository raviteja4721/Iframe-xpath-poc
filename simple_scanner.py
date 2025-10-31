#!/usr/bin/env python3
"""
Simple Comprehensive Scanner - No locator strategies needed!

Just provide URL and text to search - it does everything automatically:
1. Shows all iframes first
2. Searches everywhere automatically
"""

from comprehensive_iframe_scanner import ComprehensiveIframeScanner

def simple_scan():
    """Simple interface for comprehensive scanning."""
    print("🔍 COMPREHENSIVE IFRAME & TEXT SCANNER")
    print("="*50)
    print("✨ No locator strategies needed!")
    print("✨ Automatically finds all iframes!")
    print("✨ Searches everywhere automatically!")
    print("✨ Supports both URL and DOM/HTML input!")
    print("="*50)
    
    # Choose input method
    print("\n📝 Choose input method:")
    print("1. Enter URL to scan")
    print("2. Provide HTML/DOM source")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    url = None
    html_source = None
    
    if choice == "1":
        # URL input
        url = input("\n📄 Enter URL to scan: ").strip()
        if not url:
            print("❌ URL is required!")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            print(f"🔗 Using: {url}")
    
    elif choice == "2":
        # HTML/DOM input
        print("\n📄 Enter HTML/DOM source:")
        print("   (Paste your HTML content, then press Enter twice to finish)")
        
        lines = []
        empty_lines = 0
        
        while True:
            try:
                line = input()
                if not line.strip():
                    empty_lines += 1
                    if empty_lines >= 2:  # Two empty lines to finish
                        break
                else:
                    empty_lines = 0
                lines.append(line)
            except EOFError:
                break
        
        html_source = '\n'.join(lines).strip()
        
        if not html_source:
            print("❌ HTML source is required!")
            return
        
        print(f"✅ HTML source received ({len(html_source)} characters)")
    
    else:
        print("❌ Invalid choice!")
        return
    
    # Get search text
    search_text = input("\n🔎 Enter text to search for: ").strip()
    if not search_text:
        print("❌ Search text is required!")
        return
    
    print(f"\n🚀 Starting comprehensive scan...")
    if url:
        print(f"   URL: {url}")
    else:
        print(f"   HTML Source: {len(html_source)} characters")
    print(f"   Searching for: '{search_text}'")
    print("-"*50)
    
    # Create scanner
    scanner = ComprehensiveIframeScanner(headless=False, timeout=20)  # Visible browser
    
    try:
        # Run comprehensive scan
        if url:
            report = scanner.scan_page(url=url, search_text=search_text)
        else:
            report = scanner.scan_page(html_source=html_source, search_text=search_text)
        
        # Print results
        scanner.print_report(report)
        
        # Summary
        total_iframes = report['scan_summary']['total_iframes_found']
        total_matches = report['search_results']['total_locations_found'] if report['search_results'] else 0
        
        print(f"\n🎉 SCAN COMPLETE!")
        print(f"   Found {total_iframes} iframe(s)")
        print(f"   Found '{search_text}' in {total_matches} location(s)")
        
        if total_matches > 0:
            print(f"✅ SUCCESS: Text found!")
        else:
            print(f"❌ Text not found anywhere")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        scanner.close()

if __name__ == "__main__":
    simple_scan()
