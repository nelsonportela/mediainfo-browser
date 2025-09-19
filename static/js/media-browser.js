class MediaBrowser {
    constructor() {
        this.currentPath = '';
        this.loadContent();
    }

    async loadContent(path = '') {
        this.showLoading();
        
        try {
            const response = await fetch(`/api/browse?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to load content');
            }
            
            this.currentPath = path;
            this.renderContent(data);
            this.renderBreadcrumb(data.breadcrumb);
            this.hideLoading();
            
        } catch (error) {
            this.showError(error.message);
        }
    }

    renderContent(data) {
        const content = document.getElementById('content');
        content.innerHTML = '';

        // Separate folders and videos
        const folders = data.items.filter(item => item.type === 'folder');
        const videos = data.items.filter(item => item.type === 'file');

        // Create folders section if there are folders
        if (folders.length > 0) {
            const foldersGrid = document.createElement('div');
            foldersGrid.className = 'folders-grid';
            
            if (videos.length > 0) {
                const foldersTitle = document.createElement('h2');
                foldersTitle.className = 'section-title';
                foldersTitle.textContent = 'Folders';
                content.appendChild(foldersTitle);
            }
            
            folders.forEach(item => {
                const card = this.createCard(item);
                foldersGrid.appendChild(card);
            });
            
            content.appendChild(foldersGrid);
        }

        // Create videos section if there are videos
        if (videos.length > 0) {
            if (folders.length > 0) {
                const videosTitle = document.createElement('h2');
                videosTitle.className = 'section-title';
                videosTitle.textContent = 'Videos';
                content.appendChild(videosTitle);
            }
            
            const videosSection = document.createElement('div');
            videosSection.className = 'videos-section';
            
            videos.forEach(item => {
                const card = this.createCard(item);
                videosSection.appendChild(card);
            });
            
            content.appendChild(videosSection);
        }
    }

    createCard(item) {
        const card = document.createElement('div');
        card.className = item.type === 'folder' ? 'card folder-card' : 'card video-card';

        if (item.type === 'folder') {
            card.innerHTML = `
                <div class="card-header">
                    <div class="card-title">
                        <svg class="icon folder-icon" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
                        </svg>
                        ${item.name}
                    </div>
                    <div class="card-subtitle">
                        ${item.video_count} video file${item.video_count !== 1 ? 's' : ''}
                    </div>
                </div>
            `;

            card.addEventListener('click', () => {
                const newPath = this.currentPath ? `${this.currentPath}/${item.name}` : item.name;
                this.loadContent(newPath);
            });

        } else if (item.type === 'file') {
            const cardId = Math.random().toString(36).substr(2, 9);
            card.innerHTML = `
                <div class="card-header">
                    <div class="card-title">
                        <div class="card-title-wrapper">
                            <svg class="icon video-icon" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm3 2h6v4H7V5zm8 8v2h1v-2h-1zM6 15H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 8H8v-2h2v2zm0-4H8V9h2v2zm4 4h-2v-2h2v2zm0-4h-2V9h2v2z" clip-rule="evenodd" />
                            </svg>
                            <span class="card-title-text">${item.name}</span>
                            <span id="badge-${cardId}" class="compatibility-badge badge-unknown" style="display: none;">
                                Checking...
                            </span>
                        </div>
                    </div>
                    <div class="card-subtitle">
                        ${item.size}
                    </div>
                </div>
                <div class="video-info" id="info-${cardId}">
                    <div class="loading">Loading video information...</div>
                </div>
            `;

            const infoDiv = card.querySelector('.video-info');
            const badgeDiv = card.querySelector(`#badge-${cardId}`);

            // Load compatibility info in background
            this.loadCompatibilityInfo(item.path, badgeDiv);

            card.addEventListener('click', async () => {
                if (infoDiv.style.display === 'block') {
                    infoDiv.style.display = 'none';
                    return;
                }

                infoDiv.style.display = 'block';
                
                try {
                    const response = await fetch(`/api/video-info?path=${encodeURIComponent(item.path)}`);
                    const videoInfo = await response.json();
                    
                    if (!response.ok) {
                        throw new Error(videoInfo.error || 'Failed to load video info');
                    }
                    
                    this.renderVideoInfo(infoDiv, videoInfo);
                    
                } catch (error) {
                    infoDiv.innerHTML = `<div class="error">Error loading video info: ${error.message}</div>`;
                }
            });
        }

        return card;
    }

    async loadCompatibilityInfo(filePath, badgeElement) {
        try {
            const response = await fetch(`/api/video-info?path=${encodeURIComponent(filePath)}`);
            const videoInfo = await response.json();
            
            if (response.ok && videoInfo.compatibility) {
                const compatibility = videoInfo.compatibility;
                
                if (compatibility.needs_remux) {
                    const issues = [];
                    if (compatibility.primary_audio_problematic) {
                        issues.push(compatibility.primary_audio_codec);
                    }
                    if (compatibility.video_problematic) {
                        issues.push(compatibility.video_codec);
                    }
                    
                    badgeElement.textContent = `⚠️ ${issues.join(' + ')}`;
                    badgeElement.className = 'compatibility-badge badge-problematic';
                } else {
                    badgeElement.textContent = '✓ Compatible';
                    badgeElement.className = 'compatibility-badge badge-compatible';
                }
                
                badgeElement.style.display = 'inline-flex';
            } else {
                // Hide badge if we can't determine compatibility
                badgeElement.style.display = 'none';
            }
        } catch (error) {
            // Hide badge on error
            badgeElement.style.display = 'none';
        }
    }

    renderVideoInfo(container, info) {
        const content = document.createElement('div');
        content.className = 'video-info-content';
        
        // General Information Section
        const generalSection = document.createElement('div');
        generalSection.className = 'info-section';
        generalSection.innerHTML = `
            <div class="info-section-title">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm3 2h6v4H7V5zm8 8v2h1v-2h-1zM6 15H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 8H8v-2h2v2zm0-4H8V9h2v2zm4 4h-2v-2h2v2zm0-4h-2V9h2v2z" clip-rule="evenodd" />
                </svg>
                General Information
            </div>
            <div class="info-grid">
                ${this.createInfoItem('Duration', info.duration)}
                ${this.createInfoItem('File Size', info.size)}
                ${this.createInfoItem('Bitrate', info.bitrate)}
                ${this.createInfoItem('Container', info.container)}
            </div>
        `;
        content.appendChild(generalSection);
        
        // Video Information Section
        if (info.video && info.video.codec) {
            const videoSection = document.createElement('div');
            videoSection.className = 'info-section';
            videoSection.innerHTML = `
                <div class="info-section-title">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v2h2a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM4 6v10h10V8h-2V6H4z"/>
                    </svg>
                    Video Stream
                </div>
                <div class="info-grid">
                    ${this.createInfoItem('Codec', info.video.codec)}
                    ${this.createInfoItem('Resolution', info.video.resolution)}
                    ${this.createInfoItem('Frame Rate', info.video.framerate)}
                    ${this.createInfoItem('Bitrate', info.video.bitrate)}
                    ${info.video.profile ? this.createInfoItem('Profile', info.video.profile) : ''}
                    ${info.video.pixel_format ? this.createInfoItem('Pixel Format', info.video.pixel_format) : ''}
                    ${info.video.aspect_ratio ? this.createInfoItem('Aspect Ratio', info.video.aspect_ratio) : ''}
                </div>
            `;
            content.appendChild(videoSection);
        }
        
        // Audio Tracks Section
        const audioSection = document.createElement('div');
        audioSection.className = 'info-section';
        audioSection.innerHTML = `
            <div class="info-section-title">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM12 5a1 1 0 011.414 0L15 6.586l1.586-1.586a1 1 0 011.414 1.414L16.414 8 18 9.586a1 1 0 01-1.414 1.414L15 9.414 13.414 11a1 1 0 01-1.414-1.414L13.586 8 12 6.414A1 1 0 0112 5z" clip-rule="evenodd" />
                </svg>
                Audio Tracks (${info.audio_tracks ? info.audio_tracks.length : 0})
            </div>
            <div class="track-list">
                ${this.renderAudioTracks(info.audio_tracks)}
            </div>
        `;
        content.appendChild(audioSection);
        
        // Subtitle Tracks Section  
        const subtitleSection = document.createElement('div');
        subtitleSection.className = 'info-section';
        subtitleSection.innerHTML = `
            <div class="info-section-title">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V8zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2z" clip-rule="evenodd" />
                </svg>
                Subtitle Tracks (${info.subtitle_tracks ? info.subtitle_tracks.length : 0})
            </div>
            <div class="track-list">
                ${this.renderSubtitleTracks(info.subtitle_tracks)}
            </div>
        `;
        content.appendChild(subtitleSection);
        
        container.innerHTML = '';
        container.appendChild(content);
    }

    createInfoItem(label, value) {
        if (!value || value === 'Unknown' || value === 'None') {
            return '';
        }
        return `
            <div class="info-item">
                <div class="info-label">${label}</div>
                <div class="info-value">${value}</div>
            </div>
        `;
    }

    renderAudioTracks(tracks) {
        if (!tracks || tracks.length === 0) {
            return '<div class="no-tracks">No audio tracks found</div>';
        }
        
        return tracks.map((track, index) => `
            <div class="track-item">
                <div class="track-header">
                    <div class="track-title">Audio Track ${index + 1}</div>
                    <div class="track-badge audio">${track.codec}</div>
                </div>
                <div class="track-details">
                    ${track.channel_layout ? `
                        <div class="track-detail">
                            <div class="track-detail-label">Channels</div>
                            <div class="track-detail-value">${track.channel_layout}</div>
                        </div>
                    ` : ''}
                    ${track.sample_rate ? `
                        <div class="track-detail">
                            <div class="track-detail-label">Sample Rate</div>
                            <div class="track-detail-value">${track.sample_rate}</div>
                        </div>
                    ` : ''}
                    ${track.bitrate ? `
                        <div class="track-detail">
                            <div class="track-detail-label">Bitrate</div>
                            <div class="track-detail-value">${track.bitrate}</div>
                        </div>
                    ` : ''}
                    ${track.language && track.language !== 'Unknown' ? `
                        <div class="track-detail">
                            <div class="track-detail-label">Language</div>
                            <div class="track-detail-value">${track.language.toUpperCase()}</div>
                        </div>
                    ` : ''}
                    ${track.title ? `
                        <div class="track-detail">
                            <div class="track-detail-label">Title</div>
                            <div class="track-detail-value">${track.title}</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    renderSubtitleTracks(tracks) {
        if (!tracks || tracks.length === 0) {
            return '<div class="no-tracks">No subtitle tracks found</div>';
        }
        
        return tracks.map((track, index) => `
            <div class="track-item">
                <div class="track-header">
                    <div class="track-title">
                        ${track.external ? 'External Subtitle' : `Subtitle Track ${index + 1}`}
                        ${track.forced ? ' (Forced)' : ''}
                        ${track.default ? ' (Default)' : ''}
                    </div>
                    <div class="track-badge ${track.external ? 'external' : 'subtitle'}">${track.codec}</div>
                </div>
                <div class="track-details">
                    ${track.language && track.language !== 'Unknown' ? `
                        <div class="track-detail">
                            <div class="track-detail-label">Language</div>
                            <div class="track-detail-value">${track.language.toUpperCase()}</div>
                        </div>
                    ` : ''}
                    ${track.title ? `
                        <div class="track-detail">
                            <div class="track-detail-label">${track.external ? 'Filename' : 'Title'}</div>
                            <div class="track-detail-value">${track.title}</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    renderBreadcrumb(breadcrumb) {
        const breadcrumbEl = document.getElementById('breadcrumb');
        const backButtonContainer = document.getElementById('back-button-container');
        
        if (breadcrumb.length === 0) {
            breadcrumbEl.style.display = 'none';
            backButtonContainer.innerHTML = '';
            return;
        }

        breadcrumbEl.style.display = 'flex';
        breadcrumbEl.innerHTML = '';

        // Add home link
        const homeLink = document.createElement('a');
        homeLink.href = '#';
        homeLink.className = 'breadcrumb-item';
        homeLink.textContent = 'Home';
        homeLink.addEventListener('click', (e) => {
            e.preventDefault();
            this.loadContent('');
        });
        breadcrumbEl.appendChild(homeLink);

        // Add breadcrumb items
        breadcrumb.forEach((item, index) => {
            const separator = document.createElement('span');
            separator.className = 'breadcrumb-separator';
            separator.textContent = '/';
            breadcrumbEl.appendChild(separator);

            const link = document.createElement('a');
            link.href = '#';
            link.className = 'breadcrumb-item';
            link.textContent = item.name;
            
            if (index < breadcrumb.length - 1) {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.loadContent(item.path);
                });
            } else {
                link.style.color = 'var(--text-primary)';
                link.style.fontWeight = '600';
            }
            
            breadcrumbEl.appendChild(link);
        });

        // Add back button
        backButtonContainer.innerHTML = `
            <a href="#" class="back-button">
                <svg class="icon" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
                </svg>
                Back
            </a>
        `;

        backButtonContainer.querySelector('.back-button').addEventListener('click', (e) => {
            e.preventDefault();
            const parentPath = breadcrumb.length > 1 ? 
                breadcrumb[breadcrumb.length - 2].path : '';
            this.loadContent(parentPath);
        });
    }

    showLoading() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('error').style.display = 'none';
        document.getElementById('content').innerHTML = '';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showError(message) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = `Error: ${message}`;
    }
}