# Media Info Web Browser

> **⚠️ Disclaimer**: This application is completely "vibe coded" (yes, including this disclaimer) - meaning an AI did all the heavy lifting while a human occasionally said "make it work" and "add more features." The result is a surprisingly functional codec compatibility analyzer that somehow evolved from a simple file browser. If you find any questionable design decisions, blame the robots! 🤖⚡

A clean and modern web UI for browsing video files and analyzing their codec compatibility for streaming devices like Fire TV Stick, with real-time analysis and smart caching.

## ✨ Key Features

- 🎬 **Media Browser**: Clean, responsive interface for browsing video files and folders
- 📊 **Codec Analysis**: Comprehensive compatibility checking for streaming devices
- ⚡ **Smart Caching**: Instant dashboard loading with server-side cache persistence
- � **Real-time Progress**: Live progress updates during bulk library analysis
- 🎯 **Compatibility Focus**: Specifically designed for Jellyfin → Fire Stick streaming pipelines
- 📱 **Mobile Friendly**: Responsive design that works everywhere
- 🐳 **Docker Ready**: Complete containerization with automated builds
- 📋 **Export Support**: CSV export of problematic files for further analysis

## 🚀 New in v1.1.x

### Smart Caching System
- **Instant Loading**: Dashboard shows cached results immediately (no waiting!)
- **Cross-Device**: Server-side cache works across all devices
- **Manual Refresh**: Clean refresh button when you need fresh data
- **Persistent**: Cache survives server restarts

### Modular Architecture
- **90% HTML Reduction**: Cleaned up from 1,762 to 175 lines
- **Organized Structure**: Separate CSS, JavaScript, and HTML files
- **Better Maintainability**: Clean separation of concerns
- **Enhanced Performance**: Optimized loading and real-time updates

### Enhanced Analysis
- **Two-Line Progress**: File count and current filename on separate lines
- **Detailed Statistics**: Comprehensive codec breakdown and compatibility metrics
- **Issue Categorization**: Audio, video, and combined compatibility problems
- **Size Information**: File sizes included in problematic files list

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Your media files accessible on the host system

### 1. Clone or Download
```bash
git clone https://github.com/nelsonportela/mediainfo-browser.git # or download the files
cd mediainfo-browser
```

### 2. Build the Image (Optional - for local development)
```bash
docker build -t mediainfo-browser:latest .
```

Or use the pre-built image from Docker Hub:
```bash
docker pull fuguone/mediainfo-browser:latest
# Latest stable: v1.1.1 (includes smart caching and modular architecture)
```

### 3. Configure Media Path
Edit `docker-compose.yaml` and update the media path:
```yaml
volumes:
  - /your/media/path:/media:ro  # Change this to your media directory
```

### 4. Deploy
```bash
docker-compose up -d
```

### 5. Access
- Local: http://localhost:5000
- Network: http://your-server-ip:5000

## 🎯 Codec Compatibility Analysis

This application is specifically designed to identify problematic audio/video codecs that may cause issues when streaming from Jellyfin to devices like Fire TV Stick.

### Supported Analysis
- **Audio Codec Issues**: DTS, DTS-HD, TrueHD, FLAC, PCM variants
- **Video Codec Issues**: Configurable (prepared for future expansion)
- **Bulk Library Analysis**: Scan entire media library with real-time progress
- **Statistical Overview**: Compatibility percentages and issue breakdowns
- **Export Functionality**: CSV export of problematic files

### How It Works
1. **Browse Your Library**: Navigate through your media folders
2. **Individual Analysis**: Click any video file to see detailed codec information
3. **Bulk Analysis**: Use the Dashboard for comprehensive library scanning
4. **Smart Caching**: Results are cached for instant subsequent access
5. **Export Results**: Download CSV reports of files needing attention

### Use Case: Jellyfin Streaming Pipeline
Perfect for identifying which files in your library need transcoding or remuxing for optimal streaming performance to Fire TV Stick and similar devices.

## Manual Installation

### Requirements

- Python 3.7+
- FFmpeg (for ffprobe)
- Flask

### Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure FFmpeg is installed on your system:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg

# macOS
brew install ffmpeg
```

### Configuration

By default, the application is configured to browse `/mnt/wd_2tb/media`. To change this:

**For local development**, edit the `MEDIA_ROOT` variable in `app.py`:
```python
MEDIA_ROOT = "/your/media/path/here"
```

**For Docker deployment**, set environment variables:
```bash
export MEDIA_ROOT="/your/media/path"
export HOST="0.0.0.0"
export PORT="5000"
```

### Usage

1. Start the application:
```bash
# Development
python app.py

# Or use the startup script
./start.sh
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Docker Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEDIA_ROOT` | `/mnt/wd_2tb/media` | Path to media files |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `5000` | Server port |
| `FLASK_ENV` | `development` | Flask environment |

### Docker Compose Options

The `docker-compose.yaml` includes:

- **Volume mounting**: Media directory mounted as read-only
- **Health checks**: Automatic container health monitoring
- **Resource limits**: Memory limits for stable operation
- **Logging**: Structured logging with rotation
- **Restart policy**: Automatic restart on failure

### Custom Configuration

Create a `.env` file for custom settings:
```bash
MEDIA_ROOT=/custom/media/path
PORT=8080
FLASK_ENV=production
```

## Management Commands

### Building and Deployment
```bash
# Pull latest image from Docker Hub
docker pull fuguone/mediainfo-browser:latest

# Or build locally for development
docker build -t mediainfo-browser:latest .

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop services
docker-compose down

# Update to latest version
docker pull fuguone/mediainfo-browser:latest && docker-compose up -d
```

## Features Overview

### Smart Dashboard
- **Instant Loading**: Cached analysis results load immediately
- **Real-time Progress**: Live updates during library analysis with file count and current filename
- **Cache Management**: Shows when analysis was last performed with manual refresh option
- **Export Options**: Download CSV reports of problematic files

### Codec Compatibility Analysis
- **Bulk Library Scanning**: Analyze entire media library for streaming compatibility
- **Issue Categorization**: Separate audio, video, and combined compatibility problems
- **Statistical Overview**: Compatibility percentages and detailed breakdowns
- **Problematic Files List**: Detailed list with file paths, issues, and sizes

### Individual File Analysis
Click on any video file to see:
- **General**: Duration, file size, bitrate, container format
- **Video Stream**: Codec, resolution, frame rate, profile
- **Audio Tracks**: Multiple tracks with codec, channels, sample rate
- **Compatibility**: Streaming device compatibility assessment
- **Subtitles**: Embedded and external subtitle files

### Folder View
- Shows folders with recursive video file counts
- Clean card-based layout with file statistics
- Breadcrumb navigation
- Responsive design for all screen sizes

### Navigation
- Breadcrumb navigation
- Back button
- Responsive design for mobile devices

## Security Notes

- The application includes path traversal protection
- Only files within the configured media root can be accessed
- No file modification capabilities - read-only access
- Container runs as non-root user
- Media directory mounted as read-only in Docker

## 💾 Cache System

### How Caching Works
- **Server-Side Storage**: Analysis results stored in `analysis_cache.json`
- **Instant Access**: Dashboard loads cached data immediately
- **Cross-Device**: Same cache accessible from all devices
- **Persistence**: Cache survives server restarts
- **Manual Control**: Refresh button forces new analysis when needed

### Cache Management
- **Automatic**: Results automatically cached after each analysis
- **Validation**: Cache validates against media root changes
- **Refresh**: Manual refresh bypasses cache for fresh analysis
- **Storage**: Lightweight JSON format with timestamps

## Troubleshooting

### Cache Issues
```bash
# Clear cache if corrupted
rm analysis_cache.json

# Force fresh analysis
# Use the "Refresh Analysis" button in the dashboard
```

### FFprobe not found
Make sure FFmpeg is installed and `ffprobe` is available in your system PATH.

### Permission errors
Ensure the user running the application has read access to the media directories.

### Docker volume issues
Check that the media path in `docker-compose.yaml` is correct and accessible.

### Container won't start
Check logs with: `docker-compose logs mediainfo`

### Network access issues
Ensure port 5000 is not blocked by firewall and is available.

### Dashboard loading issues
- Check browser console for JavaScript errors
- Verify all static files (CSS/JS) are properly served
- Clear browser cache and reload

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start in development mode
python app.py
```

### Building for Production
```bash
# Build Docker image
docker build -t mediainfo-browser .

# Run container
docker run -d \
  -p 5000:5000 \
  -v /path/to/media:/media:ro \
  -e MEDIA_ROOT=/media \
  -e FLASK_ENV=production \
  mediainfo-browser
```
