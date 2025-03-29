from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from utils.system import get_system_stats, get_system_info
from utils.network import get_network_stats, get_interfaces_status
from models import SystemLog, FreeswitchExtension

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Get basic system information for the dashboard
    system_info = get_system_info()
    
    # Get recent system logs
    recent_logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(10).all()
    
    # Get network interfaces status
    network_status = get_interfaces_status()
    
    # Get FreeSWITCH extensions
    extensions = FreeswitchExtension.query.all()
    
    return render_template('dashboard.html', 
                          system_info=system_info,
                          recent_logs=recent_logs,
                          network_status=network_status,
                          extensions=extensions)

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def stats():
    """API endpoint to fetch live system stats for the dashboard"""
    system_stats = get_system_stats()
    network_stats = get_network_stats()
    
    return jsonify({
        'system': system_stats,
        'network': network_stats
    })
