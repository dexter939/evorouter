import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required
from utils.system import (
    get_system_stats, reboot_system, shutdown_system,
    get_system_logs, clear_logs, run_diagnostic,
    get_installed_packages, check_for_updates, install_update
)
import io

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint
system_bp = Blueprint('system', __name__)

@system_bp.route('/')
@login_required
def index():
    """System overview page"""
    try:
        system_stats = get_system_stats()
        return render_template('system/index.html', 
                               active_page="system",
                               system_stats=system_stats)
    except Exception as e:
        logger.error(f"Error loading system overview: {str(e)}")
        flash("Si è verificato un errore nel caricamento delle informazioni di sistema.", "danger")
        return render_template('system/index.html', 
                               active_page="system",
                               error=True)

@system_bp.route('/reboot', methods=['POST'])
@login_required
def reboot():
    """Reboot the system"""
    try:
        reboot_system()
        return jsonify({'success': True, 'message': 'Sistema in riavvio...'})
    except Exception as e:
        logger.error(f"Error rebooting system: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore nel riavvio del sistema: {str(e)}'}), 500

@system_bp.route('/shutdown', methods=['POST'])
@login_required
def shutdown():
    """Shutdown the system"""
    try:
        shutdown_system()
        return jsonify({'success': True, 'message': 'Sistema in spegnimento...'})
    except Exception as e:
        logger.error(f"Error shutting down system: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore nello spegnimento del sistema: {str(e)}'}), 500

@system_bp.route('/logs')
@login_required
def logs():
    """View system logs"""
    try:
        log_type = request.args.get('type', 'system')
        lines = int(request.args.get('lines', 100))
        
        logs = get_system_logs(log_type, lines)
        
        return render_template('system/logs.html', 
                               active_page="system",
                               logs=logs,
                               current_log_type=log_type)
    except Exception as e:
        logger.error(f"Error loading system logs: {str(e)}")
        flash("Si è verificato un errore nel caricamento dei log di sistema.", "danger")
        return render_template('system/logs.html', 
                               active_page="system",
                               error=True)

@system_bp.route('/logs/clear', methods=['POST'])
@login_required
def clear_system_logs():
    """Clear system logs"""
    try:
        log_type = request.form.get('type', 'system')
        
        result = clear_logs(log_type)
        
        if result:
            flash(f"Log {log_type} cancellati con successo.", "success")
        else:
            flash(f"Errore nella cancellazione dei log {log_type}.", "danger")
            
        return redirect(url_for('system.logs', type=log_type))
    except Exception as e:
        logger.error(f"Error clearing logs: {str(e)}")
        flash(f"Errore nella cancellazione dei log: {str(e)}", "danger")
        return redirect(url_for('system.logs'))

@system_bp.route('/logs/download')
@login_required
def download_logs():
    """Download system logs as a file"""
    try:
        log_type = request.args.get('type', 'system')
        lines = int(request.args.get('lines', 1000))
        
        logs = get_system_logs(log_type, lines)
        
        # Create a file-like object to contain logs
        log_file = io.StringIO()
        for log in logs:
            log_file.write(f"{log['timestamp']} [{log['level']}] {log['message']}\n")
        
        log_file.seek(0)
        
        return send_file(
            io.BytesIO(log_file.read().encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=f"{log_type}_logs.txt"
        )
    except Exception as e:
        logger.error(f"Error downloading logs: {str(e)}")
        flash(f"Errore nel download dei log: {str(e)}", "danger")
        return redirect(url_for('system.logs', type=log_type))

@system_bp.route('/diagnostics')
@login_required
def diagnostics():
    """System diagnostics page"""
    try:
        return render_template('system/diagnostics.html', 
                               active_page="system")
    except Exception as e:
        logger.error(f"Error loading diagnostics page: {str(e)}")
        flash("Si è verificato un errore nel caricamento della pagina di diagnostica.", "danger")
        return redirect(url_for('system.index'))

@system_bp.route('/advanced_diagnostics')
@login_required
def advanced_diagnostics():
    """Advanced network diagnostics page"""
    try:
        return render_template('system/advanced_diagnostics.html', 
                              active_page="system")
    except Exception as e:
        logger.error(f"Error loading advanced diagnostics page: {str(e)}")
        flash("Si è verificato un errore nel caricamento della pagina di diagnostica avanzata.", "danger")
        return redirect(url_for('system.index'))

@system_bp.route('/diagnostics/run', methods=['POST'])
@login_required
def run_diagnostic_tool():
    """Run a diagnostic tool"""
    try:
        tool = request.form.get('tool')
        parameters = request.form.get('parameters', '')
        
        result = run_diagnostic(tool, parameters)
        
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Error running diagnostic tool: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore nell\'esecuzione del test diagnostico: {str(e)}'}), 500
        
@system_bp.route('/network/test', methods=['POST'])
@login_required
def run_network_test():
    """Run advanced network test"""
    try:
        test_type = request.form.get('test_type')
        target = request.form.get('target', '')
        options = request.form.get('options', '{}')
        
        if test_type == 'ping':
            # Test di ping
            host = target if target else '8.8.8.8'
            count = request.form.get('count', '5')
            size = request.form.get('size', '56')
            
            result = run_diagnostic('ping', f"-c {count} -s {size} {host}")
        
        elif test_type == 'traceroute':
            # Test di traceroute
            host = target if target else 'google.com'
            max_hop = request.form.get('max_hop', '20')
            
            result = run_diagnostic('traceroute', f"-m {max_hop} {host}")
        
        elif test_type == 'dns':
            # Test di risoluzione DNS
            domain = target if target else 'google.com'
            record_type = request.form.get('record_type', 'A')
            
            result = run_diagnostic('dig', f"{domain} {record_type}")
            
        elif test_type == 'speed':
            # Test di velocità
            server = request.form.get('server', 'auto')
            duration = request.form.get('duration', '10')
            
            # Simula un test di velocità
            import random
            import time
            
            time.sleep(2)  # Simulazione di test in corso
            
            download = random.uniform(30, 100)
            upload = random.uniform(10, 30)
            ping = random.uniform(10, 50)
            
            result = {
                'download': round(download, 2),
                'upload': round(upload, 2),
                'ping': round(ping, 2),
                'server': 'Milan, IT (TIM)',
                'isp': 'Telecom Italia'
            }
            
            return jsonify({'success': True, 'result': result})
        
        elif test_type == 'packet_loss':
            # Test di perdita di pacchetti
            host = target if target else '8.8.8.8'
            duration = request.form.get('duration', '30')
            interval = request.form.get('interval', '500')
            
            # Simula un test di perdita di pacchetti
            import random
            import time
            
            time.sleep(2)  # Simulazione di test in corso
            
            latency = random.uniform(15, 50)
            jitter = random.uniform(1, 8)
            packet_loss = random.uniform(0, 2)
            
            result = {
                'latency': round(latency, 2),
                'jitter': round(jitter, 2),
                'packet_loss': round(packet_loss, 2),
                'packets_sent': 50,
                'packets_received': round(50 - (50 * packet_loss / 100))
            }
            
            return jsonify({'success': True, 'result': result})
            
        elif test_type == 'port_check':
            # Verifica porta
            port = target
            protocol = request.form.get('protocol', 'tcp')
            
            # Simula una verifica porta
            import random
            
            is_open = random.random() > 0.7
            
            result = {
                'port': port,
                'protocol': protocol,
                'is_open': is_open,
                'service': get_service_for_port(port) if is_open else None
            }
            
            return jsonify({'success': True, 'result': result})
        
        else:
            return jsonify({'success': False, 'message': f'Tipo di test non supportato: {test_type}'}), 400
        
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Error running network test: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore nell\'esecuzione del test di rete: {str(e)}'}), 500
    
@system_bp.route('/network/devices', methods=['GET'])
@login_required
def get_connected_devices():
    """Get connected devices on the network"""
    try:
        from utils.network import get_connected_devices
        
        devices = get_connected_devices()
        return jsonify({'success': True, 'devices': devices})
    except Exception as e:
        logger.error(f"Error getting connected devices: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore nel recupero dei dispositivi connessi: {str(e)}'}), 500

@system_bp.route('/network/interfaces', methods=['GET'])
@login_required
def get_network_interfaces():
    """Get network interfaces status"""
    try:
        from utils.network import get_interfaces_status
        
        interfaces = get_interfaces_status()
        return jsonify({'success': True, 'interfaces': interfaces})
    except Exception as e:
        logger.error(f"Error getting interface status: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore nel recupero dello stato delle interfacce: {str(e)}'}), 500

@system_bp.route('/network/bandwidth', methods=['GET'])
@login_required
def get_bandwidth_usage():
    """Get bandwidth usage data"""
    try:
        interface = request.args.get('interface', 'all')
        period = request.args.get('period', '1h')
        
        # Simula dati di utilizzo della larghezza di banda
        import random
        import time
        from datetime import datetime, timedelta
        
        # Genera 30 punti dati
        now = datetime.now()
        timestamps = [(now - timedelta(minutes=i)).strftime('%H:%M:%S') for i in range(30, 0, -1)]
        
        download = [round(random.uniform(5, 50), 1) for _ in range(30)]
        upload = [round(random.uniform(1, 15), 1) for _ in range(30)]
        
        return jsonify({
            'success': True, 
            'data': {
                'timestamps': timestamps,
                'download': download,
                'upload': upload,
                'current_download': download[-1],
                'current_upload': upload[-1],
                'interface': interface
            }
        })
    except Exception as e:
        logger.error(f"Error getting bandwidth usage: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore nel recupero dell\'utilizzo della banda: {str(e)}'}), 500
        
def get_service_for_port(port):
    """Get service name for a port number"""
    port = int(port)
    
    # Mapping delle porte comuni
    services = {
        21: 'FTP',
        22: 'SSH',
        23: 'Telnet',
        25: 'SMTP',
        53: 'DNS',
        80: 'HTTP',
        443: 'HTTPS',
        3389: 'Remote Desktop',
        1194: 'OpenVPN',
        5060: 'SIP',
        5061: 'SIP/TLS'
    }
    
    return services.get(port, 'Sconosciuto')

@system_bp.route('/updates')
@login_required
def updates():
    """System updates page"""
    try:
        installed_packages = get_installed_packages()
        updates_available = check_for_updates()
        
        return render_template('system/index.html', 
                               active_page="system",
                               section="updates",
                               installed_packages=installed_packages,
                               updates_available=updates_available)
    except Exception as e:
        logger.error(f"Error checking for updates: {str(e)}")
        flash("Si è verificato un errore nel controllo degli aggiornamenti.", "danger")
        return redirect(url_for('system.index'))

@system_bp.route('/updates/install', methods=['POST'])
@login_required
def install_system_update():
    """Install system updates"""
    try:
        package = request.form.get('package', 'all')
        
        result = install_update(package)
        
        if result['success']:
            flash(f"Aggiornamento {package} installato con successo.", "success")
        else:
            flash(f"Errore nell'installazione dell'aggiornamento {package}: {result['message']}", "danger")
            
        return redirect(url_for('system.updates'))
    except Exception as e:
        logger.error(f"Error installing updates: {str(e)}")
        flash(f"Errore nell'installazione degli aggiornamenti: {str(e)}", "danger")
        return redirect(url_for('system.updates'))
