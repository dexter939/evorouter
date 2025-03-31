# Integrazione con Stripe per Dimostrazioni

## Introduzione

Il sistema EvoRouter R4 OS è completamente gratuito e non prevede funzionalità a pagamento o abbonamenti. Questa guida è inclusa esclusivamente per scopi dimostrativi, per mostrare come potrebbe essere implementata un'integrazione con Stripe, senza che questa venga effettivamente utilizzata nel sistema.

> **NOTA IMPORTANTE**: Una versione dimostrativa di questa integrazione è stata implementata nel sistema e può essere visualizzata attraverso il menu "Documentazione Stripe" nella sidebar. Non inserire mai dati di carte di credito reali in questa dimostrazione.

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

## Funzionalità che Potrebbero Essere Teoricamente Integrate

### 1. Esempi di Pagamenti Una Tantum

In un sistema con funzionalità a pagamento, si potrebbero implementare pagamenti una tantum per sbloccare funzionalità premium.

#### Esempio di Flusso di Pagamento (Non Implementato):

1. L'utente seleziona un servizio o funzionalità nel pannello di controllo
2. Viene reindirizzato alla pagina di checkout di Stripe
3. Dopo il pagamento, l'utente viene reindirizzato alla pagina di successo
4. La funzionalità verrebbe attivata

### 2. Esempi di Abbonamenti Ricorrenti

In altri sistemi, per servizi continuativi, potrebbero essere implementati abbonamenti ricorrenti.

#### Esempi di Possibili Piani (Non Implementati in EvoRouter R4):

- **Esempio Base**: Supporto email, aggiornamenti
- **Esempio Premium**: Supporto prioritario, backup remoti
- **Esempio Business**: Monitoraggio 24/7, assistenza telefonica avanzata

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

## Implementazione Dimostrativa

Una implementazione dimostrativa di questa integrazione è stata aggiunta al sistema principalmente per scopi educativi. Questa implementazione:

1. Non processa pagamenti effettivi
2. Non memorizza dati di pagamento
3. È accessibile attraverso il menu "Documentazione Stripe" nella sidebar
4. È progettata per mostrare l'architettura di un'integrazione con Stripe senza effettivamente processare transazioni

Per visualizzare il codice di esempio, consulta il file `routes/payments.py` che contiene l'implementazione degli endpoint discussi in questa guida.

## Nota Conclusiva

**Questa guida e l'implementazione associata sono puramente dimostrative**. Il sistema EvoRouter R4 OS è completamente gratuito e non richiede pagamenti per alcuna funzionalità. L'implementazione di Stripe è inclusa solo come esempio di architettura di integrazione con sistemi di pagamento.

Tutte le funzionalità del router sono disponibili gratuitamente senza limitazioni, abbonamenti o costi aggiuntivi.