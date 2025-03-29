"""
Configuration settings for the EvoRouter R4
"""
import os

# Router hardware configuration
ROUTER_MODEL = "EvoRouter R4"
CPU_MODEL = "RK3566 Quad-core ARM Cortex-A55 processor"
RAM = "4GB LPDDR4"
ETHERNET_PORTS = 5

# Network configuration
DEFAULT_LAN_INTERFACE = "eth0"
DEFAULT_WAN_INTERFACE = "eth1"
DEFAULT_WIFI_INTERFACE = "wlan0"
DEFAULT_LAN_IP = "192.168.1.1"
DEFAULT_LAN_SUBNET = "255.255.255.0"
DEFAULT_DHCP_RANGE_START = "192.168.1.100"
DEFAULT_DHCP_RANGE_END = "192.168.1.200"

# FreeSWITCH configuration
FREESWITCH_PATH = "/usr/local/freeswitch"
FREESWITCH_CONFIG_PATH = "/usr/local/freeswitch/conf"
FREESWITCH_LOG_PATH = "/var/log/freeswitch"
FREESWITCH_DEFAULT_PORT = 5060
FREESWITCH_RTP_START = 16384
FREESWITCH_RTP_END = 32768

# System paths
SYSTEM_LOG_PATH = "/var/log/bpir4"
NETWORK_CONFIG_PATH = "/etc/network/interfaces.d"
DHCP_CONFIG_PATH = "/etc/dhcp"
DNS_CONFIG_PATH = "/etc/resolv.conf"

# Web interface settings
SESSION_TIMEOUT = 3600  # 1 hour
API_TOKEN_EXPIRY = 30  # 30 days

# Security settings
PASSWORD_MIN_LENGTH = 8
FAILED_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_TIME = 15 * 60  # 15 minutes

# System update settings
UPDATE_CHECK_INTERVAL = 24 * 60 * 60  # 24 hours
PACKAGE_REPOSITORY = "https://packages.bpi-r4-os.org"

# Dashboard settings
BANDWIDTH_HISTORY_DAYS = 7
CPU_HISTORY_HOURS = 24
TEMPERATURE_WARNING = 70  # Celsius
TEMPERATURE_CRITICAL = 80  # Celsius

# Default diagnostic tools
DIAGNOSTIC_TOOLS = {
    "ping": "/bin/ping",
    "traceroute": "/usr/bin/traceroute",
    "nslookup": "/usr/bin/nslookup",
    "dig": "/usr/bin/dig",
    "iperf": "/usr/bin/iperf3"
}
