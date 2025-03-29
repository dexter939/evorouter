from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from models import NetworkInterface
from forms import NetworkInterfaceForm
from app import db
from utils.network import (
    apply_network_config, 
    restart_interface, 
    scan_wifi_networks,
    get_interface_details,
    get_interfaces_status
)
import logging

logger = logging.getLogger(__name__)
network_bp = Blueprint('network', __name__)

@network_bp.route('/network')
@login_required
def index():
    interfaces = NetworkInterface.query.all()
    status = get_interfaces_status()
    return render_template('network.html', interfaces=interfaces, status=status)

@network_bp.route('/network/interface/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_interface(id):
    interface = NetworkInterface.query.get_or_404(id)
    form = NetworkInterfaceForm(obj=interface)
    
    if form.validate_on_submit():
        # Save form data to model
        form.populate_obj(interface)
        db.session.commit()
        
        # Apply changes to system
        try:
            apply_network_config(interface)
            flash('Network interface updated successfully', 'success')
        except Exception as e:
            logger.error(f"Failed to apply network config: {str(e)}")
            flash(f'Error applying network configuration: {str(e)}', 'danger')
        
        return redirect(url_for('network.index'))
    
    return render_template('network.html', form=form, interface=interface)

@network_bp.route('/network/interface/<int:id>/restart', methods=['POST'])
@login_required
def restart_network_interface(id):
    interface = NetworkInterface.query.get_or_404(id)
    try:
        restart_interface(interface.name)
        flash(f'Interface {interface.name} restarted successfully', 'success')
    except Exception as e:
        logger.error(f"Failed to restart interface: {str(e)}")
        flash(f'Error restarting interface: {str(e)}', 'danger')
    
    return redirect(url_for('network.index'))

@network_bp.route('/network/scan_wifi', methods=['GET'])
@login_required
def scan_wifi():
    try:
        networks = scan_wifi_networks()
        return jsonify({'success': True, 'networks': networks})
    except Exception as e:
        logger.error(f"Failed to scan WiFi networks: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@network_bp.route('/network/interface/<int:id>/stats', methods=['GET'])
@login_required
def interface_stats(id):
    interface = NetworkInterface.query.get_or_404(id)
    try:
        stats = get_interface_details(interface.name)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Failed to get interface stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
