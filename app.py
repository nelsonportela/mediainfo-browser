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
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'

SUPPORTED_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp'}

# Configuration file for codec compatibility
CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.json')

def load_codec_config():
    """Load codec compatibility configuration from file."""
    default_config = {
        "problematic_codecs": {
            "audio": ["dts", "dts-hd", "truehd", "flac", "pcm_s16le", "pcm_s24le"],
            "video": []  # Prepared for future video codec configuration
        },
        "version": "1.0"
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure all required keys exist
                if "problematic_codecs" not in config:
                    config["problematic_codecs"] = default_config["problematic_codecs"]
                if "audio" not in config["problematic_codecs"]:
                    config["problematic_codecs"]["audio"] = default_config["problematic_codecs"]["audio"]
                if "video" not in config["problematic_codecs"]:
                    config["problematic_codecs"]["video"] = default_config["problematic_codecs"]["video"]
                return config
        else:
            # Create default config file
            save_codec_config(default_config)
            return default_config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config file: {e}")
        return default_config

def save_codec_config(config):
    """Save codec compatibility configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving config file: {e}")
        return False

def is_audio_problematic(audio_codec, config=None):
    """Check if an audio codec is marked as problematic."""
    if config is None:
        config = CODEC_CONFIG  # Use the global config instead of reloading
    
    problematic_audio = config.get("problematic_codecs", {}).get("audio", [])
    return audio_codec.lower() in [codec.lower() for codec in problematic_audio]

def is_video_problematic(video_codec, config=None):
    """Check if a video codec is marked as problematic."""
    if config is None:
        config = CODEC_CONFIG
    
    problematic_video = config.get("problematic_codecs", {}).get("video", [])
    return video_codec.lower() in [codec.lower() for codec in problematic_video]

def get_primary_audio_track(audio_tracks):
    """Identify the primary audio track from a list of audio tracks."""
    if not audio_tracks:
        return None
    
    # Look for default track first
    for track in audio_tracks:
        if track.get('disposition', {}).get('default', False):
            return track
    
    # If no default, return first track
    return audio_tracks[0]

# Load configuration at startup
CODEC_CONFIG = load_codec_config()

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
                    
                    # Check if video codec is problematic
                    codec_name = stream.get('codec_name', '').lower()
                    video_info['video']['is_problematic'] = is_video_problematic(codec_name, CODEC_CONFIG)
                
                elif stream_type == 'audio':
                    # Audio track details
                    audio_track = {
                        'index': i,
                        'codec': stream.get('codec_name', 'Unknown').upper(),
                        'channels': stream.get('channels', 'Unknown'),
                        'sample_rate': None,
                        'bitrate': None,
                        'language': stream.get('tags', {}).get('language', 'Unknown'),
                        'title': stream.get('tags', {}).get('title', ''),
                        'disposition': stream.get('disposition', {}),
                        'is_problematic': False  # Will be set below
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
                    
                    # Check if codec is problematic
                    codec_name = stream.get('codec_name', '').lower()
                    audio_track['is_problematic'] = is_audio_problematic(codec_name, CODEC_CONFIG)
                    
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
        
        # Analyze overall file compatibility
        primary_audio = get_primary_audio_track(video_info['audio_tracks'])
        video_problematic = video_info['video'].get('is_problematic', False)
        audio_problematic = primary_audio['is_problematic'] if primary_audio else False
        
        video_info['compatibility'] = {
            'primary_audio_problematic': audio_problematic,
            'primary_audio_codec': primary_audio['codec'] if primary_audio else None,
            'video_problematic': video_problematic,
            'video_codec': video_info['video'].get('codec', None),
            'needs_remux': audio_problematic or video_problematic,
            'problematic_track_count': sum(1 for track in video_info['audio_tracks'] if track['is_problematic']),
            'total_audio_tracks': len(video_info['audio_tracks'])
        }
        
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

@app.route('/api/config')
def get_config():
    """API endpoint to get current codec configuration."""
    return jsonify(CODEC_CONFIG)

@app.route('/api/config', methods=['POST'])
def update_config():
    """API endpoint to update codec configuration."""
    global CODEC_CONFIG
    
    try:
        new_config = request.get_json()
        
        # Validate config structure
        if not isinstance(new_config, dict):
            return jsonify({'error': 'Invalid config format'}), 400
        
        if 'problematic_codecs' not in new_config:
            return jsonify({'error': 'Missing problematic_codecs section'}), 400
        
        problematic = new_config['problematic_codecs']
        if not isinstance(problematic.get('audio', []), list):
            return jsonify({'error': 'Invalid audio codecs format'}), 400
        
        if not isinstance(problematic.get('video', []), list):
            return jsonify({'error': 'Invalid video codecs format'}), 400
        
        # Save the configuration
        if save_codec_config(new_config):
            CODEC_CONFIG = new_config
            return jsonify({'success': True, 'message': 'Configuration updated successfully'})
        else:
            return jsonify({'error': 'Failed to save configuration'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Invalid request: {str(e)}'}), 400

@app.route('/api/available-codecs')
def get_available_codecs():
    """API endpoint to get list of audio codecs found in media files."""
    # This will scan a subset of files to discover available codecs
    # For now, return a predefined list of common codecs
    common_audio_codecs = [
        'aac', 'ac3', 'eac3', 'dts', 'dts-hd', 'truehd', 
        'flac', 'mp3', 'pcm_s16le', 'pcm_s24le', 'opus', 'vorbis'
    ]
    
    common_video_codecs = [
        'h264', 'h265', 'hevc', 'av1', 'vp8', 'vp9', 'mpeg2', 'mpeg4'
    ]
    
    return jsonify({
        'audio': common_audio_codecs,
        'video': common_video_codecs
    })

def scan_media_files_recursive(directory_path, max_files=None, max_depth=10):
    """Recursively scan for video files and return their paths."""
    if max_depth <= 0:
        return []
    
    video_files = []
    try:
        for item in sorted(os.listdir(directory_path)):
            if max_files and len(video_files) >= max_files:
                break
                
            item_path = os.path.join(directory_path, item)
            
            try:
                if os.path.isfile(item_path) and is_video_file(item):
                    video_files.append(item_path)
                elif os.path.isdir(item_path):
                    # Skip system directories and hidden directories
                    if not item.startswith('.') and item != 'System Volume Information':
                        subdirectory_files = scan_media_files_recursive(item_path, max_files - len(video_files) if max_files else None, max_depth - 1)
                        video_files.extend(subdirectory_files)
            except (PermissionError, OSError):
                # Skip directories/files we can't access
                continue
                
    except (PermissionError, OSError):
        # Can't read the directory
        pass
    
    return video_files

@app.route('/api/bulk-analysis')
def bulk_analysis():
    """API endpoint for bulk media library analysis."""
    try:
        max_files = request.args.get('max_files', type=int)
        sample_only = request.args.get('sample', 'false').lower() == 'true'
        
        # If sampling, limit to first 50 files for performance
        if sample_only and not max_files:
            max_files = 50
        
        # Scan for all video files
        video_files = scan_media_files_recursive(MEDIA_ROOT, max_files)
        
        # Initialize statistics
        stats = {
            'total_files': len(video_files),
            'compatible_files': 0,
            'problematic_files': 0,
            'audio_issues': 0,
            'video_issues': 0,
            'both_issues': 0,
            'codec_breakdown': {
                'audio': {},
                'video': {}
            },
            'problematic_files_list': []
        }
        
        # Analyze each file
        for file_path in video_files:
            try:
                video_info = get_video_info(file_path)
                if not video_info or 'compatibility' not in video_info:
                    continue
                
                compatibility = video_info['compatibility']
                relative_path = os.path.relpath(file_path, MEDIA_ROOT)
                
                # Count compatibility status
                if compatibility['needs_remux']:
                    stats['problematic_files'] += 1
                    
                    # Track specific issue types
                    has_audio_issue = compatibility.get('primary_audio_problematic', False)
                    has_video_issue = compatibility.get('video_problematic', False)
                    
                    if has_audio_issue:
                        stats['audio_issues'] += 1
                    if has_video_issue:
                        stats['video_issues'] += 1
                    if has_audio_issue and has_video_issue:
                        stats['both_issues'] += 1
                    
                    # Add to problematic files list
                    issues = []
                    if has_audio_issue:
                        issues.append(compatibility.get('primary_audio_codec', 'Unknown'))
                    if has_video_issue:
                        issues.append(compatibility.get('video_codec', 'Unknown'))
                    
                    stats['problematic_files_list'].append({
                        'path': relative_path,
                        'name': os.path.basename(file_path),
                        'issues': issues,
                        'audio_codec': compatibility.get('primary_audio_codec'),
                        'video_codec': compatibility.get('video_codec'),
                        'size': video_info.get('size', 'Unknown')
                    })
                else:
                    stats['compatible_files'] += 1
                
                # Track codec usage
                if video_info.get('audio_tracks'):
                    primary_audio = get_primary_audio_track(video_info['audio_tracks'])
                    if primary_audio:
                        audio_codec = primary_audio['codec'].lower()
                        stats['codec_breakdown']['audio'][audio_codec] = stats['codec_breakdown']['audio'].get(audio_codec, 0) + 1
                
                if video_info.get('video', {}).get('codec'):
                    video_codec = video_info['video']['codec'].lower()
                    stats['codec_breakdown']['video'][video_codec] = stats['codec_breakdown']['video'].get(video_codec, 0) + 1
                    
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                continue
        
        # Calculate percentages
        if stats['total_files'] > 0:
            stats['compatibility_percentage'] = round((stats['compatible_files'] / stats['total_files']) * 100, 1)
        else:
            stats['compatibility_percentage'] = 0
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': f'Bulk analysis failed: {str(e)}'}), 500

@app.route('/api/bulk-analysis-progress')
def bulk_analysis_progress():
    """API endpoint for bulk media library analysis with progress updates via Server-Sent Events."""
    def generate_progress():
        try:
            yield "data: " + json.dumps({'status': 'starting', 'message': 'Scanning for video files...'}) + "\n\n"
            
            # Scan for all video files
            video_files = scan_media_files_recursive(MEDIA_ROOT)
            total_files = len(video_files)
            
            yield "data: " + json.dumps({
                'status': 'progress', 
                'total_files': total_files,
                'current_file': 0,
                'message': f'Found {total_files} video files. Starting analysis...'
            }) + "\n\n"
            
            # Initialize statistics
            stats = {
                'total_files': total_files,
                'compatible_files': 0,
                'problematic_files': 0,
                'audio_issues': 0,
                'video_issues': 0,
                'both_issues': 0,
                'codec_breakdown': {
                    'audio': {},
                    'video': {}
                },
                'problematic_files_list': []
            }
            
            # Analyze each file with progress updates
            for index, file_path in enumerate(video_files, 1):
                try:
                    # Send progress update
                    filename = os.path.basename(file_path)
                    yield "data: " + json.dumps({
                        'status': 'progress',
                        'total_files': total_files,
                        'current_file': index,
                        'current_filename': filename,
                        'message': f'Analyzing {index}/{total_files}: {filename}'
                    }) + "\n\n"
                    
                    video_info = get_video_info(file_path)
                    if not video_info or 'compatibility' not in video_info:
                        continue
                    
                    compatibility = video_info['compatibility']
                    relative_path = os.path.relpath(file_path, MEDIA_ROOT)
                    
                    # Count compatibility status
                    if compatibility['needs_remux']:
                        stats['problematic_files'] += 1
                        
                        # Track specific issue types
                        has_audio_issue = compatibility.get('primary_audio_problematic', False)
                        has_video_issue = compatibility.get('video_problematic', False)
                        
                        if has_audio_issue:
                            stats['audio_issues'] += 1
                        if has_video_issue:
                            stats['video_issues'] += 1
                        if has_audio_issue and has_video_issue:
                            stats['both_issues'] += 1
                        
                        # Add to problematic files list
                        issues = []
                        if has_audio_issue:
                            issues.append(compatibility.get('primary_audio_codec', 'Unknown'))
                        if has_video_issue:
                            issues.append(compatibility.get('video_codec', 'Unknown'))
                        
                        stats['problematic_files_list'].append({
                            'path': relative_path,
                            'name': os.path.basename(file_path),
                            'issues': issues,
                            'audio_codec': compatibility.get('primary_audio_codec'),
                            'video_codec': compatibility.get('video_codec'),
                            'size': video_info.get('size', 'Unknown')
                        })
                    else:
                        stats['compatible_files'] += 1
                    
                    # Track codec usage
                    if video_info.get('audio_tracks'):
                        primary_audio = get_primary_audio_track(video_info['audio_tracks'])
                        if primary_audio:
                            audio_codec = primary_audio['codec'].lower()
                            stats['codec_breakdown']['audio'][audio_codec] = stats['codec_breakdown']['audio'].get(audio_codec, 0) + 1
                    
                    if video_info.get('video', {}).get('codec'):
                        video_codec = video_info['video']['codec'].lower()
                        stats['codec_breakdown']['video'][video_codec] = stats['codec_breakdown']['video'].get(video_codec, 0) + 1
                        
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
                    continue
            
            # Calculate percentages
            if stats['total_files'] > 0:
                stats['compatibility_percentage'] = round((stats['compatible_files'] / stats['total_files']) * 100, 1)
            else:
                stats['compatibility_percentage'] = 0
            
            # Send final results
            yield "data: " + json.dumps({
                'status': 'complete',
                'message': 'Analysis complete!',
                **stats
            }) + "\n\n"
            
        except Exception as e:
            yield "data: " + json.dumps({'status': 'error', 'message': str(e)}) + "\n\n"
    
    return app.response_class(
        generate_progress(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

if __name__ == '__main__':
    print(f"Starting Media Info Web Browser...")
    print(f"Media root: {MEDIA_ROOT}")
    print(f"Server will be available at http://{HOST}:{PORT}")
    app.run(debug=DEBUG, host=HOST, port=PORT)
