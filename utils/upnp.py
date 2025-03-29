import logging
import miniupnpc
import socket
import random
from datetime import datetime, timedelta
from config import DEFAULT_WAN_INTERFACE

# Create logger
logger = logging.getLogger(__name__)

class UPnPManager:
    """
    Gestione UPnP (Universal Plug and Play)
    """
    def __init__(self):
        self.upnp = miniupnpc.UPnP()
    
    def discover(self):
        """
        Scopri i dispositivi UPnP nella rete
        
        Returns:
            dict: Informazioni sul dispositivo UPnP trovato, o None se non trovato
        """
        try:
            logger.info("Ricerca dispositivi UPnP...")
            
            # In ambiente reale usare:
            # self.upnp.discoverdelay = 200  # Millisecondi
            # devices_found = self.upnp.discover()
            # self.upnp.selectigd()
            
            # Simulazione per Replit
            return {
                'device_found': True,
                'external_ip': '203.0.113.' + str(random.randint(1, 254)),
                'device_type': 'InternetGatewayDevice',
                'manufacturer': 'EvoRouter R4',
                'model_name': 'EvoRouter R4',
                'device_url': 'http://192.168.1.1:1900/device.xml'
            }
        except Exception as e:
            logger.error(f"Errore durante la scoperta dei dispositivi UPnP: {str(e)}")
            return None
    
    def get_status(self):
        """
        Ottieni lo stato UPnP
        
        Returns:
            dict: Stato UPnP
        """
        try:
            # In ambiente reale usare:
            # if not self.upnp.lanaddr:
            #     self.discover()
            # external_ip = self.upnp.externalipaddress()
            # status = self.upnp.statusinfo()
            
            # Simulazione per Replit
            return {
                'enabled': True,
                'external_ip': '203.0.113.' + str(random.randint(1, 254)),
                'status': 'Connected',
                'uptime': f"{random.randint(1, 48)} ore, {random.randint(0, 59)} minuti",
                'last_error': None,
                'nat_type': random.choice(['Full Cone', 'Restricted Cone', 'Port Restricted Cone']),
                'connection': {
                    'type': 'Cable/DSL',
                    'upstream': round(random.uniform(10, 50), 2),  # Mbps
                    'downstream': round(random.uniform(50, 150), 2)  # Mbps
                }
            }
        except Exception as e:
            logger.error(f"Errore durante il recupero dello stato UPnP: {str(e)}")
            return {
                'enabled': False,
                'status': 'Error',
                'error': str(e)
            }
    
    def get_mapped_ports(self):
        """
        Ottieni i port mapping UPnP attivi
        
        Returns:
            list: Lista dei port mapping attivi
        """
        try:
            # In ambiente reale usare:
            # mappings = []
            # i = 0
            # while True:
            #     p = self.upnp.getgenericportmapping(i)
            #     if p is None:
            #         break
            #     mappings.append({
            #         'index': i,
            #         'remote_host': p[0],
            #         'external_port': p[1],
            #         'protocol': p[2],
            #         'internal_ip': p[3],
            #         'internal_port': p[4],
            #         'description': p[5],
            #         'lease_duration': p[6]
            #     })
            #     i += 1
            
            # Simulazione per Replit
            number_of_mappings = random.randint(3, 8)
            mappings = []
            
            services = [
                "HTTP Server", "HTTPS Server", "SSH Access", "Game Server", 
                "Media Streaming", "VoIP", "FTP Server", "VNC Remote Desktop"
            ]
            
            protocols = ["TCP", "UDP"]
            
            for i in range(number_of_mappings):
                service = services[i % len(services)]
                protocol = protocols[i % 2]
                external_port = random.randint(1000, 65000)
                internal_port = external_port if random.random() > 0.3 else random.randint(1000, 65000)
                
                # Simulazione di port mapping interna/esterna
                mappings.append({
                    'index': i,
                    'remote_host': '',  # Empty string means any external host
                    'external_port': external_port,
                    'protocol': protocol,
                    'internal_ip': f"192.168.1.{random.randint(2, 253)}",
                    'internal_port': internal_port,
                    'description': service,
                    'lease_duration': random.choice([0, 3600, 86400, 604800]),  # 0=permanent, others are seconds
                    'creation_time': (datetime.now() - timedelta(hours=random.randint(0, 72))).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return mappings
        except Exception as e:
            logger.error(f"Errore durante il recupero dei port mapping UPnP: {str(e)}")
            return []
    
    def add_port_mapping(self, external_port, internal_port, internal_client, protocol='TCP', description='', lease_duration=0):
        """
        Aggiungi un port mapping UPnP
        
        Args:
            external_port (int): Porta esterna
            internal_port (int): Porta interna
            internal_client (str): IP client interno
            protocol (str): Protocollo (TCP, UDP)
            description (str): Descrizione del mapping
            lease_duration (int): Durata del lease in secondi (0 = permanente)
            
        Returns:
            bool: True se il mapping è stato aggiunto con successo
        """
        try:
            # In ambiente reale usare:
            # result = self.upnp.addportmapping(
            #     external_port, protocol, internal_client, internal_port, description, lease_duration
            # )
            
            # Simulazione per Replit
            success = random.random() > 0.1  # 90% di successo
            
            if success:
                logger.info(f"Port mapping aggiunto: {external_port} -> {internal_client}:{internal_port} ({protocol})")
                return True
            else:
                logger.error(f"Errore durante l'aggiunta del port mapping: Porta {external_port} già in uso o non disponibile")
                return False
        except Exception as e:
            logger.error(f"Errore durante l'aggiunta del port mapping: {str(e)}")
            return False
    
    def delete_port_mapping(self, external_port, protocol='TCP'):
        """
        Elimina un port mapping UPnP
        
        Args:
            external_port (int): Porta esterna del mapping da eliminare
            protocol (str): Protocollo (TCP, UDP)
            
        Returns:
            bool: True se il mapping è stato eliminato con successo
        """
        try:
            # In ambiente reale usare:
            # result = self.upnp.deleteportmapping(external_port, protocol)
            
            # Simulazione per Replit
            success = random.random() > 0.1  # 90% di successo
            
            if success:
                logger.info(f"Port mapping eliminato: {external_port} ({protocol})")
                return True
            else:
                logger.error(f"Errore durante l'eliminazione del port mapping: Porta {external_port} non trovata")
                return False
        except Exception as e:
            logger.error(f"Errore durante l'eliminazione del port mapping: {str(e)}")
            return False
    
    def get_external_ip(self):
        """
        Ottieni l'IP esterno tramite UPnP
        
        Returns:
            str: Indirizzo IP esterno
        """
        try:
            # In ambiente reale usare:
            # return self.upnp.externalipaddress()
            
            # Simulazione per Replit
            return '203.0.113.' + str(random.randint(1, 254))
        except Exception as e:
            logger.error(f"Errore durante il recupero dell'IP esterno: {str(e)}")
            return None
    
    def is_port_mapped(self, external_port, protocol='TCP'):
        """
        Verifica se una porta è già mappata
        
        Args:
            external_port (int): Porta esterna da verificare
            protocol (str): Protocollo (TCP, UDP)
            
        Returns:
            bool: True se la porta è già mappata
        """
        try:
            mappings = self.get_mapped_ports()
            for mapping in mappings:
                if mapping['external_port'] == external_port and mapping['protocol'] == protocol:
                    return True
            return False
        except Exception as e:
            logger.error(f"Errore durante la verifica del port mapping: {str(e)}")
            return False


# Istanza globale per l'uso nel resto dell'applicazione
upnp_manager = UPnPManager()