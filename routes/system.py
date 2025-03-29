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
