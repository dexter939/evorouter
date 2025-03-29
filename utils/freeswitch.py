import logging
import subprocess
import os
import re
import psutil
import xml.etree.ElementTree as ET
from config import (
    FREESWITCH_PATH, FREESWITCH_CONFIG_PATH, 
    FREESWITCH_LOG_PATH, FREESWITCH_DEFAULT_PORT
)
from app import db
from models import FreeswitchConfig, SipExtension, SipTrunk

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
        'uptime': '',
        'version': '',
        'active_calls': 0,
        'sip_registrations': 0,
        'cpu_usage': 0,
        'memory_usage': 0,
        'ports': {}
    }
    
    try:
        # Check if FreeSWITCH is running
        fs_running = False
        fs_pid = None
        
        for proc in psutil.process_iter(['pid', 'name']):
            if 'freeswitch' in proc.info['name'].lower():
                fs_running = True
                fs_pid = proc.info['pid']
                break
        
        status['running'] = fs_running
        
        if fs_running and fs_pid:
            # Get process info
            proc = psutil.Process(fs_pid)
            
            # Get CPU and memory usage
            status['cpu_usage'] = proc.cpu_percent(interval=0.1)
            status['memory_usage'] = proc.memory_info().rss / (1024 * 1024)  # MB
            
            # Get process creation time (uptime)
            uptime_seconds = psutil.time.time() - proc.create_time()
            status['uptime'] = {
                'days': int(uptime_seconds // (60*60*24)),
                'hours': int((uptime_seconds % (60*60*24)) // (60*60)),
                'minutes': int((uptime_seconds % (60*60)) // 60),
                'seconds': int(uptime_seconds % 60)
            }
            
            # Get listening ports
            connections = proc.connections(kind='inet')
            for conn in connections:
                if conn.status == 'LISTEN':
                    status['ports'][conn.laddr.port] = {
                        'ip': conn.laddr.ip,
                        'protocol': 'tcp' if conn.type == socket.SOCK_STREAM else 'udp'
                    }
            
            # Get FreeSWITCH version
            try:
                # Try to get version from FreeSWITCH CLI
                output = subprocess.run(['fs_cli', '-x', 'version'], 
                                      capture_output=True, text=True, timeout=5).stdout
                version_match = re.search(r'FreeSWITCH Version\s+(\S+)', output)
                if version_match:
                    status['version'] = version_match.group(1)
            except:
                status['version'] = 'Unknown'
            
            # Get active calls count
            try:
                output = subprocess.run(['fs_cli', '-x', 'show calls count'], 
                                      capture_output=True, text=True, timeout=5).stdout
                calls_match = re.search(r'total\s+(\d+)', output)
                if calls_match:
                    status['active_calls'] = int(calls_match.group(1))
            except:
                status['active_calls'] = 0
            
            # Get SIP registrations count
            try:
                output = subprocess.run(['fs_cli', '-x', 'sofia status'], 
                                      capture_output=True, text=True, timeout=5).stdout
                reg_match = re.search(r'(\d+)\s+sip', output)
                if reg_match:
                    status['sip_registrations'] = int(reg_match.group(1))
            except:
                status['sip_registrations'] = 0
        
        # Get configuration
        fs_config = FreeswitchConfig.query.first()
        if fs_config:
            status['config'] = {
                'enabled': fs_config.enabled,
                'sip_port': fs_config.sip_port,
                'rtp_port_start': fs_config.rtp_port_start,
                'rtp_port_end': fs_config.rtp_port_end
            }
        else:
            # Create default config
            fs_config = FreeswitchConfig(
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
        # Restart FreeSWITCH service
        subprocess.run(['systemctl', 'restart', 'freeswitch'], check=True)
        
        logger.info("FreeSWITCH service restarted successfully")
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
    Update FreeSWITCH configuration files based on database settings
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get FreeSWITCH config
        fs_config = FreeswitchConfig.query.first()
        if not fs_config:
            logger.error("FreeSWITCH config not found in database")
            return False
        
        # Get extensions and trunks
        extensions = SipExtension.query.all()
        trunks = SipTrunk.query.all()
        
        # Update configuration files
        # In a real implementation, this would modify the actual FreeSWITCH
        # configuration files. For this example, we'll just log the changes.
        
        logger.info("Updating FreeSWITCH configuration:")
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
        
        # Then restart FreeSWITCH to apply changes
        #restart_freeswitch()
        
        return True
    except Exception as e:
        logger.error(f"Error updating FreeSWITCH configuration: {str(e)}")
        return False
