import logging
import subprocess
import re
import os
import ipaddress
from config import (
    DEFAULT_LAN_INTERFACE, DEFAULT_WAN_INTERFACE, DEFAULT_WIFI_INTERFACE,
    DEFAULT_LAN_IP, DEFAULT_LAN_SUBNET,
    NETWORK_CONFIG_PATH, DHCP_CONFIG_PATH, DNS_CONFIG_PATH
)

# Create logger
logger = logging.getLogger(__name__)

def get_interfaces_status():
    """
    Get status of all network interfaces
    
    Returns:
        list: List of dictionaries with interface information
    """
    interfaces = []
    
    try:
        # In Replit environment, we'll simulate the network interfaces
        # Instead of using 'ip' command which isn't available
        
        # Define default interfaces for simulation
        simulated_interfaces = [
            {
                'name': DEFAULT_LAN_INTERFACE,
                'status': 'up',
                'mac_address': '02:42:ac:11:00:02',
                'ip_address': DEFAULT_LAN_IP,
                'subnet_mask': DEFAULT_LAN_SUBNET,
                'gateway': '',
                'mode': 'static',
                'type': 'lan'
            },
            {
                'name': DEFAULT_WAN_INTERFACE,
                'status': 'up',
                'mac_address': '02:42:ac:11:00:03',
                'ip_address': '192.168.0.100',
                'subnet_mask': '255.255.255.0',
                'gateway': '192.168.0.1',
                'mode': 'dhcp',
                'type': 'wan'
            }
        ]
        
        # In Replit environment we want to use simulated interfaces
        # with customized data to match our configuration expectations
        
        # We'll maintain the simulated interfaces for our router demo
        # but try to incorporate real MAC addresses from the actual interfaces
        try:
            import psutil
            import socket
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            # Get real MAC addresses if possible
            real_macs = {}
            for interface_name, addrs in net_if_addrs.items():
                if interface_name == 'lo':  # Skip loopback
                    continue
                
                for addr in addrs:
                    if hasattr(addr, 'family') and addr.family == psutil.AF_LINK:
                        real_macs[interface_name] = addr.address
            
            # Update our simulated interfaces with real MAC addresses if available
            for interface in simulated_interfaces:
                if interface['name'] in real_macs:
                    interface['mac_address'] = real_macs[interface['name']]
                    
            # Get the most likely real network interface for external access
            real_interface = None
            for interface_name, addrs in net_if_addrs.items():
                if interface_name != 'lo':  # Skip loopback
                    for addr in addrs:
                        if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                            # Found a likely external interface
                            if 'wan_interface' not in locals():
                                # Update the WAN interface with the real IP in our simulated data
                                for interface in simulated_interfaces:
                                    if interface['type'] == 'wan':
                                        interface['ip_address'] = addr.address
                                        interface['subnet_mask'] = addr.netmask or '255.255.255.0'
                                        # Add possible gateway
                                        octets = addr.address.split('.')
                                        if len(octets) == 4:
                                            interface['gateway'] = f"{octets[0]}.{octets[1]}.{octets[2]}.1"
                                        break
        except Exception as psutil_err:
            logger.warning(f"Couldn't get network interfaces from psutil: {str(psutil_err)}")
        
        return simulated_interfaces
    except Exception as e:
        logger.error(f"Error getting interface status: {str(e)}")
        # Return minimal simulated interfaces on error
        return [
            {
                'name': DEFAULT_LAN_INTERFACE,
                'status': 'up',
                'mac_address': '02:42:ac:11:00:02',
                'ip_address': DEFAULT_LAN_IP,
                'subnet_mask': DEFAULT_LAN_SUBNET,
                'gateway': '',
                'mode': 'static',
                'type': 'lan'
            }
        ]

def configure_interface(interface_name, ip_mode, ip_address=None, subnet_mask=None, gateway=None, dns_servers=None, 
                      pppoe_username=None, pppoe_password=None, pppoe_service_name=None):
    """
    Configure a network interface
    
    Args:
        interface_name: Name of the interface to configure
        ip_mode: 'dhcp', 'static' or 'pppoe'
        ip_address: Static IP address (required if ip_mode is 'static')
        subnet_mask: Subnet mask (required if ip_mode is 'static')
        gateway: Default gateway (optional for static)
        dns_servers: DNS servers (optional for static and pppoe)
        pppoe_username: PPPoE username (required if ip_mode is 'pppoe')
        pppoe_password: PPPoE password (required if ip_mode is 'pppoe')
        pppoe_service_name: PPPoE service name (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate input
        if ip_mode not in ['dhcp', 'static', 'pppoe']:
            logger.error(f"Invalid IP mode: {ip_mode}")
            return False
            
        if ip_mode == 'static' and (not ip_address or not subnet_mask):
            logger.error("IP address and subnet mask are required for static configuration")
            return False
            
        if ip_mode == 'pppoe' and (not pppoe_username or not pppoe_password):
            logger.error("Username and password are required for PPPoE configuration")
            return False
        
        # Create network interface configuration file
        config_file = os.path.join(NETWORK_CONFIG_PATH, interface_name)
        
        # Generate configuration content
        if ip_mode == 'dhcp':
            config_content = f"""auto {interface_name}
iface {interface_name} inet dhcp
"""
        elif ip_mode == 'static':
            # Convert subnet mask to CIDR notation
            subnet = ipaddress.IPv4Network(f'0.0.0.0/{subnet_mask}', False)
            cidr = subnet.prefixlen
            
            config_content = f"""auto {interface_name}
iface {interface_name} inet static
    address {ip_address}/{cidr}
"""
            if gateway:
                config_content += f"    gateway {gateway}\n"
        else:  # pppoe
            # For PPPoE, first configure the Ethernet interface
            config_content = f"""auto {interface_name}
iface {interface_name} inet manual
    pre-up ip link set dev {interface_name} up
    post-down ip link set dev {interface_name} down

# PPPoE connection
auto ppp0
iface ppp0 inet ppp
    provider {interface_name}_provider
"""
            
            # Create provider file for PPPoE
            provider_file = os.path.join('/etc/ppp/peers', f'{interface_name}_provider')
            provider_content = f"""# PPPoE provider configuration for {interface_name}
plugin rp-pppoe.so
{interface_name}
user "{pppoe_username}"
password "{pppoe_password}"
"""
            if pppoe_service_name:
                provider_content += f'servicename "{pppoe_service_name}"\n'
                
            provider_content += """noipdefault
defaultroute
replacedefaultroute
hide-password
noauth
persist
maxfail 0
"""
            
            # In Replit environment, just log the provider file that would be created
            logger.info(f"Would create PPPoE provider file at {provider_file} with configuration:\n{provider_content}")
        
        # Log the configuration that would be written
        logger.info(f"Would write interface configuration to {config_file}:\n{config_content}")
        
        # If DNS servers are provided, simulate updating resolv.conf
        if dns_servers:
            logger.info(f"Would update DNS settings: Primary={dns_servers.split(',')[0] if ',' in dns_servers else dns_servers}, Secondary={dns_servers.split(',')[1] if ',' in dns_servers else None}")
        
        logger.info(f"Successfully simulated configuration of interface {interface_name} with {ip_mode} mode")
        return True
    except Exception as e:
        logger.error(f"Error configuring interface {interface_name}: {str(e)}")
        return False

def set_dhcp_config(enabled, start_ip, end_ip, lease_time):
    """
    Configure DHCP server
    
    Args:
        enabled: Whether to enable DHCP server
        start_ip: Start of DHCP IP range
        end_ip: End of DHCP IP range
        lease_time: Lease time in hours
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        dhcp_conf_file = os.path.join(DHCP_CONFIG_PATH, 'dhcpd.conf')
        
        if not enabled:
            # If disabled, write minimal config
            config_content = """# DHCP server disabled
"""
        else:
            # For Replit environment, we'll use the configured LAN IP and settings
            # rather than relying on the actual interface detected
            
            # Get the LAN IP and subnet from our default configuration
            lan_ip = DEFAULT_LAN_IP
            lan_subnet = DEFAULT_LAN_SUBNET
            
            # Calculate network address and broadcast for the default/configured LAN
            try:
                # Try to get network details from the local interface configuration if possible
                interfaces = get_interfaces_status()
                lan_interface = next((i for i in interfaces if i['type'] == 'lan'), None)
                
                if lan_interface and lan_interface['ip_address'] and lan_interface['subnet_mask']:
                    # Make sure we're using the correct subnet for LAN range
                    first_three_octets_lan = '.'.join(start_ip.split('.')[:3])
                    first_three_octets_router = '.'.join(lan_interface['ip_address'].split('.')[:3])
                    
                    # If the DHCP range is in a different subnet than the router,
                    # force the range to be in the router's subnet
                    if first_three_octets_lan != first_three_octets_router:
                        logger.warning(f"DHCP range {start_ip}-{end_ip} is not in the same subnet as the router ({lan_interface['ip_address']})")
                        # Keep the same last octet but change the first three to match the router
                        start_ip_last = start_ip.split('.')[-1]
                        end_ip_last = end_ip.split('.')[-1]
                        start_ip = f"{first_three_octets_router}.{start_ip_last}"
                        end_ip = f"{first_three_octets_router}.{end_ip_last}"
                        logger.info(f"Adjusted DHCP range to: {start_ip}-{end_ip}")
                    
                    lan_ip = lan_interface['ip_address']
                    lan_subnet = lan_interface['subnet_mask']
            except Exception as calc_error:
                logger.warning(f"Error calculating DHCP range with interface info: {str(calc_error)}")
                # Fall back to defaults if there's any error
            
            try:
                # Calculate network address and broadcast
                subnet = ipaddress.IPv4Network(f"{lan_ip}/{lan_subnet}", False)
                network = subnet.network_address
                broadcast = subnet.broadcast_address
                
                # Write DHCP config
                config_content = f"""# DHCP Server Configuration
default-lease-time {int(lease_time) * 3600};
max-lease-time {int(lease_time) * 3600 * 2};

subnet {network} netmask {lan_subnet} {{
    range {start_ip} {end_ip};
    option routers {lan_ip};
    option broadcast-address {broadcast};
    option domain-name-servers {lan_ip};
}}
"""
            except Exception as subnet_error:
                # If there's an error with the IP calculations, create a simpler config
                logger.error(f"Error calculating subnet information: {str(subnet_error)}")
                config_content = f"""# DHCP Server Configuration
default-lease-time {int(lease_time) * 3600};
max-lease-time {int(lease_time) * 3600 * 2};

subnet 192.168.1.0 netmask 255.255.255.0 {{
    range {start_ip} {end_ip};
    option routers {DEFAULT_LAN_IP};
    option broadcast-address 192.168.1.255;
    option domain-name-servers {DEFAULT_LAN_IP};
}}
"""
        
        # Log the DHCP configuration instead of writing to file
        logger.info(f"Would write DHCP configuration to {dhcp_conf_file}:\n{config_content}")
        
        logger.info(f"Successfully simulated DHCP server configuration (enabled: {enabled})")
        return True
    except Exception as e:
        logger.error(f"Error configuring DHCP server: {str(e)}")
        return False

def restart_network():
    """
    Restart networking services
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # In Replit environment, just log the restart attempt
        # since we don't have systemctl commands available
        logger.info("Network services restart simulated in Replit environment")
        
        # If we were on a real BPI-R4 system, we would execute:
        # subprocess.run(['systemctl', 'restart', 'networking'], check=True)
        # subprocess.run(['systemctl', 'restart', 'isc-dhcp-server'], check=True)
        
        return True
    except Exception as e:
        logger.error(f"Error restarting network services: {str(e)}")
        return False

def get_dhcp_leases():
    """
    Get DHCP leases
    
    Returns:
        list: List of dictionaries with lease information
    """
    leases = []
    
    try:
        # In Replit environment, return simulated DHCP leases
        # This is a simulation - in a real router, we'd read from dhcpd.leases
        
        # Generate some realistic looking leases for demo purposes
        import datetime
        
        simulated_leases = [
            {
                'ip_address': '192.168.1.100',
                'mac_address': '00:1A:2B:3C:4D:5E',
                'hostname': 'laptop-user1',
                'start_time': (datetime.datetime.now() - datetime.timedelta(hours=2)).strftime('%Y/%m/%d %H:%M:%S'),
                'end_time': (datetime.datetime.now() + datetime.timedelta(hours=22)).strftime('%Y/%m/%d %H:%M:%S')
            },
            {
                'ip_address': '192.168.1.101',
                'mac_address': '00:2C:3D:4E:5F:6A',
                'hostname': 'smartphone-user2',
                'start_time': (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime('%Y/%m/%d %H:%M:%S'),
                'end_time': (datetime.datetime.now() + datetime.timedelta(hours=23)).strftime('%Y/%m/%d %H:%M:%S')
            },
            {
                'ip_address': '192.168.1.102',
                'mac_address': '00:3E:4F:5A:6B:7C',
                'hostname': 'smart-tv',
                'start_time': (datetime.datetime.now() - datetime.timedelta(hours=5)).strftime('%Y/%m/%d %H:%M:%S'),
                'end_time': (datetime.datetime.now() + datetime.timedelta(hours=19)).strftime('%Y/%m/%d %H:%M:%S')
            }
        ]
        
        # Try to read real leases file if it exists, but fallback to simulation
        leases_file = '/var/lib/dhcp/dhcpd.leases'
        if os.path.exists(leases_file):
            try:
                with open(leases_file, 'r') as f:
                    content = f.read()
                
                # Parse leases file
                lease_blocks = re.findall(r'lease ([\d.]+) {([^}]+)}', content, re.DOTALL)
                
                for ip, details in lease_blocks:
                    lease_info = {'ip_address': ip}
                    
                    # Extract MAC address
                    mac_match = re.search(r'hardware ethernet ([0-9a-f:]+);', details)
                    if mac_match:
                        lease_info['mac_address'] = mac_match.group(1)
                    
                    # Extract hostname
                    hostname_match = re.search(r'client-hostname "([^"]+)";', details)
                    if hostname_match:
                        lease_info['hostname'] = hostname_match.group(1)
                    else:
                        lease_info['hostname'] = 'unknown'
                    
                    # Extract lease start and end times
                    start_match = re.search(r'starts \d+ ([^;]+);', details)
                    if start_match:
                        lease_info['start_time'] = start_match.group(1)
                    
                    end_match = re.search(r'ends \d+ ([^;]+);', details)
                    if end_match:
                        lease_info['end_time'] = end_match.group(1)
                    
                    leases.append(lease_info)
                
                if leases:
                    return leases  # Return real leases if we found any
            except Exception as inner_e:
                logger.debug(f"Could not read DHCP leases file, using simulated data: {str(inner_e)}")
        
        # Return simulated data
        return simulated_leases
    except Exception as e:
        logger.error(f"Error getting DHCP leases: {str(e)}")
        return []

def get_dns_settings():
    """
    Get DNS server settings
    
    Returns:
        dict: Dictionary with DNS settings
    """
    dns_settings = {
        'primary': '',
        'secondary': ''
    }
    
    try:
        # In Replit environment, return simulated DNS settings
        dns_settings = {
            'primary': '8.8.8.8',  # Google DNS as example
            'secondary': '8.8.4.4'
        }
        
        # Try to read resolv.conf if it exists, but don't fail if it doesn't
        try:
            if os.path.exists(DNS_CONFIG_PATH):
                with open(DNS_CONFIG_PATH, 'r') as f:
                    content = f.read()
                
                # Extract nameservers
                nameservers = re.findall(r'nameserver\s+([0-9.]+)', content)
                
                if len(nameservers) > 0:
                    dns_settings['primary'] = nameservers[0]
                
                if len(nameservers) > 1:
                    dns_settings['secondary'] = nameservers[1]
        except Exception as inner_e:
            logger.debug(f"Could not read DNS config, using defaults: {str(inner_e)}")
        
        return dns_settings
    except Exception as e:
        logger.error(f"Error getting DNS settings: {str(e)}")
        return dns_settings

def set_dns_settings(primary_dns, secondary_dns=None):
    """
    Set DNS server settings
    
    Args:
        primary_dns: Primary DNS server
        secondary_dns: Secondary DNS server (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Generate resolv.conf content
        content = f"# Generated by BPI-R4 Router OS\n"
        
        if primary_dns:
            content += f"nameserver {primary_dns}\n"
        
        if secondary_dns:
            content += f"nameserver {secondary_dns}\n"
        
        # Log the DNS configuration that would be written
        logger.info(f"Would write DNS configuration to {DNS_CONFIG_PATH}:\n{content}")
        
        logger.info("DNS settings simulation completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting DNS settings: {str(e)}")
        return False
