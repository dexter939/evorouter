/**
 * Dashboard scripts for EvoRouter R4 Router OS
 * Handles dashboard UI interactions, charts, and data refreshing
 */

// Initialize charts on page load
document.addEventListener('DOMContentLoaded', function() {
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Check FreeSWITCH status
  checkFreeswitchStatus();
  
  // Initialize CPU usage chart
  const cpuCtx = document.getElementById('cpuChart');
  if (cpuCtx) {
    const cpuChart = new Chart(cpuCtx, {
      type: 'line',
      data: {
        labels: Array(24).fill('').map((_, i) => i.toString()),
        datasets: [{
          label: 'Utilizzo CPU (%)',
          data: [],
          borderColor: '#3498db',
          backgroundColor: 'rgba(52, 152, 219, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: function(value) {
                return value + '%';
              }
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                return context.dataset.label + ': ' + context.parsed.y + '%';
              }
            }
          },
          legend: {
            display: false
          }
        }
      }
    });
    
    // Add initial CPU data
    const cpuValue = document.getElementById('cpuUsage');
    if (cpuValue) {
      const cpuUsage = parseFloat(cpuValue.getAttribute('data-value'));
      cpuChart.data.datasets[0].data.push(cpuUsage);
      cpuChart.update();
    }
  }
  
  // Initialize Memory usage chart
  const memCtx = document.getElementById('memoryChart');
  if (memCtx) {
    const memoryChart = new Chart(memCtx, {
      type: 'doughnut',
      data: {
        labels: ['Usata', 'Libera'],
        datasets: [{
          data: [0, 100],
          backgroundColor: ['#3498db', '#ecf0f1'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return context.label + ': ' + context.parsed + '%';
              }
            }
          }
        }
      }
    });
    
    // Add initial memory data
    const memValue = document.getElementById('memoryUsage');
    if (memValue) {
      const memUsage = parseFloat(memValue.getAttribute('data-value'));
      memoryChart.data.datasets[0].data = [memUsage, 100 - memUsage];
      memoryChart.update();
    }
  }
  
  // Initialize Network traffic chart
  const netCtx = document.getElementById('networkChart');
  if (netCtx) {
    const networkChart = new Chart(netCtx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Download (Mbps)',
            data: [],
            borderColor: '#2ecc71',
            backgroundColor: 'rgba(46, 204, 113, 0.1)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
          },
          {
            label: 'Upload (Mbps)',
            data: [],
            borderColor: '#e74c3c',
            backgroundColor: 'rgba(231, 76, 60, 0.1)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return value + ' Mbps';
              }
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                return context.dataset.label + ': ' + context.parsed.y + ' Mbps';
              }
            }
          }
        }
      }
    });
    
    // Fetch network history data and update chart
    fetchNetworkHistoryData(networkChart);
  }
  
  // Set up periodic data refresh
  setInterval(refreshDashboardData, 10000); // Refresh every 10 seconds
  
  // Update sidebar stats if available
  updateSidebarStats();
  setInterval(updateSidebarStats, 10000); // Update sidebar stats every 10 seconds
  
  // Check FreeSWITCH status periodically
  setInterval(checkFreeswitchStatus, 30000); // Check every 30 seconds
});

/**
 * Fetch network traffic history data
 * @param {Chart} chart - Chart.js instance to update
 */
function fetchNetworkHistoryData(chart) {
  fetch('/dashboard/api/network_usage_history')
    .then(response => response.json())
    .then(data => {
      chart.data.labels = data.timestamps;
      chart.data.datasets[0].data = data.wan_download;
      chart.data.datasets[1].data = data.wan_upload;
      chart.update();
    })
    .catch(error => {
      console.error('Error fetching network history:', error);
    });
}

/**
 * Refresh dashboard data via API
 */
function refreshDashboardData() {
  fetch('/dashboard/api/stats')
    .then(response => response.json())
    .then(data => {
      // Update CPU info
      if (data.system && data.system.cpu) {
        const cpuUsage = data.system.cpu.usage;
        document.getElementById('cpuUsageValue').textContent = cpuUsage + '%';
        
        // Update CPU chart if exists
        const cpuChart = Chart.getChart('cpuChart');
        if (cpuChart) {
          if (cpuChart.data.datasets[0].data.length >= 24) {
            cpuChart.data.datasets[0].data.shift();
          }
          cpuChart.data.datasets[0].data.push(cpuUsage);
          cpuChart.update();
        }
      }
      
      // Update memory info
      if (data.system && data.system.memory) {
        const memUsage = data.system.memory.percent;
        const memUsed = formatBytes(data.system.memory.used);
        const memTotal = formatBytes(data.system.memory.total);
        
        document.getElementById('memoryUsageValue').textContent = memUsage + '%';
        document.getElementById('memoryDetails').textContent = `${memUsed} / ${memTotal}`;
        
        // Update memory chart if exists
        const memoryChart = Chart.getChart('memoryChart');
        if (memoryChart) {
          memoryChart.data.datasets[0].data = [memUsage, 100 - memUsage];
          memoryChart.update();
        }
      }
      
      // Update network info
      if (data.network) {
        for (const [interface, stats] of Object.entries(data.network)) {
          if (interface === 'total') continue;
          
          const downloadEl = document.getElementById(`${interface}Download`);
          const uploadEl = document.getElementById(`${interface}Upload`);
          
          if (downloadEl) downloadEl.textContent = formatBitrate(stats.mbits_recv);
          if (uploadEl) uploadEl.textContent = formatBitrate(stats.mbits_sent);
        }
      }
    })
    .catch(error => {
      console.error('Error refreshing dashboard data:', error);
    });
}

/**
 * Format bytes to human-readable string
 * @param {number} bytes - Bytes to format
 * @param {number} decimals - Decimal places
 * @return {string} Formatted string
 */
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format bitrate to human-readable string
 * @param {number} mbits - Megabits per second
 * @return {string} Formatted string
 */
function formatBitrate(mbits) {
  if (mbits < 1) {
    return (mbits * 1000).toFixed(0) + ' Kbps';
  } else if (mbits > 1000) {
    return (mbits / 1000).toFixed(2) + ' Gbps';
  } else {
    return mbits.toFixed(1) + ' Mbps';
  }
}

/**
 * Update sidebar statistics if available
 */
function updateSidebarStats() {
  // Check if sidebar stats elements exist
  const cpuStat = document.getElementById('sidebar-cpu-usage');
  const memStat = document.getElementById('sidebar-memory-usage');
  const uptimeStat = document.getElementById('sidebar-uptime');
  
  if (!cpuStat && !memStat && !uptimeStat) return;
  
  // Fetch system stats
  fetch('/dashboard/api/stats')
    .then(response => response.json())
    .then(data => {
      // Update CPU usage
      if (cpuStat && data.system && data.system.cpu) {
        cpuStat.textContent = data.system.cpu.usage + '%';
      }
      
      // Update memory usage
      if (memStat && data.system && data.system.memory) {
        memStat.textContent = data.system.memory.percent + '%';
      }
      
      // Update uptime
      if (uptimeStat && data.system && data.system.uptime) {
        uptimeStat.textContent = formatUptime(data.system.uptime);
      }
    })
    .catch(error => {
      console.error('Error updating sidebar stats:', error);
    });
}

/**
 * Format uptime seconds to human-readable string
 * @param {number} seconds - Uptime in seconds
 * @return {string} Formatted uptime
 */
function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) {
    return `${days}d ${hours}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
}

/**
 * Check FreeSWITCH status and update UI accordingly
 */
function checkFreeswitchStatus() {
  // Check if FreeSWITCH status element exists
  const fsStatusEl = document.getElementById('freeswitchStatus');
  if (!fsStatusEl) return;
  
  fetch('/api/freeswitch/status')
    .then(response => response.json())
    .then(data => {
      // Update FreeSWITCH status in UI
      if (data.status === 'success' && data.data) {
        const status = data.data;
        
        // Update status icon and text
        if (status.installed) {
          if (status.running) {
            fsStatusEl.innerHTML = '<span class="badge bg-success">Attivo</span>';
          } else {
            fsStatusEl.innerHTML = '<span class="badge bg-warning">Installato (non attivo)</span>';
          }
        } else {
          fsStatusEl.innerHTML = '<span class="badge bg-danger">Non installato</span>';
        }
        
        // Update version if available
        const fsVersionEl = document.getElementById('freeswitchVersion');
        if (fsVersionEl && status.version) {
          fsVersionEl.textContent = status.version;
        } else if (fsVersionEl) {
          fsVersionEl.textContent = 'N/A';
        }
      } else {
        fsStatusEl.innerHTML = '<span class="badge bg-secondary">Stato sconosciuto</span>';
      }
    })
    .catch(error => {
      console.error('Error checking FreeSWITCH status:', error);
      if (fsStatusEl) {
        fsStatusEl.innerHTML = '<span class="badge bg-danger">Errore</span>';
      }
    });
}
