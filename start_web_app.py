#!/usr/bin/env python3
"""
Startup script for the Comprehensive Iframe Scanner Web Application
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import flask
        import flask_socketio
        import selenium
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def main():
    """Main startup function."""
    print("🚀 Comprehensive Iframe Scanner - Web Application")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("comprehensive_iframe_scanner.py"):
        print("❌ Error: comprehensive_iframe_scanner.py not found")
        print("   Please run this script from the iframe scanner directory")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\n📦 Installing missing dependencies...")
        if not install_dependencies():
            return
    
    print("\n🌐 Starting web application...")
    print("📱 The application will be available at: http://localhost:5000")
    print("🔧 Features:")
    print("   • Modern responsive web interface")
    print("   • Real-time progress updates")
    print("   • Support for URL and HTML/DOM input")
    print("   • Comprehensive iframe discovery")
    print("   • Advanced text search with multiple strategies")
    print("   • Live logging and detailed results")
    print("   • Export functionality")
    print("=" * 60)
    print("\n⏳ Starting server... (Press Ctrl+C to stop)")
    
    try:
        # Import and run the web application
        from web_app import app, socketio
        socketio.run(app, debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Web application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting web application: {e}")

if __name__ == "__main__":
    main()
