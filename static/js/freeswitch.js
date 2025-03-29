// FreeSWITCH PBX management functionality
document.addEventListener('DOMContentLoaded', function() {
    // FreeSWITCH toggle functionality
    const enableFreeswitchCheckbox = document.getElementById('enabled');
    const freeswitchSettingsDiv = document.getElementById('freeswitch-settings');
    
    if (enableFreeswitchCheckbox && freeswitchSettingsDiv) {
        enableFreeswitchCheckbox.addEventListener('change', function() {
            freeswitchSettingsDiv.style.display = this.checked ? 'block' : 'none';
        });
        
        // Set initial state
        freeswitchSettingsDiv.style.display = enableFreeswitchCheckbox.checked ? 'block' : 'none';
    }
    
    // Voicemail settings toggle
    const voicemailCheckboxes = document.querySelectorAll('.voicemail-toggle');
    
    voicemailCheckboxes.forEach(checkbox => {
        const pinField = document.getElementById(`voicemail-pin-${checkbox.dataset.extension}`);
        
        if (pinField) {
            checkbox.addEventListener('change', function() {
                pinField.style.display = this.checked ? 'block' : 'none';
            });
            
            // Set initial state
            pinField.style.display = checkbox.checked ? 'block' : 'none';
        }
    });
    
    // Extension edit/delete confirmation
    const deleteExtensionButtons = document.querySelectorAll('.delete-extension');
    
    deleteExtensionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this extension?')) {
                e.preventDefault();
            }
        });
    });
    
    // FreeSWITCH restart confirmation
    const restartFreeswitchButton = document.getElementById('restart-freeswitch');
    
    if (restartFreeswitchButton) {
        restartFreeswitchButton.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to restart FreeSWITCH? All active calls will be disconnected.')) {
                e.preventDefault();
            }
        });
    }
    
    // Extension registration status updating
    function updateRegistrationStatus() {
        fetch('/freeswitch/registrations')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const registrations = data.registrations || [];
                    
                    // Reset all extensions to offline
                    document.querySelectorAll('.extension-status').forEach(statusEl => {
                        statusEl.innerHTML = '<span class="badge bg-secondary">Offline</span>';
                    });
                    
                    // Update registered extensions
                    registrations.forEach(reg => {
                        const statusEl = document.getElementById(`extension-status-${reg.extension}`);
                        if (statusEl) {
                            statusEl.innerHTML = `
                                <span class="badge bg-success">Online</span>
                                <small class="text-muted ms-2">${reg.ip}</small>
                                <small class="text-muted ms-2">${reg.user_agent}</small>
                            `;
                        }
                    });
                }
            })
            .catch(error => console.error('Error updating registration status:', error));
    }
    
    // FreeSWITCH status updating
    function updateFreeswitchStatus() {
        const statusContainer = document.getElementById('freeswitch-status-container');
        
        if (!statusContainer) return;
        
        fetch('/api/v1/freeswitch/status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const status = data.status || {};
                    
                    // Update status indicator
                    const statusIndicator = document.getElementById('fs-status-indicator');
                    if (statusIndicator) {
                        if (status.running) {
                            statusIndicator.className = 'status-indicator status-up';
                            statusIndicator.nextElementSibling.textContent = 'Running';
                        } else {
                            statusIndicator.className = 'status-indicator status-down';
                            statusIndicator.nextElementSibling.textContent = 'Not Running';
                        }
                    }
                    
                    // Update statistics
                    if (status.running) {
                        document.getElementById('fs-uptime-value').textContent = formatUptime(status.uptime || 0);
                        document.getElementById('fs-calls-value').textContent = status.calls || 0;
                        document.getElementById('fs-channels-value').textContent = status.channels || 0;
                        document.getElementById('fs-registrations-value').textContent = status.registrations || 0;
                    }
                }
            })
            .catch(error => {
                console.error('Error updating FreeSWITCH status:', error);
                const statusIndicator = document.getElementById('fs-status-indicator');
                if (statusIndicator) {
                    statusIndicator.className = 'status-indicator status-unknown';
                    statusIndicator.nextElementSibling.textContent = 'Unknown';
                }
            });
    }
    
    // Format uptime
    function formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        let result = '';
        if (days > 0) result += days + ' days ';
        if (hours > 0) result += hours + ' hours ';
        if (minutes > 0 && days === 0) result += minutes + ' minutes';
        
        return result.trim() || '0 minutes';
    }
    
    // Check if we're on the FreeSWITCH page and update statuses
    if (document.getElementById('freeswitch-page')) {
        updateRegistrationStatus();
        updateFreeswitchStatus();
        
        // Update every 10 seconds
        setInterval(updateRegistrationStatus, 10000);
        setInterval(updateFreeswitchStatus, 10000);
    }
    
    // Password generation
    const generatePasswordButtons = document.querySelectorAll('.generate-password');
    
    generatePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const passwordField = document.getElementById(button.dataset.target);
            if (passwordField) {
                const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
                let password = '';
                
                for (let i = 0; i < 12; i++) {
                    password += chars.charAt(Math.floor(Math.random() * chars.length));
                }
                
                passwordField.value = password;
            }
        });
    });
});
