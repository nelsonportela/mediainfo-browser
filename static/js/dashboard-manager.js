class DashboardManager {
    constructor() {
        this.modal = document.getElementById('dashboard-modal');
        this.analysisData = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Dashboard button
        document.getElementById('dashboard-btn').addEventListener('click', () => {
            this.openModal();
        });

        // Close modal
        document.getElementById('close-dashboard').addEventListener('click', () => {
            this.closeModal();
        });

        // Close modal when clicking outside
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Export CSV
        document.getElementById('export-csv').addEventListener('click', () => {
            this.exportCSV();
        });
    }

    openModal() {
        this.modal.style.display = 'block';
        // Load cached data first, then check for updates
        this.loadCachedAnalysisFirst();
    }

    closeModal() {
        this.modal.style.display = 'none';
    }

    async loadCachedAnalysisFirst() {
        const loadingDiv = document.getElementById('dashboard-loading');
        const contentDiv = document.getElementById('dashboard-content');
        const errorDiv = document.getElementById('dashboard-error');

        // Show loading initially
        loadingDiv.style.display = 'block';
        contentDiv.style.display = 'none';
        errorDiv.style.display = 'none';

        try {
            // First, try to get cached results
            const response = await fetch('/api/cached-analysis');
            
            if (response.ok) {
                const cachedData = await response.json();
                
                if (cachedData.has_cache) {
                    // Show cached data immediately
                    this.displayAnalysis(cachedData);
                    this.showContentWithCacheInfo(cachedData.cache_timestamp);
                    return;
                }
            }
            
            // No cache available, run full analysis
            this.loadAnalysis();
            
        } catch (error) {
            console.warn('Failed to load cached analysis, running fresh analysis:', error);
            this.loadAnalysis();
        }
    }

    showContentWithCacheInfo(cacheTimestamp) {
        const loadingDiv = document.getElementById('dashboard-loading');
        const contentDiv = document.getElementById('dashboard-content');
        
        // Show content
        loadingDiv.style.display = 'none';
        contentDiv.style.display = 'block';
        
        // Add cache info banner
        this.addCacheInfoBanner(cacheTimestamp);
    }

    addCacheInfoBanner(timestamp) {
        const contentDiv = document.getElementById('dashboard-content');
        
        // Remove existing cache info if present
        const existingInfo = contentDiv.querySelector('.cache-info');
        if (existingInfo) {
            existingInfo.remove();
        }
        
        const cacheInfo = document.createElement('div');
        cacheInfo.className = 'cache-info';
        cacheInfo.style.cssText = `
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 0.75rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
            align-items: center;
        `;
        
        const lastAnalyzed = new Date(timestamp * 1000).toLocaleString();
        cacheInfo.innerHTML = `
            <span>📊 Showing cached analysis from ${lastAnalyzed}</span>
            <button id="force-refresh" style="
                background: var(--accent);
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                font-size: 0.85rem;
                cursor: pointer;
            ">Refresh Analysis</button>
        `;
        
        // Insert at the beginning of content
        contentDiv.insertBefore(cacheInfo, contentDiv.firstChild);
        
        // Add refresh functionality
        const refreshBtn = cacheInfo.querySelector('#force-refresh');
        refreshBtn.addEventListener('click', () => {
            cacheInfo.remove(); // Remove cache info
            this.loadAnalysis(true); // Force fresh analysis
        });
    }

    async loadAnalysis(forceRefresh = false) {
        const loadingDiv = document.getElementById('dashboard-loading');
        const contentDiv = document.getElementById('dashboard-content');
        const errorDiv = document.getElementById('dashboard-error');

        // Show loading
        loadingDiv.style.display = 'block';
        contentDiv.style.display = 'none';
        errorDiv.style.display = 'none';

        // Create or update progress display
        let progressText = loadingDiv.querySelector('.loading');
        let progressDetail = loadingDiv.querySelector('.progress-detail');
        
        if (!progressDetail) {
            progressDetail = document.createElement('div');
            progressDetail.className = 'progress-detail';
            progressDetail.style.cssText = 'margin-top: 0.5rem; font-size: 0.9rem; color: var(--text-secondary);';
            loadingDiv.appendChild(progressDetail);
        }

        try {
            // Use different endpoint based on whether we're forcing refresh
            const endpoint = forceRefresh ? '/api/bulk-analysis-progress?force=true' : '/api/bulk-analysis-progress';
            const eventSource = new EventSource(endpoint);
            
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                switch (data.status) {
                    case 'starting':
                        progressText.textContent = 'Starting analysis...';
                        progressDetail.textContent = data.message;
                        break;
                        
                    case 'progress':
                        const percentage = Math.round((data.current_file / data.total_files) * 100);
                        progressText.textContent = `Analyzing library... ${percentage}%`;
                        progressDetail.innerHTML = `${data.current_file}/${data.total_files}<br>${data.current_filename || 'Processing...'}`;
                        break;
                        
                    case 'complete':
                        progressText.textContent = 'Analysis complete!';
                        progressDetail.textContent = `Processed ${data.total_files} files`;
                        
                        // Display results
                        this.displayAnalysis(data);
                        
                        // Show content
                        contentDiv.style.display = 'block';
                        loadingDiv.style.display = 'none';
                        
                        eventSource.close();
                        break;
                        
                    case 'error':
                        throw new Error(data.message);
                }
            };
            
            eventSource.onerror = (error) => {
                eventSource.close();
                throw new Error('Connection to server lost');
            };
            
        } catch (error) {
            console.error('Analysis error:', error);
            errorDiv.style.display = 'block';
            loadingDiv.style.display = 'none';
            
            // Find or create error message element
            let errorMessage = errorDiv.querySelector('.error-message');
            if (!errorMessage) {
                errorMessage = errorDiv;
            }
            errorMessage.textContent = `Error: ${error.message}`;
        }
    }

    displayAnalysis(data) {
        // Update summary cards
        document.getElementById('total-files').textContent = data.total_files;
        document.getElementById('compatible-files').textContent = data.compatible_files;
        document.getElementById('problematic-files').textContent = data.problematic_files;
        document.getElementById('compatibility-percentage').textContent = `${data.compatibility_percentage}%`;

        // Update issue breakdown
        document.getElementById('audio-issues').textContent = data.audio_issues;
        document.getElementById('video-issues').textContent = data.video_issues;
        document.getElementById('both-issues').textContent = data.both_issues;

        // Update problematic files table
        this.updateProblematicFilesTable(data.problematic_files_list);

        // Store data for export
        this.analysisData = data;
    }

    updateProblematicFilesTable(files) {
        const tbody = document.getElementById('problematic-files-body');
        tbody.innerHTML = '';

        if (files.length === 0) {
            const row = tbody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 3;
            cell.style.textAlign = 'center';
            cell.style.padding = '2rem';
            cell.style.color = 'var(--text-secondary)';
            cell.textContent = '🎉 No problematic files found!';
            return;
        }

        files.forEach(file => {
            const row = tbody.insertRow();
            
            // File name
            const nameCell = row.insertCell();
            nameCell.style.padding = '0.75rem';
            nameCell.style.borderBottom = '1px solid var(--border)';
            nameCell.textContent = file.name;
            nameCell.title = file.path;
            
            // Issues
            const issuesCell = row.insertCell();
            issuesCell.style.padding = '0.75rem';
            issuesCell.style.borderBottom = '1px solid var(--border)';
            issuesCell.innerHTML = `<span style="font-family: monospace; background: var(--background); padding: 0.25rem 0.5rem; border-radius: 4px;">${file.issues.join(' + ')}</span>`;
            
            // Size
            const sizeCell = row.insertCell();
            sizeCell.style.padding = '0.75rem';
            sizeCell.style.borderBottom = '1px solid var(--border)';
            sizeCell.style.textAlign = 'right';
            sizeCell.textContent = file.size;
        });
    }

    exportCSV() {
        if (!this.analysisData || !this.analysisData.problematic_files_list) {
            alert('No data to export');
            return;
        }

        const files = this.analysisData.problematic_files_list;
        
        // Create CSV content
        const headers = ['File Name', 'Path', 'Audio Codec', 'Video Codec', 'Issues', 'Size'];
        const csvContent = [
            headers.join(','),
            ...files.map(file => [
                `"${file.name}"`,
                `"${file.path}"`,
                `"${file.audio_codec || ''}"`,
                `"${file.video_codec || ''}"`,
                `"${file.issues.join(' + ')}"`,
                `"${file.size}"`
            ].join(','))
        ].join('\n');

        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mediainfo-problematic-files-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
}