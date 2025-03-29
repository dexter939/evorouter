/**
 * FreeSWITCH management scripts for Banana Pi BPI-R4 Router OS
 * Handles PBX configuration, extensions, trunks, and call routing
 */

// Initialize PBX page functionality
document.addEventListener('DOMContentLoaded', function() {
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Add listener for restart PBX button
  const restartFsBtn = document.getElementById('restartFreeswitch');
  if (restartFsBtn) {
    restartFsBtn.addEventListener('click', confirmRestartFreeswitch);
  }
  
  // Add listener for the additional start PBX button in warning message
  const startFsBtn = document.getElementById('startFreeswitchBtn');
  if (startFsBtn) {
    startFsBtn.addEventListener('click', confirmRestartFreeswitch);
  }
  
  // Add listener for delete extension buttons
  const deleteExtensionBtns = document.querySelectorAll('.delete-extension-btn');
  if (deleteExtensionBtns.length > 0) {
    deleteExtensionBtns.forEach(btn => {
      btn.addEventListener('click', confirmDeleteExtension);
    });
  }
  
  // Add listener for delete trunk buttons
  const deleteTrunkBtns = document.querySelectorAll('.delete-trunk-btn');
  if (deleteTrunkBtns.length > 0) {
    deleteTrunkBtns.forEach(btn => {
      btn.addEventListener('click', confirmDeleteTrunk);
    });
  }
  
  // Toggle voicemail fields based on voicemail enabled checkbox
  const voicemailCheckbox = document.getElementById('voicemail_enabled');
  if (voicemailCheckbox) {
    voicemailCheckbox.addEventListener('change', toggleVoicemailFields);
    // Initial toggle based on current state
    toggleVoicemailFields();
  }
  
  // Password visibility toggle
  const togglePasswordBtns = document.querySelectorAll('.toggle-password');
  if (togglePasswordBtns.length > 0) {
    togglePasswordBtns.forEach(btn => {
      btn.addEventListener('click', togglePasswordVisibility);
    });
  }
  
  // Extension number validation
  const extensionNumberInput = document.getElementById('extension_number');
  if (extensionNumberInput) {
    extensionNumberInput.addEventListener('blur', validateExtensionNumber);
  }
  
  // Initialize password strength meter
  const passwordInput = document.getElementById('password');
  if (passwordInput) {
    passwordInput.addEventListener('input', updatePasswordStrength);
  }
});

/**
 * Show confirmation dialog for FreeSWITCH service restart
 */
function confirmRestartFreeswitch(event) {
  // Check if service is already running
  const statusIndicator = document.querySelector('.status-indicator');
  const isRunning = statusIndicator && statusIndicator.classList.contains('status-up');
  
  // Change message based on service status
  let confirmMessage = 'Sei sicuro di voler avviare il servizio del centralino telefonico?';
  
  if (isRunning) {
    confirmMessage = 'Sei sicuro di voler riavviare il servizio del centralino telefonico? Tutte le chiamate attive verranno interrotte.';
  }
  
  if (confirm(confirmMessage)) {
    restartFreeswitchService();
  }
}

/**
 * Restart FreeSWITCH service via API
 */
function restartFreeswitchService() {
  // Determine which button was clicked (either the header button or the in-page button)
  const headerBtn = document.getElementById('restartFreeswitch');
  const inPageBtn = document.getElementById('startFreeswitchBtn');
  
  let clickedBtn = headerBtn; // Default to header button
  
  // If the in-page button exists and is visible, use it for UI updates
  if (inPageBtn && inPageBtn.offsetParent !== null) {
    clickedBtn = inPageBtn;
  }
  
  if (clickedBtn) {
    // Disable both buttons to prevent multiple clicks
    if (headerBtn) headerBtn.disabled = true;
    if (inPageBtn) inPageBtn.disabled = true;
    
    // Store original text and show loading state
    const originalText = clickedBtn.innerHTML;
    clickedBtn.innerHTML = '<span class="loader"></span> Avvio in corso...';
    
    // Call API to restart FreeSWITCH
    fetch('/freeswitch/restart', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Show success message
        showAlert('Centralino avviato con successo.', 'success');
        
        // After a delay, refresh the page to show updated status
        setTimeout(() => {
          window.location.reload();
        }, 3000);
      } else {
        // Show error message
        showAlert('Errore durante l\'avvio del centralino: ' + data.message, 'danger');
        
        // Reset button states
        if (headerBtn) {
          headerBtn.innerHTML = headerBtn === clickedBtn ? originalText : headerBtn.innerHTML;
          headerBtn.disabled = false;
        }
        if (inPageBtn) {
          inPageBtn.innerHTML = inPageBtn === clickedBtn ? originalText : inPageBtn.innerHTML;
          inPageBtn.disabled = false;
        }
      }
    })
    .catch(error => {
      console.error('Error starting PBX:', error);
      showAlert('Errore durante l\'avvio del centralino.', 'danger');
      
      // Reset button states
      if (headerBtn) {
        headerBtn.innerHTML = headerBtn === clickedBtn ? originalText : headerBtn.innerHTML;
        headerBtn.disabled = false;
      }
      if (inPageBtn) {
        inPageBtn.innerHTML = inPageBtn === clickedBtn ? originalText : inPageBtn.innerHTML;
        inPageBtn.disabled = false;
      }
    });
  }
}

/**
 * Show confirmation dialog for extension deletion
 * @param {Event} event - Click event
 */
function confirmDeleteExtension(event) {
  const btn = event.currentTarget;
  const extensionId = btn.getAttribute('data-id');
  const extensionNumber = btn.getAttribute('data-number');
  
  if (confirm(`Sei sicuro di voler eliminare l'estensione ${extensionNumber}? Questa azione non può essere annullata.`)) {
    // Submit the delete form
    const form = document.getElementById(`deleteExtensionForm${extensionId}`);
    if (form) {
      form.submit();
    }
  }
}

/**
 * Show confirmation dialog for trunk deletion
 * @param {Event} event - Click event
 */
function confirmDeleteTrunk(event) {
  const btn = event.currentTarget;
  const trunkId = btn.getAttribute('data-id');
  const trunkName = btn.getAttribute('data-name');
  
  if (confirm(`Sei sicuro di voler eliminare il trunk SIP "${trunkName}"? Questa azione non può essere annullata.`)) {
    // Submit the delete form
    const form = document.getElementById(`deleteTrunkForm${trunkId}`);
    if (form) {
      form.submit();
    }
  }
}

/**
 * Toggle voicemail configuration fields visibility
 */
function toggleVoicemailFields() {
  const voicemailEnabled = document.getElementById('voicemail_enabled');
  if (!voicemailEnabled) return;
  
  const voicemailFields = document.getElementById('voicemailFields');
  if (voicemailFields) {
    if (voicemailEnabled.checked) {
      voicemailFields.classList.remove('d-none');
      // Make PIN required
      const pinInput = document.getElementById('voicemail_pin');
      if (pinInput) {
        pinInput.required = true;
      }
    } else {
      voicemailFields.classList.add('d-none');
      // Remove required attribute
      const pinInput = document.getElementById('voicemail_pin');
      if (pinInput) {
        pinInput.required = false;
      }
    }
  }
}

/**
 * Toggle password field visibility
 * @param {Event} event - Click event
 */
function togglePasswordVisibility(event) {
  const btn = event.currentTarget;
  const targetId = btn.getAttribute('data-target');
  const passwordField = document.getElementById(targetId);
  
  if (passwordField) {
    if (passwordField.type === 'password') {
      passwordField.type = 'text';
      btn.innerHTML = '<i data-feather="eye-off"></i>';
    } else {
      passwordField.type = 'password';
      btn.innerHTML = '<i data-feather="eye"></i>';
    }
    
    // Re-initialize feather icons
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
  }
}

/**
 * Validate extension number format
 * @param {Event} event - Blur event
 */
function validateExtensionNumber(event) {
  const input = event.target;
  const value = input.value.trim();
  
  // Extension should be numeric and typically 3-6 digits
  const extensionRegex = /^\d{3,6}$/;
  
  if (!extensionRegex.test(value)) {
    input.classList.add('is-invalid');
    
    // Create or update validation message
    let feedbackEl = input.nextElementSibling;
    if (!feedbackEl || !feedbackEl.classList.contains('invalid-feedback')) {
      feedbackEl = document.createElement('div');
      feedbackEl.classList.add('invalid-feedback');
      input.parentNode.insertBefore(feedbackEl, input.nextSibling);
    }
    feedbackEl.textContent = 'Numero estensione non valido. Deve essere un numero composto da 3-6 cifre.';
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
 * Update password strength meter
 * @param {Event} event - Input event
 */
function updatePasswordStrength(event) {
  const password = event.target.value;
  const meterEl = document.getElementById('passwordStrength');
  
  if (!meterEl) return;
  
  // Password strength criteria
  const criteria = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[^A-Za-z0-9]/.test(password)
  };
  
  // Calculate strength score (0-4)
  const score = Object.values(criteria).filter(Boolean).length;
  
  // Update meter appearance
  meterEl.style.width = `${score * 25}%`;
  
  // Set color based on score
  if (score < 2) {
    meterEl.className = 'progress-bar bg-danger';
    meterEl.textContent = 'Debole';
  } else if (score < 4) {
    meterEl.className = 'progress-bar bg-warning';
    meterEl.textContent = 'Media';
  } else {
    meterEl.className = 'progress-bar bg-success';
    meterEl.textContent = 'Forte';
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
