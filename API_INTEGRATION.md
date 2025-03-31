# Guida all'Integrazione API

## Introduzione

Il sistema operativo EvoRouter R4 offre un'API RESTful completa che consente l'integrazione con sistemi di gestione remota e altri servizi. Questa guida spiega come utilizzare le API disponibili per automatizzare e controllare remotamente il tuo dispositivo EvoRouter R4.

## Autenticazione

L'API utilizza autenticazione JWT (JSON Web Token) per proteggere le richieste. Per ottenere un token di accesso:

```
POST /api/token
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

Risposta:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Utilizza questo token in ogni richiesta successiva nell'header di autorizzazione:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## API Disponibili

### 1. Informazioni di Sistema

#### Ottieni Stato Sistema

```
GET /api/system/status
```

Risposta:

```json
{
  "status": "online",
  "uptime": "10 days, 4 hours, 30 minutes",
  "cpu_load": 12.5,
  "memory_usage": {
    "total": 4096,
    "used": 1024,
    "free": 3072,
    "percent": 25.0
  },
  "disk_usage": {
    "total": 7864,
    "used": 2532,
    "free": 5332,
    "percent": 32.2
  },
  "temperature": 45.6
}
```

#### Riavvia Sistema

```
POST /api/system/reboot
```

Risposta:

```json
{
  "status": "success",
  "message": "System reboot initiated"
}
```

### 2. Configurazione Rete

#### Ottieni Interfacce di Rete

```
GET /api/network/interfaces
```

Risposta:

```json
{
  "interfaces": [
    {
      "name": "eth0",
      "type": "wan",
      "ip_mode": "dhcp",
      "ip_address": "192.168.1.100",
      "subnet_mask": "255.255.255.0",
      "gateway": "192.168.1.1",
      "dns_servers": "8.8.8.8,8.8.4.4",
      "is_active": true
    },
    {
      "name": "eth1",
      "type": "lan",
      "ip_mode": "static",
      "ip_address": "192.168.0.1",
      "subnet_mask": "255.255.255.0",
      "is_active": true
    }
  ]
}
```

#### Configura Interfaccia di Rete

```
PUT /api/network/interfaces/{interface_name}
Content-Type: application/json

{
  "ip_mode": "static",
  "ip_address": "192.168.1.10",
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "dns_servers": "8.8.8.8,8.8.4.4"
}
```

Risposta:

```json
{
  "status": "success",
  "message": "Network interface eth0 configured successfully"
}
```

### 3. Configurazione Centralino (FreeSWITCH)

#### Ottieni Stato Centralino

```
GET /api/freeswitch/status
```

Risposta:

```json
{
  "status": {
    "installed": true,
    "running": true,
    "version": "1.10.9",
    "uptime": "2 days, 5 hours, 12 minutes",
    "active_calls": 2,
    "registered_extensions": 5
  }
}
```

#### Ottieni Estensioni SIP

```
GET /api/freeswitch/extensions
```

Risposta:

```json
{
  "extensions": [
    {
      "id": 1,
      "extension_number": "100",
      "name": "Reception",
      "voicemail_enabled": true,
      "created_at": "2023-11-15T10:30:00Z",
      "updated_at": "2023-11-15T10:30:00Z"
    },
    {
      "id": 2,
      "extension_number": "101",
      "name": "Sales",
      "voicemail_enabled": true,
      "created_at": "2023-11-15T10:35:00Z",
      "updated_at": "2023-11-15T10:35:00Z"
    }
  ]
}
```

#### Aggiungi Estensione SIP

```
POST /api/freeswitch/extensions
Content-Type: application/json

{
  "extension_number": "102",
  "name": "Support",
  "password": "secure_password",
  "voicemail_enabled": true,
  "voicemail_pin": "1234"
}
```

Risposta:

```json
{
  "status": "success",
  "message": "Extension added successfully",
  "extension": {
    "id": 3,
    "extension_number": "102",
    "name": "Support",
    "voicemail_enabled": true,
    "created_at": "2023-11-15T14:20:00Z",
    "updated_at": "2023-11-15T14:20:00Z"
  }
}
```

#### Aggiorna Estensione SIP

```
PUT /api/freeswitch/extensions/{extension_id}
Content-Type: application/json

{
  "name": "Support Team",
  "voicemail_enabled": false
}
```

Risposta:

```json
{
  "status": "success",
  "message": "Extension updated successfully"
}
```

#### Elimina Estensione SIP

```
DELETE /api/freeswitch/extensions/{extension_id}
```

Risposta:

```json
{
  "status": "success",
  "message": "Extension deleted successfully"
}
```

## Gestione dei Token API

### Lista Token

```
GET /api/tokens
```

Risposta:

```json
{
  "tokens": [
    {
      "id": 1,
      "name": "Management System",
      "created_at": "2023-11-10T08:15:00Z",
      "expires_at": "2024-11-10T08:15:00Z",
      "last_used_at": "2023-11-15T14:30:00Z",
      "is_active": true
    }
  ]
}
```

### Crea Token

```
POST /api/tokens
Content-Type: application/json

{
  "name": "Monitoring System",
  "expires_in": 31536000
}
```

Risposta:

```json
{
  "status": "success",
  "message": "Token created successfully",
  "token": {
    "id": 2,
    "name": "Monitoring System",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "created_at": "2023-11-15T15:00:00Z",
    "expires_at": "2024-11-14T15:00:00Z",
    "is_active": true
  }
}
```

### Revoca Token

```
DELETE /api/tokens/{token_id}
```

Risposta:

```json
{
  "status": "success",
  "message": "Token revoked successfully"
}
```

## Gestione Errori

L'API restituisce errori standard HTTP con un corpo JSON che fornisce ulteriori dettagli:

```json
{
  "error": "unauthorized",
  "message": "Invalid authentication credentials",
  "status": 401
}
```

Codici di errore comuni:
- 400: Bad Request - La richiesta contiene parametri non validi
- 401: Unauthorized - Autenticazione fallita
- 403: Forbidden - L'utente non ha i permessi necessari
- 404: Not Found - La risorsa richiesta non esiste
- 500: Internal Server Error - Errore interno del server

## Integrazione con Sistemi Esterni

### Esempio di Script di Integrazione (Python)

```python
import requests
import json

API_BASE_URL = "http://your-evorouter-ip/api"
USERNAME = "admin"
PASSWORD = "your_password"

def get_auth_token():
    """Ottiene un token di autenticazione JWT"""
    response = requests.post(
        f"{API_BASE_URL}/token",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Autenticazione fallita: {response.text}")

def get_system_status(token):
    """Ottiene lo stato del sistema"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/system/status", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Errore nel recupero dello stato: {response.text}")

def add_sip_extension(token, extension_data):
    """Aggiunge una nuova estensione SIP"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{API_BASE_URL}/freeswitch/extensions",
        headers=headers,
        json=extension_data
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Errore nell'aggiunta dell'estensione: {response.text}")

# Esempio di utilizzo
if __name__ == "__main__":
    try:
        # Ottieni token
        token = get_auth_token()
        
        # Verifica stato sistema
        status = get_system_status(token)
        print(f"CPU Load: {status['cpu_load']}%")
        print(f"Memory Usage: {status['memory_usage']['percent']}%")
        
        # Aggiungi estensione SIP
        extension = {
            "extension_number": "103",
            "name": "Marketing",
            "password": "secure_password123",
            "voicemail_enabled": True,
            "voicemail_pin": "5678"
        }
        result = add_sip_extension(token, extension)
        print(f"Extension added: {result['extension']['name']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
```

## Considerazioni sulla Sicurezza

1. **Protezione dell'API**:
   - Utilizza sempre HTTPS per proteggere le comunicazioni
   - Limita l'accesso all'API a indirizzi IP fidati quando possibile
   - Ruota regolarmente i token API

2. **Gestione Token**:
   - Memorizza i token in modo sicuro
   - Utilizza token con privilegi minimi necessari
   - Revoca i token non utilizzati o compromessi

3. **Monitoraggio**:
   - Controlla regolarmente i log di accesso all'API
   - Configura avvisi per attività sospette
   - Implementa limiti di rate per prevenire attacchi di forza bruta