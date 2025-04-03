"""
Modulo per le route relative ai test di velocità della rete.
Fornisce endpoint per eseguire test di velocità e visualizzare i risultati.
"""

from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
import json
import os
from datetime import datetime
import time
import threading
import logging

from utils.speed_test import (
    run_comprehensive_test,
    get_ping_stats,
    run_speed_test,
    measure_jitter,
    check_internet_connectivity,
    get_network_interfaces
)

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Percorso per salvare i risultati dei test
RESULTS_PATH = "instance/speed_tests"

# Creazione del blueprint
speed_test_bp = Blueprint("speed_test", __name__, url_prefix="/speed-test")

# Test in corso e loro stato
active_tests = {}

def save_test_result(result, test_id=None):
    """
    Salva i risultati del test in un file JSON.
    
    Args:
        result (dict): Risultati del test da salvare
        test_id (str): ID opzionale del test
    
    Returns:
        str: Path del file salvato
    """
    if not os.path.exists(RESULTS_PATH):
        os.makedirs(RESULTS_PATH)
    
    test_id = test_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(RESULTS_PATH, f"test_{test_id}.json")
    
    with open(file_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return file_path

def get_saved_tests(limit=10):
    """
    Recupera i test salvati.
    
    Args:
        limit (int): Numero massimo di test da recuperare
        
    Returns:
        list: Lista di test salvati
    """
    if not os.path.exists(RESULTS_PATH):
        return []
    
    files = [f for f in os.listdir(RESULTS_PATH) if f.endswith('.json')]
    files.sort(reverse=True)  # Ordina per data (più recenti prima)
    
    tests = []
    for f in files[:limit]:
        try:
            with open(os.path.join(RESULTS_PATH, f), 'r') as file:
                test = json.load(file)
                # Aggiunge il nome del file senza estensione come ID
                test['id'] = f.replace('.json', '')
                tests.append(test)
        except Exception as e:
            logger.error(f"Errore nel caricamento del test {f}: {str(e)}")
    
    return tests

@speed_test_bp.route("/")
@login_required
def index():
    """
    Pagina principale per i test di velocità.
    """
    # Recupera i test recenti
    recent_tests = get_saved_tests(5)
    
    # Recupera le interfacce di rete
    interfaces = get_network_interfaces()
    
    return render_template(
        "speed_test/index.html",
        recent_tests=recent_tests,
        interfaces=interfaces
    )

@speed_test_bp.route("/run", methods=["POST"])
@login_required
def run_test():
    """
    Endpoint per avviare un test di velocità.
    """
    test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    active_tests[test_id] = {"status": "running", "progress": 0}
    
    def background_task():
        try:
            # Aggiorna stato
            active_tests[test_id]["progress"] = 10
            active_tests[test_id]["status_message"] = "Controllo connettività..."
            
            # Controllo della connettività
            connectivity = check_internet_connectivity()
            if not connectivity["connectivity"]:
                active_tests[test_id]["status"] = "error"
                active_tests[test_id]["status_message"] = "Nessuna connessione Internet rilevata"
                active_tests[test_id]["result"] = connectivity
                return
            
            # Ping
            active_tests[test_id]["progress"] = 20
            active_tests[test_id]["status_message"] = "Esecuzione test di ping..."
            ping_result = get_ping_stats()
            
            # Jitter
            active_tests[test_id]["progress"] = 40
            active_tests[test_id]["status_message"] = "Misurazione jitter..."
            jitter_result = measure_jitter()
            
            # Test di velocità
            active_tests[test_id]["progress"] = 60
            active_tests[test_id]["status_message"] = "Misurazione velocità download..."
            
            # Test completo
            active_tests[test_id]["progress"] = 80
            active_tests[test_id]["status_message"] = "Misurazione velocità upload..."
            test_result = run_comprehensive_test()
            
            # Salva risultato
            active_tests[test_id]["progress"] = 95
            active_tests[test_id]["status_message"] = "Salvataggio risultati..."
            save_test_result(test_result, test_id)
            
            # Completa
            active_tests[test_id]["status"] = "completed"
            active_tests[test_id]["progress"] = 100
            active_tests[test_id]["status_message"] = "Test completato"
            active_tests[test_id]["result"] = test_result
            
        except Exception as e:
            logger.error(f"Errore durante l'esecuzione del test: {str(e)}")
            active_tests[test_id]["status"] = "error"
            active_tests[test_id]["status_message"] = f"Errore: {str(e)}"
    
    # Avvia test in background
    thread = threading.Thread(target=background_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "test_id": test_id,
        "status": "started"
    })

@speed_test_bp.route("/status/<test_id>")
@login_required
def test_status(test_id):
    """
    Endpoint per controllare lo stato di un test.
    """
    if test_id not in active_tests:
        return jsonify({
            "status": "not_found",
            "message": "Test non trovato"
        }), 404
    
    status = active_tests[test_id]
    
    # Se il test è completato o in errore, includiamo il risultato
    if status["status"] in ["completed", "error"] and "result" in status:
        result = status["result"]
    else:
        result = None
    
    return jsonify({
        "test_id": test_id,
        "status": status["status"],
        "progress": status["progress"],
        "status_message": status.get("status_message", ""),
        "result": result
    })

@speed_test_bp.route("/history")
@login_required
def history():
    """
    Pagina per visualizzare la cronologia dei test.
    """
    # Recupera tutti i test salvati
    all_tests = get_saved_tests(50)
    
    return render_template(
        "speed_test/history.html",
        tests=all_tests
    )

@speed_test_bp.route("/download/<test_id>")
@login_required
def download_results(test_id):
    """
    Endpoint per scaricare i risultati di un test.
    """
    file_path = os.path.join(RESULTS_PATH, f"test_{test_id}.json")
    
    if not os.path.exists(file_path):
        return jsonify({
            "status": "error",
            "message": "Test non trovato"
        }), 404
    
    try:
        with open(file_path, 'r') as f:
            result = json.load(f)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Errore nel caricamento del test: {str(e)}"
        }), 500

@speed_test_bp.route("/quick-test")
@login_required
def quick_test():
    """
    Esegue un rapido test di connettività e ping.
    """
    connectivity = check_internet_connectivity()
    
    if connectivity["connectivity"]:
        ping = get_ping_stats(count=5)
    else:
        ping = {"success": False, "error": "Nessuna connessione Internet"}
    
    return jsonify({
        "connectivity": connectivity,
        "ping": ping,
        "timestamp": datetime.now().isoformat()
    })

@speed_test_bp.route("/compare", methods=["GET", "POST"])
@login_required
def compare_tests():
    """
    Pagina per confrontare più test di velocità.
    """
    if request.method == "POST":
        test_ids = request.form.getlist("test_ids")
        tests = []
        
        for test_id in test_ids:
            file_path = os.path.join(RESULTS_PATH, f"test_{test_id}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        test = json.load(f)
                        test['id'] = test_id
                        tests.append(test)
                except Exception as e:
                    logger.error(f"Errore nel caricamento del test {test_id}: {str(e)}")
        
        return render_template(
            "speed_test/compare.html",
            tests=tests,
            selected_ids=test_ids
        )
    
    # GET: mostra la pagina per selezionare i test da confrontare
    all_tests = get_saved_tests(50)
    
    return render_template(
        "speed_test/select_compare.html",
        tests=all_tests
    )