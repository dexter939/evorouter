// Variabili globali
let currentStep = 1;
let extensionCount = 1;
const totalSteps = 5;

// Inizializzazione quando il documento è caricato
document.addEventListener('DOMContentLoaded', function() {
  // Inizializza icone Feather
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Mostra il primo step
  showStep(currentStep);
  
  // Genera una password sicura per l'interno iniziale
  document.querySelector('input[name="ext_password_1"]').value = generateSecurePassword();
  
  // Aggiungi listener per pulsanti avanti/indietro
  document.getElementById('nextBtn').addEventListener('click', nextStep);
  document.getElementById('prevBtn').addEventListener('click', prevStep);
  
  // Aggiungi listener per il pulsante di aggiunta interno
  document.getElementById('add-extension').addEventListener('click', addExtension);
  
  // Aggiungi listener per il toggle del trunk SIP
  document.getElementById('configure_trunk').addEventListener('change', toggleTrunkConfig);
  
  // Aggiungi listener per il toggle della voicemail
  document.getElementById('voicemail_enabled').addEventListener('change', toggleVoicemailSettings);
  
  // Aggiungi listener per il toggle della registrazione chiamate
  document.getElementById('call_recording_enabled').addEventListener('change', toggleRecordingSettings);
  
  // Inizializza i toggle in base allo stato iniziale
  toggleTrunkConfig();
  toggleVoicemailSettings();
  toggleRecordingSettings();
  
  // Aggiungi listener per gli input che influenzano il riepilogo
  addSummaryListeners();
});

// Mostra lo step specifico e aggiorna gli indicatori
function showStep(step) {
  // Nascondi tutti gli step
  const steps = document.querySelectorAll('.wizard-step');
  steps.forEach(s => {
    s.style.display = 'none';
  });
  
  // Mostra lo step corrente
  document.getElementById(`step-${step}`).style.display = 'block';
  
  // Aggiorna la variabile hidden per tracciare lo step corrente
  document.getElementById('current_step').value = step;
  
  // Aggiorna gli indicatori di step
  updateStepIndicators(step);
  
  // Aggiorna i pulsanti di navigazione
  updateNavigationButtons(step);
  
  // Se è l'ultimo step, aggiorna il riepilogo
  if (step === totalSteps) {
    updateSummary();
  }
}

// Aggiorna gli indicatori visivi degli step
function updateStepIndicators(currentStep) {
  // Resetta tutti gli indicatori
  const indicators = document.querySelectorAll('.wizard-step-indicator');
  indicators.forEach(indicator => {
    indicator.classList.remove('active', 'completed');
  });
  
  // Imposta gli step completati e lo step attivo
  for (let i = 1; i <= totalSteps; i++) {
    const indicator = document.getElementById(`step-indicator-${i}`);
    if (i < currentStep) {
      indicator.classList.add('completed');
    } else if (i === currentStep) {
      indicator.classList.add('active');
    }
  }
}

// Aggiorna lo stato dei pulsanti di navigazione
function updateNavigationButtons(step) {
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const submitBtn = document.getElementById('submitBtn');
  
  // Gestisci il pulsante "Indietro"
  if (step === 1) {
    prevBtn.style.visibility = 'hidden';
  } else {
    prevBtn.style.visibility = 'visible';
  }
  
  // Gestisci i pulsanti "Avanti" e "Applica"
  if (step === totalSteps) {
    nextBtn.style.display = 'none';
    submitBtn.style.display = 'block';
  } else {
    nextBtn.style.display = 'block';
    submitBtn.style.display = 'none';
  }
}

// Passa allo step successivo
function nextStep() {
  // Validazione dello step corrente
  if (!validateCurrentStep()) {
    return false;
  }
  
  // Passa allo step successivo se non siamo all'ultimo
  if (currentStep < totalSteps) {
    currentStep++;
    showStep(currentStep);
  }
}

// Torna allo step precedente
function prevStep() {
  if (currentStep > 1) {
    currentStep--;
    showStep(currentStep);
  }
}

// Valida lo step corrente prima di procedere
function validateCurrentStep() {
  const currentStepElement = document.getElementById(`step-${currentStep}`);
  const requiredInputs = currentStepElement.querySelectorAll('input[required]');
  
  // Verifica che tutti i campi obbligatori siano compilati
  let isValid = true;
  requiredInputs.forEach(input => {
    if (!input.value.trim()) {
      isValid = false;
      input.classList.add('is-invalid');
    } else {
      input.classList.remove('is-invalid');
    }
  });
  
  // Validazioni specifiche per ogni step
  switch(currentStep) {
    case 1: // Configurazione generale
      return validateStep1();
    case 2: // Configurazione interni
      return validateStep2() && isValid;
    case 3: // Configurazione trunk SIP
      return validateStep3() && isValid;
    case 4: // Configurazioni avanzate
      return validateStep4() && isValid;
    case 5: // Riepilogo e conferma
      return true; // Non c'è nulla da validare nel riepilogo
    default:
      return isValid;
  }
}

// Validazione step 1 (Configurazione generale)
function validateStep1() {
  const sipPort = parseInt(document.getElementById('sip_port').value);
  const rtpStart = parseInt(document.getElementById('rtp_port_start').value);
  const rtpEnd = parseInt(document.getElementById('rtp_port_end').value);
  
  let isValid = true;
  
  // Controlla che le porte siano nell'intervallo valido
  if (isNaN(sipPort) || sipPort < 1024 || sipPort > 65535) {
    document.getElementById('sip_port').classList.add('is-invalid');
    isValid = false;
  } else {
    document.getElementById('sip_port').classList.remove('is-invalid');
  }
  
  if (isNaN(rtpStart) || rtpStart < 1024 || rtpStart > 65535) {
    document.getElementById('rtp_port_start').classList.add('is-invalid');
    isValid = false;
  } else {
    document.getElementById('rtp_port_start').classList.remove('is-invalid');
  }
  
  if (isNaN(rtpEnd) || rtpEnd < 1024 || rtpEnd > 65535 || rtpEnd <= rtpStart) {
    document.getElementById('rtp_port_end').classList.add('is-invalid');
    isValid = false;
  } else {
    document.getElementById('rtp_port_end').classList.remove('is-invalid');
  }
  
  return isValid;
}

// Validazione step 2 (Configurazione interni)
function validateStep2() {
  let isValid = true;
  
  // Verifica che ci sia almeno un interno configurato
  if (extensionCount < 1) {
    showAlert('È necessario configurare almeno un interno telefonico.', 'danger');
    isValid = false;
  }
  
  // Verifica che i numeri degli interni siano unici
  const extNumbers = new Set();
  const extNumberInputs = document.querySelectorAll('input[name^="ext_number_"]');
  
  extNumberInputs.forEach(input => {
    const value = input.value.trim();
    if (value && extNumbers.has(value)) {
      input.classList.add('is-invalid');
      isValid = false;
      showAlert('I numeri degli interni devono essere unici.', 'danger');
    } else {
      extNumbers.add(value);
      input.classList.remove('is-invalid');
    }
  });
  
  return isValid;
}

// Validazione step 3 (Configurazione trunk SIP)
function validateStep3() {
  // Solo se il trunk è abilitato, valida i campi
  const configureTrunk = document.getElementById('configure_trunk').checked;
  
  if (configureTrunk) {
    const trunkHost = document.getElementById('trunk_host').value.trim();
    
    if (!trunkHost) {
      document.getElementById('trunk_host').classList.add('is-invalid');
      return false;
    } else {
      document.getElementById('trunk_host').classList.remove('is-invalid');
    }
    
    // Verifica che la porta trunk sia valida
    const trunkPort = parseInt(document.getElementById('trunk_port').value);
    if (isNaN(trunkPort) || trunkPort < 1 || trunkPort > 65535) {
      document.getElementById('trunk_port').classList.add('is-invalid');
      return false;
    } else {
      document.getElementById('trunk_port').classList.remove('is-invalid');
    }
  }
  
  return true;
}

// Validazione step 4 (Configurazioni avanzate)
function validateStep4() {
  const voicemailEnabled = document.getElementById('voicemail_enabled').checked;
  
  if (voicemailEnabled) {
    const email = document.getElementById('voicemail_email').value.trim();
    
    // Se l'email è specificata, verifica che sia valida
    if (email && !validateEmail(email)) {
      document.getElementById('voicemail_email').classList.add('is-invalid');
      return false;
    } else {
      document.getElementById('voicemail_email').classList.remove('is-invalid');
    }
  }
  
  return true;
}

// Aggiunge un nuovo interno al modulo
function addExtension() {
  extensionCount++;
  
  const extensionsList = document.getElementById('extensions-list');
  const newExtension = document.createElement('div');
  newExtension.className = 'card mb-3 extension-item';
  newExtension.innerHTML = `
    <div class="card-body">
      <div class="row g-3">
        <div class="col-md-3">
          <div class="form-floating">
            <input type="text" class="form-control" name="ext_number_${extensionCount}" value="${100 + extensionCount}" required>
            <label>Numero Interno</label>
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-floating">
            <input type="text" class="form-control" name="ext_name_${extensionCount}" value="Interno ${extensionCount}" required>
            <label>Nome</label>
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-floating">
            <input type="password" class="form-control" name="ext_password_${extensionCount}" value="${generateSecurePassword()}" required>
            <label>Password</label>
          </div>
        </div>
        <div class="col-md-1 d-flex align-items-center">
          <button type="button" class="btn btn-outline-danger remove-extension">
            <i data-feather="trash-2"></i>
          </button>
        </div>
      </div>
    </div>
  `;
  
  extensionsList.appendChild(newExtension);
  
  // Reinizializza le icone Feather nel nuovo elemento
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Aggiungi listener per il pulsante di rimozione
  const removeBtn = newExtension.querySelector('.remove-extension');
  removeBtn.addEventListener('click', function() {
    removeExtension(newExtension);
  });
}

// Rimuove un interno dal modulo
function removeExtension(extensionElement) {
  const extensionsList = document.getElementById('extensions-list');
  extensionsList.removeChild(extensionElement);
  
  // Aggiorna i nomi e gli indici degli interni rimanenti
  const extensionItems = document.querySelectorAll('.extension-item');
  extensionCount = extensionItems.length;
  
  // Se è rimasto solo un interno, disabilita il pulsante di rimozione
  if (extensionCount === 1) {
    document.querySelector('.remove-extension').disabled = true;
  }
}

// Mostra/nasconde la configurazione del trunk SIP
function toggleTrunkConfig() {
  const configureTrunk = document.getElementById('configure_trunk').checked;
  const trunkConfig = document.getElementById('trunk-config');
  
  if (configureTrunk) {
    trunkConfig.style.display = 'block';
  } else {
    trunkConfig.style.display = 'none';
  }
}

// Mostra/nasconde le impostazioni della voicemail
function toggleVoicemailSettings() {
  const voicemailEnabled = document.getElementById('voicemail_enabled').checked;
  const voicemailSettings = document.getElementById('voicemail-settings');
  
  if (voicemailEnabled) {
    voicemailSettings.style.display = 'flex';
  } else {
    voicemailSettings.style.display = 'none';
  }
}

// Mostra/nasconde le impostazioni della registrazione chiamate
function toggleRecordingSettings() {
  const recordingEnabled = document.getElementById('call_recording_enabled').checked;
  const recordingSettings = document.getElementById('recording-settings');
  
  if (recordingEnabled) {
    recordingSettings.style.display = 'flex';
  } else {
    recordingSettings.style.display = 'none';
  }
}

// Aggiorna il riepilogo prima della conferma
function updateSummary() {
  // Configurazione generale
  document.getElementById('summary-status').textContent = 
    document.getElementById('enabled').checked ? 'Abilitato' : 'Disabilitato';
  
  document.getElementById('summary-sip-port').textContent = 
    document.getElementById('sip_port').value;
  
  document.getElementById('summary-rtp-range').textContent = 
    `${document.getElementById('rtp_port_start').value}-${document.getElementById('rtp_port_end').value}`;
  
  // Interni configurati
  const summaryExtensions = document.getElementById('summary-extensions').querySelector('tbody');
  summaryExtensions.innerHTML = '';
  
  const extNumberInputs = document.querySelectorAll('input[name^="ext_number_"]');
  const extNameInputs = document.querySelectorAll('input[name^="ext_name_"]');
  
  for (let i = 0; i < extNumberInputs.length; i++) {
    const extNumber = extNumberInputs[i].value;
    const extName = extNameInputs[i].value;
    
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${extNumber}</td>
      <td>${extName}</td>
    `;
    
    summaryExtensions.appendChild(row);
  }
  
  // Trunk SIP
  const configureTrunk = document.getElementById('configure_trunk').checked;
  const trunkCard = document.getElementById('summary-trunk-card');
  const trunkContent = document.getElementById('summary-trunk-content');
  
  if (configureTrunk) {
    trunkCard.style.display = 'block';
    const trunkName = document.getElementById('trunk_name').value;
    const trunkHost = document.getElementById('trunk_host').value;
    const trunkPort = document.getElementById('trunk_port').value;
    const trunkUsername = document.getElementById('trunk_username').value;
    
    trunkContent.innerHTML = `
      <div class="row">
        <div class="col-md-6">
          <div class="mb-3">
            <strong>Nome:</strong> ${trunkName}
          </div>
          <div class="mb-3">
            <strong>Host:</strong> ${trunkHost}
          </div>
        </div>
        <div class="col-md-6">
          <div class="mb-3">
            <strong>Porta:</strong> ${trunkPort}
          </div>
          <div class="mb-3">
            <strong>Username:</strong> ${trunkUsername || 'Non specificato'}
          </div>
        </div>
      </div>
    `;
  } else {
    trunkCard.style.display = 'none';
  }
  
  // Funzionalità avanzate
  const voicemailEnabled = document.getElementById('voicemail_enabled').checked;
  document.getElementById('summary-voicemail').textContent = 
    voicemailEnabled ? 'Abilitato' : 'Disabilitato';
  
  if (voicemailEnabled) {
    document.getElementById('summary-voicemail-email-container').style.display = 'block';
    const voicemailEmail = document.getElementById('voicemail_email').value;
    document.getElementById('summary-voicemail-email').textContent = 
      voicemailEmail || 'Non configurata';
  } else {
    document.getElementById('summary-voicemail-email-container').style.display = 'none';
  }
  
  const recordingEnabled = document.getElementById('call_recording_enabled').checked;
  document.getElementById('summary-call-recording').textContent = 
    recordingEnabled ? 'Abilitato' : 'Disabilitato';
  
  const recordingDetailsContainer = document.getElementById('summary-recording-details-container');
  if (recordingEnabled) {
    recordingDetailsContainer.style.display = 'block';
    
    const recordInbound = document.getElementById('record_inbound').checked;
    const recordOutbound = document.getElementById('record_outbound').checked;
    
    let recordingDetails = [];
    if (recordInbound) recordingDetails.push('Chiamate in entrata');
    if (recordOutbound) recordingDetails.push('Chiamate in uscita');
    
    document.getElementById('summary-recording-details').textContent = 
      recordingDetails.join(', ');
  } else {
    recordingDetailsContainer.style.display = 'none';
  }
}

// Aggiunge listener agli input che influenzano il riepilogo
function addSummaryListeners() {
  // Quando gli input cambiano, aggiorniamo il riepilogo se siamo all'ultimo step
  const inputs = document.querySelectorAll('input, select');
  inputs.forEach(input => {
    input.addEventListener('change', () => {
      if (currentStep === totalSteps) {
        updateSummary();
      }
    });
  });
}

// Utility per generare una password sicura
function generateSecurePassword(length = 12) {
  const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+';
  let password = '';
  
  // Assicuriamoci che ci sia almeno un carattere da ogni categoria
  password += getRandomChar('ABCDEFGHIJKLMNOPQRSTUVWXYZ');
  password += getRandomChar('abcdefghijklmnopqrstuvwxyz');
  password += getRandomChar('0123456789');
  password += getRandomChar('!@#$%^&*()-_=+');
  
  // Completa il resto della password
  for (let i = 4; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * charset.length);
    password += charset[randomIndex];
  }
  
  // Mescola la password
  return shuffleString(password);
}

// Ottiene un carattere casuale da una stringa
function getRandomChar(charset) {
  const randomIndex = Math.floor(Math.random() * charset.length);
  return charset[randomIndex];
}

// Mescola una stringa
function shuffleString(str) {
  const array = str.split('');
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array.join('');
}

// Valida un indirizzo email
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// Mostra un messaggio di alert
function showAlert(message, type = 'info') {
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  const cardBody = document.querySelector('.card-body');
  cardBody.insertBefore(alertDiv, cardBody.firstChild);
  
  // Rimuovi automaticamente l'alert dopo 5 secondi
  setTimeout(() => {
    alertDiv.remove();
  }, 5000);
}