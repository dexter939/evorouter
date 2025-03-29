import logging
import subprocess
import os
import re
import psutil
import time
from datetime import datetime, timedelta
from config import (
    SYSTEM_LOG_PATH, DIAGNOSTIC_TOOLS,
    DEFAULT_LAN_INTERFACE, DEFAULT_WAN_INTERFACE
)

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
        logger.info("System reboot simulated in Replit environment")
        # In a real BPI-R4 system, we would execute:
        # subprocess.Popen(['sleep', '5', '&&', 'reboot'], shell=True)
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
        logger.info("System shutdown simulated in Replit environment")
        # In a real BPI-R4 system, we would execute:
        # subprocess.Popen(['sleep', '5', '&&', 'poweroff'], shell=True)
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
        # In Replit environment, simulate system logs
        # since we don't have access to the real system logs
        
        # Generate simulated log entries based on log type
        current_time = datetime.now()
        for i in range(min(lines, 50)):
            # Create a timestamp 10 minutes apart for each entry
            entry_time = current_time - timedelta(minutes=10 * (lines - i))
            timestamp = entry_time.strftime('%b %d %H:%M:%S')
            
            # Determine log level (mostly info, some warnings and errors)
            level_roll = i % 10
            if level_roll == 0:
                level = 'error'
            elif level_roll in [3, 7]:
                level = 'warning'
            else:
                level = 'info'
                
            # Create appropriate message based on log type
            if log_type == 'system':
                if level == 'error':
                    message = f"System process crashed: Out of memory"
                elif level == 'warning':
                    message = f"System resource usage high: CPU at 85%"
                else:
                    message = f"System service started: systemd[{i+100}]"
            elif log_type == 'network':
                if level == 'error':
                    message = f"Network connection lost on {DEFAULT_WAN_INTERFACE}"
                elif level == 'warning':
                    message = f"DHCP lease renewal failed, retrying..."
                else:
                    message = f"Network interface {DEFAULT_LAN_INTERFACE} is up"
            elif log_type == 'freeswitch':
                if level == 'error':
                    message = f"SIP registration failed for extension 1001"
                elif level == 'warning':
                    message = f"Call quality degraded for call ID: CALL-{i+1000}"
                else:
                    message = f"FreeSWITCH processed call to extension 1003"
            elif log_type == 'security':
                if level == 'error':
                    message = f"Failed login attempt for user admin from 192.168.1.{i+10}"
                elif level == 'warning':
                    message = f"Multiple login attempts detected from 192.168.1.{i+10}"
                else:
                    message = f"User admin logged in successfully"
            else:
                message = f"Log entry {i+1} for {log_type}"
                
            log_entries.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
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
        
        # In Replit environment, simulate diagnostic tools
        # since we don't have the real tools available
        
        # Simulate different outputs based on the tool
        if tool == 'ping':
            # Parse parameters to extract hostname
            params = parameters.split()
            hostname = 'localhost'
            
            for i, param in enumerate(params):
                if not param.startswith('-') and i > 0 and params[i-1] not in ['-c', '-s']:
                    hostname = param
                    break
                if i == len(params) - 1:
                    hostname = param
            
            # Random ping times
            import random
            ping_time_base = random.uniform(10, 100)
            ping_times = [ping_time_base + random.uniform(-5, 5) for _ in range(4)]
            
            return f"PING {hostname} 56(84) bytes of data.\n" + \
                   f"64 bytes from {hostname}: icmp_seq=1 ttl=64 time={ping_times[0]:.3f} ms\n" + \
                   f"64 bytes from {hostname}: icmp_seq=2 ttl=64 time={ping_times[1]:.3f} ms\n" + \
                   f"64 bytes from {hostname}: icmp_seq=3 ttl=64 time={ping_times[2]:.3f} ms\n" + \
                   f"64 bytes from {hostname}: icmp_seq=4 ttl=64 time={ping_times[3]:.3f} ms\n\n" + \
                   f"--- {hostname} ping statistics ---\n" + \
                   f"4 packets transmitted, 4 received, 0% packet loss, time 3003ms\n" + \
                   f"rtt min/avg/max/mdev = {min(ping_times):.3f}/{sum(ping_times)/4:.3f}/{max(ping_times):.3f}/{(max(ping_times)-min(ping_times))/4:.3f} ms"
        
        elif tool == 'traceroute':
            # Parse parameters to extract hostname
            params = parameters.split()
            hostname = 'localhost'
            
            for i, param in enumerate(params):
                if not param.startswith('-') and i > 0 and params[i-1] not in ['-m']:
                    hostname = param
                    break
                if i == len(params) - 1:
                    hostname = param
            
            # Generate random hops
            import random
            
            # Number of hops to simulate
            max_hops = 5 + random.randint(0, 10)
            output = f"traceroute to {hostname}, 30 hops max, 60 byte packets\n"
            
            current_time = 20.0  # Start with base latency
            
            for hop in range(1, max_hops + 1):
                # Random IP for router
                router_ip = f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
                router_name = f"router-{hop}.net"
                
                # Random latency that increases with each hop
                latency1 = current_time + random.uniform(1, 5)
                latency2 = current_time + random.uniform(1, 5)
                latency3 = current_time + random.uniform(1, 5)
                
                output += f" {hop}  {router_name} ({router_ip})  {latency1:.3f} ms  {latency2:.3f} ms  {latency3:.3f} ms\n"
                
                current_time += random.uniform(5, 15)  # Increment base latency
            
            # Final hop to destination
            final_latency1 = current_time + random.uniform(1, 5)
            final_latency2 = current_time + random.uniform(1, 5)
            final_latency3 = current_time + random.uniform(1, 5)
            
            output += f" {max_hops + 1}  {hostname} ({random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)})  {final_latency1:.3f} ms  {final_latency2:.3f} ms  {final_latency3:.3f} ms\n"
            
            return output
            
        elif tool == 'nslookup':
            # Parse parameters to extract domain
            params = parameters.split()
            domain = params[-1] if params else 'localhost'
            
            # Generate random IP
            import random
            ip1 = random.randint(1, 255)
            ip2 = random.randint(0, 255)
            ip3 = random.randint(0, 255)
            ip4 = random.randint(1, 254)
            
            return f"Server:\t\t8.8.8.8\n" + \
                   f"Address:\t8.8.8.8#53\n\n" + \
                   f"Non-authoritative answer:\n" + \
                   f"Name:\t{domain}\n" + \
                   f"Address: {ip1}.{ip2}.{ip3}.{ip4}\n"
        
        elif tool == 'dig':
            # Parse parameters to extract domain and record type
            params = parameters.split()
            domain = params[0] if params else 'localhost'
            record_type = params[1] if len(params) > 1 else 'A'
            
            # Generate simulated dig output based on record type
            import random
            from datetime import datetime
            
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            query_time = random.uniform(10, 100)
            
            header = f"; <<>> DiG 9.16.1-Ubuntu <<>> {domain} {record_type}\n" + \
                     f";; global options: +cmd\n" + \
                     f";; Got answer:\n" + \
                     f";; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: {random.randint(1000, 9999)}\n" + \
                     f";; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1\n\n"
            
            question = f";; QUESTION SECTION:\n" + \
                       f";{domain}.\t\tIN\t{record_type}\n\n"
            
            answer = f";; ANSWER SECTION:\n"
            
            if record_type == 'A' or record_type == 'a':
                # Generate random IP
                ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
                answer += f"{domain}.\t\t3600\tIN\tA\t{ip}\n\n"
            elif record_type == 'MX' or record_type == 'mx':
                # Generate random mail server
                answer += f"{domain}.\t\t3600\tIN\tMX\t10 mail1.{domain}.\n"
                answer += f"{domain}.\t\t3600\tIN\tMX\t20 mail2.{domain}.\n\n"
            elif record_type == 'NS' or record_type == 'ns':
                # Generate random name servers
                answer += f"{domain}.\t\t3600\tIN\tNS\tns1.{domain}.\n"
                answer += f"{domain}.\t\t3600\tIN\tNS\tns2.{domain}.\n\n"
            elif record_type == 'TXT' or record_type == 'txt':
                # Generate random TXT record
                answer += f"{domain}.\t\t3600\tIN\tTXT\t\"v=spf1 include:_spf.{domain} ~all\"\n\n"
            else:
                # Default record
                answer += f"{domain}.\t\t3600\tIN\t{record_type}\tgeneric.{domain}.\n\n"
            
            footer = f";; Query time: {int(query_time)} msec\n" + \
                     f";; SERVER: 8.8.8.8#53(8.8.8.8)\n" + \
                     f";; WHEN: {datetime.now().strftime('%a %b %d %H:%M:%S')} UTC {datetime.now().year}\n" + \
                     f";; MSG SIZE  rcvd: {random.randint(50, 150)}\n"
            
            return header + question + answer + footer
        
        elif tool == 'iperf':
            # Generate simulated iperf output
            import random
            from datetime import datetime
            
            output = f"Connecting to host iperf.server.com, port 5201\n"
            output += f"[  5] local 192.168.1.10 port 49152 connected to 203.0.113.45 port 5201\n"
            output += f"[ ID] Interval           Transfer     Bitrate         Retr\n"
            
            total_bits = 0
            
            # Generate 10 intervals
            for i in range(1, 11):
                # Random bandwidth between 50-150 Mbits/sec
                bandwidth = random.uniform(50, 150)
                total_bits += bandwidth
                
                output += f"[  5] {i-1:.1f}-{i:.1f}   sec  {bandwidth/8:.1f} MBytes  {bandwidth:.1f} Mbits/sec  {random.randint(0, 2)}\n"
            
            # Summary line
            output += f"- - - - - - - - - - - - - - - - - - - - - - - - -\n"
            output += f"[ ID] Interval           Transfer     Bitrate         Retr\n"
            output += f"[  5] 0.0-10.0  sec  {total_bits/8:.1f} MBytes  {total_bits/10:.1f} Mbits/sec  {random.randint(1, 10)}\n"
            
            return output
            
        # Default fallback for unknown tools
        return f"Simulated output for {tool} with parameters: {parameters}"
        
    except Exception as e:
        logger.error(f"Error running diagnostic tool {tool}: {str(e)}")
        return f"Error: {str(e)}"

def get_network_usage():
    """
    Get network usage statistics
    
    Returns:
        dict: Dictionary with network usage statistics
    """
    try:
        # In Replit environment, we'll create simulated data
        import random
        
        # Generate random usage data
        usage = {
            "total_rx": random.randint(1000000000, 10000000000),  # Total received bytes
            "total_tx": random.randint(500000000, 5000000000),    # Total transmitted bytes
            "current_rx": random.randint(50000, 5000000),         # Current receive rate (bytes/sec)
            "current_tx": random.randint(10000, 1000000),         # Current transmit rate (bytes/sec)
            "interfaces": {
                "eth0": {
                    "rx": random.randint(500000000, 5000000000),
                    "tx": random.randint(100000000, 1000000000),
                    "rx_rate": random.randint(10000, 1000000),
                    "tx_rate": random.randint(5000, 500000)
                },
                "eth1": {
                    "rx": random.randint(500000000, 5000000000),
                    "tx": random.randint(100000000, 1000000000),
                    "rx_rate": random.randint(10000, 1000000),
                    "tx_rate": random.randint(5000, 500000)
                },
                "wlan0": {
                    "rx": random.randint(100000000, 1000000000),
                    "tx": random.randint(50000000, 500000000),
                    "rx_rate": random.randint(5000, 500000),
                    "tx_rate": random.randint(1000, 100000)
                }
            }
        }
        
        return usage
    except Exception as e:
        logger.error(f"Error getting network usage: {str(e)}")
        return {}

def get_installed_packages():
    """
    Get list of installed packages
    
    Returns:
        list: List of dictionaries with package information
    """
    packages = []
    
    try:
        # In Replit environment, simulate installed packages
        # for the BPI-R4 Router OS
        
        # Core packages
        packages = [
            {'name': 'freeswitch', 'version': '1.10.7', 'status': 'installed'},
            {'name': 'bpi-r4-kernel', 'version': '5.10.0', 'status': 'installed'},
            {'name': 'nginx', 'version': '1.18.0', 'status': 'installed'},
            {'name': 'isc-dhcp-server', 'version': '4.4.1', 'status': 'installed'},
            {'name': 'hostapd', 'version': '2.9', 'status': 'installed'},
            {'name': 'nftables', 'version': '0.9.8', 'status': 'installed'},
            {'name': 'bind9', 'version': '9.16.1', 'status': 'installed'},
            {'name': 'python3', 'version': '3.9.2', 'status': 'installed'},
            {'name': 'flask', 'version': '2.0.1', 'status': 'installed'},
            {'name': 'sqlite3', 'version': '3.34.1', 'status': 'installed'},
            {'name': 'openssh-server', 'version': '8.4p1', 'status': 'installed'},
            {'name': 'snmpd', 'version': '5.9', 'status': 'installed'},
            {'name': 'iptables', 'version': '1.8.7', 'status': 'installed'}
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
        # In Replit environment, simulate update check results
        # for the BPI-R4 Router OS
        
        # Security updates available
        updates = [
            {'name': 'freeswitch', 'current_version': '1.10.7', 'new_version': '1.10.8'},
            {'name': 'bpi-r4-kernel', 'current_version': '5.10.0', 'new_version': '5.10.1'},
            {'name': 'openssh-server', 'current_version': '8.4p1', 'new_version': '8.4p2'},
            {'name': 'bind9', 'current_version': '9.16.1', 'new_version': '9.16.3'}
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
        # In Replit environment, simulate updating packages
        # for the BPI-R4 Router OS
        
        # Generate simulated output based on package
        if package == 'all':
            # Simulate output for updating all packages
            result = {
                'success': True,
                'message': 'All updates installed successfully',
                'details': 'Reading package lists...\n' + 
                           'Building dependency tree...\n' + 
                           'Reading state information...\n' + 
                           'Calculating upgrade...\n' + 
                           'The following packages will be upgraded:\n' +
                           '  freeswitch bpi-r4-kernel openssh-server bind9\n' +
                           '4 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.\n' +
                           'Need to get 15.2 MB of archives.\n' +
                           'After this operation, 156 kB of additional disk space will be used.\n' +
                           'Get:1 http://deb.debian.org/debian buster/main amd64 freeswitch amd64 1.10.8 [5,642 kB]\n' +
                           'Get:2 http://security.debian.org/debian-security buster/updates/main amd64 openssh-server amd64 8.4p2 [336 kB]\n' +
                           'Get:3 http://deb.debian.org/debian buster/main amd64 bpi-r4-kernel amd64 5.10.1 [8,724 kB]\n' +
                           'Get:4 http://security.debian.org/debian-security buster/updates/main amd64 bind9 amd64 9.16.3 [521 kB]\n' +
                           'Fetched 15.2 MB in 3s (5,067 kB/s)\n' +
                           'Preparing to unpack .../freeswitch_1.10.8_amd64.deb ...\n' +
                           'Unpacking freeswitch (1.10.8) over (1.10.7) ...\n' +
                           'Preparing to unpack .../openssh-server_8.4p2_amd64.deb ...\n' +
                           'Unpacking openssh-server (8.4p2) over (8.4p1) ...\n' +
                           'Preparing to unpack .../bpi-r4-kernel_5.10.1_amd64.deb ...\n' +
                           'Unpacking bpi-r4-kernel (5.10.1) over (5.10.0) ...\n' +
                           'Preparing to unpack .../bind9_9.16.3_amd64.deb ...\n' +
                           'Unpacking bind9 (9.16.3) over (9.16.1) ...\n' +
                           'Setting up freeswitch (1.10.8) ...\n' +
                           'Setting up openssh-server (8.4p2) ...\n' +
                           'Setting up bpi-r4-kernel (5.10.1) ...\n' +
                           'Setting up bind9 (9.16.3) ...\n' +
                           'Processing triggers for man-db (2.8.5-2) ...\n' +
                           'Processing triggers for systemd (241-7~deb10u10) ...'
            }
        else:
            # Simulate output for updating a specific package
            if package in ['freeswitch', 'bpi-r4-kernel', 'openssh-server', 'bind9']:
                # Get the current and new version information
                current_version = '1.10.7' if package == 'freeswitch' else '5.10.0' if package == 'bpi-r4-kernel' else '8.4p1' if package == 'openssh-server' else '9.16.1'
                new_version = '1.10.8' if package == 'freeswitch' else '5.10.1' if package == 'bpi-r4-kernel' else '8.4p2' if package == 'openssh-server' else '9.16.3'
                
                result = {
                    'success': True,
                    'message': f'Package {package} updated successfully',
                    'details': f'Reading package lists...\n' + 
                               f'Building dependency tree...\n' + 
                               f'Reading state information...\n' + 
                               f'The following packages will be upgraded:\n' +
                               f'  {package}\n' +
                               f'1 upgraded, 0 newly installed, 0 to remove and 3 not upgraded.\n' +
                               f'Need to get 5.6 MB of archives.\n' +
                               f'After this operation, 36 kB of additional disk space will be used.\n' +
                               f'Get:1 http://deb.debian.org/debian buster/main amd64 {package} amd64 {new_version} [5,642 kB]\n' +
                               f'Fetched 5.6 MB in 1s (5,642 kB/s)\n' +
                               f'Preparing to unpack .../{package}_{new_version}_amd64.deb ...\n' +
                               f'Unpacking {package} ({new_version}) over ({current_version}) ...\n' +
                               f'Setting up {package} ({new_version}) ...\n' +
                               f'Processing triggers for man-db (2.8.5-2) ...\n' +
                               f'Processing triggers for systemd (241-7~deb10u10) ...'
                }
            else:
                # Package not found
                result = {
                    'success': False,
                    'message': f'Error updating package {package}',
                    'details': f'E: Unable to locate package {package}'
                }
        
        return result
    except Exception as e:
        logger.error(f"Error installing updates: {str(e)}")
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'details': ''
        }
