// Setup wizard functionality
document.addEventListener('DOMContentLoaded', function() {
    // Connection type selection logic
    const internetTypeSelect = document.getElementById('internet_type');
    const staticFields = document.getElementById('static-ip-fields');
    const pppoeFields = document.getElementById('pppoe-fields');
    
    if (internetTypeSelect) {
        internetTypeSelect.addEventListener('change', function() {
            const selectedType = this.value;
            
            // Hide all connection type specific fields
            if (staticFields) staticFields.style.display = 'none';
            if (pppoeFields) pppoeFields.style.display = 'none';
            
            // Show only the relevant fields for the selected connection type
            if (selectedType === 'static' && staticFields) {
                staticFields.style.display = 'block';
            } else if (selectedType === 'pppoe' && pppoeFields) {
                pppoeFields.style.display = 'block';
            }
        });
        
        // Trigger the change event to set initial visibility
        internetTypeSelect.dispatchEvent(new Event('change'));
    }
    
    // WiFi settings toggle
    const wifiEnabledCheckbox = document.getElementById('wifi_enabled');
    const wifiSettingsDiv = document.getElementById('wifi-settings');
    
    if (wifiEnabledCheckbox && wifiSettingsDiv) {
        wifiEnabledCheckbox.addEventListener('change', function() {
            wifiSettingsDiv.style.display = this.checked ? 'block' : 'none';
        });
        
        // Set initial state
        wifiSettingsDiv.style.display = wifiEnabledCheckbox.checked ? 'block' : 'none';
    }
    
    // FreeSWITCH setup toggle
    const freeswitchEnabledCheckbox = document.getElementById('enable_freeswitch');
    const freeswitchSettingsDiv = document.getElementById('freeswitch-settings');
    
    if (freeswitchEnabledCheckbox && freeswitchSettingsDiv) {
        freeswitchEnabledCheckbox.addEventListener('change', function() {
            freeswitchSettingsDiv.style.display = this.checked ? 'block' : 'none';
        });
        
        // Set initial state
        freeswitchSettingsDiv.style.display = freeswitchEnabledCheckbox.checked ? 'block' : 'none';
    }

    // Trunk settings toggle
    const trunkEnabledCheckbox = document.getElementById('trunk_enabled');
    const trunkSettingsDiv = document.getElementById('trunk-settings');
    
    if (trunkEnabledCheckbox && trunkSettingsDiv) {
        trunkEnabledCheckbox.addEventListener('change', function() {
            trunkSettingsDiv.style.display = this.checked ? 'block' : 'none';
        });
        
        // Set initial state
        trunkSettingsDiv.style.display = trunkEnabledCheckbox.checked ? 'block' : 'none';
    }
    
    // Previous step button
    const prevButton = document.getElementById('prev-step');
    if (prevButton) {
        prevButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.history.back();
        });
    }
    
    // Form validation
    const wizardForms = document.querySelectorAll('.wizard-form');
    wizardForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Progress tracker
    const wizardSteps = document.querySelectorAll('.wizard-step');
    const currentStep = document.querySelector('.wizard-step.active');
    
    if (wizardSteps.length && currentStep) {
        const currentIndex = Array.from(wizardSteps).indexOf(currentStep);
        
        // Mark previous steps as completed
        for (let i = 0; i < currentIndex; i++) {
            wizardSteps[i].classList.add('completed');
        }
    }
});
