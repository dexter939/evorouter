# EvoRouter R4 OS

Sistema operativo personalizzato per router EvoRouter R4, con interfaccia web avanzata, supporto per firewall, VPN, QoS e centralino telefonico integrato.

## Caratteristiche

- 🚀 **Interfaccia Web Responsive**: Gestisci facilmente il tuo router da qualsiasi dispositivo
- 🔒 **Sicurezza Avanzata**: Firewall configurabile, VPN, e protezione da attacchi comuni
- 📞 **Centralino Telefonico Integrato**: Configurazione e gestione di telefonia VoIP
- 🌐 **Gestione di Rete Completa**: DHCP, DNS, QoS, UPnP e molto altro
- 🔄 **Supporto VPN**: OpenVPN per connessioni sicure
- 📊 **Monitoraggio Real-time**: Dashboard con statistiche e grafici
- 💼 **Gestione Remota**: API per l'integrazione con sistemi di monitoraggio esterni
- 🔍 **Test di Velocità**: Strumento integrato per misurare prestazioni di rete con grafici dettagliati
- 🖥️ **Multi-piattaforma**: Supporto per EvoRouter R4 hardware e installazioni su Ubuntu/Debian

## Installazione

### Per dispositivi EvoRouter R4
Per installare EvoRouter R4 OS su un dispositivo EvoRouter R4, esegui:

```bash
curl -sSL https://raw.githubusercontent.com/dexter939/evorouter/main/install_evorouter.sh | sudo bash
```

### Per sistemi Ubuntu/Debian
Per installare su sistemi Ubuntu/Debian standard, usa lo script specifico:

```bash
curl -sSL https://raw.githubusercontent.com/dexter939/evorouter/main/install_evorouter_ubuntu.sh | sudo bash
```

### Installazione personalizzata
Per un'installazione personalizzata, scarica lo script e modificalo secondo le tue esigenze:

```bash
wget https://raw.githubusercontent.com/dexter939/evorouter/main/install_evorouter.sh
chmod +x install_evorouter.sh
# Personalizza il file secondo le tue esigenze
sudo ./install_evorouter.sh
```

### Problemi comuni

Se dopo l'installazione riscontri un errore 404 di Nginx, usa lo script di correzione:

```bash
sudo ./fix_nginx_configuration.sh
```

## Aggiornamento

Per aggiornare l'installazione esistente di EvoRouter R4 OS, utilizza:

```bash
sudo /opt/evorouter/update_evorouter.sh
```

Oppure scarica l'ultimo script di aggiornamento:

```bash
curl -sSL https://raw.githubusercontent.com/dexter939/evorouter/main/update_evorouter.sh | sudo bash
```

## Requisiti hardware

EvoRouter R4 OS è progettato specificamente per l'hardware EvoRouter R4 con le seguenti specifiche:

- CPU: Quad-core Arm Cortex-A53 (1.5 GHz)
- RAM: 2GB DDR4
- Storage: eMMC 8GB (minimo)
- Porte: 5x Gigabit Ethernet
- Wi-Fi: 802.11ac

Per maggiori dettagli sull'hardware supportato, consulta [HARDWARE.md](HARDWARE.md).

## Documentazione

Documentazione completa disponibile nei seguenti file:

- [INSTALL.md](INSTALL.md): Istruzioni dettagliate per l'installazione
- [API_INTEGRATION.md](API_INTEGRATION.md): Documentazione API per l'integrazione con sistemi esterni
- [HARDWARE.md](HARDWARE.md): Specifiche hardware supportate
- [CONTRIBUTING.md](CONTRIBUTING.md): Linee guida per contribuire al progetto

## Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file [LICENSE](LICENSE) per i dettagli.

## Supporto

Per problemi, domande o suggerimenti, apri una issue su GitHub o contatta il team di supporto.

---

&copy; 2025 EvoRouter. Tutti i diritti riservati.