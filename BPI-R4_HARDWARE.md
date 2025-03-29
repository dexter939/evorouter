# Guida all'Hardware Banana Pi BPI-R4

## Specifiche Tecniche

Il Banana Pi BPI-R4 è un router open source con le seguenti caratteristiche:

- **Processore**: MediaTek MT7988A (Filogic 880) quad-core Arm Cortex-A73 @2.0GHz
- **RAM**: 4GB DDR4
- **Storage**: eMMC 8GB + slot microSD
- **Networking**:
  - 5 porte Ethernet 2.5GbE
  - 1 porta SFP+ 10GbE
  - WiFi 6E (IEEE 802.11ax) con 4x4 MIMO
  - Bluetooth 5.0
- **Porte I/O**:
  - 1x USB 3.0
  - 1x USB 2.0
  - 1x M.2 Key-M slot
  - 1x M.2 Key-E slot
  - 30 pin GPIO header
  - Porta console UART
- **Alimentazione**: DC 12V/2A

## Interazione con l'Hardware

### Accesso alle Porte GPIO

Il BPI-R4 fornisce un header GPIO da 30 pin che può essere utilizzato per collegare sensori, display, o altri dispositivi esterni. I pin GPIO possono essere controllati attraverso il file system `/sys/class/gpio/` o utilizzando librerie Python come `RPi.GPIO` o `gpiod`.

```python
# Esempio di controllo GPIO con gpiod
import gpiod

# Ottieni il chip GPIO
chip = gpiod.Chip('gpiochip0')

# Configura il pin come output
line = chip.get_line(5)  # Esempio con GPIO 5
line.request(consumer="mia_app", type=gpiod.LINE_REQ_DIR_OUT)

# Imposta il pin a livello alto
line.set_value(1)

# Imposta il pin a livello basso
line.set_value(0)
```

### Configurazione Rete

Il BPI-R4 supporta switch integrato con VLAN hardware. È possibile configurare le porte Ethernet utilizzando `swconfig` o `DSA (Distributed Switch Architecture)`.

#### Esempio di configurazione VLAN con DSA:

```bash
# Assegnare un IP alla porta WAN
ip addr add 192.168.1.1/24 dev eth0

# Configurare il bridge per le porte LAN
ip link add name br0 type bridge
ip link set eth1 master br0
ip link set eth2 master br0
ip link set eth3 master br0
ip link set eth4 master br0
ip addr add 192.168.0.1/24 dev br0
ip link set br0 up
```

### Gestione WiFi

Il chip WiFi può essere gestito utilizzando gli strumenti standard Linux come `iw`, `iwconfig` e `hostapd`.

#### Esempio di configurazione Access Point:

```bash
# Installare hostapd
apt install hostapd

# Configurazione hostapd
cat > /etc/hostapd/hostapd.conf << EOF
interface=wlan0
driver=nl80211
ssid=BPI-R4-AP
hw_mode=a
channel=36
ieee80211d=1
country_code=IT
ieee80211n=1
ieee80211ac=1
wmm_enabled=1
auth_algs=1
wpa=2
wpa_passphrase=password_sicura
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

# Avviare il servizio
systemctl enable hostapd
systemctl start hostapd
```

### Configurazione SFP+

La porta SFP+ 10GbE può essere configurata come qualsiasi altra interfaccia di rete:

```bash
# Configurare l'interfaccia SFP+
ip addr add 10.0.0.1/24 dev sfp0
ip link set sfp0 up

# Verificare lo stato
ethtool sfp0
```

## FreeSWITCH e Supporto VoIP

Il BPI-R4 è potente abbastanza da funzionare come un PBX completo con FreeSWITCH:

### Ottimizzazione per FreeSWITCH

1. **Priorità dei processi**: È possibile assegnare priorità più alte al processo FreeSWITCH

```bash
# Impostare priorità alta per FreeSWITCH
chrt -f -p 80 $(pidof freeswitch)
```

2. **Configurazione kernel**: Modificare alcuni parametri del kernel per migliorare le prestazioni in tempo reale

```bash
# Modificare parametri di rete
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
```

## Gestione dell'Alimentazione

Il BPI-R4 consuma circa 5-10W in condizioni normali. È possibile ridurre il consumo disabilitando componenti non utilizzati:

```bash
# Disabilitare WiFi se non utilizzato
rfkill block wifi

# Ridurre la frequenza della CPU
echo powersave > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
echo powersave > /sys/devices/system/cpu/cpu1/cpufreq/scaling_governor
echo powersave > /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor
echo powersave > /sys/devices/system/cpu/cpu3/cpufreq/scaling_governor
```

## Risoluzione Problemi Hardware

### Problemi di Boot

Se il dispositivo non si avvia:
1. Verificare che l'alimentatore fornisca 12V/2A
2. Controllare il LED di accensione
3. Provare a riavviare premendo il pulsante di reset
4. Verificare che l'immagine microSD sia scritta correttamente

### Problemi di Rete

Per problemi con le porte Ethernet:
1. Verificare lo stato dei LED delle porte
2. Controllare i cavi di rete
3. Verificare lo stato delle interfacce con `ip link`
4. Controllare i log di sistema: `dmesg | grep eth`

### Sovratemperatura

Il BPI-R4 può surriscaldarsi sotto carico intenso. È consigliabile:
1. Installare un dissipatore di calore adeguato
2. Garantire una buona ventilazione
3. Monitorare la temperatura: `cat /sys/class/thermal/thermal_zone0/temp`