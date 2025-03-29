import subprocess
import re
import socket
import json
import os
import logging
import netifaces
import psutil

logger = logging.getLogger(__name__)

def get_interfaces_status():
    """Get status of all network interfaces"""
    interfaces = {}
    
    try:
        # Get all network interfaces
        for iface in netifaces.interfaces():
            if iface == 'lo':  # Skip loopback
                continue
            
            iface_info = {
                'name': iface,
                'status': 'down',
                'mac_address': '',
                'ip_address': '',
                'netmask': '',
                'gateway': '',
                'tx_bytes': 0,
                'rx_bytes': 0,
                'tx_errors': 0,
                'rx_errors': 0
            }
            
            # Get interface addresses
            addrs = netifaces.ifaddresses(iface)
            
            # Get MAC address (link layer)
            if netifaces.AF_LINK in addrs:
                iface_info['mac_address'] = addrs[netifaces.AF_LINK][0]['addr']
            
            # Get IP address (IPv4)
            if netifaces.AF_INET in addrs:
                iface_info['status'] = 'up'
                iface_info['ip_address'] = addrs[netifaces.AF_INET][0]['addr']
                iface_info['netmask'] = addrs[netifaces.AF_INET][0]['netmask']
            
            # Get gateway
            gws = netifaces.gateways()
            if 'default' in gws and netifaces.AF_INET in gws['default']:
                gw_info = gws['default'][netifaces.AF_INET]
                if gw_info[1] == iface:
                    iface_info['gateway'] = gw_info[0]
            
            # Get network stats
            net_stats = psutil.net_io_counters(pernic=True)
            if iface in net_stats:
                iface_info['tx_bytes'] = net_stats[iface].bytes_sent
                iface_info['rx_bytes'] = net_stats[iface].bytes_recv
                iface_info['tx_errors'] = net_stats[iface].errout
                iface_info['rx_errors'] = net_stats[iface].errin
            
            interfaces[iface] = iface_info
    except Exception as e:
        logger.error(f"Error getting interface status: {str(e)}")
    
    return interfaces

def get_interface_details(iface_name):
    """Get detailed statistics for a specific interface"""
    try:
        details = {}
        
        # Get basic info from interfaces
        interfaces = get_interfaces_status()
        if iface_name in interfaces:
            details.update(interfaces[iface_name])
        
        # Get additional details using ethtool (bandwidth, duplex, etc.)
        try:
            ethtool_output = subprocess.check_output(
                ['ethtool', iface_name], 
                stderr=subprocess.STDOUT
            ).decode('utf-8')
            
            # Parse speed
            speed_match = re.search(r'Speed: (\d+\w+)', ethtool_output)
            if speed_match:
                details['speed'] = speed_match.group(1)
            
            # Parse duplex
            duplex_match = re.search(r'Duplex: (\w+)', ethtool_output)
            if duplex_match:
                details['duplex'] = duplex_match.group(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # ethtool might not be available or interface might not support it
            pass
        
        # Get wireless information if applicable
        try:
            iwconfig_output = subprocess.check_output(
                ['iwconfig', iface_name],
                stderr=subprocess.DEVNULL
            ).decode('utf-8')
            
            # If we got output without error, it's a wireless interface
            details['is_wireless'] = True
            
            # Parse SSID
            ssid_match = re.search(r'ESSID:"([^"]*)"', iwconfig_output)
            if ssid_match:
                details['ssid'] = ssid_match.group(1)
            
            # Parse signal level
            signal_match = re.search(r'Signal level=([0-9-]+)', iwconfig_output)
            if signal_match:
                details['signal_level'] = signal_match.group(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            details['is_wireless'] = False
        
        return details
    except Exception as e:
        logger.error(f"Error getting interface details: {str(e)}")
        raise

def apply_network_config(interface):
    """Apply network configuration for an interface
    
    In a real implementation, this would modify network configuration files
    and restart the networking service.
    """
    try:
        logger.info(f"Applying network configuration for {interface.name}")
        
        # For demonstration purposes - in real implementation, we would write to
        # /etc/network/interfaces or use similar system configuration tools
        
        # Simulate interface configuration using ip commands
        if interface.dhcp_enabled:
            logger.info(f"Setting {interface.name} to use DHCP")
            # In a real system, would update the proper config files
            # subprocess.run(['ip', 'addr', 'flush', 'dev', interface.name])
            # subprocess.run(['dhclient', interface.name])
        else:
            logger.info(f"Setting {interface.name} to static IP {interface.ip_address}/{interface.netmask}")
            # In a real system, would update the proper config files
            # subprocess.run(['ip', 'addr', 'flush', 'dev', interface.name])
            # subprocess.run(['ip', 'addr', 'add', f"{interface.ip_address}/{interface.netmask}", 'dev', interface.name])
            # subprocess.run(['ip', 'link', 'set', 'dev', interface.name, 'up'])
            
            # If it's a WAN interface, configure default route
            if interface.is_wan and interface.gateway:
                logger.info(f"Setting default route via {interface.gateway}")
                # subprocess.run(['ip', 'route', 'add', 'default', 'via', interface.gateway])
            
            # Configure DNS servers
            if interface.dns_servers:
                dns_list = interface.dns_servers.split(',')
                logger.info(f"Setting DNS servers: {dns_list}")
                # Would update /etc/resolv.conf or equivalent
        
        return True
    except Exception as e:
        logger.error(f"Error applying network config: {str(e)}")
        raise

def restart_interface(iface_name):
    """Restart a network interface"""
    try:
        logger.info(f"Restarting interface {iface_name}")
        # In a real implementation, we would use system commands to restart the interface
        # subprocess.run(['ip', 'link', 'set', 'dev', iface_name, 'down'])
        # subprocess.run(['ip', 'link', 'set', 'dev', iface_name, 'up'])
        return True
    except Exception as e:
        logger.error(f"Error restarting interface: {str(e)}")
        raise

def scan_wifi_networks():
    """Scan for available WiFi networks"""
    try:
        # In a real implementation, we would use iwlist or similar
        # Example: networks = subprocess.check_output(['iwlist', 'wlan0', 'scan'])
        
        # For demonstration, return some example networks
        networks = [
            {
                'ssid': 'Home Network',
                'signal_strength': -45,
                'channel': 6,
                'security': 'WPA2'
            },
            {
                'ssid': 'Office WiFi',
                'signal_strength': -60,
                'channel': 11,
                'security': 'WPA2-Enterprise'
            },
            {
                'ssid': 'Guest Network',
                'signal_strength': -70,
                'channel': 1,
                'security': 'Open'
            }
        ]
        return networks
    except Exception as e:
        logger.error(f"Error scanning WiFi networks: {str(e)}")
        raise

def get_network_stats():
    """Get network traffic statistics"""
    try:
        stats = {
            'interfaces': {},
            'connections': 0,
            'bytes_sent': 0,
            'bytes_recv': 0
        }
        
        # Get interface stats
        net_io = psutil.net_io_counters(pernic=True)
        for iface, iface_stats in net_io.items():
            if iface != 'lo':  # Skip loopback
                stats['interfaces'][iface] = {
                    'bytes_sent': iface_stats.bytes_sent,
                    'bytes_recv': iface_stats.bytes_recv,
                    'packets_sent': iface_stats.packets_sent,
                    'packets_recv': iface_stats.packets_recv,
                    'errors_in': iface_stats.errin,
                    'errors_out': iface_stats.errout,
                    'drop_in': iface_stats.dropin,
                    'drop_out': iface_stats.dropout
                }
                stats['bytes_sent'] += iface_stats.bytes_sent
                stats['bytes_recv'] += iface_stats.bytes_recv
        
        # Count active connections
        connections = psutil.net_connections()
        stats['connections'] = len([c for c in connections if c.status == 'ESTABLISHED'])
        
        return stats
    except Exception as e:
        logger.error(f"Error getting network stats: {str(e)}")
        return {}

def run_ping(target, count=5):
    """Run ping command and return results"""
    try:
        output = subprocess.check_output(
            ['ping', '-c', str(count), target],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        return output
    except subprocess.CalledProcessError as e:
        return e.output
    except Exception as e:
        logger.error(f"Error running ping: {str(e)}")
        raise

def run_traceroute(target):
    """Run traceroute command and return results"""
    try:
        output = subprocess.check_output(
            ['traceroute', target],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        return output
    except subprocess.CalledProcessError as e:
        return e.output
    except Exception as e:
        logger.error(f"Error running traceroute: {str(e)}")
        raise

def run_dns_lookup(target):
    """Run DNS lookup and return results"""
    try:
        # Get all IP addresses for the hostname
        result = socket.getaddrinfo(target, None)
        
        # Format output
        output = f"DNS lookup for {target}:\n"
        for info in result:
            family, socktype, proto, canonname, sockaddr = info
            if family == socket.AF_INET:  # IPv4
                ip, port = sockaddr
                output += f"IPv4: {ip}\n"
            elif family == socket.AF_INET6:  # IPv6
                ip, port, flow, scope = sockaddr
                output += f"IPv6: {ip}\n"
        
        return output
    except socket.gaierror as e:
        return f"DNS lookup failed: {e}"
    except Exception as e:
        logger.error(f"Error running DNS lookup: {str(e)}")
        raise
