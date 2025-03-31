"""
Utilities per gestire il Quality of Service (QoS) sul router.
Questo modulo fornisce funzioni per configurare e gestire il QoS
usando tc (Traffic Control) e iptables per la marcatura dei pacchetti.
"""
import logging
import json
import subprocess
from typing import List, Dict, Tuple, Optional, Any, Union

# Configurazione del logger
logger = logging.getLogger(__name__)

# Costanti per tc
TC_PATH = "/sbin/tc"
IP_PATH = "/sbin/ip"
IPTABLES_PATH = "/sbin/iptables"

# DSCP mappings (Differentiated Services Code Point)
DSCP_VALUES = {
    "CS0": "0x00",  # Default
    "CS1": "0x08",  # Priority
    "AF11": "0x0A", # Priority data 1
    "AF12": "0x0C", # Priority data 2
    "AF13": "0x0E", # Priority data 3
    "CS2": "0x10",  # Immediate
    "AF21": "0x12", # Immediate data 1
    "AF22": "0x14", # Immediate data 2
    "AF23": "0x16", # Immediate data 3
    "CS3": "0x18",  # Flash
    "AF31": "0x1A", # Flash data 1
    "AF32": "0x1C", # Flash data 2
    "AF33": "0x1E", # Flash data 3
    "CS4": "0x20",  # Flash Override
    "AF41": "0x22", # Flash override data 1
    "AF42": "0x24", # Flash override data 2
    "AF43": "0x26", # Flash override data 3
    "CS5": "0x28",  # Critical
    "EF": "0x2E",   # Voice Admit (Expedited Forwarding)
    "CS6": "0x30",  # Internetwork Control
    "CS7": "0x38"   # Network Control
}

def execute_command(command: List[str]) -> Tuple[bool, str]:
    """
    Esegue un comando di sistema e ne restituisce l'output.
    
    Args:
        command: Lista di stringhe che rappresentano il comando da eseguire
        
    Returns:
        Tupla con stato di successo e output del comando
    """
    try:
        # Esecuzione del comando
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Errore nell'esecuzione del comando {' '.join(command)}: {e}")
        return False, e.stderr
    except Exception as e:
        logger.error(f"Eccezione durante l'esecuzione del comando {' '.join(command)}: {str(e)}")
        return False, str(e)

def get_interfaces() -> List[Dict[str, str]]:
    """
    Ottiene la lista delle interfacce di rete disponibili.
    
    Returns:
        Lista di dizionari con informazioni sulle interfacce
    """
    # Esempio di implementazione (in un sistema reale useremmo i comandi del sistema)
    interfaces = [
        {"name": "eth0", "description": "WAN - Internet", "type": "ethernet"},
        {"name": "eth1", "description": "LAN - Rete Locale", "type": "ethernet"},
        {"name": "wlan0", "description": "WiFi", "type": "wireless"},
        {"name": "br0", "description": "Bridge LAN", "type": "bridge"},
    ]
    return interfaces

def get_bandwidth_usage(interface: str) -> Dict[str, Any]:
    """
    Ottiene l'utilizzo di banda attuale per un'interfaccia.
    
    Args:
        interface: Nome dell'interfaccia
        
    Returns:
        Dizionario con dati sull'utilizzo di banda
    """
    # In un sistema reale questa funzione utilizzerebbe comandi come 'tc -s class show dev <interface>'
    # oppure 'iftop' o altri strumenti per monitorare il traffico in tempo reale
    # Per esempio: execute_command([TC_PATH, "-s", "class", "show", "dev", interface])
    
    # Per ora restituiamo dati di esempio
    return {
        "interface": interface,
        "download": {
            "current": 1024,  # kbps
            "peak": 2048,     # kbps
            "total": 15000    # KB trasferiti
        },
        "upload": {
            "current": 256,   # kbps
            "peak": 512,      # kbps
            "total": 5000     # KB trasferiti
        },
        "classes": {
            "high": {
                "download": 512,
                "upload": 128
            },
            "default": {
                "download": 256,
                "upload": 64
            },
            "low": {
                "download": 128,
                "upload": 32
            }
        }
    }

def setup_qos(config_id: int, interface: str, download_bandwidth: int, upload_bandwidth: int, 
             default_class: str, hierarchical: bool = True) -> bool:
    """
    Configura il QoS su un'interfaccia.
    
    Args:
        config_id: ID della configurazione QoS nel database
        interface: Nome dell'interfaccia
        download_bandwidth: Banda massima in download (kbps)
        upload_bandwidth: Banda massima in upload (kbps)
        default_class: Nome della classe predefinita
        hierarchical: Se usare HTB (hierarchical token bucket)
        
    Returns:
        True se la configurazione è avvenuta con successo, False altrimenti
    """
    logger.info(f"Configurazione QoS su {interface}: download={download_bandwidth}kbps, upload={upload_bandwidth}kbps")
    
    # In un sistema reale, questa funzione eseguirebbe comandi tc per impostare il QoS
    # Ad esempio:
    
    # 1. Eliminazione delle vecchie configurazioni
    # execute_command([TC_PATH, "qdisc", "del", "dev", interface, "root"])
    
    # 2. Creazione della disciplina di accodamento root (HTB o altro)
    # Esempio per HTB:
    # execute_command([
    #     TC_PATH, "qdisc", "add", "dev", interface, "root", "handle", "1:", 
    #     "htb", "default", "10"
    # ])
    
    # 3. Creazione della classe principale con la larghezza di banda massima
    # execute_command([
    #     TC_PATH, "class", "add", "dev", interface, "parent", "1:", "classid", "1:1", 
    #     "htb", "rate", f"{upload_bandwidth}kbit", "ceil", f"{upload_bandwidth}kbit"
    # ])
    
    # 4. Creazione delle classi per i diversi tipi di traffico
    
    # Per ora, simuliamo il successo dell'operazione
    logger.info("QoS configurato con successo (simulazione)")
    return True

def add_qos_class(config_id: int, class_id: int, name: str, priority: int, 
                min_bandwidth: int, max_bandwidth: int) -> bool:
    """
    Aggiunge una classe di traffico QoS.
    
    Args:
        config_id: ID della configurazione QoS nel database
        class_id: ID della classe QoS nel database
        name: Nome della classe
        priority: Priorità (1-7, dove 1 è la priorità più alta)
        min_bandwidth: Percentuale minima di banda garantita
        max_bandwidth: Percentuale massima di banda utilizzabile
        
    Returns:
        True se la classe è stata aggiunta con successo, False altrimenti
    """
    logger.info(f"Aggiunta classe QoS {name} con priorità {priority}")
    
    # In un sistema reale, questa funzione eseguirebbe comandi tc per aggiungere la classe
    # Ad esempio:
    
    # Ottenere la configurazione QoS
    # from app import db
    # from models import QoSConfig
    # qos_config = db.session.get(QoSConfig, config_id)
    
    # Calcolare la banda in base alle percentuali
    # min_rate = (qos_config.upload_bandwidth * min_bandwidth) // 100
    # max_rate = (qos_config.upload_bandwidth * max_bandwidth) // 100
    
    # Aggiungere la classe
    # tc_priority = 8 - priority  # Convertire in priorità tc (7 = più bassa, 1 = più alta)
    # execute_command([
    #     TC_PATH, "class", "add", "dev", qos_config.interface, 
    #     "parent", "1:1", "classid", f"1:{10+class_id}", 
    #     "htb", "rate", f"{min_rate}kbit", "ceil", f"{max_rate}kbit", "prio", str(tc_priority)
    # ])
    
    # Per ora, simuliamo il successo dell'operazione
    logger.info("Classe QoS aggiunta con successo (simulazione)")
    return True

def add_qos_rule(rule_id: int, class_id: int, source: Optional[str], destination: Optional[str],
               protocol: str, src_port: Optional[str], dst_port: Optional[str],
               dscp: Optional[str], direction: str) -> bool:
    """
    Aggiunge una regola per la classificazione del traffico QoS.
    
    Args:
        rule_id: ID della regola QoS nel database
        class_id: ID della classe QoS associata
        source: IP o rete sorgente (opzionale)
        destination: IP o rete destinazione (opzionale)
        protocol: Protocollo (tcp, udp, icmp, all)
        src_port: Porta o range di porte sorgente (opzionale)
        dst_port: Porta o range di porte destinazione (opzionale)
        dscp: Differentiated Services Code Point (opzionale)
        direction: Direzione del traffico (in, out, both)
        
    Returns:
        True se la regola è stata aggiunta con successo, False altrimenti
    """
    logger.info(f"Aggiunta regola QoS per classe {class_id}")
    
    # In un sistema reale, questa funzione eseguirebbe comandi iptables per marcare i pacchetti
    # e tc filter per classificarli
    # Ad esempio:
    
    # Ottenere la classe QoS
    # from app import db
    # from models import QoSClass, QoSConfig
    # qos_class = db.session.get(QoSClass, class_id)
    # qos_config = db.session.get(QoSConfig, qos_class.config_id)
    
    # Costruire il comando iptables per marcare i pacchetti
    # mark_value = 10 + class_id
    # cmd = [IPTABLES_PATH, "-t", "mangle", "-A", "POSTROUTING"]
    
    # if direction in ["out", "both"]:
    #     if source:
    #         cmd.extend(["-s", source])
    #     if destination:
    #         cmd.extend(["-d", destination])
    #     if protocol != "all":
    #         cmd.extend(["-p", protocol])
    #     if src_port and protocol in ["tcp", "udp"]:
    #         cmd.extend(["--sport", src_port])
    #     if dst_port and protocol in ["tcp", "udp"]:
    #         cmd.extend(["--dport", dst_port])
    #     if dscp and dscp in DSCP_VALUES:
    #         cmd.extend(["-m", "dscp", "--dscp-class", dscp])
    #     
    #     cmd.extend(["-j", "MARK", "--set-mark", str(mark_value)])
    #     execute_command(cmd)
    
    # Aggiungere il filtro tc
    # execute_command([
    #     TC_PATH, "filter", "add", "dev", qos_config.interface, 
    #     "parent", "1:", "protocol", "ip", "prio", "1", "handle", str(mark_value), "fw", 
    #     "flowid", f"1:{mark_value}"
    # ])
    
    # Per ora, simuliamo il successo dell'operazione
    logger.info("Regola QoS aggiunta con successo (simulazione)")
    return True

def remove_qos_rule(rule_id: int) -> bool:
    """
    Rimuove una regola QoS.
    
    Args:
        rule_id: ID della regola QoS nel database
        
    Returns:
        True se la regola è stata rimossa con successo, False altrimenti
    """
    logger.info(f"Rimozione regola QoS {rule_id}")
    
    # In un sistema reale, questa funzione eseguirebbe comandi per rimuovere la regola
    # Esempio:
    # execute_command([IPTABLES_PATH, "-t", "mangle", "-D", "POSTROUTING", "-m", "comment", 
    #                 "--comment", f"QoSRule{rule_id}", "-j", "MARK", "--set-mark", str(mark_value)])
    
    # Per ora, simuliamo il successo dell'operazione
    logger.info("Regola QoS rimossa con successo (simulazione)")
    return True

def remove_qos_class(class_id: int) -> bool:
    """
    Rimuove una classe QoS.
    
    Args:
        class_id: ID della classe QoS nel database
        
    Returns:
        True se la classe è stata rimossa con successo, False altrimenti
    """
    logger.info(f"Rimozione classe QoS {class_id}")
    
    # In un sistema reale, questa funzione eseguirebbe comandi per rimuovere la classe
    # Esempio:
    # from app import db
    # from models import QoSClass
    # qos_class = db.session.get(QoSClass, class_id)
    # execute_command([TC_PATH, "class", "del", "dev", interface, "classid", f"1:{10+class_id}"])
    
    # Per ora, simuliamo il successo dell'operazione
    logger.info("Classe QoS rimossa con successo (simulazione)")
    return True

def disable_qos(config_id: int) -> bool:
    """
    Disabilita completamente il QoS su un'interfaccia.
    
    Args:
        config_id: ID della configurazione QoS nel database
        
    Returns:
        True se il QoS è stato disabilitato con successo, False altrimenti
    """
    logger.info(f"Disabilitazione QoS per config {config_id}")
    
    # In un sistema reale, questa funzione eseguirebbe comandi per rimuovere tutte le configurazioni QoS
    # Esempio:
    # from app import db
    # from models import QoSConfig
    # qos_config = db.session.get(QoSConfig, config_id)
    # execute_command([TC_PATH, "qdisc", "del", "dev", qos_config.interface, "root"])
    # execute_command([IPTABLES_PATH, "-t", "mangle", "-F", "POSTROUTING"])
    
    # Per ora, simuliamo il successo dell'operazione
    logger.info("QoS disabilitato con successo (simulazione)")
    return True

def get_qos_status(config_id: int) -> Dict[str, Any]:
    """
    Ottiene lo stato attuale del QoS.
    
    Args:
        config_id: ID della configurazione QoS nel database
        
    Returns:
        Dizionario con informazioni sullo stato del QoS
    """
    # In un sistema reale, questa funzione eseguirebbe comandi per ottenere lo stato del QoS
    # Ad esempio:
    # from app import db
    # from models import QoSConfig
    # qos_config = db.session.get(QoSConfig, config_id)
    # tc_output = execute_command([TC_PATH, "-s", "qdisc", "show", "dev", qos_config.interface])[1]
    
    # Per ora, restituiamo dati di esempio
    return {
        "enabled": True,
        "interface": "eth0",
        "download_bandwidth": 10000,
        "upload_bandwidth": 1000,
        "active_classes": 3,
        "active_rules": 5,
        "status": "running"
    }

def apply_all_qos_rules() -> bool:
    """
    Applica tutte le regole QoS configurate nel database.
    
    Returns:
        True se tutte le regole sono state applicate con successo, False altrimenti
    """
    logger.info("Applicazione di tutte le regole QoS")
    
    # In un sistema reale, questa funzione otterrebbe tutte le configurazioni dal database
    # e le applicherebbe usando le funzioni definite sopra
    # Ad esempio:
    # from app import db
    # from models import QoSConfig, QoSClass, QoSRule
    # 
    # Pulisci tutte le configurazioni esistenti
    # execute_command([TC_PATH, "qdisc", "del", "dev", "eth0", "root"])
    # execute_command([IPTABLES_PATH, "-t", "mangle", "-F", "POSTROUTING"])
    # 
    # Per ogni configurazione attiva
    # for config in QoSConfig.query.filter_by(enabled=True).all():
    #     setup_qos(config.id, config.interface, config.download_bandwidth, 
    #               config.upload_bandwidth, config.default_class, config.hierarchical)
    #     
    #     # Per ogni classe
    #     for qos_class in config.classes:
    #         add_qos_class(config.id, qos_class.id, qos_class.name, qos_class.priority,
    #                        qos_class.min_bandwidth, qos_class.max_bandwidth)
    #         
    #         # Per ogni regola della classe
    #         for rule in qos_class.rules:
    #             if rule.enabled:
    #                 add_qos_rule(rule.id, qos_class.id, rule.source, rule.destination,
    #                              rule.protocol, rule.src_port, rule.dst_port,
    #                              rule.dscp, rule.direction)
    
    # Per ora, simuliamo il successo dell'operazione
    logger.info("Tutte le regole QoS applicate con successo (simulazione)")
    return True