from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
import subprocess
import threading
import os
import time
import logging

# Creazione del blueprint
freeswitch_install_bp = Blueprint('freeswitch_install', __name__)

# Variabili globali per tracciare lo stato dell'installazione
installation_status = {
    'in_progress': False,
    'complete': False,
    'success': False,
    'log': [],
    'start_time': None,
    'end_time': None,
    'method': None
}

def reset_installation_status():
    """Resetta lo stato dell'installazione."""
    global installation_status
    installation_status = {
        'in_progress': False,
        'complete': False,
        'success': False,
        'log': [],
        'start_time': None,
        'end_time': None,
        'method': None
    }

def run_installation(method):
    """Esegue l'installazione di FreeSWITCH come thread separato."""
    global installation_status
    
    # Inizializzazione dello stato
    reset_installation_status()
    installation_status['in_progress'] = True
    installation_status['start_time'] = time.time()
    installation_status['method'] = method
    
    try:
        # Determinazione dello script da eseguire
        if method == 'repository':
            script_path = '/opt/evorouter/scripts/install_freeswitch.sh'
        else:  # method == 'source'
            script_path = '/opt/evorouter/scripts/install_freeswitch_from_source.sh'
        
        # Verifica se lo script esiste
        if not os.path.exists(script_path):
            # Creazione della directory se non esiste
            os.makedirs('/opt/evorouter/scripts', exist_ok=True)
            
            # Copia dello script dalla directory corrente
            if method == 'repository':
                subprocess.run(['cp', 'install_freeswitch.sh', script_path], check=True)
            else:
                subprocess.run(['cp', 'install_freeswitch_from_source.sh', script_path], check=True)
            
            # Rendi lo script eseguibile
            subprocess.run(['chmod', '+x', script_path], check=True)
        
        # Esecuzione dello script
        process = subprocess.Popen(
            ['bash', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Lettura dell'output in tempo reale
        for line in process.stdout:
            line = line.strip()
            if line:
                installation_status['log'].append(line)
                logging.info(f"FreeSWITCH Installation: {line}")
        
        # Attendi il completamento del processo
        return_code = process.wait()
        
        # Aggiornamento dello stato
        installation_status['complete'] = True
        installation_status['success'] = (return_code == 0)
        installation_status['end_time'] = time.time()
        
        if installation_status['success']:
            logging.info("FreeSWITCH installato con successo.")
        else:
            logging.error(f"Installazione di FreeSWITCH fallita con codice: {return_code}")
    
    except Exception as e:
        installation_status['log'].append(f"Errore durante l'installazione: {str(e)}")
        installation_status['complete'] = True
        installation_status['success'] = False
        installation_status['end_time'] = time.time()
        logging.exception("Errore durante l'installazione di FreeSWITCH")

@freeswitch_install_bp.route('/freeswitch/install', methods=['GET'])
@login_required
def install_page():
    """Visualizza la pagina di installazione di FreeSWITCH."""
    # Verifica se FreeSWITCH è già installato
    freeswitch_installed = False
    try:
        result = subprocess.run(['which', 'freeswitch'], capture_output=True, text=True)
        freeswitch_installed = (result.returncode == 0)
    except Exception:
        pass
    
    return render_template(
        'freeswitch/install.html',
        installation_status=installation_status,
        freeswitch_installed=freeswitch_installed
    )

@freeswitch_install_bp.route('/freeswitch/start_install', methods=['POST'])
@login_required
def start_install():
    """Avvia il processo di installazione di FreeSWITCH."""
    method = request.form.get('method', 'repository')
    
    if installation_status['in_progress']:
        flash('Un\'installazione è già in corso. Attendere il completamento.', 'warning')
        return redirect(url_for('freeswitch_install.install_page'))
    
    # Avvio del thread di installazione
    install_thread = threading.Thread(target=run_installation, args=(method,))
    install_thread.daemon = True
    install_thread.start()
    
    flash(f'Installazione di FreeSWITCH avviata con il metodo: {method}', 'info')
    return redirect(url_for('freeswitch_install.install_page'))

@freeswitch_install_bp.route('/freeswitch/install_status', methods=['GET'])
@login_required
def get_install_status():
    """API per ottenere lo stato corrente dell'installazione."""
    return jsonify(installation_status)

@freeswitch_install_bp.route('/freeswitch/reset_install', methods=['POST'])
@login_required
def reset_install():
    """Resetta lo stato dell'installazione."""
    reset_installation_status()
    flash('Stato dell\'installazione resettato.', 'info')
    return redirect(url_for('freeswitch_install.install_page'))