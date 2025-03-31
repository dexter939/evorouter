"""
Utility per la gestione del firewall dell'EvoRouter R4.
Fornisce funzioni per manipolare iptables, nftables, ipset e altre componenti del firewall.
"""
import os
import json
import logging
import subprocess
import ipaddress
from typing import List, Dict, Any, Optional, Union

# Configurazione del logger
logger = logging.getLogger(__name__)

def is_valid_ip(ip: str) -> bool:
    """Verifica se un indirizzo IP è valido (IPv4 o IPv6)"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_valid_network(network: str) -> bool:
    """Verifica se una rete è valida (IPv4 o IPv6)"""
    try:
        ipaddress.ip_network(network, strict=False)
        return True
    except ValueError:
        return False

def execute_command(command: List[str]) -> Dict[str, Any]:
    """Esegue un comando e restituisce l'output"""
    result = {
        "success": False,
        "output": "",
        "error": ""
    }
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        result["output"] = stdout.decode('utf-8')
        result["error"] = stderr.decode('utf-8')
        result["success"] = process.returncode == 0
        if not result["success"]:
            logger.error(f"Command failed: {' '.join(command)}, Error: {result['error']}")
        return result
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Exception executing command: {e}")
        return result

def get_firewall_status() -> Dict[str, Any]:
    """Restituisce lo stato attuale del firewall"""
    result = {
        "active": False,
        "version": "",
        "backend": "iptables",  # o nftables
        "zones": [],
        "rules_count": 0,
        "forwards_count": 0
    }
    
    # Verifica se il firewall è attivo
    iptables_check = execute_command(["iptables", "-L", "-n"])
    if iptables_check["success"]:
        result["active"] = True
    
    # Ottieni versione backend
    version_check = execute_command(["iptables", "--version"])
    if version_check["success"]:
        result["version"] = version_check["output"].strip()
    
    # Conta le regole
    rules_count = execute_command(["iptables", "-L", "-n", "--line-numbers"])
    if rules_count["success"]:
        # Conteggio approssimativo delle regole
        lines = rules_count["output"].splitlines()
        result["rules_count"] = sum(1 for line in lines if line.strip() and line[0].isdigit())
    
    # Conta i forwards
    forwards_count = execute_command(["iptables", "-t", "nat", "-L", "PREROUTING", "-n", "--line-numbers"])
    if forwards_count["success"]:
        lines = forwards_count["output"].splitlines()
        result["forwards_count"] = sum(1 for line in lines if line.strip() and line[0].isdigit())
        
    return result

def get_active_connections() -> List[Dict[str, Any]]:
    """Restituisce le connessioni attive"""
    connections = []
    
    # Usa conntrack o netstat per ottenere le connessioni
    conntrack_result = execute_command(["conntrack", "-L", "-n"])
    if conntrack_result["success"]:
        lines = conntrack_result["output"].splitlines()
        for line in lines:
            # Parsing molto semplificato, da migliorare nella versione reale
            if "ESTABLISHED" in line:
                parts = line.split()
                proto_idx = line.find("tcp")
                if proto_idx == -1:
                    proto_idx = line.find("udp")
                if proto_idx != -1:
                    proto = line[proto_idx:proto_idx+3]
                    src_dst = line.split("src=")[1]
                    src = src_dst.split(" ")[0]
                    dst = src_dst.split("dst=")[1].split(" ")[0]
                    sport = src_dst.split("sport=")[1].split(" ")[0]
                    dport = src_dst.split("dport=")[1].split(" ")[0]
                    
                    connections.append({
                        "protocol": proto,
                        "source": src,
                        "destination": dst,
                        "sport": sport,
                        "dport": dport,
                        "state": "ESTABLISHED"
                    })
    
    return connections

def apply_zone_config(zone_id: int, interfaces: List[str], default_policy: str = "drop",
                     masquerade: bool = False) -> bool:
    """Applica la configurazione di zona al firewall"""
    try:
        # Questo è un esempio, implementazione reale più complessa
        # Per ogni interfaccia associata alla zona:
        for interface in interfaces:
            # Configura la policy predefinita per l'interfaccia
            cmd_input = ["iptables", "-P"]
            if interface.startswith("wan"):
                cmd_input.extend(["INPUT", default_policy.upper()])
                execute_command(cmd_input)
                cmd_forward = ["iptables", "-P", "FORWARD", default_policy.upper()]
                execute_command(cmd_forward)
            
            # Se è abilitato il masquerading (NAT)
            if masquerade and interface.startswith("wan"):
                cmd_masq = ["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", 
                           interface, "-j", "MASQUERADE"]
                execute_command(cmd_masq)
        
        logger.info(f"Firewall zone {zone_id} configuration applied successfully")
        return True
    except Exception as e:
        logger.error(f"Error applying firewall zone {zone_id} configuration: {str(e)}")
        return False

def apply_rule(rule_id: int, zone: str, source: str, destination: str, 
              protocol: str, src_port: str, dst_port: str, action: str) -> bool:
    """Applica una regola del firewall"""
    try:
        cmd = ["iptables", "-A", "FORWARD"]
        
        # Impostazioni interfaccia
        if zone:
            zone_interfaces = get_zone_interfaces(zone)
            if zone_interfaces:
                cmd.extend(["-i", zone_interfaces[0]])  # Semplificazione, usa solo la prima interfaccia
        
        # Impostazioni source e destination
        if source and source != "any":
            cmd.extend(["-s", source])
        if destination and destination != "any":
            cmd.extend(["-d", destination])
        
        # Impostazioni protocollo e porte
        if protocol and protocol != "all":
            cmd.extend(["-p", protocol])
            if src_port and src_port != "any":
                cmd.extend(["--sport", src_port])
            if dst_port and dst_port != "any":
                cmd.extend(["--dport", dst_port])
        
        # Impostazione azione
        cmd.extend(["-j", action.upper()])
        
        # Esegui il comando
        result = execute_command(cmd)
        if result["success"]:
            logger.info(f"Firewall rule {rule_id} applied successfully")
            return True
        else:
            logger.error(f"Error applying firewall rule {rule_id}: {result['error']}")
            return False
    except Exception as e:
        logger.error(f"Exception applying firewall rule {rule_id}: {str(e)}")
        return False

def get_zone_interfaces(zone_name: str) -> List[str]:
    """Ottiene le interfacce di una zona"""
    # Implementazione di esempio, nella versione reale questo verrebbe letto dal DB
    zone_interfaces = {
        "wan": ["wan0", "wwan0"],
        "lan": ["lan0", "lan1", "br0"],
        "dmz": ["dmz0"],
        "guest": ["guest0"]
    }
    return zone_interfaces.get(zone_name, [])

def apply_port_forwarding(forward_id: int, source_zone: str, protocol: str, 
                         src_port: str, dest_ip: str, dest_port: str) -> bool:
    """Applica una regola di port forwarding"""
    try:
        cmd_dnat = ["iptables", "-t", "nat", "-A", "PREROUTING"]
        
        # Impostazioni interfaccia
        if source_zone:
            zone_interfaces = get_zone_interfaces(source_zone)
            if zone_interfaces:
                cmd_dnat.extend(["-i", zone_interfaces[0]])  # Semplificazione
        
        # Impostazioni protocollo e porta
        if protocol and protocol != "all":
            cmd_dnat.extend(["-p", protocol])
        if src_port:
            cmd_dnat.extend(["--dport", src_port])
        
        # Impostazioni destinazione
        if dest_ip and dest_port:
            cmd_dnat.extend(["-j", "DNAT", "--to", f"{dest_ip}:{dest_port}"])
        
        # Esegui il comando
        result = execute_command(cmd_dnat)
        if result["success"]:
            # Aggiungi anche una regola FORWARD se necessario
            cmd_forward = ["iptables", "-A", "FORWARD", "-p", protocol, 
                          "-d", dest_ip, "--dport", dest_port, "-j", "ACCEPT"]
            execute_command(cmd_forward)
            
            logger.info(f"Port forwarding {forward_id} applied successfully")
            return True
        else:
            logger.error(f"Error applying port forwarding {forward_id}: {result['error']}")
            return False
    except Exception as e:
        logger.error(f"Exception applying port forwarding {forward_id}: {str(e)}")
        return False

def create_ipset(ipset_name: str, ipset_type: str = "hash:ip") -> bool:
    """Crea un nuovo ipset"""
    try:
        # Verifica se l'ipset esiste già
        check_cmd = ["ipset", "list", ipset_name]
        check_result = execute_command(check_cmd)
        if check_result["success"]:
            # L'ipset esiste già
            return True
        
        # Crea il nuovo ipset
        create_cmd = ["ipset", "create", ipset_name, ipset_type]
        result = execute_command(create_cmd)
        if result["success"]:
            logger.info(f"IPSet {ipset_name} created successfully")
            return True
        else:
            logger.error(f"Error creating IPSet {ipset_name}: {result['error']}")
            return False
    except Exception as e:
        logger.error(f"Exception creating IPSet {ipset_name}: {str(e)}")
        return False

def add_to_ipset(ipset_name: str, address: str) -> bool:
    """Aggiunge un indirizzo a un ipset"""
    try:
        # Verifica se l'indirizzo è valido
        if not (is_valid_ip(address) or is_valid_network(address)):
            logger.error(f"Invalid address for IPSet: {address}")
            return False
        
        # Aggiungi l'indirizzo all'ipset
        add_cmd = ["ipset", "add", ipset_name, address]
        result = execute_command(add_cmd)
        if result["success"]:
            logger.info(f"Address {address} added to IPSet {ipset_name}")
            return True
        else:
            logger.error(f"Error adding address to IPSet: {result['error']}")
            return False
    except Exception as e:
        logger.error(f"Exception adding address to IPSet: {str(e)}")
        return False

def get_firewall_rules() -> List[Dict[str, Any]]:
    """Ottiene l'elenco attuale delle regole di firewall"""
    rules = []
    
    # Ottieni le regole dalla catena FORWARD
    forward_rules = execute_command(["iptables", "-L", "FORWARD", "-n", "--line-numbers"])
    if forward_rules["success"]:
        lines = forward_rules["output"].splitlines()
        
        # Salta l'intestazione
        for line in lines[2:]:
            if line.strip():
                parts = line.split(None, 8)
                if len(parts) >= 9:
                    rule_num = parts[0]
                    target = parts[1]
                    prot = parts[2]
                    source = parts[4]
                    dest = parts[5]
                    
                    rule = {
                        "num": rule_num,
                        "action": target,
                        "protocol": prot,
                        "source": source,
                        "destination": dest,
                        "extra": parts[8] if len(parts) > 8 else ""
                    }
                    
                    # Estrai porte se presenti
                    if "dpt:" in rule["extra"]:
                        rule["dest_port"] = rule["extra"].split("dpt:")[1].split()[0]
                    if "spt:" in rule["extra"]:
                        rule["source_port"] = rule["extra"].split("spt:")[1].split()[0]
                    
                    rules.append(rule)
    
    return rules

def get_port_forwardings() -> List[Dict[str, Any]]:
    """Ottiene l'elenco attuale dei port forwarding"""
    forwardings = []
    
    # Ottieni le regole dalla catena PREROUTING della tabella nat
    nat_rules = execute_command(["iptables", "-t", "nat", "-L", "PREROUTING", "-n", "--line-numbers"])
    if nat_rules["success"]:
        lines = nat_rules["output"].splitlines()
        
        # Salta l'intestazione
        for line in lines[2:]:
            if line.strip() and "DNAT" in line:
                parts = line.split()
                rule_num = parts[0]
                
                forwarding = {
                    "num": rule_num,
                    "protocol": "all",
                    "source": "",
                    "destination": "",
                    "src_port": "",
                    "dest_ip": "",
                    "dest_port": ""
                }
                
                # Estrai il protocollo
                proto_idx = parts.index("tcp") if "tcp" in parts else parts.index("udp") if "udp" in parts else -1
                if proto_idx != -1:
                    forwarding["protocol"] = parts[proto_idx]
                
                # Estrai porte e destinazione
                for i, part in enumerate(parts):
                    if part.startswith("dpt:"):
                        forwarding["src_port"] = part[4:]
                    if part == "to:" and i < len(parts) - 1:
                        dest_parts = parts[i + 1].split(":")
                        if len(dest_parts) == 2:
                            forwarding["dest_ip"] = dest_parts[0]
                            forwarding["dest_port"] = dest_parts[1]
                
                forwardings.append(forwarding)
    
    return forwardings

def flush_all_rules() -> bool:
    """Resetta tutte le regole di firewall"""
    try:
        # Flush di tutte le catene in tutte le tabelle
        for table in ["filter", "nat", "mangle"]:
            execute_command(["iptables", "-t", table, "-F"])
            execute_command(["iptables", "-t", table, "-X"])
        
        # Ripristina le policy predefinite
        execute_command(["iptables", "-P", "INPUT", "ACCEPT"])
        execute_command(["iptables", "-P", "OUTPUT", "ACCEPT"])
        execute_command(["iptables", "-P", "FORWARD", "ACCEPT"])
        
        logger.info("All firewall rules have been flushed")
        return True
    except Exception as e:
        logger.error(f"Error flushing firewall rules: {str(e)}")
        return False

def save_firewall_config(filename: str = "/etc/evorouter/firewall.rules") -> bool:
    """Salva la configurazione attuale del firewall su file"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        result = execute_command(["iptables-save"])
        if result["success"]:
            with open(filename, "w") as f:
                f.write(result["output"])
            logger.info(f"Firewall rules saved to {filename}")
            return True
        else:
            logger.error(f"Error saving firewall rules: {result['error']}")
            return False
    except Exception as e:
        logger.error(f"Exception saving firewall rules: {str(e)}")
        return False

def load_firewall_config(filename: str = "/etc/evorouter/firewall.rules") -> bool:
    """Carica la configurazione del firewall da file"""
    try:
        if not os.path.exists(filename):
            logger.error(f"Firewall rules file {filename} does not exist")
            return False
        
        result = execute_command(["iptables-restore", filename])
        if result["success"]:
            logger.info(f"Firewall rules loaded from {filename}")
            return True
        else:
            logger.error(f"Error loading firewall rules: {result['error']}")
            return False
    except Exception as e:
        logger.error(f"Exception loading firewall rules: {str(e)}")
        return False