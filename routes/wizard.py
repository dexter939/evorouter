from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required
from forms import WizardNetworkForm, WizardFreeswitchForm
from models import NetworkInterface, FreeswitchConfig, FreeswitchExtension
from app import db
from utils.network import apply_network_config
from utils.freeswitch import apply_freeswitch_config, generate_extension_config, restart_freeswitch
import logging

logger = logging.getLogger(__name__)
wizard_bp = Blueprint('wizard', __name__)

@wizard_bp.route('/wizard')
@login_required
def index():
    session['wizard_step'] = 1
    return redirect(url_for('wizard.network_setup'))

@wizard_bp.route('/wizard/network', methods=['GET', 'POST'])
@login_required
def network_setup():
    form = WizardNetworkForm()
    
    if form.validate_on_submit():
        # Store form data in session
        session['network_config'] = {
            'internet_type': form.internet_type.data,
            'static_ip': form.static_ip.data,
            'static_netmask': form.static_netmask.data,
            'static_gateway': form.static_gateway.data,
            'static_dns1': form.static_dns1.data,
            'static_dns2': form.static_dns2.data,
            'pppoe_username': form.pppoe_username.data,
            'pppoe_password': form.pppoe_password.data,
            'wifi_enabled': form.wifi_enabled.data,
            'wifi_ssid': form.wifi_ssid.data,
            'wifi_password': form.wifi_password.data
        }
        
        session['wizard_step'] = 2
        return redirect(url_for('wizard.freeswitch_setup'))
    
    return render_template('wizard/network.html', form=form, step=1)

@wizard_bp.route('/wizard/freeswitch', methods=['GET', 'POST'])
@login_required
def freeswitch_setup():
    if session.get('wizard_step') != 2:
        return redirect(url_for('wizard.index'))
    
    form = WizardFreeswitchForm()
    
    if form.validate_on_submit():
        # Store form data in session
        session['freeswitch_config'] = {
            'enable_freeswitch': form.enable_freeswitch.data,
            'company_name': form.company_name.data,
            'num_extensions': form.num_extensions.data,
            'extension_prefix': form.extension_prefix.data,
            'trunk_enabled': form.trunk_enabled.data,
            'trunk_provider': form.trunk_provider.data,
            'trunk_username': form.trunk_username.data,
            'trunk_password': form.trunk_password.data,
            'trunk_server': form.trunk_server.data
        }
        
        # Process and apply all configuration
        try:
            apply_wizard_config(session.get('network_config'), session.get('freeswitch_config'))
            flash('Configuration applied successfully!', 'success')
        except Exception as e:
            logger.error(f"Wizard configuration error: {str(e)}")
            flash(f'Error applying configuration: {str(e)}', 'danger')
        
        # Clear wizard session data
        session.pop('wizard_step', None)
        session.pop('network_config', None)
        session.pop('freeswitch_config', None)
        
        return redirect(url_for('dashboard.index'))
    
    return render_template('wizard/freeswitch.html', form=form, step=2)

def apply_wizard_config(network_config, freeswitch_config):
    """Apply all configurations from the wizard"""
    if not network_config or not freeswitch_config:
        raise ValueError("Missing configuration data")
    
    # Apply network configuration
    # WAN Interface
    wan_interface = NetworkInterface.query.filter_by(is_wan=True).first()
    if not wan_interface:
        wan_interface = NetworkInterface(name="eth0", type="ethernet", is_wan=True)
        db.session.add(wan_interface)
    
    internet_type = network_config.get('internet_type')
    if internet_type == 'dhcp':
        wan_interface.dhcp_enabled = True
    elif internet_type == 'static':
        wan_interface.dhcp_enabled = False
        wan_interface.ip_address = network_config.get('static_ip')
        wan_interface.netmask = network_config.get('static_netmask')
        wan_interface.gateway = network_config.get('static_gateway')
        
        dns_servers = []
        if network_config.get('static_dns1'):
            dns_servers.append(network_config.get('static_dns1'))
        if network_config.get('static_dns2'):
            dns_servers.append(network_config.get('static_dns2'))
        
        wan_interface.dns_servers = ','.join(dns_servers)
    elif internet_type == 'pppoe':
        # This would require additional configuration in actual implementation
        logger.info("PPPoE configuration would be applied here")
    
    db.session.commit()
    apply_network_config(wan_interface)
    
    # WiFi Configuration
    if network_config.get('wifi_enabled'):
        wifi_interface = NetworkInterface.query.filter_by(type="wifi").first()
        if not wifi_interface:
            wifi_interface = NetworkInterface(name="wlan0", type="wifi")
            db.session.add(wifi_interface)
        
        # This would set up hostapd in the actual implementation
        logger.info(f"WiFi AP would be configured: SSID={network_config.get('wifi_ssid')}")
    
    # FreeSWITCH Configuration
    if freeswitch_config.get('enable_freeswitch'):
        fs_config = FreeswitchConfig.query.first()
        if not fs_config:
            fs_config = FreeswitchConfig()
            db.session.add(fs_config)
        
        fs_config.enabled = True
        db.session.commit()
        
        # Create extensions
        num_extensions = freeswitch_config.get('num_extensions', 2)
        prefix = freeswitch_config.get('extension_prefix', '10')
        
        # Clear existing extensions if doing a fresh setup
        FreeswitchExtension.query.delete()
        
        for i in range(1, num_extensions + 1):
            extension_number = f"{prefix}{i:02d}"
            extension = FreeswitchExtension(
                extension=extension_number,
                name=f"Extension {i}",
                password=f"password{i}",  # In a real setup, would generate secure passwords
                voicemail_enabled=True,
                voicemail_pin=f"{i:04d}"  # Example PIN
            )
            db.session.add(extension)
        
        db.session.commit()
        
        # Apply FreeSWITCH configuration
        apply_freeswitch_config(fs_config)
        
        # Generate extension configs
        for extension in FreeswitchExtension.query.all():
            generate_extension_config(extension)
        
        # Restart FreeSWITCH
        restart_freeswitch()
