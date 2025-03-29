from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from forms import DiagnosticsForm
from utils.network import run_ping, run_traceroute, run_dns_lookup
import logging

logger = logging.getLogger(__name__)
diagnostics_bp = Blueprint('diagnostics', __name__)

@diagnostics_bp.route('/diagnostics')
@login_required
def index():
    form = DiagnosticsForm()
    return render_template('diagnostics.html', form=form)

@diagnostics_bp.route('/diagnostics/ping', methods=['POST'])
@login_required
def ping():
    form = DiagnosticsForm()
    if form.ping_submit.data:
        target = form.ping_target.data
        try:
            result = run_ping(target)
            return jsonify({'success': True, 'result': result})
        except Exception as e:
            logger.error(f"Ping error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Invalid form data'})

@diagnostics_bp.route('/diagnostics/traceroute', methods=['POST'])
@login_required
def traceroute():
    form = DiagnosticsForm()
    if form.traceroute_submit.data:
        target = form.traceroute_target.data
        try:
            result = run_traceroute(target)
            return jsonify({'success': True, 'result': result})
        except Exception as e:
            logger.error(f"Traceroute error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Invalid form data'})

@diagnostics_bp.route('/diagnostics/dns', methods=['POST'])
@login_required
def dns_lookup():
    form = DiagnosticsForm()
    if form.dns_submit.data:
        target = form.dns_target.data
        try:
            result = run_dns_lookup(target)
            return jsonify({'success': True, 'result': result})
        except Exception as e:
            logger.error(f"DNS lookup error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Invalid form data'})

@diagnostics_bp.route('/diagnostics/logs')
@login_required
def logs():
    log_type = request.args.get('type', 'system')
    lines = request.args.get('lines', 100, type=int)
    
    try:
        if log_type == 'system':
            log_data = get_system_logs(lines)
        elif log_type == 'freeswitch':
            log_data = get_freeswitch_logs(lines)
        elif log_type == 'network':
            log_data = get_network_logs(lines)
        else:
            return jsonify({'success': False, 'error': 'Invalid log type'})
        
        return jsonify({'success': True, 'logs': log_data})
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def get_system_logs(lines):
    # Implementation would read from actual system logs
    with open('/var/log/syslog', 'r') as f:
        return f.readlines()[-lines:]

def get_freeswitch_logs(lines):
    # Implementation would read from FreeSWITCH logs
    with open('/var/log/freeswitch/freeswitch.log', 'r') as f:
        return f.readlines()[-lines:]

def get_network_logs(lines):
    # Implementation would read from network logs
    with open('/var/log/kern.log', 'r') as f:
        return f.readlines()[-lines:]
