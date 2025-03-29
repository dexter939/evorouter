/**
 * Network configuration wizard for Banana Pi BPI-R4 Router OS
 * Guides users through step-by-step network setup
 */

// Wizard current step
let currentStep = 1;
const totalSteps = 4;

// Initialize wizard functionality
document.addEventListener('DOMContentLoaded', function() {
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Show first step
  showStep(currentStep);
  
  // Add listeners for next/prev buttons
  const nextButtons = document.querySelectorAll('.wizard-next-btn');
  const prevButtons = document.querySelectorAll('.wizard-prev-btn');
  
  nextButtons.forEach(btn => {
    btn.addEventListener('click', nextStep);
  });
  
  prevButtons.forEach(btn => {
    btn.addEventListener('click', prevStep);
  });
  
  // Add listeners for WAN mode selection
  const wanModeRadios = document.querySelectorAll('input[name="wan_mode"]');
  if (wanModeRadios.length > 0) {
    wanModeRadios.forEach(radio => {
      radio.addEventListener('change', toggleWanFields);
    });
    // Initial toggle based on selected mode
    toggleWanFields();
  }
  
  // Add listeners for DHCP server toggle
  const dhcpToggle = document.getElementById('dhcp_enabled');
  if (dhcpToggle) {
    dhcpToggle.addEventListener('change', toggleDhcpFields);
    // Initial toggle based on current state
    toggleDhcpFields();
  }
  
  // Add validation for IP address fields
  const ipInputs = document.querySelectorAll('input[data-validate="ip"]');
  if (ipInputs.length > 0) {
    ipInputs.forEach(input => {
      input.addEventListener('blur', validateIPAddress);
    });
  }
  
  // Add form submit handler
  const wizardForm = document.getElementById('wizardForm');
  if (wizardForm) {
    wizardForm.addEventListener('submit', function(event) {
      if (!validateForm()) {
        event.preventDefault();
      } else {
        // Show loading overlay during form submission
        showLoadingOverlay('Configurazione di rete in corso...');
      }
    });
  }
});

/**
 * Show specified wizard step
 * @param {number} step - Step number to show
 */
function showStep(step) {
  // Hide all steps
  const steps = document.querySelectorAll('.wizard-step-content');
  steps.forEach(stepEl => {
    stepEl.style.display = 'none';
  });
  
  // Show current step
  const currentStepEl = document.getElementById(`wizardStep${step}`);
  if (currentStepEl) {
    currentStepEl.style.display = 'block';
  }
  
  // Update progress bar
  updateProgress(step);
  
  // Update step indicators
  updateStepIndicators(step);
}

/**
 * Move to next wizard step
 */
function nextStep() {
  // Validate current step before proceeding
  if (!validateStep(currentStep)) {
    return;
  }
  
  // If on last step, submit form
  if (currentStep >= totalSteps) {
    const wizardForm = document.getElementById('wizardForm');
    if (wizardForm) {
      wizardForm.submit();
    }
    return;
  }
  
  // Increment step and display
  currentStep++;
  showStep(currentStep);
  
  // Scroll to top of step
  window.scrollTo(0, 0);
}

/**
 * Move to previous wizard step
 */
function prevStep() {
  if (currentStep <= 1) return;
  
  currentStep--;
  showStep(currentStep);
  
  // Scroll to top of step
  window.scrollTo(0, 0);
}

/**
 * Update progress bar
 * @param {number} step - Current step
 */
function updateProgress(step) {
  const progressBar = document.getElementById('wizardProgress');
  if (progressBar) {
    const percent = ((step - 1) / (totalSteps - 1)) * 100;
    progressBar.style.width = `${percent}%`;
    progressBar.setAttribute('aria-valuenow', percent);
  }
}

/**
 * Update step indicators
 * @param {number} currentStep - Current step
 */
function updateStepIndicators(currentStep) {
  const stepIndicators = document.querySelectorAll('.wizard-step');
  stepIndicators.forEach((indicator, index) => {
    const stepNum = index + 1;
    
    // Remove all status classes
    indicator.classList.remove('active', 'completed');
    
    if (stepNum === currentStep) {
      indicator.classList.add('active');
    } else if (stepNum < currentStep) {
      indicator.classList.add('completed');
    }
  });
}

/**
 * Toggle WAN configuration fields based on selected mode
 */
function toggleWanFields() {
  const selectedMode = document.querySelector('input[name="wan_mode"]:checked');
  if (!selectedMode) return;
  
  const wanStaticFields = document.getElementById('wanStaticFields');
  const wanPppoeFields = document.getElementById('wanPppoeFields');
  
  // Hide all fields first
  if (wanStaticFields) {
    wanStaticFields.classList.add('d-none');
    // Remove required attribute
    const staticInputs = wanStaticFields.querySelectorAll('input');
    staticInputs.forEach(input => {
      input.required = false;
    });
  }
  
  if (wanPppoeFields) {
    wanPppoeFields.classList.add('d-none');
    // Remove required attribute
    const pppoeInputs = wanPppoeFields.querySelectorAll('input');
    pppoeInputs.forEach(input => {
      input.required = false;
    });
  }
  
  // Show fields based on selected mode
  if (selectedMode.value === 'static' && wanStaticFields) {
    wanStaticFields.classList.remove('d-none');
    // Make fields required
    const inputs = wanStaticFields.querySelectorAll('input');
    inputs.forEach(input => {
      // Don't make DNS servers required
      if (input.id !== 'wan_dns') {
        input.required = true;
      }
    });
  } else if (selectedMode.value === 'pppoe' && wanPppoeFields) {
    wanPppoeFields.classList.remove('d-none');
    // Make username and password required, but not service name or DNS
    const usernameInput = wanPppoeFields.querySelector('#wan_pppoe_username');
    const passwordInput = wanPppoeFields.querySelector('#wan_pppoe_password');
    if (usernameInput) usernameInput.required = true;
    if (passwordInput) passwordInput.required = true;
  }
}

/**
 * Toggle DHCP server configuration fields
 */
function toggleDhcpFields() {
  const dhcpEnabled = document.getElementById('dhcp_enabled');
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
    return false;
  } else {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    
    // Remove validation message if exists
    const feedbackEl = input.nextElementSibling;
    if (feedbackEl && feedbackEl.classList.contains('invalid-feedback')) {
      feedbackEl.remove();
    }
    return true;
  }
}

/**
 * Validate current step before proceeding
 * @param {number} step - Current step
 * @returns {boolean} Validation result
 */
function validateStep(step) {
  // Get visible inputs in current step
  const stepEl = document.getElementById(`wizardStep${step}`);
  if (!stepEl) return true;
  
  const visibleInputs = Array.from(stepEl.querySelectorAll('input, select, textarea'))
    .filter(el => {
      // Skip hidden elements and those in hidden containers
      if (el.type === 'hidden') return false;
      if (window.getComputedStyle(el).display === 'none') return false;
      if (el.closest('.d-none')) return false;
      return true;
    });
  
  let isValid = true;
  
  // Check required fields
  visibleInputs.forEach(input => {
    if (input.required && !input.value.trim()) {
      isValid = false;
      input.classList.add('is-invalid');
      
      // Create validation message if doesn't exist
      let feedbackEl = input.nextElementSibling;
      if (!feedbackEl || !feedbackEl.classList.contains('invalid-feedback')) {
        feedbackEl = document.createElement('div');
        feedbackEl.classList.add('invalid-feedback');
        input.parentNode.insertBefore(feedbackEl, input.nextSibling);
      }
      feedbackEl.textContent = 'Questo campo è obbligatorio';
    }
  });
  
  // Validate IP addresses
  const ipInputs = stepEl.querySelectorAll('input[data-validate="ip"]:not(.d-none)');
  ipInputs.forEach(input => {
    if (input.value.trim() && !validateIPAddress({ target: input })) {
      isValid = false;
    }
  });
  
  // Specific validation for step 2 (LAN setup)
  if (step === 2) {
    // Make sure LAN and WAN subnets don't conflict
    const lanIp = document.getElementById('lan_ip')?.value;
    const lanSubnet = document.getElementById('lan_subnet')?.value;
    const wanIp = document.getElementById('wan_ip')?.value;
    
    if (lanIp && lanSubnet && wanIp && document.querySelector('input[name="wan_mode"]:checked')?.value === 'static') {
      // This is a simplified check - in a real implementation, you'd need to check subnet overlap
      const lanFirstThreeOctets = lanIp.split('.').slice(0, 3).join('.');
      const wanFirstThreeOctets = wanIp.split('.').slice(0, 3).join('.');
      
      if (lanFirstThreeOctets === wanFirstThreeOctets) {
        isValid = false;
        showAlert('La rete LAN non può utilizzare la stessa sottorete della WAN.', 'danger');
      }
    }
  }
  
  // Specific validation for step 3 (DHCP setup)
  if (step === 3 && document.getElementById('dhcp_enabled')?.checked) {
    const dhcpStart = document.getElementById('dhcp_start')?.value;
    const dhcpEnd = document.getElementById('dhcp_end')?.value;
    const lanIp = document.getElementById('lan_ip')?.value;
    
    if (dhcpStart && dhcpEnd && lanIp) {
      // Simplified check - in a real implementation, you'd need more comprehensive validation
      const lanPrefix = lanIp.split('.').slice(0, 3).join('.');
      const startPrefix = dhcpStart.split('.').slice(0, 3).join('.');
      const endPrefix = dhcpEnd.split('.').slice(0, 3).join('.');
      
      if (startPrefix !== lanPrefix || endPrefix !== lanPrefix) {
        isValid = false;
        showAlert('L\'intervallo DHCP deve essere nella stessa sottorete dell\'indirizzo LAN.', 'danger');
      }
    }
  }
  
  if (!isValid) {
    showAlert('Si prega di correggere gli errori prima di continuare.', 'danger');
  }
  
  return isValid;
}

/**
 * Validate entire form before submission
 * @returns {boolean} Validation result
 */
function validateForm() {
  let isValid = true;
  
  // Validate each step
  for (let i = 1; i <= totalSteps; i++) {
    if (!validateStep(i)) {
      isValid = false;
      currentStep = i;
      showStep(i);
      break;
    }
  }
  
  return isValid;
}

/**
 * Show loading overlay during form submission
 * @param {string} message - Loading message to display
 */
function showLoadingOverlay(message) {
  const overlay = document.createElement('div');
  overlay.className = 'position-fixed w-100 h-100 d-flex align-items-center justify-content-center';
  overlay.style.top = '0';
  overlay.style.left = '0';
  overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
  overlay.style.zIndex = '9999';
  
  overlay.innerHTML = `
    <div class="bg-white p-4 rounded shadow text-center">
      <div class="spinner-border text-primary mb-3" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <div class="text-dark">${message}</div>
    </div>
  `;
  
  document.body.appendChild(overlay);
}

/**
 * Show alert message
 * @param {string} message - Alert message text
 * @param {string} type - Alert type (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
  // Create alert container if it doesn't exist
  let alertContainer = document.getElementById('wizardAlerts');
  if (!alertContainer) {
    alertContainer = document.createElement('div');
    alertContainer.id = 'wizardAlerts';
    const wizardForm = document.getElementById('wizardForm');
    if (wizardForm) {
      wizardForm.parentNode.insertBefore(alertContainer, wizardForm);
    } else {
      document.body.appendChild(alertContainer);
    }
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
