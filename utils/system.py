import logging
import subprocess
import os
import re
import psutil
import time
from datetime import datetime
from config import SYSTEM_LOG_PATH, DIAGNOSTIC_TOOLS

# Create logger
logger = logging.getLogger(__name__)

def get_system_stats():
    """
    Get system statistics
    
    Returns:
        dict: Dictionary with system statistics
    """
    stats = {}
    
    try:
        # CPU information
        stats['cpu'] = {}
        stats['cpu']['usage'] = psutil.cpu_percent(interval=0.1)
        stats['cpu']['count'] = psutil.cpu_count()
        stats['cpu']['frequency'] = psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'
        
        # Memory information
        memory = psutil.virtual_memory()
        stats['memory'] = {}
        stats['memory']['total'] = memory.total
        stats['memory']['available'] = memory.available
        stats['memory']['used'] = memory.used
        stats['memory']['percent'] = memory.percent
        
        # Disk information
        disk = psutil.disk_usage('/')
        stats['disk'] = {}
        stats['disk']['total'] = disk.total
        stats['disk']['free'] = disk.free
        stats['disk']['used'] = disk.used
        stats['disk']['percent'] = disk.percent
        
        # System load
        stats['load_avg'] = os.getloadavg()
        
        # System uptime
        uptime_seconds = time.time() - psutil.boot_time()
        stats['uptime'] = {
            'days': int(uptime_seconds // (60*60*24)),
            'hours': int((uptime_seconds % (60*60*24)) // (60*60)),
            'minutes': int((uptime_seconds % (60*60)) // 60),
            'seconds': int(uptime_seconds % 60)
        }
        
        # System temperature (if available)
        stats['temperature'] = {}
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                # Extract CPU temperature on different systems
                for chip, sensors in temps.items():
                    for sensor in sensors:
                        if any(x in sensor.label.lower() for x in ['cpu', 'core', 'package']):
                            stats['temperature']['cpu'] = sensor.current
                        elif 'sys' in sensor.label.lower():
                            stats['temperature']['system'] = sensor.current
        
        # Network usage information
        network = psutil.net_io_counters(pernic=True)
        stats['network'] = {}
        
        # Get total bytes sent/received across all interfaces
        total_bytes_sent = 0
        total_bytes_recv = 0
        
        for interface, data in network.items():
            if interface != 'lo':  # Skip loopback
                stats['network'][interface] = {
                    'bytes_sent': data.bytes_sent,
                    'bytes_recv': data.bytes_recv,
                    'packets_sent': data.packets_sent,
                    'packets_recv': data.packets_recv,
                    'errin': data.errin,
                    'errout': data.errout,
                    'dropin': data.dropin,
                    'dropout': data.dropout
                }
                total_bytes_sent += data.bytes_sent
                total_bytes_recv += data.bytes_recv
        
        stats['network']['total'] = {
            'bytes_sent': total_bytes_sent,
            'bytes_recv': total_bytes_recv
        }
        
        # System information
        stats['system'] = {}
        
        try:
            # Get OS information
            with open('/etc/os-release', 'r') as f:
                os_info = {}
                for line in f:
                    if '=' in line:
                        key, value = line.rstrip().split('=', 1)
                        os_info[key] = value.strip('"')
            
            stats['system']['os_name'] = os_info.get('PRETTY_NAME', 'Unknown')
        except:
            stats['system']['os_name'] = 'Custom BPI-R4 Router OS'
        
        # Get kernel version
        try:
            kernel_version = subprocess.run(['uname', '-r'], 
                                       capture_output=True, text=True, check=True).stdout.strip()
            stats['system']['kernel'] = kernel_version
        except:
            stats['system']['kernel'] = 'Unknown'
        
        # Get hostname
        try:
            hostname = subprocess.run(['hostname'], 
                                 capture_output=True, text=True, check=True).stdout.strip()
            stats['system']['hostname'] = hostname
        except:
            stats['system']['hostname'] = 'bpi-r4-router'
        
        return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return {'error': str(e)}

def get_network_usage():
    """
    Get current network usage (real-time)
    
    Returns:
        dict: Dictionary with network usage information
    """
    try:
        # Get initial counters
        network_1 = psutil.net_io_counters(pernic=True)
        
        # Wait for a short time
        time.sleep(1)
        
        # Get counters again
        network_2 = psutil.net_io_counters(pernic=True)
        
        # Calculate usage
        usage = {}
        
        for interface, data_2 in network_2.items():
            if interface != 'lo' and interface in network_1:  # Skip loopback
                data_1 = network_1[interface]
                
                # Calculate bytes/sec
                bytes_sent = data_2.bytes_sent - data_1.bytes_sent
                bytes_recv = data_2.bytes_recv - data_1.bytes_recv
                
                usage[interface] = {
                    'bytes_sent': bytes_sent,
                    'bytes_recv': bytes_recv,
                    'mbits_sent': bytes_sent * 8 / 1000000,
                    'mbits_recv': bytes_recv * 8 / 1000000
                }
        
        return usage
    except Exception as e:
        logger.error(f"Error getting network usage: {str(e)}")
        return {'error': str(e)}

def reboot_system():
    """
    Reboot the system
    
    Returns:
        bool: True if successful
    """
    try:
        logger.info("System reboot initiated")
        subprocess.Popen(['sleep', '5', '&&', 'reboot'], shell=True)
        return True
    except Exception as e:
        logger.error(f"Error rebooting system: {str(e)}")
        return False

def shutdown_system():
    """
    Shutdown the system
    
    Returns:
        bool: True if successful
    """
    try:
        logger.info("System shutdown initiated")
        subprocess.Popen(['sleep', '5', '&&', 'poweroff'], shell=True)
        return True
    except Exception as e:
        logger.error(f"Error shutting down system: {str(e)}")
        return False

def get_system_logs(log_type='system', lines=100):
    """
    Get system logs
    
    Args:
        log_type: Type of log to retrieve (system, network, freeswitch, security)
        lines: Number of lines to retrieve
        
    Returns:
        list: List of log entries
    """
    log_entries = []
    
    try:
        log_file = None
        
        if log_type == 'system':
            log_file = '/var/log/syslog'
        elif log_type == 'network':
            log_file = '/var/log/network.log'
        elif log_type == 'freeswitch':
            log_file = '/var/log/freeswitch/freeswitch.log'
        elif log_type == 'security':
            log_file = '/var/log/auth.log'
        else:
            logger.error(f"Unknown log type: {log_type}")
            return []
        
        if not os.path.exists(log_file):
            # Return mock data if log file doesn't exist
            # In a real system, these log files should exist
            for i in range(min(lines, 10)):
                log_entries.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'level': 'info',
                    'message': f'Example {log_type} log entry {i+1}'
                })
            return log_entries
        
        # Get the last N lines of the log file
        output = subprocess.run(['tail', '-n', str(lines), log_file], 
                               capture_output=True, text=True, check=True).stdout
        
        # Parse log entries
        for line in output.splitlines():
            # Try to parse syslog format
            match = re.match(r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+\w+\s+([^:]+):\s+(.+)', line)
            if match:
                timestamp, facility, message = match.groups()
                level = 'info'
                
                # Try to determine log level from message or facility
                if any(x in message.lower() for x in ['error', 'fail', 'critical']):
                    level = 'error'
                elif any(x in message.lower() for x in ['warn']):
                    level = 'warning'
                elif any(x in message.lower() for x in ['debug']):
                    level = 'debug'
                
                log_entries.append({
                    'timestamp': timestamp,
                    'level': level,
                    'message': message
                })
            else:
                # If can't parse, add as-is
                log_entries.append({
                    'timestamp': '',
                    'level': 'info',
                    'message': line
                })
        
        return log_entries
    except Exception as e:
        logger.error(f"Error getting system logs: {str(e)}")
        return []

def clear_logs(log_type='system'):
    """
    Clear system logs
    
    Args:
        log_type: Type of log to clear (system, network, freeswitch, security)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        log_file = None
        
        if log_type == 'system':
            log_file = '/var/log/syslog'
        elif log_type == 'network':
            log_file = '/var/log/network.log'
        elif log_type == 'freeswitch':
            log_file = '/var/log/freeswitch/freeswitch.log'
        elif log_type == 'security':
            log_file = '/var/log/auth.log'
        else:
            logger.error(f"Unknown log type: {log_type}")
            return False
        
        # Check if log file exists
        if not os.path.exists(log_file):
            logger.warning(f"Log file {log_file} does not exist")
            return True
        
        # Clear log file
        with open(log_file, 'w') as f:
            f.write('')
        
        logger.info(f"Log file {log_file} cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing logs: {str(e)}")
        return False

def run_diagnostic(tool, parameters=''):
    """
    Run a diagnostic tool
    
    Args:
        tool: Name of the diagnostic tool to run
        parameters: Parameters to pass to the tool
        
    Returns:
        str: Result of the diagnostic tool
    """
    try:
        if tool not in DIAGNOSTIC_TOOLS:
            logger.error(f"Unknown diagnostic tool: {tool}")
            return f"Error: Unknown diagnostic tool '{tool}'"
        
        # Get tool path
        tool_path = DIAGNOSTIC_TOOLS.get(tool)
        
        # Parse parameters
        params = parameters.split()
        
        # Run the diagnostic tool
        output = subprocess.run([tool_path] + params, 
                               capture_output=True, text=True, timeout=30)
        
        return output.stdout if output.stdout else output.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Diagnostic tool {tool} timed out")
        return "Error: Diagnostic tool timed out"
    except Exception as e:
        logger.error(f"Error running diagnostic tool {tool}: {str(e)}")
        return f"Error: {str(e)}"

def get_installed_packages():
    """
    Get list of installed packages
    
    Returns:
        list: List of dictionaries with package information
    """
    packages = []
    
    try:
        # Try with dpkg (Debian-based)
        try:
            output = subprocess.run(['dpkg-query', '-W', '-f=${Package}|${Version}|${Status}\n'], 
                                   capture_output=True, text=True, check=True).stdout
            
            for line in output.splitlines():
                parts = line.split('|')
                if len(parts) >= 3 and 'install ok installed' in parts[2]:
                    packages.append({
                        'name': parts[0],
                        'version': parts[1],
                        'status': 'installed'
                    })
        except:
            # Try with rpm (Red Hat-based)
            try:
                output = subprocess.run(['rpm', '-qa', '--queryformat', '%{NAME}|%{VERSION}|installed\n'], 
                                       capture_output=True, text=True, check=True).stdout
                
                for line in output.splitlines():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        packages.append({
                            'name': parts[0],
                            'version': parts[1],
                            'status': parts[2]
                        })
            except:
                # Mock data for simulation
                packages = [
                    {'name': 'freeswitch', 'version': '1.10.7', 'status': 'installed'},
                    {'name': 'bpi-r4-kernel', 'version': '5.10.0', 'status': 'installed'},
                    {'name': 'nginx', 'version': '1.18.0', 'status': 'installed'},
                    {'name': 'isc-dhcp-server', 'version': '4.4.1', 'status': 'installed'}
                ]
        
        return packages
    except Exception as e:
        logger.error(f"Error getting installed packages: {str(e)}")
        return []

def check_for_updates():
    """
    Check for available updates
    
    Returns:
        list: List of dictionaries with update information
    """
    updates = []
    
    try:
        # Try with apt (Debian-based)
        try:
            # Update package lists
            subprocess.run(['apt-get', 'update'], 
                          capture_output=True, text=True, check=True)
            
            # Get list of upgradable packages
            output = subprocess.run(['apt-get', 'upgrade', '-s'], 
                                   capture_output=True, text=True, check=True).stdout
            
            for line in output.splitlines():
                if 'Inst' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        package_name = parts[1]
                        current_version = parts[2].strip('[]')
                        new_version = parts[3].strip('()').split(':')[-1]
                        
                        updates.append({
                            'name': package_name,
                            'current_version': current_version,
                            'new_version': new_version
                        })
        except:
            # Mock data for simulation
            updates = [
                {'name': 'freeswitch', 'current_version': '1.10.7', 'new_version': '1.10.8'},
                {'name': 'bpi-r4-kernel', 'current_version': '5.10.0', 'new_version': '5.10.1'}
            ]
        
        return updates
    except Exception as e:
        logger.error(f"Error checking for updates: {str(e)}")
        return []

def install_update(package='all'):
    """
    Install updates
    
    Args:
        package: Package to update, or 'all' for all packages
        
    Returns:
        dict: Result of the update operation
    """
    try:
        if package == 'all':
            # Update all packages
            try:
                # Try with apt (Debian-based)
                output = subprocess.run(['apt-get', 'upgrade', '-y'], 
                                       capture_output=True, text=True, check=True).stdout
                
                return {
                    'success': True,
                    'message': 'All updates installed successfully',
                    'details': output
                }
            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'message': 'Error installing updates',
                    'details': e.stderr
                }
        else:
            # Update specific package
            try:
                # Try with apt (Debian-based)
                output = subprocess.run(['apt-get', 'install', '--only-upgrade', package, '-y'], 
                                       capture_output=True, text=True, check=True).stdout
                
                return {
                    'success': True,
                    'message': f'Package {package} updated successfully',
                    'details': output
                }
            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'message': f'Error updating package {package}',
                    'details': e.stderr
                }
    except Exception as e:
        logger.error(f"Error installing updates: {str(e)}")
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'details': ''
        }
