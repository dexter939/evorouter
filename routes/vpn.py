from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, make_response, current_app
from flask_login import login_required, current_user
from app import db
from models import VpnServer, VpnClient
from forms.vpn import VpnServerForm, VpnWizardForm, VpnClientForm
from utils.vpn import (create_vpn_server, update_vpn_server, start_vpn_server, 
                      stop_vpn_server, create_vpn_client, update_vpn_client, 
                      delete_vpn_client, get_client_config, get_public_ip)
import io
import os

vpn = Blueprint('vpn', __name__)

@vpn.route('/')
@login_required
def index():
    """Pagina principale della VPN"""
    server = VpnServer.query.first()
    clients = []
    public_ip = None
    
    if server:
        clients = VpnClient.query.filter_by(server_id=server.id).all()
        public_ip = get_public_ip()
    
    return render_template('vpn/index.html', active_page='vpn', 
                          server=server, clients=clients, public_ip=public_ip)


@vpn.route('/wizard', methods=['GET', 'POST'])
@login_required
def wizard():
    """Wizard per la configurazione del server VPN"""
    form = VpnWizardForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        current_step = int(request.form.get('current_step', 1))
        
        # Se siamo all'ultimo passo, procediamo con la creazione
        if current_step == 4:
            # Check if a server already exists
            existing_server = VpnServer.query.first()
            if existing_server:
                db.session.delete(existing_server)
                db.session.commit()
            
            # Create a new server from the wizard data
            server_data = {
                'enabled': form.server_enabled.data,
                'vpn_type': request.form.get('server_type', 'openvpn'),
                'port': form.server_port.data,
                'protocol': form.server_protocol.data,
                'subnet': form.server_subnet.data,
                'dns_servers': '8.8.8.8,8.8.4.4',  # Default DNS
                'cipher': 'AES-256-GCM',  # Default cipher
                'auth_method': 'certificate'  # Default auth method
            }
            
            try:
                server = create_vpn_server(server_data)
                
                # Create clients based on client_count
                client_count = form.client_count.data
                for i in range(1, client_count + 1):
                    client_data = {
                        'name': f'Client{i}',
                        'description': f'Client creato dal wizard VPN',
                        'enabled': True
                    }
                    create_vpn_client(server, client_data)
                
                flash('Server VPN configurato con successo!', 'success')
                return redirect(url_for('vpn.index'))
            except Exception as e:
                flash(f'Errore durante la creazione del server VPN: {str(e)}', 'danger')
    
    return render_template('vpn/wizard.html', active_page='vpn', form=form)


@vpn.route('/server', methods=['GET', 'POST'])
@login_required
def server_config():
    """Configurazione manuale del server VPN"""
    server = VpnServer.query.first()
    
    if server:
        form = VpnServerForm(obj=server)
    else:
        form = VpnServerForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            if server:
                # Update existing server
                server_data = {
                    'enabled': form.enabled.data,
                    'vpn_type': form.vpn_type.data,
                    'port': form.port.data,
                    'protocol': form.protocol.data,
                    'subnet': form.subnet.data,
                    'dns_servers': form.dns_servers.data,
                    'cipher': form.cipher.data,
                    'auth_method': form.auth_method.data
                }
                
                update_vpn_server(server, server_data)
                flash('Configurazione del server VPN aggiornata con successo!', 'success')
            else:
                # Create new server
                server_data = {
                    'enabled': form.enabled.data,
                    'vpn_type': form.vpn_type.data,
                    'port': form.port.data,
                    'protocol': form.protocol.data,
                    'subnet': form.subnet.data,
                    'dns_servers': form.dns_servers.data,
                    'cipher': form.cipher.data,
                    'auth_method': form.auth_method.data
                }
                
                create_vpn_server(server_data)
                flash('Server VPN creato con successo!', 'success')
            
            return redirect(url_for('vpn.index'))
        except Exception as e:
            flash(f'Errore durante la configurazione del server VPN: {str(e)}', 'danger')
    
    return render_template('vpn/server_config.html', active_page='vpn', form=form, server=server)


@vpn.route('/server/toggle/<action>')
@login_required
def toggle_server(action):
    """Avvia o ferma il server VPN"""
    server = VpnServer.query.first()
    
    if not server:
        flash('Server VPN non configurato.', 'warning')
        return redirect(url_for('vpn.index'))
    
    if action == 'start':
        if start_vpn_server(server):
            flash('Server VPN avviato con successo!', 'success')
        else:
            flash('Errore durante l\'avvio del server VPN.', 'danger')
    elif action == 'stop':
        if stop_vpn_server(server):
            flash('Server VPN fermato con successo!', 'success')
        else:
            flash('Errore durante l\'arresto del server VPN.', 'danger')
    
    return redirect(url_for('vpn.index'))


@vpn.route('/client/add', methods=['GET', 'POST'])
@login_required
def add_client():
    """Aggiunge un nuovo client VPN"""
    server = VpnServer.query.first()
    
    if not server:
        flash('Server VPN non configurato.', 'warning')
        return redirect(url_for('vpn.index'))
    
    form = VpnClientForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            client_data = {
                'name': form.name.data,
                'description': form.description.data,
                'ip_address': form.ip_address.data,
                'enabled': form.enabled.data
            }
            
            create_vpn_client(server, client_data)
            flash('Client VPN creato con successo!', 'success')
            return redirect(url_for('vpn.index'))
        except Exception as e:
            flash(f'Errore durante la creazione del client VPN: {str(e)}', 'danger')
    
    return render_template('vpn/client_form.html', active_page='vpn', form=form, mode='create')


@vpn.route('/client/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    """Modifica un client VPN esistente"""
    client = VpnClient.query.get_or_404(client_id)
    form = VpnClientForm(obj=client)
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            client_data = {
                'name': form.name.data,
                'description': form.description.data,
                'ip_address': form.ip_address.data,
                'enabled': form.enabled.data
            }
            
            update_vpn_client(client, client_data)
            flash('Client VPN aggiornato con successo!', 'success')
            return redirect(url_for('vpn.index'))
        except Exception as e:
            flash(f'Errore durante l\'aggiornamento del client VPN: {str(e)}', 'danger')
    
    return render_template('vpn/client_form.html', active_page='vpn', form=form, 
                          client=client, mode='edit')


@vpn.route('/client/delete/<int:client_id>', methods=['POST'])
@login_required
def delete_client(client_id):
    """Elimina un client VPN"""
    client = VpnClient.query.get_or_404(client_id)
    
    if delete_vpn_client(client):
        flash('Client VPN eliminato con successo!', 'success')
    else:
        flash('Errore durante l\'eliminazione del client VPN.', 'danger')
    
    return redirect(url_for('vpn.index'))


@vpn.route('/client/download/<int:client_id>')
@login_required
def download_client(client_id):
    """Scarica il file di configurazione di un client VPN"""
    client = VpnClient.query.get_or_404(client_id)
    server = VpnServer.query.get(client.server_id)
    
    if not server:
        flash('Server VPN non configurato.', 'warning')
        return redirect(url_for('vpn.index'))
    
    filename, config = get_client_config(server, client)
    
    # Crea un file in memoria per il download
    config_file = io.BytesIO()
    config_file.write(config.encode('utf-8'))
    config_file.seek(0)
    
    return send_file(
        config_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/octet-stream'
    )