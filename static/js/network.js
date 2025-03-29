/**
 * Network configuration scripts for Banana Pi BPI-R4 Router OS
 * Handles network interfaces management, DHCP, DNS configuration
 */

// Initialize network page functionality
document.addEventListener('DOMContentLoaded', function() {
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Add listeners for IP mode selection
  const ipModeRadios = document.querySelectorAll('input[name="ip_mode"]');
  if (ipModeRadios.length > 0) {
    ipModeRadios.forEach(radio => {
      radio.addEventListener('change', toggleStaticIPFields);
    });
    // Initial toggle based on selected mode
    toggleStaticIPFields();
  }
  
  // Add listeners for DHCP toggle
  const dhcpToggle = document.getElementById('enabled');
  if (dhcpToggle) {
    dhcpToggle.addEventListener('change', toggleDhcpFields);
    // Initial toggle based on current state
    toggleDhcpFields();
  }
  
  // Listen for restart network button
  const restartNetworkBtn = document.getElementById('restartNetwork');
  if (restartNetworkBtn) {
    restartNetworkBtn.addEventListener('click', confirmRestartNetwork);
  }
  
  // Attach event handler to interface status buttons
  const interfaceStatusBtns = document.querySelectorAll('.interface-status-btn');
  if (interfaceStatusBtns.length > 0) {
    interfaceStatusBtns.forEach(btn => {
      btn.addEventListener('click', toggleInterfaceStatus);
    });
  }
  
  // Initialize IP input validation
  const ipInputs = document.querySelectorAll('input[data-validate="ip"]');
  if (ipInputs.length > 0) {
    ipInputs.forEach(input => {
      input.addEventListener('blur', validateIPAddress);
    });
  }
});

/**
 * Toggle IP configuration fields visibility based on IP mode
 */
function toggleStaticIPFields() {
  const selectedMode = document.querySelector('input[name="ip_mode"]:checked');
  if (!selectedMode) return;
  
  const staticFields = document.getElementById('staticIPFields');
  const pppoeFields = document.getElementById('pppoeFields');
  
  // Hide all fields first
  if (staticFields) {
    staticFields.classList.add('d-none');
    // Remove required attribute
    const inputs = staticFields.querySelectorAll('input');
    inputs.forEach(input => {
      input.required = false;
    });
  }
  
  if (pppoeFields) {
    pppoeFields.classList.add('d-none');
    // Remove required attribute
    const inputs = pppoeFields.querySelectorAll('input');
    inputs.forEach(input => {
      input.required = false;
    });
  }
  
  // Show fields based on selected mode
  if (selectedMode.value === 'static' && staticFields) {
    staticFields.classList.remove('d-none');
    // Make fields required
    const inputs = staticFields.querySelectorAll('input');
    inputs.forEach(input => {
      // Don't make DNS servers required
      if (input.id !== 'dns_servers') {
        input.required = true;
      }
    });
  } else if (selectedMode.value === 'pppoe' && pppoeFields) {
    pppoeFields.classList.remove('d-none');
    // Make username and password required
    const usernameInput = pppoeFields.querySelector('#pppoe_username');
    const passwordInput = pppoeFields.querySelector('#pppoe_password');
    if (usernameInput) usernameInput.required = true;
    if (passwordInput) passwordInput.required = true;
  }
}

/**
 * Toggle DHCP server configuration fields visibility
 */
function toggleDhcpFields() {
  const dhcpEnabled = document.getElementById('enabled');
  if (!dhcpEnabled) return;
  
  const dhcpFields = document.getElementById('dhcpFields');
  if (dhcpFields) {
    if (dhcpEnabled.checked) {
      dhcpFields.classList.remove('d-none');
      // Make fields required
      const inputs = dhcpFields.querySelectorAll('input');
      inputs.forEach(input => {
        input.required = true;
      });
    } else {
      dhcpFields.classList.add('d-none');
      // Remove required attribute
      const inputs = dhcpFields.querySelectorAll('input');
      inputs.forEach(input => {
        input.required = false;
      });
    }
  }
}

/**
 * Show confirmation dialog for network service restart
 */
function confirmRestartNetwork() {
  if (confirm('Sei sicuro di voler riavviare i servizi di rete? Tutte le connessioni attive verranno interrotte.')) {
    restartNetworkService();
  }
}

/**
 * Restart network services via API
 */
function restartNetworkService() {
  const btn = document.getElementById('restartNetwork');
  if (btn) {
    // Disable button and show loading state
    btn.disabled = true;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loader"></span> Riavvio in corso...';
    
    // Call API to restart network
    fetch('/network/restart', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Show success message
        showAlert('Servizi di rete riavviati con successo.', 'success');
        
        // After a delay, refresh the page to show updated network status
        setTimeout(() => {
          window.location.reload();
        }, 3000);
      } else {
        // Show error message
        showAlert('Errore durante il riavvio dei servizi di rete: ' + data.message, 'danger');
        
        // Reset button state
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    })
    .catch(error => {
      console.error('Error restarting network services:', error);
      showAlert('Errore durante il riavvio dei servizi di rete.', 'danger');
      
      // Reset button state
      btn.innerHTML = originalText;
      btn.disabled = false;
    });
  }
}

/**
 * Toggle interface status (up/down)
 * @param {Event} event - Click event
 */
function toggleInterfaceStatus(event) {
  const btn = event.currentTarget;
  const interfaceName = btn.getAttribute('data-interface');
  const currentStatus = btn.getAttribute('data-status');
  const newStatus = currentStatus === 'up' ? 'down' : 'up';
  
  if (confirm(`Sei sicuro di voler ${newStatus === 'up' ? 'attivare' : 'disattivare'} l'interfaccia ${interfaceName}?`)) {
    // Disable button and show loading state
    btn.disabled = true;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loader"></span> In corso...';
    
    // This would be an actual API call in a real implementation
    // For now, just simulate the action with a timeout
    setTimeout(() => {
      // Show success message
      showAlert(`Interfaccia ${interfaceName} ${newStatus === 'up' ? 'attivata' : 'disattivata'} con successo.`, 'success');
      
      // Update button state
      btn.setAttribute('data-status', newStatus);
      btn.innerHTML = newStatus === 'up' ? 'Disattiva' : 'Attiva';
      btn.classList.toggle('btn-danger', newStatus === 'up');
      btn.classList.toggle('btn-success', newStatus === 'down');
      
      // Update status indicator
      const statusIndicator = document.querySelector(`[data-interface-indicator="${interfaceName}"]`);
      if (statusIndicator) {
        statusIndicator.classList.toggle('status-up', newStatus === 'up');
        statusIndicator.classList.toggle('status-down', newStatus === 'down');
        
        const statusText = statusIndicator.nextElementSibling;
        if (statusText) {
          statusText.textContent = newStatus === 'up' ? 'Attivo' : 'Disattivo';
        }
      }
      
      btn.disabled = false;
    }, 1500);
  }
}

/**
 * Validate IP address format
 * @param {Event} event - Blur event
 */
function validateIPAddress(event) {
  const input = event.target;
  const ipValue = input.value.trim();
  
  if (ipValue === '') return;
  
  // Basic IP address validation regex
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  
  if (!ipRegex.test(ipValue)) {
    input.classList.add('is-invalid');
    
    // Create or update validation message
    let feedbackEl = input.nextElementSibling;
    if (!feedbackEl || !feedbackEl.classList.contains('invalid-feedback')) {
      feedbackEl = document.createElement('div');
      feedbackEl.classList.add('invalid-feedback');
      input.parentNode.insertBefore(feedbackEl, input.nextSibling);
    }
    feedbackEl.textContent = 'Indirizzo IP non valido. Formato corretto: xxx.xxx.xxx.xxx';
  } else {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    
    // Remove validation message if exists
    const feedbackEl = input.nextElementSibling;
    if (feedbackEl && feedbackEl.classList.contains('invalid-feedback')) {
      feedbackEl.remove();
    }
  }
}

/**
 * Show alert message
 * @param {string} message - Alert message text
 * @param {string} type - Alert type (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
  // Create alert container if it doesn't exist
  let alertContainer = document.getElementById('alertContainer');
  if (!alertContainer) {
    alertContainer = document.createElement('div');
    alertContainer.id = 'alertContainer';
    alertContainer.style.position = 'fixed';
    alertContainer.style.top = '15px';
    alertContainer.style.right = '15px';
    alertContainer.style.zIndex = '9999';
    document.body.appendChild(alertContainer);
  }
  
  // Create alert element
  const alertEl = document.createElement('div');
  alertEl.className = `alert alert-${type} alert-dismissible fade show`;
  alertEl.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  // Add alert to container
  alertContainer.appendChild(alertEl);
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    alertEl.classList.remove('show');
    setTimeout(() => {
      alertEl.remove();
    }, 150);
  }, 5000);
}
