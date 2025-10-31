#!/usr/bin/env python3
"""
Modern Web Frontend for Comprehensive Iframe Scanner

A Flask-based web application with real-time updates, modern UI,
and comprehensive iframe scanning capabilities.
"""

import os
import json
import threading
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
from comprehensive_iframe_scanner import ComprehensiveIframeScanner
from dom_scanner import find_iframe_xpaths_in_dom

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'iframe_scanner_frontend_2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global storage for scan sessions
scan_sessions = {}
active_scanners = {}

class WebSocketHandler(logging.Handler):
    """Custom logging handler for real-time web updates."""
    
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id
        self.setLevel(logging.INFO)
    
    def emit(self, record):
        if record.levelno >= self.level:
            log_entry = self.format(record)
            socketio.emit('log_message', {
                'message': log_entry,
                'level': record.levelname.lower(),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }, room=self.session_id)

@app.route('/')
def index():
    """Main application page."""
    return render_template('index.html')

@app.route('/api/start-scan', methods=['POST'])
def start_scan():
    """Start a new comprehensive scan."""
    try:
        data = request.get_json()
        
        # Validate input
        url = data.get('url', '').strip()
        html_source = data.get('html_source', '').strip()
        search_text = data.get('search_text', '').strip()
        
        if not url and not html_source:
            return jsonify({'error': 'Either URL or HTML source is required'}), 400
        
        if not search_text:
            return jsonify({'error': 'Search text is required'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Initialize session data
        scan_sessions[session_id] = {
            'id': session_id,
            'status': 'initializing',
            'progress': 0,
            'message': 'Preparing scan...',
            'phase': 'init',
            'start_time': datetime.now(),
            'url': url,
            'html_source': html_source[:500] + '...' if len(html_source) > 500 else html_source,
            'search_text': search_text,
            'results': None,
            'error': None
        }
        
        # Start scan in background thread
        thread = threading.Thread(
            target=run_scan_background,
            args=(session_id, url, html_source, search_text, data.get('headless', True))
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Scan started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}")
        return jsonify({'error': f'Failed to start scan: {str(e)}'}), 500

@app.route('/api/scan-status/<session_id>')
def get_scan_status(session_id):
    """Get current status of a scan session."""
    session_data = scan_sessions.get(session_id)
    
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'session_id': session_id,
        'status': session_data['status'],
        'progress': session_data['progress'],
        'message': session_data['message'],
        'phase': session_data['phase'],
        'start_time': session_data['start_time'].isoformat(),
        'error': session_data['error']
    })

@app.route('/api/scan-results/<session_id>')
def get_scan_results(session_id):
    """Get results of a completed scan."""
    session_data = scan_sessions.get(session_id)
    
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    if session_data['status'] != 'completed':
        return jsonify({'error': 'Scan not completed yet'}), 400
    
    return jsonify({
        'session_id': session_id,
        'results': session_data['results'],
        'scan_info': {
            'url': session_data['url'],
            'html_source_preview': session_data['html_source'],
            'search_text': session_data['search_text'],
            'start_time': session_data['start_time'].isoformat()
        }
    })

@app.route('/api/stop-scan/<session_id>', methods=['POST'])
def stop_scan(session_id):
    """Stop an active scan."""
    try:
        if session_id in active_scanners:
            scanner = active_scanners[session_id]
            scanner.close()
            del active_scanners[session_id]
        
        if session_id in scan_sessions:
            scan_sessions[session_id]['status'] = 'stopped'
            scan_sessions[session_id]['message'] = 'Scan stopped by user'
        
        socketio.emit('scan_stopped', {'session_id': session_id}, room=session_id)
        
        return jsonify({'success': True, 'message': 'Scan stopped'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dom-iframe-xpaths', methods=['POST'])
def dom_iframe_xpaths():
    """Return iframe XPaths from provided HTML and search text (DOM-only, no Selenium)."""
    try:
        data = request.get_json()
        html_source = (data.get('html_source') or '').strip()
        search_text = (data.get('search_text') or '').strip()
        if not html_source:
            return jsonify({'error': 'html_source is required'}), 400
        if not search_text:
            return jsonify({'error': 'search_text is required'}), 400

        xpaths = find_iframe_xpaths_in_dom(html_source, search_text)
        return jsonify({
            'success': True,
            'count': len(xpaths),
            'xpaths': xpaths
        })
    except Exception as e:
        logger.error(f"DOM-only XPath error: {e}")
        return jsonify({'error': str(e)}), 500

def run_scan_background(session_id, url, html_source, search_text, headless):
    """Run comprehensive scan in background thread."""
    scanner = None
    
    try:
        # Update status
        update_scan_status(session_id, 'initializing', 5, 'Setting up browser...')
        
        # Initialize scanner
        scanner = ComprehensiveIframeScanner(headless=headless, timeout=20)
        active_scanners[session_id] = scanner
        
        # Add WebSocket logging handler
        ws_handler = WebSocketHandler(session_id)
        ws_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        scanner.logger.addHandler(ws_handler)
        
        # Notify client that scan is starting
        socketio.emit('scan_started', {
            'session_id': session_id,
            'input_type': 'url' if url else 'html_source'
        }, room=session_id)
        
        # Phase 1: Load content
        update_scan_status(session_id, 'loading', 15, 'Loading content...')
        
        # Phase 2: Discover iframes
        update_scan_status(session_id, 'discovering', 30, 'Discovering iframes...')
        
        # Phase 3: Search for text
        update_scan_status(session_id, 'searching', 60, f'Searching for "{search_text}"...')
        
        # Run the actual scan
        if url:
            report = scanner.scan_page(url=url, search_text=search_text)
        else:
            report = scanner.scan_page(html_source=html_source, search_text=search_text)
        
        # Phase 4: Generate results
        update_scan_status(session_id, 'finalizing', 90, 'Generating results...')
        
        # Process and store results
        processed_results = process_scan_results(report)
        scan_sessions[session_id]['results'] = processed_results
        
        # Complete
        update_scan_status(session_id, 'completed', 100, 'Scan completed successfully!')
        
        # Send completion notification
        socketio.emit('scan_completed', {
            'session_id': session_id,
            'summary': {
                'total_iframes': processed_results['summary']['total_iframes'],
                'accessible_iframes': processed_results['summary']['accessible_iframes'],
                'total_matches': processed_results['summary']['total_matches']
            }
        }, room=session_id)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Scan error for session {session_id}: {error_msg}")
        
        scan_sessions[session_id]['status'] = 'error'
        scan_sessions[session_id]['error'] = error_msg
        scan_sessions[session_id]['message'] = f'Error: {error_msg}'
        
        socketio.emit('scan_error', {
            'session_id': session_id,
            'error': error_msg
        }, room=session_id)
        
    finally:
        # Clean up
        if scanner:
            scanner.close()
        
        if session_id in active_scanners:
            del active_scanners[session_id]

def update_scan_status(session_id, status, progress, message):
    """Update scan status and notify clients."""
    if session_id in scan_sessions:
        scan_sessions[session_id]['status'] = status
        scan_sessions[session_id]['progress'] = progress
        scan_sessions[session_id]['message'] = message
        
        socketio.emit('status_update', {
            'session_id': session_id,
            'status': status,
            'progress': progress,
            'message': message
        }, room=session_id)

def process_scan_results(report):
    """Process raw scan results for frontend consumption."""
    try:
        # Extract summary information
        summary = report.get('scan_summary', {})
        search_results = report.get('search_results', {})
        iframe_details = report.get('iframe_details', [])
        
        # Process iframe information
        processed_iframes = []
        for iframe in iframe_details:
            processed_iframes.append({
                'path': iframe['hierarchy_path'],
                'id': iframe.get('id', ''),
                'name': iframe.get('name', ''),
                'src': iframe.get('src', ''),
                'title': iframe.get('title', ''),
                'class': iframe.get('class', ''),
                'accessible': iframe['is_accessible'],
                'error': iframe.get('error_message', ''),
                'preview': iframe.get('content_preview', ''),
                'matches_found': iframe.get('text_found_count', 0)
            })
        
        # Process search results
        processed_matches = []
        if search_results and search_results.get('locations'):
            for match in search_results['locations']:
                processed_matches.append({
                    'location_path': ' → '.join(match['location_path']),
                    'element_tag': match.get('tag_name', ''),
                    'element_text': match.get('element_text', ''),
                    'element_xpath': match.get('element_xpath', ''),
                    'strategy_used': match.get('strategy_used', ''),
                    'found_text': match.get('found_text', '')
                })
        
        return {
            'summary': {
                'total_iframes': summary.get('total_iframes_found', 0),
                'accessible_iframes': summary.get('accessible_iframes', 0),
                'inaccessible_iframes': summary.get('inaccessible_iframes', 0),
                'total_matches': search_results.get('total_locations_found', 0) if search_results else 0,
                'search_text': search_results.get('search_text', '') if search_results else ''
            },
            'iframes': processed_iframes,
            'matches': processed_matches
        }
        
    except Exception as e:
        logger.error(f"Error processing results: {str(e)}")
        return {
            'summary': {'total_iframes': 0, 'accessible_iframes': 0, 'total_matches': 0},
            'iframes': [],
            'matches': [],
            'error': str(e)
        }

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Iframe Scanner'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_scan')
def handle_join_scan(data):
    """Join a scan session room for real-time updates."""
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined_scan', {'session_id': session_id})
        logger.info(f"Client {request.sid} joined scan session {session_id}")

@socketio.on('leave_scan')
def handle_leave_scan(data):
    """Leave a scan session room."""
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        emit('left_scan', {'session_id': session_id})

if __name__ == '__main__':
    # Create templates and static directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🚀 Comprehensive Iframe Scanner - Web Frontend")
    print("=" * 60)
    print("📱 Access the application at: http://localhost:5000")
    print("🔧 Features:")
    print("   • Modern responsive UI")
    print("   • Real-time progress updates")
    print("   • Support for URL and HTML/DOM input")
    print("   • Comprehensive iframe discovery")
    print("   • Advanced text search capabilities")
    print("   • Live logging and results")
    print("=" * 60)
    
    # Run the application
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
