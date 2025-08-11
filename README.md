# Media Info Web Browser

A clean and minimal web UI for browsing video files and displaying their metadata using ffprobe.

## Features

- 🎬 Browse video files and folders with a clean, modern interface
- 📊 Display detailed video metadata (codec, resolution, duration, bitrate, etc.)
- � Multiple audio track support with channel information
- 📝 Subtitle track detection (embedded and external files)
- �📱 Responsive design that works on desktop and mobile
- 🗂️ Folder navigation with breadcrumb support
- 🎯 Support for common video formats (MP4, MKV, AVI, MOV, etc.)
- 🐳 Docker support for easy deployment

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Your media files accessible on the host system

### 1. Clone or Download
```bash
git clone <repository> # or download the files
cd mediainfo
```

### 2. Build the Image (Optional - for local development)
```bash
docker build -t mediainfo-browser:latest .
```

Or use the pre-built image from Docker Hub:
```bash
docker pull fuguone/mediainfo-browser:latest
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

### Folder View
- Shows folders with recursive video file counts
- Clean card-based layout
- Breadcrumb navigation

### Video File Information
Click on any video file to see:
- **General**: Duration, file size, bitrate, container format
- **Video Stream**: Codec, resolution, frame rate, profile
- **Audio Tracks**: Multiple tracks with codec, channels, sample rate
- **Subtitles**: Embedded and external subtitle files

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

## Troubleshooting

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
