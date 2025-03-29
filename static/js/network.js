// Network management functionality
document.addEventListener('DOMContentLoaded', function() {
    // Network interface management
    const interfaceTypeSelect = document.getElementById('type');
    const dhcpEnabledCheckbox = document.getElementById('dhcp_enabled');
    const staticIpFields = document.getElementById('static-ip-fields');
    
    // Toggle DHCP/Static settings visibility
    if (dhcpEnabledCheckbox && staticIpFields) {
        dhcpEnabledCheckbox.addEventListener('change', function() {
            staticIpFields.style.display = this.checked ? 'none' : 'block';
        });
        
        // Set initial state
        staticIpFields.style.display = dhcpEnabledCheckbox.checked ? 'none' : 'block';
    }
    
    // WiFi scanning functionality
    const scanWifiButton = document.getElementById('scan-wifi');
    const wifiNetworksList = document.getElementById('wifi-networks');
    const wifiSsidField = document.getElementById('wifi_ssid');
    
    if (scanWifiButton && wifiNetworksList) {
        scanWifiButton.addEventListener('click', function() {
            // Show loading state
            scanWifiButton.disabled = true;
            scanWifiButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Scanning...';
            
            // Clear previous results
            wifiNetworksList.innerHTML = '';
            
            // Request WiFi scan
            fetch('/network/scan_wifi')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const networks = data.networks || [];
                        
                        if (networks.length === 0) {
                            wifiNetworksList.innerHTML = '<div class="alert alert-info">No networks found</div>';
                        } else {
                            // Create list of networks
                            const listGroup = document.createElement('div');
                            listGroup.className = 'list-group';
                            
                            networks.forEach(network => {
                                const item = document.createElement('button');
                                item.type = 'button';
                                item.className = 'list-group-item list-group-item-action';
                                
                                // Signal strength indicator
                                let signalStrength = 'weak';
                                if (network.signal_strength > -60) {
                                    signalStrength = 'strong';
                                } else if (network.signal_strength > -70) {
                                    signalStrength = 'medium';
                                }
                                
                                item.innerHTML = `
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 class="mb-0">${network.ssid}</h6>
                                            <small class="text-muted">Channel: ${network.channel} | Security: ${network.security}</small>
                                        </div>
                                        <div>
                                            <i class="fas fa-wifi text-${signalStrength === 'strong' ? 'success' : (signalStrength === 'medium' ? 'warning' : 'danger')}"></i>
                                            <small>${network.signal_strength} dBm</small>
                                        </div>
                                    </div>
                                `;
                                
                                // Select network on click
                                item.addEventListener('click', function() {
                                    if (wifiSsidField) {
                                        wifiSsidField.value = network.ssid;
                                    }
                                });
                                
                                listGroup.appendChild(item);
                            });
                            
                            wifiNetworksList.appendChild(listGroup);
                        }
                    } else {
                        wifiNetworksList.innerHTML = `<div class="alert alert-danger">${data.error || 'Failed to scan WiFi networks'}</div>`;
                    }
                })
                .catch(error => {
                    console.error('Error scanning WiFi networks:', error);
                    wifiNetworksList.innerHTML = `<div class="alert alert-danger">Error scanning WiFi networks</div>`;
                })
                .finally(() => {
                    // Reset button
                    scanWifiButton.disabled = false;
                    scanWifiButton.innerHTML = '<i class="fas fa-sync-alt"></i> Scan WiFi Networks';
                });
        });
    }
    
    // Interface restart confirmation
    const restartButtons = document.querySelectorAll('.restart-interface');
    restartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to restart this interface? This may disrupt network connectivity.')) {
                e.preventDefault();
            }
        });
    });
    
    // Interface statistics updating
    const interfaceStats = document.querySelectorAll('.interface-stats');
    
    function updateInterfaceStats() {
        interfaceStats.forEach(statContainer => {
            const interfaceId = statContainer.dataset.interfaceId;
            if (!interfaceId) return;
            
            fetch(`/network/interface/${interfaceId}/stats`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.stats || {};
                        
                        // Update each statistic field
                        for (const [key, value] of Object.entries(stats)) {
                            const element = statContainer.querySelector(`.stat-${key}`);
                            if (element) {
                                if (key.includes('bytes')) {
                                    // Format byte values
                                    const bytes = parseInt(value);
                                    element.textContent = formatBytes(bytes);
                                } else {
                                    element.textContent = value;
                                }
                            }
                        }
                    }
                })
                .catch(error => console.error(`Error updating interface ${interfaceId} stats:`, error));
        });
    }
    
    // Format bytes to human-readable format
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    // Update interface stats if any are present
    if (interfaceStats.length > 0) {
        updateInterfaceStats();
        // Update every 5 seconds
        setInterval(updateInterfaceStats, 5000);
    }
});
