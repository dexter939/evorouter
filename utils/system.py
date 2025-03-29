import os
import platform
import socket
import subprocess
import psutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_system_info():
    """Get basic system information"""
    try:
        info = {
            'hostname': socket.gethostname(),
            'platform': platform.platform(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'uptime': get_uptime(),
            'kernel_version': platform.release(),
            'cpu_model': get_cpu_model(),
            'memory_total': psutil.virtual_memory().total,
            'disk_total': psutil.disk_usage('/').total,
        }
        return info
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {}

def get_system_stats():
    """Get current system statistics"""
    try:
        stats = {
            'cpu_percent': psutil.cpu_percent(interval=0.5),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'cpu_temperature': get_cpu_temperature(),
            'memory_used': psutil.virtual_memory().used,
            'disk_used': psutil.disk_usage('/').used,
            'load_avg': os.getloadavg(),
            'processes': len(psutil.pids()),
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return {}

def get_uptime():
    """Get system uptime in seconds"""
    try:
        return int(time.time() - psutil.boot_time())
    except Exception as e:
        logger.error(f"Error getting uptime: {str(e)}")
        return 0

def get_cpu_model():
    """Get CPU model information"""
    try:
        if platform.system() == 'Linux':
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        return line.split(':', 1)[1].strip()
        # Fallback
        return platform.processor() or "Unknown CPU"
    except Exception as e:
        logger.error(f"Error getting CPU model: {str(e)}")
        return "Unknown CPU"

def get_cpu_temperature():
    """Get CPU temperature"""
    try:
        if platform.system() == 'Linux':
            # Try reading from thermal zones
            for i in range(10):  # Check thermal zones 0-9
                thermal_zone = f"/sys/class/thermal/thermal_zone{i}/temp"
                if os.path.exists(thermal_zone):
                    with open(thermal_zone, 'r') as f:
                        temp = int(f.read().strip()) / 1000.0
                        if temp > 0:
                            return temp
        # If we didn't get a valid temperature, return None
        return None
    except Exception as e:
        logger.error(f"Error getting CPU temperature: {str(e)}")
        return None

def restart_system():
    """Restart the system"""
    try:
        logger.info("Initiating system restart")
        # In a real implementation, we would call the actual reboot command
        # subprocess.run(['reboot'])
        return True
    except Exception as e:
        logger.error(f"Error restarting system: {str(e)}")
        raise

def shutdown_system():
    """Shutdown the system"""
    try:
        logger.info("Initiating system shutdown")
        # In a real implementation, we would call the actual shutdown command
        # subprocess.run(['shutdown', '-h', 'now'])
        return True
    except Exception as e:
        logger.error(f"Error shutting down system: {str(e)}")
        raise

def backup_config(backup_path):
    """Backup system configuration to a file"""
    try:
        # This is a placeholder. In a real implementation, we would:
        # 1. Export database to file
        # 2. Copy network configuration files
        # 3. Copy FreeSWITCH configuration files
        # 4. Compress everything into a single archive
        
        logger.info(f"Backing up system configuration to {backup_path}")
        
        # Example implementation (would be expanded in a real system)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Create a mock backup file
        with open(backup_path, 'w') as f:
            f.write(f"Backup created at {datetime.now().isoformat()}\n")
            f.write("System configuration backup\n")
        
        return True
    except Exception as e:
        logger.error(f"Error backing up configuration: {str(e)}")
        raise

def restore_config(backup_path):
    """Restore system configuration from a backup file"""
    try:
        # This is a placeholder. In a real implementation, we would:
        # 1. Extract archive
        # 2. Import database from file
        # 3. Restore network configuration files
        # 4. Restore FreeSWITCH configuration files
        # 5. Restart necessary services
        
        logger.info(f"Restoring system configuration from {backup_path}")
        
        # Example implementation (would be expanded in a real system)
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file {backup_path} not found")
        
        # Read mock backup file to verify it's valid
        with open(backup_path, 'r') as f:
            if "System configuration backup" not in f.read():
                raise ValueError("Invalid backup file format")
        
        return True
    except Exception as e:
        logger.error(f"Error restoring configuration: {str(e)}")
        raise

import time  # Added for get_uptime function
