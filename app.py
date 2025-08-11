#!/usr/bin/env python3
"""
Media Info Web Browser
A clean and minimal web UI for browsing video files and displaying their metadata.
"""

import os
import json
import subprocess
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from urllib.parse import unquote

app = Flask(__name__)

# Configuration - can be overridden by environment variables
MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/mnt/wd_2tb/media')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5001))
DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'

SUPPORTED_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp'}

def get_video_info(file_path):
    """Extract comprehensive video metadata using ffprobe."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return None
            
        data = json.loads(result.stdout)
        
        # Initialize comprehensive video info structure
        video_info = {
            'duration': None,
            'size': None,
            'bitrate': None,
            'container': None,
            'video': {
                'codec': None,
                'resolution': None,
                'framerate': None,
                'bitrate': None,
                'profile': None,
                'pixel_format': None,
                'aspect_ratio': None
            },
            'audio_tracks': [],
            'subtitle_tracks': [],
            'chapters': 0
        }
        
        # Format information
        if 'format' in data:
            format_info = data['format']
            
            # Duration
            if 'duration' in format_info:
                duration_seconds = float(format_info['duration'])
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                seconds = int(duration_seconds % 60)
                video_info['duration'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # File size
            if 'size' in format_info:
                size_bytes = int(format_info['size'])
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size_bytes < 1024.0:
                        video_info['size'] = f"{size_bytes:.1f} {unit}"
                        break
                    size_bytes /= 1024.0
            
            # Overall bitrate
            if 'bit_rate' in format_info:
                bitrate_bps = int(format_info['bit_rate'])
                video_info['bitrate'] = f"{bitrate_bps / 1000:.0f} kbps"
            
            # Container format
            if 'format_name' in format_info:
                video_info['container'] = format_info['format_name'].upper()
        
        # Stream information
        if 'streams' in data:
            for i, stream in enumerate(data['streams']):
                stream_type = stream.get('codec_type', 'unknown')
                
                if stream_type == 'video':
                    # Video stream details
                    video_info['video']['codec'] = stream.get('codec_name', 'Unknown').upper()
                    
                    if 'width' in stream and 'height' in stream:
                        width, height = stream['width'], stream['height']
                        video_info['video']['resolution'] = f"{width}×{height}"
                        
                        # Determine resolution category
                        if height >= 2160:
                            video_info['video']['resolution'] += " (4K)"
                        elif height >= 1440:
                            video_info['video']['resolution'] += " (1440p)"
                        elif height >= 1080:
                            video_info['video']['resolution'] += " (1080p)"
                        elif height >= 720:
                            video_info['video']['resolution'] += " (720p)"
                        elif height >= 480:
                            video_info['video']['resolution'] += " (480p)"
                    
                    # Frame rate
                    if 'r_frame_rate' in stream:
                        framerate = stream['r_frame_rate']
                        if '/' in framerate:
                            num, den = framerate.split('/')
                            if int(den) != 0:
                                fps = int(num) / int(den)
                                video_info['video']['framerate'] = f"{fps:.2f} fps"
                    
                    # Video bitrate
                    if 'bit_rate' in stream:
                        bitrate_bps = int(stream['bit_rate'])
                        video_info['video']['bitrate'] = f"{bitrate_bps / 1000:.0f} kbps"
                    
                    # Profile and pixel format
                    if 'profile' in stream:
                        video_info['video']['profile'] = stream['profile']
                    
                    if 'pix_fmt' in stream:
                        video_info['video']['pixel_format'] = stream['pix_fmt']
                    
                    # Aspect ratio
                    if 'display_aspect_ratio' in stream:
                        video_info['video']['aspect_ratio'] = stream['display_aspect_ratio']
                
                elif stream_type == 'audio':
                    # Audio track details
                    audio_track = {
                        'index': i,
                        'codec': stream.get('codec_name', 'Unknown').upper(),
                        'channels': stream.get('channels', 'Unknown'),
                        'sample_rate': None,
                        'bitrate': None,
                        'language': stream.get('tags', {}).get('language', 'Unknown'),
                        'title': stream.get('tags', {}).get('title', '')
                    }
                    
                    # Sample rate
                    if 'sample_rate' in stream:
                        sample_rate = int(stream['sample_rate'])
                        audio_track['sample_rate'] = f"{sample_rate / 1000:.1f} kHz"
                    
                    # Audio bitrate
                    if 'bit_rate' in stream:
                        bitrate_bps = int(stream['bit_rate'])
                        audio_track['bitrate'] = f"{bitrate_bps / 1000:.0f} kbps"
                    
                    # Channel layout description
                    if 'channel_layout' in stream:
                        layout = stream['channel_layout']
                        audio_track['channel_layout'] = layout
                    elif audio_track['channels'] != 'Unknown':
                        channels = audio_track['channels']
                        if channels == 1:
                            audio_track['channel_layout'] = 'Mono'
                        elif channels == 2:
                            audio_track['channel_layout'] = 'Stereo'
                        elif channels == 6:
                            audio_track['channel_layout'] = '5.1'
                        elif channels == 8:
                            audio_track['channel_layout'] = '7.1'
                        else:
                            audio_track['channel_layout'] = f'{channels} channels'
                    
                    video_info['audio_tracks'].append(audio_track)
                
                elif stream_type == 'subtitle':
                    # Subtitle track details
                    subtitle_track = {
                        'index': i,
                        'codec': stream.get('codec_name', 'Unknown').upper(),
                        'language': stream.get('tags', {}).get('language', 'Unknown'),
                        'title': stream.get('tags', {}).get('title', ''),
                        'forced': stream.get('disposition', {}).get('forced', 0) == 1,
                        'default': stream.get('disposition', {}).get('default', 0) == 1
                    }
                    
                    video_info['subtitle_tracks'].append(subtitle_track)
        
        # Check for external subtitle files
        external_subs = []
        base_path = os.path.splitext(file_path)[0]
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.sub', '.idx', '.vtt']
        
        try:
            directory = os.path.dirname(file_path)
            filename_base = os.path.splitext(os.path.basename(file_path))[0]
            
            for file in os.listdir(directory):
                if any(file.lower().endswith(ext) for ext in subtitle_extensions):
                    if file.lower().startswith(filename_base.lower()):
                        # Extract language from filename if possible
                        lang_match = None
                        for lang_code in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh']:
                            if lang_code in file.lower():
                                lang_match = lang_code
                                break
                        
                        external_subs.append({
                            'filename': file,
                            'language': lang_match or 'Unknown',
                            'format': os.path.splitext(file)[1][1:].upper()
                        })
        except:
            pass
        
        # Add external subtitles to the list
        for ext_sub in external_subs:
            video_info['subtitle_tracks'].append({
                'index': 'ext',
                'codec': ext_sub['format'],
                'language': ext_sub['language'],
                'title': ext_sub['filename'],
                'forced': False,
                'default': False,
                'external': True
            })
        
        return video_info
        
    except Exception as e:
        print(f"Error getting video info for {file_path}: {e}")
        return None

def is_video_file(filename):
    """Check if file is a supported video format."""
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS

def count_videos_recursive(directory_path, max_depth=10):
    """Recursively count video files in a directory and its subdirectories."""
    if max_depth <= 0:
        return 0
    
    video_count = 0
    try:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            
            try:
                if os.path.isfile(item_path) and is_video_file(item):
                    video_count += 1
                elif os.path.isdir(item_path):
                    # Skip system directories and hidden directories
                    if not item.startswith('.') and item != 'System Volume Information':
                        video_count += count_videos_recursive(item_path, max_depth - 1)
            except (PermissionError, OSError):
                # Skip directories/files we can't access
                continue
                
    except (PermissionError, OSError):
        # Can't read the directory
        pass
    
    return video_count

def scan_directory(path):
    """Scan directory for folders and video files."""
    try:
        items = []
        
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            
            if os.path.isdir(item_path):
                # Skip system directories
                if item.startswith('.') or item == 'System Volume Information':
                    continue
                
                # Count video files recursively in subdirectory
                video_count = count_videos_recursive(item_path)
                
                items.append({
                    'type': 'folder',
                    'name': item,
                    'video_count': video_count
                })
            
            elif is_video_file(item):
                # Get file size
                try:
                    size_bytes = os.path.getsize(item_path)
                    # Convert to human readable format
                    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                        if size_bytes < 1024.0:
                            size_str = f"{size_bytes:.1f} {unit}"
                            break
                        size_bytes /= 1024.0
                except:
                    size_str = "Unknown"
                
                items.append({
                    'type': 'file',
                    'name': item,
                    'size': size_str,
                    'path': item_path
                })
        
        return items
    
    except Exception as e:
        print(f"Error scanning directory {path}: {e}")
        return []

@app.route('/')
def index():
    """Main page - show media root contents."""
    return render_template('index.html')

@app.route('/api/browse')
def browse():
    """API endpoint to browse directories."""
    path = request.args.get('path', '')
    
    # Ensure path is within media root
    if path:
        full_path = os.path.join(MEDIA_ROOT, path.lstrip('/'))
    else:
        full_path = MEDIA_ROOT
    
    # Security check
    if not os.path.commonpath([MEDIA_ROOT, full_path]) == MEDIA_ROOT:
        return jsonify({'error': 'Invalid path'}), 400
    
    if not os.path.exists(full_path):
        return jsonify({'error': 'Path not found'}), 404
    
    items = scan_directory(full_path)
    
    # Build breadcrumb
    breadcrumb = []
    if path:
        parts = path.strip('/').split('/')
        current_path = ''
        for part in parts:
            current_path += '/' + part
            breadcrumb.append({
                'name': part,
                'path': current_path
            })
    
    return jsonify({
        'path': path,
        'breadcrumb': breadcrumb,
        'items': items
    })

@app.route('/api/video-info')
def video_info():
    """API endpoint to get video metadata."""
    file_path = request.args.get('path')
    
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
    
    # Security check
    if not os.path.commonpath([MEDIA_ROOT, file_path]) == MEDIA_ROOT:
        return jsonify({'error': 'Invalid path'}), 400
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    info = get_video_info(file_path)
    
    if info is None:
        return jsonify({'error': 'Could not extract video information'}), 500
    
    return jsonify(info)

if __name__ == '__main__':
    print(f"Starting Media Info Web Browser...")
    print(f"Media root: {MEDIA_ROOT}")
    print(f"Server will be available at http://{HOST}:{PORT}")
    app.run(debug=DEBUG, host=HOST, port=PORT)
