import logging
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from utils.system import get_system_stats, get_network_usage
from utils.network import get_interfaces_status

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Route to render the main dashboard page"""
    try:
        return render_template('dashboard.html', 
                              active_page="dashboard",
                              system_stats=get_system_stats(),
                              network_stats=get_interfaces_status())
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        return render_template('dashboard.html', 
                              active_page="dashboard",
                              error="Si è verificato un errore nel caricamento della dashboard.")

@dashboard_bp.route('/api/stats')
@login_required
def get_stats():
    """API endpoint to get real-time system stats"""
    try:
        return jsonify({
            'system': get_system_stats(),
            'network': get_network_usage()
        })
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Si è verificato un errore nel recupero delle statistiche'}), 500

@dashboard_bp.route('/api/network_usage_history')
@login_required
def get_network_history():
    """API endpoint to get network usage history for charts"""
    try:
        # This would normally retrieve historical data from a database or log files
        # For now, we'll return example data for demonstration
        data = {
            'timestamps': ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', 
                          '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                          '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
                          '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'],
            'wan_download': [5, 7, 2, 3, 2, 1, 1, 3, 8, 12, 15, 14, 13, 14, 16, 17, 16, 14, 12, 10, 8, 6, 5, 4],
            'wan_upload': [2, 3, 1, 1, 1, 0.5, 0.5, 1, 4, 6, 7, 6, 6, 7, 8, 8, 7, 6, 5, 4, 3, 2, 2, 1]
        }
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting network history: {str(e)}")
        return jsonify({'error': 'Si è verificato un errore nel recupero dello storico di rete'}), 500
