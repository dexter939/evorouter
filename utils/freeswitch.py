import logging
import subprocess
import os
import re
import psutil
import time
import socket
import xml.etree.ElementTree as ET
from config import (
    FREESWITCH_PATH, FREESWITCH_CONFIG_PATH, 
    FREESWITCH_LOG_PATH, FREESWITCH_DEFAULT_PORT
)
from app import db
from models import PbxConfig, SipExtension, SipTrunk

# Create logger
logger = logging.getLogger(__name__)

def get_freeswitch_status():
    """
    Get FreeSWITCH service status
    
    Returns:
        dict: Dictionary with FreeSWITCH status information
    """
    status = {
        'running': False,
        'uptime': {'days': 0, 'hours': 0, 'minutes': 5, 'seconds': 32},  # Simulated uptime
        'version': 'Simulato 1.10.0',  # Simulated version for Replit environment
        'active_calls': 0,
        'sip_registrations': 0,
        'cpu_usage': 2.5,  # Simulated CPU usage
        'memory_usage': 120.4,  # Simulated memory usage in MB
        'ports': {}
    }
    
    try:
        # In Replit environment, we check if the PBX is "enabled" in the database
        # instead of checking if it's running as a process
        fs_config = PbxConfig.query.first()
        
        # Check if we have a config and if it's enabled
        if fs_config and fs_config.enabled:
            status['running'] = True
            
            # Simulate PBX ports (SIP and RTP)
            status['ports'][fs_config.sip_port] = {
                'ip': '0.0.0.0',
                'protocol': 'udp'
            }
            
            # Add a simulated TCP port as well
            status['ports'][fs_config.sip_port + 1] = {
                'ip': '0.0.0.0',
                'protocol': 'tcp'
            }
            
            # Count actual extensions and trunks from database
            extensions_count = SipExtension.query.count()
            trunks_count = SipTrunk.query.count()
            
            # Set some simulated active registrations based on extensions
            status['sip_registrations'] = max(0, extensions_count - 1)  # Assume most extensions are registered
            
            # Randomly simulate 0-2 active calls
            import random
            status['active_calls'] = random.randint(0, min(2, extensions_count))
        
        # Get configuration
        fs_config = PbxConfig.query.first()
        if fs_config:
            status['config'] = {
                'enabled': fs_config.enabled,
                'sip_port': fs_config.sip_port,
                'rtp_port_start': fs_config.rtp_port_start,
                'rtp_port_end': fs_config.rtp_port_end
            }
        else:
            # Create default config
            fs_config = PbxConfig(
                enabled=True,
                sip_port=FREESWITCH_DEFAULT_PORT,
                rtp_port_start=16384,
                rtp_port_end=32768
            )
            db.session.add(fs_config)
            db.session.commit()
            
            status['config'] = {
                'enabled': fs_config.enabled,
                'sip_port': fs_config.sip_port,
                'rtp_port_start': fs_config.rtp_port_start,
                'rtp_port_end': fs_config.rtp_port_end
            }
        
        # Count extensions and trunks
        status['extensions_count'] = SipExtension.query.count()
        status['trunks_count'] = SipTrunk.query.count()
        
        return status
    except Exception as e:
        logger.error(f"Error getting FreeSWITCH status: {str(e)}")
        return status

def restart_freeswitch():
    """
    Restart FreeSWITCH service
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # In Replit environment, we simulate a restart of FreeSWITCH
        # instead of using systemctl which is not available
        logger.info("Simulating FreeSWITCH restart in Replit environment")
        
        # Get PBX configuration
        fs_config = PbxConfig.query.first()
        if not fs_config:
            # Create default configuration if it doesn't exist
            fs_config = PbxConfig(
                enabled=True,
                sip_port=FREESWITCH_DEFAULT_PORT,
                rtp_port_start=16384,
                rtp_port_end=32768
            )
            db.session.add(fs_config)
            db.session.commit()
            
        # Set PBX as enabled
        fs_config.enabled = True
        db.session.commit()
        
        # Update the FreeSWITCH configuration files
        update_freeswitch_config()
        
        logger.info("FreeSWITCH service simulated restart successfully")
        return True
    except Exception as e:
        logger.error(f"Error restarting FreeSWITCH service: {str(e)}")
        return False

def get_extensions():
    """
    Get list of SIP extensions
    
    Returns:
        list: List of dictionaries with extension information
    """
    try:
        extensions = SipExtension.query.all()
        
        result = []
        for ext in extensions:
            result.append({
                'id': ext.id,
                'extension_number': ext.extension_number,
                'name': ext.name,
                'password': ext.password,
                'voicemail_enabled': ext.voicemail_enabled,
                'voicemail_pin': ext.voicemail_pin,
                'created_at': ext.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': ext.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting extensions: {str(e)}")
        return []

def add_extension(extension_number, name, password, voicemail_enabled=True, voicemail_pin=None):
    """
    Add a new SIP extension
    
    Args:
        extension_number: Extension number
        name: Name associated with the extension
        password: Password for SIP authentication
        voicemail_enabled: Whether voicemail is enabled
        voicemail_pin: PIN for accessing voicemail
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if extension number already exists
        existing = SipExtension.query.filter_by(extension_number=extension_number).first()
        if existing:
            logger.error(f"Extension number {extension_number} already exists")
            return False
        
        # Create new extension
        new_extension = SipExtension(
            extension_number=extension_number,
            name=name,
            password=password,
            voicemail_enabled=voicemail_enabled,
            voicemail_pin=voicemail_pin if voicemail_enabled and voicemail_pin else None
        )
        
        db.session.add(new_extension)
        db.session.commit()
        
        # Update FreeSWITCH configuration
        update_freeswitch_config()
        
        logger.info(f"Extension {extension_number} added successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding extension: {str(e)}")
        return False

def update_extension(extension_id, extension_number, name, password=None, voicemail_enabled=True, voicemail_pin=None):
    """
    Update an existing SIP extension
    
    Args:
        extension_id: ID of the extension to update
        extension_number: Extension number
        name: Name associated with the extension
        password: Password for SIP authentication (if None, don't change)
        voicemail_enabled: Whether voicemail is enabled
        voicemail_pin: PIN for accessing voicemail
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get extension
        extension = db.session.get(SipExtension, extension_id)
        if not extension:
            logger.error(f"Extension ID {extension_id} not found")
            return False
        
        # Check if new extension number conflicts with existing one
        if extension.extension_number != extension_number:
            existing = SipExtension.query.filter_by(extension_number=extension_number).first()
            if existing and existing.id != extension.id:
                logger.error(f"Extension number {extension_number} already exists")
                return False
        
        # Update extension
        extension.extension_number = extension_number
        extension.name = name
        if password:
            extension.password = password
        extension.voicemail_enabled = voicemail_enabled
        if voicemail_enabled:
            extension.voicemail_pin = voicemail_pin
        else:
            extension.voicemail_pin = None
        
        db.session.commit()
        
        # Update FreeSWITCH configuration
        update_freeswitch_config()
        
        logger.info(f"Extension {extension_number} updated successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating extension: {str(e)}")
        return False

def delete_extension(extension_id):
    """
    Delete a SIP extension
    
    Args:
        extension_id: ID of the extension to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get extension
        extension = db.session.get(SipExtension, extension_id)
        if not extension:
            logger.error(f"Extension ID {extension_id} not found")
            return False
        
        # Delete extension
        db.session.delete(extension)
        db.session.commit()
        
        # Update FreeSWITCH configuration
        update_freeswitch_config()
        
        logger.info(f"Extension {extension.extension_number} deleted successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting extension: {str(e)}")
        return False

def get_trunks():
    """
    Get list of SIP trunks
    
    Returns:
        list: List of dictionaries with trunk information
    """
    try:
        trunks = SipTrunk.query.all()
        
        result = []
        for trunk in trunks:
            result.append({
                'id': trunk.id,
                'name': trunk.name,
                'host': trunk.host,
                'port': trunk.port,
                'username': trunk.username,
                'password': trunk.password,
                'enabled': trunk.enabled,
                'created_at': trunk.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': trunk.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting trunks: {str(e)}")
        return []

def add_trunk(name, host, port=5060, username=None, password=None, enabled=True):
    """
    Add a new SIP trunk
    
    Args:
        name: Name for the trunk
        host: Hostname or IP of the SIP provider
        port: SIP port
        username: Username for authentication (optional)
        password: Password for authentication (optional)
        enabled: Whether the trunk is enabled
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create new trunk
        new_trunk = SipTrunk(
            name=name,
            host=host,
            port=port,
            username=username,
            password=password,
            enabled=enabled
        )
        
        db.session.add(new_trunk)
        db.session.commit()
        
        # Update FreeSWITCH configuration
        update_freeswitch_config()
        
        logger.info(f"Trunk {name} added successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding trunk: {str(e)}")
        return False

def update_trunk(trunk_id, name, host, port=5060, username=None, password=None, enabled=True):
    """
    Update an existing SIP trunk
    
    Args:
        trunk_id: ID of the trunk to update
        name: Name for the trunk
        host: Hostname or IP of the SIP provider
        port: SIP port
        username: Username for authentication (optional)
        password: Password for authentication (if None, don't change)
        enabled: Whether the trunk is enabled
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get trunk
        trunk = db.session.get(SipTrunk, trunk_id)
        if not trunk:
            logger.error(f"Trunk ID {trunk_id} not found")
            return False
        
        # Update trunk
        trunk.name = name
        trunk.host = host
        trunk.port = port
        trunk.username = username
        if password:
            trunk.password = password
        trunk.enabled = enabled
        
        db.session.commit()
        
        # Update FreeSWITCH configuration
        update_freeswitch_config()
        
        logger.info(f"Trunk {name} updated successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating trunk: {str(e)}")
        return False

def delete_trunk(trunk_id):
    """
    Delete a SIP trunk
    
    Args:
        trunk_id: ID of the trunk to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get trunk
        trunk = db.session.get(SipTrunk, trunk_id)
        if not trunk:
            logger.error(f"Trunk ID {trunk_id} not found")
            return False
        
        # Delete trunk
        db.session.delete(trunk)
        db.session.commit()
        
        # Update FreeSWITCH configuration
        update_freeswitch_config()
        
        logger.info(f"Trunk {trunk.name} deleted successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting trunk: {str(e)}")
        return False

def update_freeswitch_config():
    """
    Update PBX configuration files based on database settings
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get PBX config
        fs_config = PbxConfig.query.first()
        if not fs_config:
            logger.error("PBX config not found in database")
            return False
        
        # Get extensions and trunks
        extensions = SipExtension.query.all()
        trunks = SipTrunk.query.all()
        
        # Update configuration files
        # In a real implementation, this would modify the actual configuration
        # files. For this example, we'll just log the changes.
        
        logger.info("Updating PBX configuration:")
        logger.info(f"SIP port: {fs_config.sip_port}")
        logger.info(f"RTP port range: {fs_config.rtp_port_start}-{fs_config.rtp_port_end}")
        logger.info(f"Extensions: {len(extensions)}")
        logger.info(f"Trunks: {len(trunks)}")
        
        # In a real implementation, update the following files:
        # - sip_profiles/internal.xml
        # - sip_profiles/external.xml
        # - directory/default/*.xml (for extensions)
        # - dialplan/default.xml (for basic call routing)
        # - dialplan/public.xml (for inbound calls from trunks)
        
        # Then restart the service to apply changes
        #restart_freeswitch()
        
        return True
    except Exception as e:
        logger.error(f"Error updating PBX configuration: {str(e)}")
        return False

def check_freeswitch_status():
    """
    Verifica lo stato di FreeSWITCH sull'hardware effettivo
    
    Returns:
        dict: Dictionary with FreeSWITCH status information
    """
    status = {
        'installed': False,
        'running': False,
        'port_listening': False,
        'status': 'not_installed',
        'version': None
    }
    
    try:
        # Metodo 1: Verifica se il pacchetto è installato
        result = subprocess.run(['which', 'freeswitch'], capture_output=True, text=True)
        if result.returncode == 0:
            status['installed'] = True
            status['status'] = 'installed'
            
            # Se è installato, verifica la versione
            try:
                version_result = subprocess.run(['freeswitch', '-version'], capture_output=True, text=True)
                if version_result.returncode == 0:
                    version_match = re.search(r'([\d\.]+)', version_result.stdout)
                    if version_match:
                        status['version'] = version_match.group(1)
            except Exception as e:
                logger.warning(f"Errore nella verifica della versione di FreeSWITCH: {str(e)}")
        
        # Metodo 2: Verifica se il servizio è in esecuzione
        if status['installed']:
            service_result = subprocess.run(['systemctl', 'is-active', 'freeswitch'], capture_output=True, text=True)
            if service_result.stdout.strip() == 'active':
                status['running'] = True
                status['status'] = 'active'
            else:
                # Alternativa per sistemi senza systemd
                ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                if 'freeswitch' in ps_result.stdout:
                    status['running'] = True
                    status['status'] = 'active'
        
        # Metodo 3: Verifica se la porta di FreeSWITCH è in ascolto
        if status['installed']:
            netstat_result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True)
            # Verifica se la porta SIP (5060) è in ascolto
            if ':5060' in netstat_result.stdout:
                status['port_listening'] = True
            
        return status
    except Exception as e:
        logger.error(f"Errore nel controllo dello stato di FreeSWITCH: {str(e)}")
        return status
