from flask import Blueprint, jsonify, request, abort
from flask_login import login_required
from models import ApiClient, NetworkInterface, FreeswitchConfig, FreeswitchExtension, SystemLog
from app import db
from utils.security import validate_api_key, generate_api_key
from utils.network import get_interfaces_status, apply_network_config, restart_interface
from utils.freeswitch import restart_freeswitch, get_freeswitch_status
from utils.system import get_system_stats, get_system_info
from forms import ApiClientForm
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

# API Settings route
@api_bp.route('/settings/api', methods=['GET', 'POST'])
@login_required
def api_settings():
    clients = ApiClient.query.all()
    form = ApiClientForm()
    
    if form.validate_on_submit():
        client = ApiClient(
            name=form.name.data,
            api_key=generate_api_key(),
            enabled=form.enabled.data,
            ip_whitelist=form.ip_whitelist.data
        )
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('settings.api'))
    
    return render_template('settings.html', api_clients=clients, api_form=form)

@api_bp.route('/settings/api/<int:id>/delete', methods=['POST'])
@login_required
def delete_api_client(id):
    client = ApiClient.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    return redirect(url_for('settings.api'))

# API endpoints for remote management
@api_bp.route('/api/v1/system/info', methods=['GET'])
def api_system_info():
    if not validate_api_key(request):
        abort(401)
    
    try:
        info = get_system_info()
        stats = get_system_stats()
        
        # Update last used timestamp for the API client
        api_key = request.headers.get('X-API-Key')
        client = ApiClient.query.filter_by(api_key=api_key).first()
        if client:
            client.last_used = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'info': info,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"API system info error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/api/v1/network/interfaces', methods=['GET'])
def api_network_interfaces():
    if not validate_api_key(request):
        abort(401)
    
    try:
        interfaces = NetworkInterface.query.all()
        status = get_interfaces_status()
        
        interface_data = []
        for interface in interfaces:
            iface_info = interface.__dict__.copy()
            iface_info.pop('_sa_instance_state', None)
            
            # Add runtime status
            if interface.name in status:
                iface_info.update(status[interface.name])
            
            interface_data.append(iface_info)
        
        return jsonify({
            'success': True,
            'interfaces': interface_data
        })
    except Exception as e:
        logger.error(f"API network interfaces error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/api/v1/network/interface/<int:id>', methods=['PUT'])
def api_update_interface(id):
    if not validate_api_key(request):
        abort(401)
    
    interface = NetworkInterface.query.get_or_404(id)
    data = request.json
    
    try:
        # Update interface settings
        for key, value in data.items():
            if hasattr(interface, key):
                setattr(interface, key, value)
        
        db.session.commit()
        
        # Apply changes to system
        apply_network_config(interface)
        
        return jsonify({
            'success': True,
            'message': f'Interface {interface.name} updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"API update interface error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/api/v1/network/interface/<int:id>/restart', methods=['POST'])
def api_restart_interface(id):
    if not validate_api_key(request):
        abort(401)
    
    interface = NetworkInterface.query.get_or_404(id)
    
    try:
        restart_interface(interface.name)
        return jsonify({
            'success': True,
            'message': f'Interface {interface.name} restarted successfully'
        })
    except Exception as e:
        logger.error(f"API restart interface error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/api/v1/freeswitch/status', methods=['GET'])
def api_freeswitch_status():
    if not validate_api_key(request):
        abort(401)
    
    try:
        config = FreeswitchConfig.query.first()
        status = get_freeswitch_status()
        
        return jsonify({
            'success': True,
            'config': config.__dict__ if config else None,
            'status': status
        })
    except Exception as e:
        logger.error(f"API FreeSWITCH status error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/api/v1/freeswitch/restart', methods=['POST'])
def api_restart_freeswitch():
    if not validate_api_key(request):
        abort(401)
    
    try:
        restart_freeswitch()
        return jsonify({
            'success': True,
            'message': 'FreeSWITCH restarted successfully'
        })
    except Exception as e:
        logger.error(f"API restart FreeSWITCH error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/api/v1/freeswitch/extensions', methods=['GET'])
def api_freeswitch_extensions():
    if not validate_api_key(request):
        abort(401)
    
    try:
        extensions = FreeswitchExtension.query.all()
        
        extension_data = []
        for extension in extensions:
            ext_info = extension.__dict__.copy()
            ext_info.pop('_sa_instance_state', None)
            extension_data.append(ext_info)
        
        return jsonify({
            'success': True,
            'extensions': extension_data
        })
    except Exception as e:
        logger.error(f"API FreeSWITCH extensions error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/api/v1/logs', methods=['GET'])
def api_logs():
    if not validate_api_key(request):
        abort(401)
    
    limit = request.args.get('limit', 100, type=int)
    
    try:
        logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(limit).all()
        
        log_data = []
        for log in logs:
            log_info = log.__dict__.copy()
            log_info.pop('_sa_instance_state', None)
            log_data.append(log_info)
        
        return jsonify({
            'success': True,
            'logs': log_data
        })
    except Exception as e:
        logger.error(f"API logs error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
