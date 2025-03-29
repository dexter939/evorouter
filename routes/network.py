import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from utils.network import (
    get_interfaces_status, configure_interface, 
    set_dhcp_config, restart_network, 
    get_dhcp_leases, get_dns_settings,
    set_dns_settings
)
from forms.network import NetworkInterfaceForm, DhcpServerForm, DnsSettingsForm

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint
network_bp = Blueprint('network', __name__)

@network_bp.route('/')
@login_required
def index():
    """Network dashboard overview page"""
    try:
        interfaces = get_interfaces_status()
        dhcp_leases = get_dhcp_leases()
        
        # Aggiungi link alla pagina UPnP
        upnp_enabled = True  # Questo valore dovrebbe provenire dalla configurazione reale
        
        return render_template('network/index.html', 
                               active_page="network",
                               interfaces=interfaces,
                               dhcp_leases=dhcp_leases,
                               upnp_enabled=upnp_enabled)
    except Exception as e:
        logger.error(f"Error loading network dashboard: {str(e)}")
        flash("Si è verificato un errore nel caricamento delle informazioni di rete.", "danger")
        return render_template('network/index.html', 
                               active_page="network",
                               error=True)

@network_bp.route('/interface/<interface_name>', methods=['GET', 'POST'])
@login_required
def configure_interface_route(interface_name):
    """Configure a specific network interface"""
    try:
        form = NetworkInterfaceForm()
        
        # If form is submitted and valid
        if form.validate_on_submit():
            result = configure_interface(
                interface_name=interface_name,
                ip_mode=form.ip_mode.data,
                ip_address=form.ip_address.data if form.ip_mode.data == 'static' else None,
                subnet_mask=form.subnet_mask.data if form.ip_mode.data == 'static' else None,
                gateway=form.gateway.data if form.ip_mode.data == 'static' else None,
                dns_servers=form.dns_servers.data,
                pppoe_username=form.pppoe_username.data if form.ip_mode.data == 'pppoe' else None,
                pppoe_password=form.pppoe_password.data if form.ip_mode.data == 'pppoe' else None,
                pppoe_service_name=form.pppoe_service_name.data if form.ip_mode.data == 'pppoe' else None
            )
            
            if result:
                flash(f"Configurazione dell'interfaccia {interface_name} aggiornata con successo.", "success")
                # Apply network changes
                restart_network()
                return redirect(url_for('network.index'))
            else:
                flash(f"Errore nell'aggiornamento della configurazione per {interface_name}.", "danger")
        
        # Get current interface info for display
        interfaces = get_interfaces_status()
        interface_info = next((i for i in interfaces if i['name'] == interface_name), None)
        
        if interface_info:
            # Pre-populate form with current values
            if not form.is_submitted():
                form.ip_mode.data = interface_info.get('mode', 'dhcp')
                if form.ip_mode.data == 'static':
                    form.ip_address.data = interface_info.get('ip_address', '')
                    form.subnet_mask.data = interface_info.get('subnet_mask', '')
                    form.gateway.data = interface_info.get('gateway', '')
                    form.dns_servers.data = interface_info.get('dns_servers', '')
            
            return render_template('network/advanced.html', 
                                active_page="network",
                                interface=interface_info,
                                form=form)
        else:
            flash(f"Interfaccia {interface_name} non trovata.", "danger")
            return redirect(url_for('network.index'))
            
    except Exception as e:
        logger.error(f"Error configuring interface {interface_name}: {str(e)}")
        flash(f"Si è verificato un errore nella configurazione dell'interfaccia {interface_name}.", "danger")
        return redirect(url_for('network.index'))

@network_bp.route('/dhcp', methods=['GET', 'POST'])
@login_required
def dhcp_config():
    """Configure DHCP server settings"""
    try:
        form = DhcpServerForm()
        
        # If form is submitted and valid
        if form.validate_on_submit():
            result = set_dhcp_config(
                enabled=form.enabled.data,
                start_ip=form.start_ip.data,
                end_ip=form.end_ip.data,
                lease_time=form.lease_time.data
            )
            
            if result:
                flash("Configurazione DHCP aggiornata con successo.", "success")
                # Apply DHCP changes
                restart_network()
                return redirect(url_for('network.index'))
            else:
                flash("Errore nell'aggiornamento della configurazione DHCP.", "danger")
        
        # Get current DHCP configuration
        dhcp_config = {
            'enabled': True,  # This would come from actual config
            'start_ip': '192.168.1.100',  # This would come from actual config
            'end_ip': '192.168.1.200',  # This would come from actual config
            'lease_time': 24  # This would come from actual config
        }
        
        # Pre-populate form with current values
        if not form.is_submitted():
            form.enabled.data = dhcp_config['enabled']
            form.start_ip.data = dhcp_config['start_ip']
            form.end_ip.data = dhcp_config['end_ip']
            form.lease_time.data = dhcp_config['lease_time']
        
        return render_template('network/advanced.html', 
                              active_page="network",
                              section="dhcp",
                              form=form)
            
    except Exception as e:
        logger.error(f"Error configuring DHCP: {str(e)}")
        flash("Si è verificato un errore nella configurazione del server DHCP.", "danger")
        return redirect(url_for('network.index'))

@network_bp.route('/dns', methods=['GET', 'POST'])
@login_required
def dns_config():
    """Configure DNS settings"""
    try:
        form = DnsSettingsForm()
        
        # If form is submitted and valid
        if form.validate_on_submit():
            result = set_dns_settings(
                primary_dns=form.primary_dns.data,
                secondary_dns=form.secondary_dns.data
            )
            
            if result:
                flash("Configurazione DNS aggiornata con successo.", "success")
                return redirect(url_for('network.index'))
            else:
                flash("Errore nell'aggiornamento della configurazione DNS.", "danger")
        
        # Get current DNS settings
        dns_settings = get_dns_settings()
        
        # Pre-populate form with current values
        if not form.is_submitted():
            form.primary_dns.data = dns_settings.get('primary', '')
            form.secondary_dns.data = dns_settings.get('secondary', '')
        
        return render_template('network/advanced.html', 
                              active_page="network",
                              section="dns",
                              form=form)
            
    except Exception as e:
        logger.error(f"Error configuring DNS: {str(e)}")
        flash("Si è verificato un errore nella configurazione DNS.", "danger")
        return redirect(url_for('network.index'))

@network_bp.route('/wizard', methods=['GET', 'POST'])
@login_required
def wizard():
    """Network configuration wizard"""
    try:
        if request.method == 'POST':
            # Process wizard data
            wizard_data = request.form
            
            # Configure WAN interface
            wan_result = configure_interface(
                interface_name='eth1',  # Assuming eth1 is WAN
                ip_mode=wizard_data.get('wan_mode', 'dhcp'),
                ip_address=wizard_data.get('wan_ip') if wizard_data.get('wan_mode') == 'static' else None,
                subnet_mask=wizard_data.get('wan_subnet') if wizard_data.get('wan_mode') == 'static' else None,
                gateway=wizard_data.get('wan_gateway') if wizard_data.get('wan_mode') == 'static' else None,
                dns_servers=wizard_data.get('wan_dns'),
                pppoe_username=wizard_data.get('wan_pppoe_username') if wizard_data.get('wan_mode') == 'pppoe' else None,
                pppoe_password=wizard_data.get('wan_pppoe_password') if wizard_data.get('wan_mode') == 'pppoe' else None,
                pppoe_service_name=wizard_data.get('wan_pppoe_service') if wizard_data.get('wan_mode') == 'pppoe' else None
            )
            
            # Configure LAN interface
            lan_result = configure_interface(
                interface_name='eth0',  # Assuming eth0 is LAN
                ip_mode='static',
                ip_address=wizard_data.get('lan_ip', '192.168.1.1'),
                subnet_mask=wizard_data.get('lan_subnet', '255.255.255.0'),
                gateway=None,
                dns_servers=None
            )
            
            # Configure DHCP server
            dhcp_result = set_dhcp_config(
                enabled=wizard_data.get('dhcp_enabled', 'on') == 'on',
                start_ip=wizard_data.get('dhcp_start', '192.168.1.100'),
                end_ip=wizard_data.get('dhcp_end', '192.168.1.200'),
                lease_time=int(wizard_data.get('dhcp_lease', '24'))
            )
            
            if wan_result and lan_result and dhcp_result:
                # Apply all network changes
                restart_network()
                flash("Configurazione di rete completata con successo!", "success")
                return redirect(url_for('network.index'))
            else:
                flash("Si è verificato un errore nella configurazione di rete. Controlla i dettagli e riprova.", "danger")
        
        return render_template('network/wizard.html', active_page="network")
            
    except Exception as e:
        logger.error(f"Error in network wizard: {str(e)}")
        flash("Si è verificato un errore nel wizard di configurazione di rete.", "danger")
        return redirect(url_for('network.index'))

@network_bp.route('/restart', methods=['POST'])
@login_required
def restart_network_service():
    """Restart networking services"""
    try:
        result = restart_network()
        if result:
            return jsonify({'success': True, 'message': 'Servizi di rete riavviati con successo.'})
        else:
            return jsonify({'success': False, 'message': 'Errore nel riavvio dei servizi di rete.'}), 500
    except Exception as e:
        logger.error(f"Error restarting network: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore nel riavvio dei servizi di rete: {str(e)}'}), 500
