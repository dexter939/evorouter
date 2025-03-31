import os
import stripe
from flask import Blueprint, jsonify, request, redirect, url_for, flash, render_template
from flask_login import current_user, login_required

# Create blueprint
payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

# Initialize Stripe (solo per dimostrazione)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Ottieni il dominio per la redirezione
def get_domain():
    domain = os.environ.get('REPLIT_DEV_DOMAIN') if os.environ.get('REPLIT_DEPLOYMENT') else os.environ.get('REPLIT_DOMAINS')
    if domain and ',' in domain:
        domain = domain.split(',')[0]
    return domain if domain else request.host

@payments_bp.route('/')
@login_required
def payments_index():
    """Visualizza la pagina informativa sui pagamenti"""
    return render_template('payments/index.html')

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """
    Crea una sessione di checkout Stripe (solo dimostrativo)
    Questa funzione non viene mai utilizzata nel sistema reale
    """
    # Verifica se Stripe è configurato
    if not stripe.api_key:
        return jsonify({
            'error': 'Stripe non è configurato. Questa è solo una dimostrazione.'
        }), 400

    try:
        # Ottenere il dominio per la redirezione
        domain = get_domain()
        
        # Ottenere il price_id dalla richiesta
        data = request.get_json()
        price_id = data.get('price_id')
        
        if not price_id:
            return jsonify({'error': 'price_id mancante'}), 400
            
        # Creare la sessione di checkout
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=f"https://{domain}/payments/success",
            cancel_url=f"https://{domain}/payments/cancel",
            customer_email=current_user.email,
        )
        
        # Restituire l'URL della sessione
        return jsonify({
            'status': 'success',
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@payments_bp.route('/success')
@login_required
def payment_success():
    """Pagina di successo pagamento (solo dimostrativa)"""
    return render_template('payments/success.html')

@payments_bp.route('/cancel')
@login_required
def payment_cancel():
    """Pagina di cancellazione pagamento (solo dimostrativa)"""
    return render_template('payments/cancel.html')

@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook di Stripe (solo dimostrativo)
    Questa funzione non viene mai utilizzata nel sistema reale
    """
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Se non c'è un webhook_secret, questo è solo dimostrativo
    if not webhook_secret:
        return jsonify({'status': 'success', 'message': 'Dimostrazione webhook'})
    
    try:
        event = None
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            # Payload non valido
            return jsonify({'error': 'Payload non valido'}), 400
        except stripe.error.SignatureVerificationError as e:
            # Firma non valida
            return jsonify({'error': 'Firma non valida'}), 400
            
        # Gestire l'evento (in un sistema reale)
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            # Qui si gestirebbe l'attivazione di una funzionalità
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500