import logging
import os
import re
import subprocess
import json
import random
from datetime import datetime, timedelta
from config import DEFAULT_LAN_INTERFACE, DEFAULT_WAN_INTERFACE

# Create logger
logger = logging.getLogger(__name__)

def get_connected_devices():
    """
    Get list of devices connected to the network
    
    Returns:
        list: List of device dictionaries with ip, mac, hostname, etc.
    """
    try:
        # In Replit environment, we'll create simulated data
        devices = []
        
        # Simulate 8-12 devices
        device_count = random.randint(8, 12)
        
        # Common device names
        device_names = [
            "Router", "Desktop-PC", "Laptop-Admin", "Smartphone-Mario", 
            "Tablet-Lucia", "Smart-TV-Soggiorno", "Stampante-Ufficio", 
            "NAS-Storage", "Termostato-Smart", "Alexa-Cucina", 
            "Raspberry-Pi", "Camera-Ingresso", "Media-Player"
        ]
        
        # Interfaces
        interfaces = ["LAN", "WiFi", "WiFi", "WiFi", "LAN", "LAN"]
        
        # Connection types
        connection_types = ["Cablata", "Wireless", "Wireless", "Wireless", "Cablata", "Cablata"]
        
        # Generate random devices
        for i in range(device_count):
            # Generate MAC address
            mac = ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)]).upper()
            
            # Generate IPv4
            ipv4 = f"192.168.1.{random.randint(2, 250)}"
            
            # Determine if this device has IPv6
            has_ipv6 = random.random() > 0.3  # 70% chance of having IPv6
            ipv6 = f"fd00::{random.randint(100, 999):x}" if has_ipv6 else None
            
            # Random device name
            device_name = device_names[random.randint(0, len(device_names) - 1)]
            if i > 0 and i < len(device_names):
                device_name = device_names[i]
            
            # Interface
            interface_idx = random.randint(0, len(interfaces) - 1)
            interface = interfaces[interface_idx]
            connection = connection_types[interface_idx]
            
            # Status (80% online)
            status = "Online" if random.random() < 0.8 else "Offline"
            
            # Last seen
            last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == "Online" else (
                datetime.now().strftime("%Y-%m-%d ") + f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
            )
            
            # Traffic
            download = round(random.uniform(0, 10), 2) if status == "Online" else 0
            upload = round(random.uniform(0, 2), 2) if status == "Online" else 0
            
            devices.append({
                "name": device_name,
                "ipv4_address": ipv4,
                "ipv6_address": ipv6,
                "ipv6_enabled": has_ipv6,
                "mac": mac,
                "interface": interface,
                "connection": connection,
                "status": status,
                "last_seen": last_seen,
                "download": download,
                "upload": upload
            })
        
        return devices
    except Exception as e:
        logger.error(f"Error getting connected devices: {str(e)}")
        return []

def get_interfaces_status():
    """
    Get network interfaces status
    
    Returns:
        list: List of interface dictionaries with name, state, etc.
    """
    try:
        # In Replit environment, we'll create simulated data
        interfaces = [
            {
                "name": "eth0",
                "type": "LAN",
                "state": "UP",
                "speed": "1 Gbps",
                # IPv4 info
                "ipv4_enabled": True,
                "ipv4_address": "192.168.1.1",
                "ipv4_subnet": "255.255.255.0",
                # IPv6 info
                "ipv6_enabled": True,
                "ipv6_address": "fd00::1",
                "ipv6_prefix": "64",
                "mac": "AA:BB:CC:11:22:33",
                "rx_bytes": random.randint(1000000, 100000000),
                "tx_bytes": random.randint(100000, 10000000)
            },
            {
                "name": "eth1",
                "type": "WAN",
                "state": "UP",
                "speed": "1 Gbps",
                # IPv4 info
                "ipv4_enabled": True,
                "ipv4_address": "203.0.113.10",
                "ipv4_subnet": "255.255.255.0",
                # IPv6 info
                "ipv6_enabled": True,
                "ipv6_address": f"2001:db8::1:{random.randint(1, 999):x}",
                "ipv6_prefix": "64",
                "mac": "AA:BB:CC:11:22:34",
                "rx_bytes": random.randint(100000000, 1000000000),
                "tx_bytes": random.randint(10000000, 100000000)
            },
            {
                "name": "wlan0",
                "type": "WiFi",
                "state": "UP",
                "speed": "300 Mbps",
                # IPv4 info
                "ipv4_enabled": True,
                "ipv4_address": "192.168.1.1",
                "ipv4_subnet": "255.255.255.0",
                # IPv6 info
                "ipv6_enabled": True,
                "ipv6_address": "fd00::1",
                "ipv6_prefix": "64",
                "mac": "AA:BB:CC:11:22:35",
                "rx_bytes": random.randint(10000000, 100000000),
                "tx_bytes": random.randint(1000000, 10000000)
            },
            {
                "name": "wlan1",
                "type": "WiFi",
                "state": "DOWN",
                "speed": "N/A",
                # IPv4 info
                "ipv4_enabled": False,
                "ipv4_address": "N/A",
                "ipv4_subnet": "N/A",
                # IPv6 info
                "ipv6_enabled": False,
                "ipv6_address": "N/A",
                "ipv6_prefix": "N/A",
                "mac": "AA:BB:CC:11:22:36",
                "rx_bytes": 0,
                "tx_bytes": 0
            }
        ]
        
        return interfaces
    except Exception as e:
        logger.error(f"Error getting interface status: {str(e)}")
        return []

def get_wan_status():
    """
    Get WAN connection status
    
    Returns:
        dict: WAN status information
    """
    try:
        # In Replit environment, we'll create simulated data
        connected = random.random() > 0.1  # 90% chance of being connected
        ipv6_enabled = random.random() > 0.3  # 70% chance of IPv6 being enabled
        
        status = {
            "connected": connected,
            "interface": DEFAULT_WAN_INTERFACE,
            # IPv4 info
            "ipv4_enabled": True,
            "ipv4_address": "203.0.113." + str(random.randint(1, 254)) if connected else "N/A",
            "ipv4_gateway": "203.0.113.1" if connected else "N/A",
            "ipv4_dns": ["8.8.8.8", "8.8.4.4"] if connected else [],
            "ipv4_type": "DHCP",
            # IPv6 info
            "ipv6_enabled": ipv6_enabled and connected,
            "ipv6_address": f"2001:db8::1:{random.randint(1, 999):x}" if connected and ipv6_enabled else "N/A",
            "ipv6_gateway": "2001:db8::1" if connected and ipv6_enabled else "N/A",
            "ipv6_dns": ["2001:4860:4860::8888", "2001:4860:4860::8844"] if connected and ipv6_enabled else [],
            "ipv6_type": "SLAAC" if ipv6_enabled else "N/A",
            # Generale
            "uptime": f"{random.randint(1, 48)} ore, {random.randint(0, 59)} minuti" if connected else "N/A"
        }
        
        return status
    except Exception as e:
        logger.error(f"Error getting WAN status: {str(e)}")
        return {"connected": False, "error": str(e)}

def get_public_ip_info():
    """
    Get public IP information
    
    Returns:
        dict: Public IP information
    """
    try:
        # In Replit environment, we'll create simulated data
        ip_types = ["Residenziale", "Business", "Datacenter"]
        ipv6_enabled = random.random() > 0.3  # 70% chance of IPv6 being available
        
        info = {
            # IPv4 info
            "ipv4_address": "203.0.113." + str(random.randint(1, 254)),
            "ipv4_location": "Milano, Italia",
            "ipv4_isp": "TIM Telecom Italia",
            "ipv4_type": ip_types[random.randint(0, len(ip_types) - 1)],
            # IPv6 info
            "ipv6_enabled": ipv6_enabled,
            "ipv6_address": f"2001:db8::1:{random.randint(1, 999):x}" if ipv6_enabled else "N/A",
            "ipv6_location": "Milano, Italia" if ipv6_enabled else "N/A",
            "ipv6_isp": "TIM Telecom Italia" if ipv6_enabled else "N/A",
            "ipv6_type": ip_types[random.randint(0, len(ip_types) - 1)] if ipv6_enabled else "N/A"
        }
        
        return info
    except Exception as e:
        logger.error(f"Error getting public IP info: {str(e)}")
        return {"error": str(e)}

def get_firewall_status():
    """
    Get firewall status
    
    Returns:
        dict: Firewall status information
    """
    try:
        # In Replit environment, we'll create simulated data
        ipv6_enabled = random.random() > 0.3  # 70% chance of IPv6 being enabled
        
        status = {
            "enabled": True,
            "ipv6_enabled": ipv6_enabled,
            "ipv4_rules": [
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "TCP:22",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "TCP:80,443",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "ICMP",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "UDP:1194",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth0",
                    "protocol": "ALL",
                    "action": "ACCEPT"
                },
                {
                    "type": "FORWARD",
                    "interface": "eth1->eth0",
                    "protocol": "ALL",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "ALL",
                    "action": "DROP"
                }
            ],
            "ipv6_rules": [
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "TCP:22",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "TCP:80,443",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "ICMPv6",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "UDP:1194",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth0",
                    "protocol": "ALL",
                    "action": "ACCEPT"
                },
                {
                    "type": "FORWARD",
                    "interface": "eth1->eth0",
                    "protocol": "ALL",
                    "action": "ACCEPT"
                },
                {
                    "type": "INPUT",
                    "interface": "eth1",
                    "protocol": "ALL",
                    "action": "DROP"
                }
            ] if ipv6_enabled else [],
            "port_forwarding": [
                {
                    "name": "HTTP Server",
                    "external": "80",
                    "internal_ipv4": "192.168.1.5",
                    "internal_ipv6": "fd00::5" if ipv6_enabled else None,
                    "internal_port": "80",
                    "protocol": "TCP",
                    "ipv6_enabled": ipv6_enabled
                },
                {
                    "name": "HTTPS Server",
                    "external": "443",
                    "internal_ipv4": "192.168.1.5",
                    "internal_ipv6": "fd00::5" if ipv6_enabled else None,
                    "internal_port": "443",
                    "protocol": "TCP",
                    "ipv6_enabled": ipv6_enabled
                },
                {
                    "name": "SSH Access",
                    "external": "2222",
                    "internal_ipv4": "192.168.1.2",
                    "internal_ipv6": "fd00::2" if ipv6_enabled else None,
                    "internal_port": "22",
                    "protocol": "TCP",
                    "ipv6_enabled": ipv6_enabled
                },
                {
                    "name": "Game Server",
                    "external": "27015",
                    "internal_ipv4": "192.168.1.6",
                    "internal_ipv6": "fd00::6" if ipv6_enabled else None,
                    "internal_port": "27015",
                    "protocol": "UDP",
                    "ipv6_enabled": ipv6_enabled
                }
            ]
        }
        
        return status
    except Exception as e:
        logger.error(f"Error getting firewall status: {str(e)}")
        return {"error": str(e)}

def check_port(port, protocol="tcp"):
    """
    Check if a port is open
    
    Args:
        port: Port number to check
        protocol: Protocol (tcp or udp)
        
    Returns:
        dict: Port status information
    """
    try:
        # In Replit environment, we'll create simulated data
        is_open = random.random() > 0.7  # 30% chance of being open
        
        services = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            443: "HTTPS",
            3389: "Remote Desktop",
            1194: "OpenVPN",
            5060: "SIP",
            5061: "SIP/TLS"
        }
        
        status = {
            "port": port,
            "protocol": protocol,
            "is_open": is_open,
            "service": services.get(int(port), "Sconosciuto") if is_open else None
        }
        
        return status
    except Exception as e:
        logger.error(f"Error checking port {port}/{protocol}: {str(e)}")
        return {"error": str(e)}

def get_bandwidth_usage(interface="all", period="1h"):
    """
    Get bandwidth usage data
    
    Args:
        interface: Interface name or 'all' for all interfaces
        period: Time period (1h, 6h, 24h, 7d)
        
    Returns:
        dict: Bandwidth usage information
    """
    try:
        # In Replit environment, we'll create simulated data
        from datetime import datetime, timedelta
        
        # Generate 30 points
        now = datetime.now()
        timestamps = [(now - timedelta(minutes=i)).strftime('%H:%M:%S') for i in range(30, 0, -1)]
        
        # Randomize download/upload data
        base_download = random.uniform(10, 40)
        base_upload = random.uniform(2, 10)
        
        download = []
        upload = []
        
        for i in range(30):
            # Add some variation
            download.append(round(base_download + random.uniform(-5, 10), 1))
            upload.append(round(base_upload + random.uniform(-2, 5), 1))
            
            # Occasionally add a spike
            if random.random() > 0.9:
                download[-1] *= 1.5
                upload[-1] *= 1.2
        
        data = {
            "timestamps": timestamps,
            "download": download,
            "upload": upload,
            "current_download": download[-1],
            "current_upload": upload[-1],
            "interface": interface,
            "period": period
        }
        
        return data
    except Exception as e:
        logger.error(f"Error getting bandwidth usage: {str(e)}")
        return {"error": str(e)}

def test_voip_quality():
    """
    Test VoIP quality
    
    Returns:
        dict: VoIP quality test results
    """
    try:
        # In Replit environment, we'll create simulated data
        mos_score = round(random.uniform(3.2, 4.2), 1)
        latency = round(random.uniform(10, 60), 1)
        jitter = round(random.uniform(1, 9), 1)
        packet_loss = round(random.uniform(0, 2), 1)
        
        # Determine quality verdict
        if mos_score >= 4.0 and latency < 30 and jitter < 5 and packet_loss < 0.5:
            verdict = "Eccellente qualità per chiamate VoIP"
            quality = "excellent"
        elif mos_score >= 3.5 and latency < 50 and jitter < 10 and packet_loss < 1:
            verdict = "Buona qualità per chiamate VoIP"
            quality = "good"
        elif mos_score >= 3.0 and latency < 100 and jitter < 15 and packet_loss < 2:
            verdict = "Qualità accettabile per chiamate VoIP"
            quality = "fair"
        else:
            verdict = "Qualità scadente per chiamate VoIP, possibili problemi"
            quality = "poor"
        
        results = {
            "mos_score": mos_score,
            "latency": latency,
            "jitter": jitter,
            "packet_loss": packet_loss,
            "verdict": verdict,
            "quality": quality,
            "details": {
                "codecs_tested": ["G.711", "G.729", "Opus"],
                "rtp_quality": "Good" if packet_loss < 1 else "Fair",
                "sip_quality": "Good" if latency < 50 else "Fair"
            }
        }
        
        return results
    except Exception as e:
        logger.error(f"Error testing VoIP quality: {str(e)}")
        return {"error": str(e)}

def get_vpn_status():
    """
    Get VPN status
    
    Returns:
        dict: VPN status information
    """
    try:
        # In Replit environment, we'll create simulated data
        is_running = random.random() > 0.2  # 80% chance of being active
        ipv6_enabled = random.random() > 0.4  # 60% chance of IPv6 being enabled
        
        status = {
            "running": is_running,
            "vpn_type": "OpenVPN",
            "protocol": "UDP",
            "port": 1194,
            "clients_connected": random.randint(0, 5) if is_running else 0,
            # IPv4 settings
            "ipv4_enabled": True,
            "ipv4_subnet": "10.8.0.0/24",
            "ipv4_dns": ["8.8.8.8", "8.8.4.4"] if is_running else [],
            # IPv6 settings
            "ipv6_enabled": ipv6_enabled and is_running,
            "ipv6_subnet": "fd00::/64" if ipv6_enabled and is_running else "N/A",
            "ipv6_dns": ["2001:4860:4860::8888", "2001:4860:4860::8844"] if ipv6_enabled and is_running else [],
            # Common settings
            "bandwidth_down": round(random.uniform(0.5, 2), 1) if is_running else 0,
            "bandwidth_up": round(random.uniform(0.2, 1), 1) if is_running else 0,
            "certificates_valid": True,
            "encryption": "AES-256-GCM"
        }
        
        return status
    except Exception as e:
        logger.error(f"Error getting VPN status: {str(e)}")
        return {"error": str(e)}

def configure_interface(interface_name, config):
    """
    Configure a network interface
    
    Args:
        interface_name: Name of the interface to configure
        config: Dictionary with interface configuration
        
    Returns:
        dict: Result of the configuration
    """
    try:
        # In Replit environment, we'll simulate success
        logger.info(f"Configuring interface {interface_name} with {config}")
        
        # Simulate a brief delay
        import time
        time.sleep(0.5)
        
        return {
            "success": True,
            "message": f"Interface {interface_name} configured successfully",
            "interface": interface_name,
            "config": config
        }
    except Exception as e:
        logger.error(f"Error configuring interface {interface_name}: {str(e)}")
        return {
            "success": False,
            "message": f"Error configuring interface: {str(e)}",
            "interface": interface_name
        }

def set_dhcp_config(config):
    """
    Configure DHCP server
    
    Args:
        config: Dictionary with DHCP configuration
        
    Returns:
        dict: Result of the configuration
    """
    try:
        # In Replit environment, we'll simulate success
        logger.info(f"Configuring DHCP server with {config}")
        
        # Simulate a brief delay
        import time
        time.sleep(0.5)
        
        return {
            "success": True,
            "message": "DHCP server configured successfully",
            "config": config
        }
    except Exception as e:
        logger.error(f"Error configuring DHCP server: {str(e)}")
        return {
            "success": False,
            "message": f"Error configuring DHCP server: {str(e)}"
        }

def restart_network():
    """
    Restart network services
    
    Returns:
        dict: Result of the restart
    """
    try:
        # In Replit environment, we'll simulate success
        logger.info("Restarting network services")
        
        # Simulate a brief delay
        import time
        time.sleep(1.5)
        
        return {
            "success": True,
            "message": "Network services restarted successfully"
        }
    except Exception as e:
        logger.error(f"Error restarting network services: {str(e)}")
        return {
            "success": False,
            "message": f"Error restarting network services: {str(e)}"
        }

def get_dhcp_leases():
    """
    Get DHCP leases
    
    Returns:
        list: List of DHCP leases
    """
    try:
        # In Replit environment, we'll create simulated data
        leases = []
        
        # Generate 5-10 leases
        lease_count = random.randint(5, 10)
        
        for i in range(lease_count):
            # Generate MAC address
            mac = ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)]).upper()
            
            # Generate IP
            ipv4 = f"192.168.1.{random.randint(100, 200)}"
            
            # Determine if this device has IPv6
            has_ipv6 = random.random() > 0.3  # 70% chance of having IPv6
            ipv6 = f"fd00::{random.randint(100, 999):x}" if has_ipv6 else None
            
            # Generate hostname
            hostnames = ["desktop-pc", "laptop-mario", "iphone-lucia", "android-giovanni", 
                         "smart-tv", "printer", "raspberry-pi", "gaming-console", 
                         "tablet-marco", "media-player", "thermostat", "security-camera"]
            
            hostname = hostnames[random.randint(0, len(hostnames) - 1)]
            if i < len(hostnames):
                hostname = hostnames[i]
                
            # Generate lease time information
            expiry = datetime.now() + timedelta(hours=random.randint(1, 24))
            
            leases.append({
                "ipv4_address": ipv4,
                "ipv6_address": ipv6,
                "ipv6_enabled": has_ipv6,
                "mac": mac,
                "hostname": hostname,
                "expiry": expiry.strftime("%Y-%m-%d %H:%M:%S"),
                "permanent": random.random() > 0.8  # 20% chance of being permanent
            })
        
        return leases
    except Exception as e:
        logger.error(f"Error getting DHCP leases: {str(e)}")
        return []

def get_dns_settings():
    """
    Get DNS settings
    
    Returns:
        dict: DNS settings
    """
    try:
        # In Replit environment, we'll create simulated data
        ipv6_enabled = random.random() > 0.4  # 60% chance of IPv6 being enabled
        
        settings = {
            # IPv4 DNS settings
            "ipv4_primary_dns": "8.8.8.8",
            "ipv4_secondary_dns": "8.8.4.4",
            # IPv6 DNS settings
            "ipv6_enabled": ipv6_enabled,
            "ipv6_primary_dns": "2001:4860:4860::8888" if ipv6_enabled else "N/A",
            "ipv6_secondary_dns": "2001:4860:4860::8844" if ipv6_enabled else "N/A",
            # General settings
            "local_domain": "home.lan",
            "enable_caching": True,
            "forward_queries": True,
            "cache_size": 1000,
            "custom_entries": [
                {"domain": "router.home.lan", "ipv4": "192.168.1.1", "ipv6": "fd00::1"},
                {"domain": "printer.home.lan", "ipv4": "192.168.1.101", "ipv6": "fd00::101"},
                {"domain": "nas.home.lan", "ipv4": "192.168.1.200", "ipv6": "fd00::200"}
            ]
        }
        
        return settings
    except Exception as e:
        logger.error(f"Error getting DNS settings: {str(e)}")
        return {}

def set_dns_settings(settings):
    """
    Configure DNS settings
    
    Args:
        settings: Dictionary with DNS settings
        
    Returns:
        dict: Result of the configuration
    """
    try:
        # In Replit environment, we'll simulate success
        logger.info(f"Configuring DNS settings with {settings}")
        
        # Simulate a brief delay
        import time
        time.sleep(0.5)
        
        return {
            "success": True,
            "message": "DNS settings configured successfully",
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Error configuring DNS settings: {str(e)}")
        return {
            "success": False,
            "message": f"Error configuring DNS settings: {str(e)}"
        }