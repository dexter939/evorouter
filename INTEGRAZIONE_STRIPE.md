# Integrazione con Stripe per Pagamenti

## Introduzione

Il Router OS per BPI-R4 supporta l'integrazione con Stripe per gestire pagamenti ricorrenti, abbonamenti per servizi premium o altri costi associati al funzionamento del dispositivo. Questa guida mostra come configurare e utilizzare l'integrazione con Stripe nel sistema.

## Prerequisiti

1. Un account Stripe (puoi registrarti su [stripe.com](https://stripe.com))
2. Chiave API segreta di Stripe (`STRIPE_SECRET_KEY`)
3. Chiave API pubblica di Stripe (per l'integrazione frontend)

## Configurazione delle Variabili di Ambiente

Per configurare Stripe, devi impostare la chiave API segreta come variabile d'ambiente nel tuo sistema:

```bash
export STRIPE_SECRET_KEY="sk_test_..."  # Usa sk_live_... in produzione
```

Per rendere questa configurazione permanente, aggiungi questa riga al file `/etc/environment` o includi nel file di servizio systemd.

## Funzionalità Integrate

### 1. Pagamenti Una Tantum

Il sistema supporta pagamenti una tantum per sbloccare funzionalità premium o per servizi specifici.

#### Esempio di Flusso di Pagamento:

1. L'utente seleziona un servizio o funzionalità premium nel pannello di controllo
2. Viene reindirizzato alla pagina di checkout di Stripe
3. Dopo il pagamento, l'utente viene reindirizzato alla pagina di successo
4. La funzionalità viene sbloccata nel sistema

### 2. Abbonamenti Ricorrenti

Per servizi continuativi, come manutenzione remota o backup automatici, sono disponibili abbonamenti ricorrenti.

#### Piani di Abbonamento Predefiniti:

- **Base**: Supporto email, aggiornamenti di sicurezza
- **Premium**: Supporto prioritario, backup remoti giornalieri
- **Business**: Monitoraggio 24/7, assistenza telefonica, backup ridondanti

## Implementazione Tecnica

### Endpoint Backend

Il sistema fornisce i seguenti endpoint per l'integrazione con Stripe:

1. **Creazione Sessione di Checkout**
   ```
   POST /api/payments/create-checkout-session
   ```
   Richiesta:
   ```json
   {
     "price_id": "price_1234567890",
     "success_url": "/success",
     "cancel_url": "/cancel"
   }
   ```
   
   Risposta:
   ```json
   {
     "session_id": "cs_test_...",
     "checkout_url": "https://checkout.stripe.com/..."
   }
   ```

2. **Verifica Stato Pagamento**
   ```
   GET /api/payments/status/{payment_id}
   ```
   
   Risposta:
   ```json
   {
     "status": "paid",
     "amount": 1999,
     "currency": "eur",
     "payment_date": "2023-11-15T14:30:00Z"
   }
   ```

3. **Gestione Webhooks**
   ```
   POST /api/payments/webhook
   ```
   
   Questo endpoint riceve notifiche da Stripe quando si verificano eventi rilevanti come pagamenti completati, falliti, abbonamenti aggiornati, ecc.

### Integrazione Frontend

Nel frontend, utilizza Stripe.js per reindirizzare l'utente alla pagina di checkout di Stripe:

```javascript
// Esempio di integrazione nel frontend
async function redirectToCheckout(priceId) {
  try {
    const response = await fetch('/api/payments/create-checkout-session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        price_id: priceId,
        success_url: window.location.origin + '/payment-success',
        cancel_url: window.location.origin + '/payment-cancel',
      }),
    });
    
    const { checkout_url } = await response.json();
    
    // Reindirizza l'utente al checkout di Stripe
    window.location.href = checkout_url;
  } catch (error) {
    console.error('Errore durante la redirezione al checkout:', error);
  }
}
```

## Configurazione dei Webhook

Per ricevere aggiornamenti in tempo reale sui pagamenti, configura i webhook di Stripe:

1. Vai su [Dashboard Stripe](https://dashboard.stripe.com/webhooks)
2. Clicca su "Aggiungi endpoint"
3. Inserisci l'URL del tuo webhook: `https://tuo-dominio.com/api/payments/webhook`
4. Seleziona gli eventi da monitorare:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Ottieni la chiave segreta del webhook e configurala nel tuo sistema:
   ```bash
   export STRIPE_WEBHOOK_SECRET="whsec_..."
   ```

## Modelli di Prodotto in Stripe

### Creazione di Prodotti e Prezzi

Prima di utilizzare l'integrazione, devi configurare prodotti e prezzi nel dashboard di Stripe:

1. Vai su [Prodotti](https://dashboard.stripe.com/products) nel Dashboard Stripe
2. Crea un nuovo prodotto (ad es. "Piano Premium Router OS")
3. Definisci il prezzo e la ricorrenza (una tantum o abbonamento)
4. Copia l'ID del prezzo (es. `price_1234567890`) per utilizzarlo nell'API

### Esempio di Struttura Prodotto

- **Prodotto**: Router OS Premium
  - **Prezzo (Una Tantum)**: €49.99 - `price_premium_onetime`
  - **Prezzo (Abbonamento Mensile)**: €4.99/mese - `price_premium_monthly`
  - **Prezzo (Abbonamento Annuale)**: €49.99/anno - `price_premium_yearly`

## Sicurezza e Best Practices

1. **Non memorizzare mai** i dati delle carte di credito
2. Usa sempre **TLS/HTTPS** per tutte le comunicazioni
3. Verifica la firma degli eventi webhook per prevenire attacchi
4. Gestisci correttamente gli errori e notifica gli utenti
5. Implementa meccanismi di retry per operazioni fallite
6. Mantieni log dettagliati delle transazioni per la risoluzione dei problemi

## Risoluzione dei Problemi

### Problemi Comuni e Soluzioni

1. **Pagamento fallito**
   - Verifica che la carta non sia scaduta o senza fondi
   - Controlla i log per eventuali errori di validazione
   - Verifica le restrizioni geografiche dell'account Stripe

2. **Webhook non ricevuti**
   - Controlla che l'URL del webhook sia accessibile pubblicamente
   - Verifica che il firewall non blocchi le richieste da Stripe
   - Controlla i log degli eventi nel dashboard di Stripe

3. **Errori di configurazione**
   - Verifica che le chiavi API siano corrette e attive
   - Controlla che l'ambiente (test/live) sia configurato correttamente
   - Verifica che i prodotti e i prezzi esistano nel tuo account Stripe

## Esempio di Implementazione Completa

Per un'implementazione completa dell'integrazione Stripe, è possibile fare riferimento al codice sorgente nella directory `/utils/payments.py` e nelle route API in `/routes/payments.py`.