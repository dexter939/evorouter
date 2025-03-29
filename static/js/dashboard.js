// Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    // Network traffic chart data
    let networkData = {
        download: Array(30).fill(0),
        upload: Array(30).fill(0),
        timestamps: Array(30).fill('').map((_, i) => `-${30-i}s`)
    };
    
    // Previous network statistics for calculating rates
    let prevNetStats = null;
    let networkChart = null;
    
    // Function to format byte sizes
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    // Function to format uptime
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
    
    // Initialize the network chart if it exists on the page
    const chartElement = document.getElementById('networkChart');
    if (chartElement) {
        const ctx = chartElement.getContext('2d');
        networkChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: networkData.timestamps,
                datasets: [
                    {
                        label: 'Download (Bytes/s)',
                        data: networkData.download,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.4
                    },
                    {
                        label: 'Upload (Bytes/s)',
                        data: networkData.upload,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatBytes(value, 1);
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                let value = context.parsed.y;
                                return label + ': ' + formatBytes(value, 2);
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Function to update dashboard data
    function updateDashboard() {
        // Update system stats
        fetch('/api/dashboard/stats')
            .then(response => response.json())
            .then(data => {
                if (data.system) {
                    // Update CPU, memory, disk usage in sidebar
                    const cpuUsage = document.getElementById('cpu-usage');
                    const memoryUsage = document.getElementById('memory-usage');
                    const diskUsage = document.getElementById('disk-usage');
                    
                    if (cpuUsage) {
                        cpuUsage.style.width = data.system.cpu_percent + '%';
                        cpuUsage.textContent = data.system.cpu_percent + '%';
                    }
                    
                    if (memoryUsage) {
                        memoryUsage.style.width = data.system.memory_percent + '%';
                        memoryUsage.textContent = data.system.memory_percent + '%';
                    }
                    
                    if (diskUsage) {
                        diskUsage.style.width = data.system.disk_percent + '%';
                        diskUsage.textContent = data.system.disk_percent + '%';
                    }
                    
                    // Update temperature display if available
                    const temperatureEl = document.getElementById('temperature');
                    if (temperatureEl) {
                        temperatureEl.textContent = 
                            data.system.cpu_temperature ? data.system.cpu_temperature.toFixed(1) + '°C' : 'N/A';
                    }
                    
                    // Update uptime if available
                    const uptimeEl = document.getElementById('uptime');
                    if (uptimeEl && data.system.uptime) {
                        uptimeEl.textContent = formatUptime(data.system.uptime);
                    }
                    
                    // Update network chart if available
                    if (networkChart && data.network && prevNetStats) {
                        const timeDiff = 2; // Assume 2 second update interval
                        let totalRx = 0;
                        let totalTx = 0;
                        
                        for (const iface in data.network.interfaces) {
                            if (iface === 'lo') continue; // Skip loopback
                            
                            if (data.network.interfaces[iface] && prevNetStats.interfaces[iface]) {
                                const current = data.network.interfaces[iface];
                                const prev = prevNetStats.interfaces[iface];
                                
                                // Calculate rates in bytes per second
                                totalRx += Math.max(0, (current.bytes_recv - prev.bytes_recv) / timeDiff);
                                totalTx += Math.max(0, (current.bytes_sent - prev.bytes_sent) / timeDiff);
                            }
                        }
                        
                        // Add new data points
                        networkData.download.push(totalRx);
                        networkData.upload.push(totalTx);
                        
                        // Remove old data points
                        if (networkData.download.length > 30) {
                            networkData.download.shift();
                            networkData.upload.shift();
                        }
                        
                        // Update chart data
                        networkChart.data.datasets[0].data = networkData.download;
                        networkChart.data.datasets[1].data = networkData.upload;
                        networkChart.update();
                    }
                    
                    prevNetStats = data.network;
                }
            })
            .catch(error => console.error('Error fetching dashboard stats:', error));
        
        // Update FreeSWITCH status if on dashboard
        const fsStatus = document.getElementById('fs-status');
        if (fsStatus) {
            // Update FreeSWITCH registration status
            fetch('/freeswitch/registrations')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const registrations = data.registrations || [];
                        
                        // Update extension statuses
                        document.querySelectorAll('[id^="ext-status-"]').forEach(el => {
                            el.textContent = 'Offline';
                            el.classList.remove('bg-success');
                            el.classList.add('bg-secondary');
                        });
                        
                        registrations.forEach(reg => {
                            const extElement = document.getElementById(`ext-status-${reg.extension}`);
                            if (extElement) {
                                extElement.textContent = 'Online';
                                extElement.classList.remove('bg-secondary');
                                extElement.classList.add('bg-success');
                            }
                        });
                        
                        // Update FreeSWITCH statistics
                        document.getElementById('fs-status').innerHTML = 
                            '<span class="status-indicator status-up"></span> Running';
                        document.getElementById('fs-regs').textContent = registrations.length;
                        
                        // Call count would be updated here in a real implementation
                        const fsCallsEl = document.getElementById('fs-calls');
                        if (fsCallsEl) {
                            // This would come from the real FreeSWITCH data
                            fsCallsEl.textContent = '0';
                        }
                        
                        // Update uptime
                        const fsUptimeEl = document.getElementById('fs-uptime');
                        if (fsUptimeEl) {
                            // This would come from the real FreeSWITCH data
                            fsUptimeEl.textContent = formatUptime(3600); // Example: 1 hour
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching FreeSWITCH status:', error);
                    fsStatus.innerHTML = '<span class="status-indicator status-down"></span> Not Running';
                });
        }
    }
    
    // Refresh dashboard data
    const refreshButton = document.getElementById('refresh-dashboard');
    if (refreshButton) {
        refreshButton.addEventListener('click', updateDashboard);
    }
    
    // Initial update and start periodic updates
    updateDashboard();
    setInterval(updateDashboard, 2000);
});
