"""
Utility module per l'esecuzione di test di velocità della rete.
Fornisce funzioni per misurare la larghezza di banda, latenza e jitter.
"""

import subprocess
import json
import re
import time
import socket
import multiprocessing
import requests
from datetime import datetime
import psutil
import logging

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_ping_stats(host="8.8.8.8", count=10):
    """
    Esegue un test di ping verso un host e restituisce statistiche.
    
    Args:
        host (str): L'indirizzo IP o nome host da pingare
        count (int): Numero di pacchetti da inviare
        
    Returns:
        dict: Dizionario contenente min/avg/max/mdev latenza in ms e packet_loss in percentuale
    """
    try:
        logger.info(f"Esecuzione test ping verso {host} con {count} pacchetti...")
        
        # Comando ping con opzioni per output parsabile
        cmd = ["ping", "-c", str(count), "-q", host]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"Ping fallito con codice {result.returncode}: {result.stderr}")
            return {
                "success": False,
                "error": f"Ping fallito: {result.stderr}",
                "min": 0,
                "avg": 0,
                "max": 0,
                "mdev": 0,
                "packet_loss": 100
            }
        
        # Estrai statistiche dall'output di ping
        output = result.stdout
        
        # Estrai packet loss
        packet_loss_match = re.search(r"(\d+)% packet loss", output)
        packet_loss = int(packet_loss_match.group(1)) if packet_loss_match else 100
        
        # Estrai statistiche di latenza (min/avg/max/mdev)
        stats_match = re.search(r"min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", output)
        
        if stats_match:
            min_latency = float(stats_match.group(1))
            avg_latency = float(stats_match.group(2))
            max_latency = float(stats_match.group(3))
            mdev_latency = float(stats_match.group(4))
        else:
            min_latency = avg_latency = max_latency = mdev_latency = 0
        
        return {
            "success": True,
            "min": min_latency,
            "avg": avg_latency,
            "max": max_latency,
            "mdev": mdev_latency,
            "packet_loss": packet_loss
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Il comando ping è scaduto dopo 30 secondi")
        return {
            "success": False,
            "error": "Timeout durante l'esecuzione del ping",
            "min": 0,
            "avg": 0,
            "max": 0, 
            "mdev": 0,
            "packet_loss": 100
        }
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione del test ping: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "min": 0,
            "avg": 0,
            "max": 0,
            "mdev": 0,
            "packet_loss": 100
        }

def run_speed_test(servers=None):
    """
    Esegue un test di velocità della rete usando speedtest-cli.
    
    Args:
        servers (list): Lista opzionale di server ID da utilizzare per il test
        
    Returns:
        dict: Risultati del test di velocità inclusi download, upload e ping
    """
    try:
        logger.info("Avvio test di velocità della rete...")
        
        cmd = ["speedtest-cli", "--json"]
        if servers:
            servers_str = ",".join(map(str, servers))
            cmd.extend(["--server", servers_str])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logger.error(f"Test di velocità fallito con codice {result.returncode}: {result.stderr}")
            return {
                "success": False,
                "error": f"Test di velocità fallito: {result.stderr}",
                "download": 0,
                "upload": 0,
                "ping": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Analizza l'output JSON
        try:
            data = json.loads(result.stdout)
            
            # Converti da bit/s a Mbit/s
            download_mbps = data["download"] / 1_000_000
            upload_mbps = data["upload"] / 1_000_000
            
            return {
                "success": True,
                "download": download_mbps,
                "upload": upload_mbps,
                "ping": data["ping"],
                "server": {
                    "name": data["server"]["name"],
                    "location": data["server"]["country"],
                    "host": data["server"]["host"]
                },
                "client": {
                    "ip": data["client"]["ip"],
                    "isp": data["client"]["isp"]
                },
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            logger.error(f"Errore nell'analisi dell'output JSON: {str(e)}")
            return {
                "success": False,
                "error": f"Errore nell'analisi dell'output: {str(e)}",
                "download": 0,
                "upload": 0,
                "ping": 0,
                "timestamp": datetime.now().isoformat()
            }
            
    except subprocess.TimeoutExpired:
        logger.error("Il test di velocità è scaduto dopo 120 secondi")
        return {
            "success": False,
            "error": "Timeout durante l'esecuzione del test di velocità",
            "download": 0,
            "upload": 0,
            "ping": 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione del test di velocità: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "download": 0,
            "upload": 0,
            "ping": 0,
            "timestamp": datetime.now().isoformat()
        }

def measure_jitter(host="8.8.8.8", count=100):
    """
    Misura il jitter della rete inviando una serie di ping e calcolando la variazione.
    
    Args:
        host (str): Host da pingare
        count (int): Numero di pacchetti da inviare
        
    Returns:
        dict: Risultati incluso jitter in ms
    """
    try:
        logger.info(f"Misurazione jitter verso {host}...")
        
        times = []
        for _ in range(count):
            start = time.time()
            try:
                # Invia un singolo pacchetto ICMP e misura il tempo
                subprocess.run(["ping", "-c", "1", "-W", "1", host], 
                               capture_output=True, timeout=1)
                elapsed = (time.time() - start) * 1000  # in ms
                times.append(elapsed)
            except:
                # Ignora eventuali errori e continua
                continue
            
            # Breve pausa tra i ping
            time.sleep(0.01)
        
        if not times:
            return {
                "success": False,
                "error": "Nessuna risposta ricevuta",
                "jitter": 0,
                "packet_loss": 100
            }
        
        # Calcola il jitter come deviazione standard dei tempi di risposta
        avg_time = sum(times) / len(times)
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)
        jitter = variance ** 0.5
        
        # Calcola packet loss
        packet_loss = 100 - (len(times) / count * 100)
        
        return {
            "success": True,
            "jitter": round(jitter, 2),
            "avg_latency": round(avg_time, 2),
            "packet_loss": round(packet_loss, 2),
            "samples": len(times)
        }
        
    except Exception as e:
        logger.error(f"Errore durante la misurazione del jitter: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "jitter": 0,
            "packet_loss": 100
        }

def get_network_interfaces():
    """
    Ottiene informazioni su tutte le interfacce di rete e le loro statistiche.
    
    Returns:
        list: Lista di dizionari contenenti informazioni sulle interfacce
    """
    try:
        interfaces = []
        
        for iface, addrs in psutil.net_if_addrs().items():
            # Ignora interfacce non fisiche o di loopback
            if iface.startswith('lo') or iface.startswith('docker') or 'vir' in iface:
                continue
                
            interface_info = {
                "name": iface,
                "addresses": [],
                "stats": {}
            }
            
            # Aggiungi indirizzi IP
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    interface_info["addresses"].append({
                        "type": "ipv4",
                        "address": addr.address,
                        "netmask": addr.netmask
                    })
                elif addr.family == socket.AF_INET6:  # IPv6
                    interface_info["addresses"].append({
                        "type": "ipv6",
                        "address": addr.address
                    })
            
            # Aggiungi statistiche se disponibili
            if iface in psutil.net_io_counters(pernic=True):
                stats = psutil.net_io_counters(pernic=True)[iface]
                interface_info["stats"] = {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "packets_sent": stats.packets_sent,
                    "packets_recv": stats.packets_recv,
                    "errin": stats.errin,
                    "errout": stats.errout,
                    "dropin": stats.dropin,
                    "dropout": stats.dropout
                }
            
            interfaces.append(interface_info)
            
        return interfaces
    except Exception as e:
        logger.error(f"Errore durante il recupero delle interfacce di rete: {str(e)}")
        return []

def run_comprehensive_test():
    """
    Esegue una serie completa di test di rete.
    
    Returns:
        dict: Risultati completi di tutti i test
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "interfaces": get_network_interfaces()
    }
    
    # Test di ping verso Google DNS
    ping_google = get_ping_stats("8.8.8.8", count=15)
    results["ping_google"] = ping_google
    
    # Test di ping verso Cloudflare DNS
    ping_cloudflare = get_ping_stats("1.1.1.1", count=15)
    results["ping_cloudflare"] = ping_cloudflare
    
    # Misura jitter
    jitter = measure_jitter("8.8.8.8", count=50)
    results["jitter"] = jitter
    
    # Test di velocità completo (se disponibile speedtest-cli)
    try:
        # Verifica se speedtest-cli è installato
        subprocess.run(["which", "speedtest-cli"], check=True, capture_output=True)
        speed_results = run_speed_test()
        results["speed_test"] = speed_results
    except subprocess.CalledProcessError:
        # speedtest-cli non installato
        results["speed_test"] = {
            "success": False,
            "error": "speedtest-cli non installato",
            "download": 0,
            "upload": 0,
            "ping": 0
        }
    except Exception as e:
        results["speed_test"] = {
            "success": False,
            "error": str(e),
            "download": 0,
            "upload": 0,
            "ping": 0
        }
    
    return results

def check_internet_connectivity():
    """
    Verifica la connettività Internet tentando di connettersi a server multipli.
    
    Returns:
        dict: Stato della connettività Internet
    """
    targets = [
        "https://www.google.com",
        "https://www.cloudflare.com",
        "https://www.amazon.com"
    ]
    
    results = []
    
    for target in targets:
        try:
            start_time = time.time()
            response = requests.get(target, timeout=5)
            elapsed = (time.time() - start_time) * 1000  # ms
            
            results.append({
                "target": target,
                "success": True,
                "status_code": response.status_code,
                "response_time": round(elapsed, 2)
            })
        except requests.RequestException as e:
            results.append({
                "target": target,
                "success": False,
                "error": str(e)
            })
    
    # Determina se la connettività Internet è presente
    connectivity = any(r["success"] for r in results)
    
    return {
        "connectivity": connectivity,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

# Funzione per eseguire il test in background
def run_background_test(callback=None):
    """
    Esegue il test completo in background usando un processo separato.
    
    Args:
        callback: Funzione di callback da chiamare con i risultati (opzionale)
        
    Returns:
        multiprocessing.Process: Il processo in esecuzione
    """
    def worker():
        results = run_comprehensive_test()
        if callback:
            callback(results)
        return results
    
    process = multiprocessing.Process(target=worker)
    process.start()
    return process

if __name__ == "__main__":
    # Test dello script se eseguito direttamente
    print("Esecuzione test di rete...")
    results = run_comprehensive_test()
    print(json.dumps(results, indent=2))