"""
Utilità per la gestione del server VPN e dei client
"""
import os
import uuid
import subprocess
import logging
import ipaddress
import re
from datetime import datetime
from models import SystemLog, VpnServer, VpnClient
from app import db

logger = logging.getLogger(__name__)

def create_vpn_server(server_data):
    """
    Crea un nuovo server VPN con i parametri forniti
    
    Args:
        server_data (dict): Dati di configurazione del server
        
    Returns:
        VpnServer: L'oggetto server VPN creato
    """
    try:
        server = VpnServer(
            enabled=server_data.get('enabled', False),
            vpn_type=server_data.get('vpn_type', 'openvpn'),
            protocol=server_data.get('protocol', 'udp'),
            port=server_data.get('port', 1194),
            subnet=server_data.get('subnet', '10.8.0.0/24'),
            dns_servers=server_data.get('dns_servers', '8.8.8.8,8.8.4.4'),
            cipher=server_data.get('cipher', 'AES-256-GCM'),
            auth_method=server_data.get('auth_method', 'certificate'),
            status='stopped'
        )
        
        # Crea una directory per i certificati (simulato)
        server_certificates_path = f'/etc/vpn/{uuid.uuid4()}'
        server.server_certificates_path = server_certificates_path
        
        # Salva il server nel database
        db.session.add(server)
        db.session.commit()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='info',
            message=f'Creato nuovo server VPN: {server.vpn_type} su porta {server.port}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return server
    except Exception as e:
        logger.error(f"Errore durante la creazione del server VPN: {str(e)}")
        db.session.rollback()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='error',
            message=f'Errore durante la creazione del server VPN: {str(e)}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        raise

def update_vpn_server(server, server_data):
    """
    Aggiorna un server VPN esistente
    
    Args:
        server (VpnServer): Server VPN da aggiornare
        server_data (dict): Nuovi dati di configurazione
        
    Returns:
        VpnServer: L'oggetto server VPN aggiornato
    """
    try:
        server.enabled = server_data.get('enabled', server.enabled)
        server.vpn_type = server_data.get('vpn_type', server.vpn_type)
        server.protocol = server_data.get('protocol', server.protocol)
        server.port = server_data.get('port', server.port)
        server.subnet = server_data.get('subnet', server.subnet)
        server.dns_servers = server_data.get('dns_servers', server.dns_servers)
        server.cipher = server_data.get('cipher', server.cipher)
        server.auth_method = server_data.get('auth_method', server.auth_method)
        
        # Aggiorna la data di modifica
        server.updated_at = datetime.utcnow()
        
        # Se il server era attivo, dobbiamo riavviarlo
        was_running = server.status == 'running'
        if was_running:
            server.status = 'stopped'
        
        db.session.commit()
        
        # Riavvio condizionale
        if was_running:
            start_vpn_server(server)
        
        log_entry = SystemLog(
            log_type='vpn',
            level='info',
            message=f'Aggiornato server VPN ID {server.id}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return server
    except Exception as e:
        logger.error(f"Errore durante l'aggiornamento del server VPN: {str(e)}")
        db.session.rollback()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='error',
            message=f'Errore durante l\'aggiornamento del server VPN: {str(e)}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        raise

def start_vpn_server(server):
    """
    Avvia un server VPN (simulato nell'ambiente Replit)
    
    Args:
        server (VpnServer): Server VPN da avviare
        
    Returns:
        bool: True se avviato con successo, False altrimenti
    """
    try:
        # In un ambiente reale, qui avvieremmo il server VPN usando 
        # subprocess.run() o systemd
        
        # Simuliamo l'avvio
        server.status = 'running'
        server.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='info',
            message=f'Avviato server VPN {server.vpn_type} su porta {server.port}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return True
    except Exception as e:
        logger.error(f"Errore durante l'avvio del server VPN: {str(e)}")
        
        server.status = 'error'
        db.session.commit()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='error',
            message=f'Errore durante l\'avvio del server VPN: {str(e)}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return False

def stop_vpn_server(server):
    """
    Ferma un server VPN (simulato nell'ambiente Replit)
    
    Args:
        server (VpnServer): Server VPN da fermare
        
    Returns:
        bool: True se fermato con successo, False altrimenti
    """
    try:
        # In un ambiente reale, qui fermeremmo il server VPN usando 
        # subprocess.run() o systemd
        
        # Simuliamo l'arresto
        server.status = 'stopped'
        server.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='info',
            message=f'Fermato server VPN {server.vpn_type}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return True
    except Exception as e:
        logger.error(f"Errore durante l'arresto del server VPN: {str(e)}")
        
        server.status = 'error'
        db.session.commit()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='error',
            message=f'Errore durante l\'arresto del server VPN: {str(e)}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return False

def get_next_ip_address(server):
    """
    Ottiene il prossimo indirizzo IP disponibile nella subnet del server
    
    Args:
        server (VpnServer): Server VPN
        
    Returns:
        str: Indirizzo IP disponibile o None se non disponibile
    """
    try:
        # Parsifica la subnet per ottenere la rete
        network = ipaddress.ip_network(server.subnet)
        
        # Ottenere tutti gli IP già assegnati
        assigned_ips = db.session.query(VpnClient.ip_address).filter(
            VpnClient.server_id == server.id,
            VpnClient.ip_address != None
        ).all()
        assigned_ips = [ip[0] for ip in assigned_ips]
        
        # Il primo indirizzo è riservato al server
        server_ip = str(network.network_address + 1)
        
        # Troviamo il primo IP disponibile a partire dal secondo
        for i in range(2, min(100, network.num_addresses - 1)):  # Limitiamo a 100 client
            ip = str(network.network_address + i)
            if ip not in assigned_ips:
                return ip
                
        # Se arriviamo qui, non ci sono IP disponibili
        return None
    except Exception as e:
        logger.error(f"Errore durante la ricerca del prossimo indirizzo IP: {str(e)}")
        return None

def create_vpn_client(server, client_data):
    """
    Crea un nuovo client VPN
    
    Args:
        server (VpnServer): Server VPN a cui associare il client
        client_data (dict): Dati del client
        
    Returns:
        VpnClient: L'oggetto client VPN creato
    """
    try:
        # Genera un ID univoco per il client
        client_id = str(uuid.uuid4())
        
        # Se non è specificato un IP, assegna il prossimo disponibile
        if not client_data.get('ip_address'):
            ip_address = get_next_ip_address(server)
        else:
            ip_address = client_data.get('ip_address')
        
        client = VpnClient(
            server_id=server.id,
            name=client_data.get('name'),
            description=client_data.get('description', ''),
            client_id=client_id,
            ip_address=ip_address,
            enabled=client_data.get('enabled', True),
            certificates_path=f'/etc/vpn/clients/{client_id}',
            config_file_path=f'/etc/vpn/clients/{client_id}/client.ovpn'
        )
        
        db.session.add(client)
        db.session.commit()
        
        # Generazione file di configurazione (in un sistema reale)
        # generate_client_config(server, client)
        
        log_entry = SystemLog(
            log_type='vpn',
            level='info',
            message=f'Creato nuovo client VPN: {client.name}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return client
    except Exception as e:
        logger.error(f"Errore durante la creazione del client VPN: {str(e)}")
        db.session.rollback()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='error',
            message=f'Errore durante la creazione del client VPN: {str(e)}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        raise

def update_vpn_client(client, client_data):
    """
    Aggiorna un client VPN esistente
    
    Args:
        client (VpnClient): Client VPN da aggiornare
        client_data (dict): Nuovi dati del client
        
    Returns:
        VpnClient: L'oggetto client VPN aggiornato
    """
    try:
        client.name = client_data.get('name', client.name)
        client.description = client_data.get('description', client.description)
        client.enabled = client_data.get('enabled', client.enabled)
        
        # Aggiorna IP solo se specificato
        if client_data.get('ip_address'):
            client.ip_address = client_data.get('ip_address')
        
        db.session.commit()
        
        # In un sistema reale, qui potremmo dover rigenerare il file di configurazione
        # se alcuni parametri sono cambiati
        
        log_entry = SystemLog(
            log_type='vpn',
            level='info',
            message=f'Aggiornato client VPN: {client.name}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return client
    except Exception as e:
        logger.error(f"Errore durante l'aggiornamento del client VPN: {str(e)}")
        db.session.rollback()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='error',
            message=f'Errore durante l\'aggiornamento del client VPN: {str(e)}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        raise

def delete_vpn_client(client):
    """
    Elimina un client VPN
    
    Args:
        client (VpnClient): Client VPN da eliminare
        
    Returns:
        bool: True se eliminato con successo, False altrimenti
    """
    try:
        client_name = client.name
        
        # In un sistema reale, qui elimineremmo i file del client
        # if os.path.exists(client.certificates_path):
        #     subprocess.run(['rm', '-rf', client.certificates_path])
        
        db.session.delete(client)
        db.session.commit()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='info',
            message=f'Eliminato client VPN: {client_name}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return True
    except Exception as e:
        logger.error(f"Errore durante l'eliminazione del client VPN: {str(e)}")
        db.session.rollback()
        
        log_entry = SystemLog(
            log_type='vpn',
            level='error',
            message=f'Errore durante l\'eliminazione del client VPN: {str(e)}'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return False

def generate_openvpn_config(server, client):
    """
    Genera un file di configurazione OpenVPN per un client (simulato in Replit)
    
    Args:
        server (VpnServer): Server VPN
        client (VpnClient): Client VPN
        
    Returns:
        str: Contenuto del file di configurazione
    """
    # In un ambiente reale, genereremmo il file di configurazione usando i certificati reali
    config = f"""
client
dev tun
proto {server.protocol}
remote YOUR_SERVER_IP {server.port}
resolv-retry infinite
nobind
persist-key
persist-tun
cipher {server.cipher}
auth SHA256
verb 3
key-direction 1

# Questo è un file di configurazione simulato
# In un sistema reale, qui ci sarebbero i certificati e chiavi
<ca>
-----BEGIN CERTIFICATE-----
# Certificato CA simulato
-----END CERTIFICATE-----
</ca>

<cert>
-----BEGIN CERTIFICATE-----
# Certificato client simulato per {client.name}
-----END CERTIFICATE-----
</cert>

<key>
-----BEGIN PRIVATE KEY-----
# Chiave privata client simulata
-----END PRIVATE KEY-----
</key>

<tls-auth>
-----BEGIN OpenVPN Static key V1-----
# Chiave TLS Auth simulata
-----END OpenVPN Static key V1-----
</tls-auth>
"""
    return config

def generate_wireguard_config(server, client):
    """
    Genera un file di configurazione WireGuard per un client (simulato in Replit)
    
    Args:
        server (VpnServer): Server VPN
        client (VpnClient): Client VPN
        
    Returns:
        str: Contenuto del file di configurazione
    """
    # In un ambiente reale, genereremmo il file di configurazione usando le chiavi reali
    client_private_key = "PRIVATE_KEY_PLACEHOLDER"
    server_public_key = "SERVER_PUBLIC_KEY_PLACEHOLDER"
    
    config = f"""
[Interface]
PrivateKey = {client_private_key}
Address = {client.ip_address}/24
DNS = {server.dns_servers}

[Peer]
PublicKey = {server_public_key}
AllowedIPs = 0.0.0.0/0
Endpoint = YOUR_SERVER_IP:{server.port}
PersistentKeepalive = 25
"""
    return config

def get_client_config(server, client):
    """
    Ottiene il file di configurazione per un client VPN
    
    Args:
        server (VpnServer): Server VPN
        client (VpnClient): Client VPN
        
    Returns:
        tuple: (nome_file, contenuto_file)
    """
    if server.vpn_type == 'openvpn':
        config = generate_openvpn_config(server, client)
        filename = f"{client.name}.ovpn"
    else:  # wireguard
        config = generate_wireguard_config(server, client)
        filename = f"{client.name}.conf"
    
    return (filename, config)

def get_public_ip():
    """
    Ottiene l'indirizzo IP pubblico del server (simulato in Replit)
    
    Returns:
        str: Indirizzo IP pubblico o None se non disponibile
    """
    # In un ambiente reale, faremmo una richiesta a un servizio come ipify
    # Qui simuliamo un IP pubblico
    return "203.0.113.10"  # Esempio da un range riservato per documentazione