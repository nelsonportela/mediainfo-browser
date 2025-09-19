class SettingsManager {
    constructor() {
        this.modal = document.getElementById('settings-modal');
        this.config = null;
        this.availableCodecs = null;
        this.initializeEventListeners();
        this.loadConfig();
    }

    initializeEventListeners() {
        // Settings button
        document.getElementById('settings-btn').addEventListener('click', () => {
            this.openModal();
        });

        // Close modal
        document.getElementById('close-settings').addEventListener('click', () => {
            this.closeModal();
        });

        // Close modal when clicking outside
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Save settings
        document.getElementById('save-settings').addEventListener('click', () => {
            this.saveSettings();
        });
    }

    async loadConfig() {
        try {
            // Load current config
            const configResponse = await fetch('/api/config');
            this.config = await configResponse.json();

            // Load available codecs
            const codecsResponse = await fetch('/api/available-codecs');
            this.availableCodecs = await codecsResponse.json();

            this.populateCodecSelectors();
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.showStatus('Error loading configuration', 'error');
        }
    }

    populateCodecSelectors() {
        // Populate audio codec selector
        const audioSelector = document.getElementById('audio-codec-selector');
        audioSelector.innerHTML = '';

        this.availableCodecs.audio.forEach(codec => {
            const isChecked = this.config.problematic_codecs.audio.includes(codec);
            const optionDiv = document.createElement('div');
            optionDiv.className = 'codec-option';
            optionDiv.innerHTML = `
                <input type="checkbox" id="audio-${codec}" ${isChecked ? 'checked' : ''}>
                <label for="audio-${codec}">${codec}</label>
            `;
            audioSelector.appendChild(optionDiv);
        });

        // Populate video codec selector
        const videoSelector = document.getElementById('video-codec-selector');
        videoSelector.innerHTML = '';

        this.availableCodecs.video.forEach(codec => {
            const isChecked = this.config.problematic_codecs.video.includes(codec);
            const optionDiv = document.createElement('div');
            optionDiv.className = 'codec-option';
            optionDiv.innerHTML = `
                <input type="checkbox" id="video-${codec}" ${isChecked ? 'checked' : ''}>
                <label for="video-${codec}">${codec}</label>
            `;
            videoSelector.appendChild(optionDiv);
        });
    }

    openModal() {
        this.modal.style.display = 'block';
        this.hideStatus();
    }

    closeModal() {
        this.modal.style.display = 'none';
        this.hideStatus();
    }

    async saveSettings() {
        const saveBtn = document.getElementById('save-settings');
        saveBtn.disabled = true;
        saveBtn.textContent = '💾 Saving...';

        try {
            // Collect selected audio codecs
            const audioCodecs = [];
            document.querySelectorAll('#audio-codec-selector input[type="checkbox"]:checked').forEach(checkbox => {
                const codec = checkbox.id.replace('audio-', '');
                audioCodecs.push(codec);
            });

            // Collect selected video codecs
            const videoCodecs = [];
            document.querySelectorAll('#video-codec-selector input[type="checkbox"]:checked').forEach(checkbox => {
                const codec = checkbox.id.replace('video-', '');
                videoCodecs.push(codec);
            });

            // Update config
            const newConfig = {
                ...this.config,
                problematic_codecs: {
                    audio: audioCodecs,
                    video: videoCodecs
                }
            };

            // Save to server
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newConfig)
            });

            const result = await response.json();

            if (response.ok) {
                this.config = newConfig;
                this.showStatus('Settings saved successfully!', 'success');
                
                // Optionally reload the current view to show updated compatibility status
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(result.error || 'Failed to save settings');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showStatus(`Error saving settings: ${error.message}`, 'error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = '💾 Save Settings';
        }
    }

    showStatus(message, type) {
        const statusDiv = document.getElementById('settings-status');
        statusDiv.textContent = message;
        statusDiv.className = `status-message status-${type}`;
        statusDiv.style.display = 'block';
    }

    hideStatus() {
        const statusDiv = document.getElementById('settings-status');
        statusDiv.style.display = 'none';
    }
}