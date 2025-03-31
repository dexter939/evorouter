from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, UPnPConfig, UPnPPortMapping, SystemLog
from utils.upnp import upnp_manager
from datetime import datetime
import json
import logging

# Crea logger
logger = logging.getLogger(__name__)

upnp_bp = Blueprint('upnp', __name__)

@upnp_bp.route('/upnp', methods=['GET'])
@login_required
def index():
    """Dashboard UPnP"""
    # Recupera la configurazione UPnP
    config = UPnPConfig.query.first()
    if not config:
        # Crea configurazione predefinita se non esiste
        config = UPnPConfig(enabled=False)
        db.session.add(config)
        db.session.commit()
    
    # Recupera i port mapping attivi dal database
    port_mappings = UPnPPortMapping.query.filter_by(enabled=True).all()
    
    # Ottieni lo stato attuale da miniupnpc
    upnp_status = upnp_manager.get_status()
    
    # Log di sistema
    log_entry = SystemLog(
        log_type='network',
        level='info',
        message=f"Visualizzazione dashboard UPnP da {request.remote_addr}"
    )
    db.session.add(log_entry)
    db.session.commit()
    
    return render_template(
        'firewall/upnp.html',
        config=config,
        port_mappings=port_mappings, 
        upnp_status=upnp_status
    )

@upnp_bp.route('/upnp/status', methods=['GET'])
@login_required
def status():
    """API: Stato UPnP"""
    # Ottieni stato UPnP
    upnp_status = upnp_manager.get_status()
    
    # Recupera mappature di porte attive
    device_mappings = upnp_manager.get_mapped_ports()
    
    # Recupera configurazione dal DB
    config = UPnPConfig.query.first()
    if not config:
        config = UPnPConfig(enabled=False)
        db.session.add(config)
        db.session.commit()
    
    data = {
        'status': upnp_status,
        'config': {
            'enabled': config.enabled,
            'secure_mode': config.secure_mode,
            'max_lease_duration': config.max_lease_duration,
            'allow_remote_host': config.allow_remote_host,
            'port_ranges': {
                'internal': {
                    'start': config.internal_port_range_start,
                    'end': config.internal_port_range_end
                },
                'external': {
                    'start': config.external_port_range_start,
                    'end': config.external_port_range_end
                }
            }
        },
        'port_mappings': device_mappings
    }
    
    return jsonify(data)

@upnp_bp.route('/upnp/config', methods=['POST'])
@login_required
def update_config():
    """Aggiorna la configurazione UPnP"""
    if not current_user.is_admin:
        flash('Devi essere amministratore per modificare la configurazione UPnP.', 'danger')
        return redirect(url_for('upnp.index'))
    
    try:
        config = UPnPConfig.query.first()
        if not config:
            config = UPnPConfig()
            db.session.add(config)
        
        # Aggiorna i campi di configurazione
        config.enabled = 'enabled' in request.form
        config.secure_mode = 'secure_mode' in request.form
        config.allow_remote_host = 'allow_remote_host' in request.form
        config.allow_loopback = 'allow_loopback' in request.form
        
        # Valori numerici
        config.internal_port_range_start = int(request.form.get('internal_port_range_start', 1024))
        config.internal_port_range_end = int(request.form.get('internal_port_range_end', 65535))
        config.external_port_range_start = int(request.form.get('external_port_range_start', 1024))
        config.external_port_range_end = int(request.form.get('external_port_range_end', 65535))
        config.max_lease_duration = int(request.form.get('max_lease_duration', 86400))
        config.notify_interval = int(request.form.get('notify_interval', 1800))
        
        # Convalida i valori
        if config.internal_port_range_start < 1 or config.internal_port_range_start > 65535:
            raise ValueError("La porta interna iniziale deve essere compresa tra 1 e 65535")
        if config.internal_port_range_end < 1 or config.internal_port_range_end > 65535:
            raise ValueError("La porta interna finale deve essere compresa tra 1 e 65535")
        if config.external_port_range_start < 1 or config.external_port_range_start > 65535:
            raise ValueError("La porta esterna iniziale deve essere compresa tra 1 e 65535")
        if config.external_port_range_end < 1 or config.external_port_range_end > 65535:
            raise ValueError("La porta esterna finale deve essere compresa tra 1 e 65535")
        if config.internal_port_range_start >= config.internal_port_range_end:
            raise ValueError("La porta interna iniziale deve essere minore della porta interna finale")
        if config.external_port_range_start >= config.external_port_range_end:
            raise ValueError("La porta esterna iniziale deve essere minore della porta esterna finale")
        
        config.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log di sistema
        log_entry = SystemLog(
            log_type='network',
            level='info',
            message=f"Configurazione UPnP aggiornata da {request.remote_addr}"
        )
        db.session.add(log_entry)
        db.session.commit()
        
        flash('Configurazione UPnP aggiornata con successo.', 'success')
    except ValueError as e:
        flash(f'Errore di validazione: {str(e)}', 'danger')
    except Exception as e:
        flash(f'Errore durante l\'aggiornamento della configurazione UPnP: {str(e)}', 'danger')
        logger.error(f"Errore durante l'aggiornamento della configurazione UPnP: {str(e)}")
    
    return redirect(url_for('upnp.index'))

@upnp_bp.route('/upnp/mapping/add', methods=['POST'])
@login_required
def add_mapping():
    """Aggiungi un port mapping UPnP"""
    if not current_user.is_admin:
        flash('Devi essere amministratore per aggiungere port mapping UPnP.', 'danger')
        return redirect(url_for('upnp.index'))
    
    try:
        # Ottieni dati dal form
        description = request.form.get('description', '')
        external_port = int(request.form.get('external_port', 0))
        internal_port = int(request.form.get('internal_port', 0))
        internal_client = request.form.get('internal_client', '')
        protocol = request.form.get('protocol', 'TCP')
        lease_duration = int(request.form.get('lease_duration', 0))
        enabled = 'enabled' in request.form
        remote_host = request.form.get('remote_host', '')
        
        # Convalida i valori
        if external_port < 1 or external_port > 65535:
            raise ValueError("La porta esterna deve essere compresa tra 1 e 65535")
        if internal_port < 1 or internal_port > 65535:
            raise ValueError("La porta interna deve essere compresa tra 1 e 65535")
        if not internal_client:
            raise ValueError("L'indirizzo IP del client interno è obbligatorio")
        
        # Verifica se la porta esterna è già mappata
        if upnp_manager.is_port_mapped(external_port, protocol):
            raise ValueError(f"La porta esterna {external_port} ({protocol}) è già mappata")
        
        # Crea il port mapping
        config = UPnPConfig.query.first()
        if not config:
            config = UPnPConfig(enabled=True)
            db.session.add(config)
            db.session.commit()
        
        # Aggiungi il port mapping tramite miniupnpc
        success = False
        if enabled:
            success = upnp_manager.add_port_mapping(
                external_port, internal_port, internal_client, protocol, description, lease_duration
            )
        
        # Salva il mapping nel database
        port_mapping = UPnPPortMapping(
            config_id=config.id,
            description=description,
            external_port=external_port,
            internal_port=internal_port,
            internal_client=internal_client,
            protocol=protocol,
            lease_duration=lease_duration,
            enabled=enabled,
            remote_host=remote_host,
            last_seen=datetime.utcnow()
        )
        db.session.add(port_mapping)
        db.session.commit()
        
        # Log di sistema
        message = f"Port mapping UPnP aggiunto: {external_port} -> {internal_client}:{internal_port} ({protocol})"
        if not success and enabled:
            message += " [NON RIUSCITO SU DISPOSITIVO]"
        
        log_entry = SystemLog(
            log_type='network',
            level='info' if success or not enabled else 'warning',
            message=message
        )
        db.session.add(log_entry)
        db.session.commit()
        
        if success or not enabled:
            flash('Port mapping UPnP aggiunto con successo.', 'success')
        else:
            flash('Port mapping salvato nel database ma non è stato possibile aggiungerlo al dispositivo.', 'warning')
    except ValueError as e:
        flash(f'Errore di validazione: {str(e)}', 'danger')
    except Exception as e:
        flash(f'Errore durante l\'aggiunta del port mapping UPnP: {str(e)}', 'danger')
        logger.error(f"Errore durante l'aggiunta del port mapping UPnP: {str(e)}")
    
    return redirect(url_for('upnp.index'))

@upnp_bp.route('/upnp/mapping/delete/<int:mapping_id>', methods=['POST'])
@login_required
def delete_mapping(mapping_id):
    """Elimina un port mapping UPnP"""
    if not current_user.is_admin:
        flash('Devi essere amministratore per eliminare port mapping UPnP.', 'danger')
        return redirect(url_for('upnp.index'))
    
    try:
        # Recupera il mapping dal database
        port_mapping = UPnPPortMapping.query.get_or_404(mapping_id)
        
        # Elimina il port mapping tramite miniupnpc
        success = True
        if port_mapping.enabled:
            success = upnp_manager.delete_port_mapping(port_mapping.external_port, port_mapping.protocol)
        
        # Elimina il mapping dal database
        external_port = port_mapping.external_port
        protocol = port_mapping.protocol
        db.session.delete(port_mapping)
        db.session.commit()
        
        # Log di sistema
        message = f"Port mapping UPnP eliminato: {external_port} ({protocol})"
        if not success:
            message += " [NON RIUSCITO SU DISPOSITIVO]"
        
        log_entry = SystemLog(
            log_type='network',
            level='info' if success else 'warning',
            message=message
        )
        db.session.add(log_entry)
        db.session.commit()
        
        if success:
            flash('Port mapping UPnP eliminato con successo.', 'success')
        else:
            flash('Port mapping eliminato dal database ma non è stato possibile eliminarlo dal dispositivo.', 'warning')
    except Exception as e:
        flash(f'Errore durante l\'eliminazione del port mapping UPnP: {str(e)}', 'danger')
        logger.error(f"Errore durante l'eliminazione del port mapping UPnP: {str(e)}")
    
    return redirect(url_for('upnp.index'))

@upnp_bp.route('/upnp/mapping/enable/<int:mapping_id>', methods=['POST'])
@login_required
def enable_mapping(mapping_id):
    """Abilita un port mapping UPnP"""
    if not current_user.is_admin:
        flash('Devi essere amministratore per gestire i port mapping UPnP.', 'danger')
        return redirect(url_for('upnp.index'))
    
    try:
        # Recupera il mapping dal database
        port_mapping = UPnPPortMapping.query.get_or_404(mapping_id)
        
        # Se già abilitato, non fare nulla
        if port_mapping.enabled:
            flash('Il port mapping è già abilitato.', 'info')
            return redirect(url_for('upnp.index'))
        
        # Aggiungi il port mapping tramite miniupnpc
        success = upnp_manager.add_port_mapping(
            port_mapping.external_port, 
            port_mapping.internal_port, 
            port_mapping.internal_client, 
            port_mapping.protocol, 
            port_mapping.description, 
            port_mapping.lease_duration
        )
        
        # Aggiorna il mapping nel database
        port_mapping.enabled = True
        port_mapping.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Log di sistema
        message = f"Port mapping UPnP abilitato: {port_mapping.external_port} -> {port_mapping.internal_client}:{port_mapping.internal_port} ({port_mapping.protocol})"
        if not success:
            message += " [NON RIUSCITO SU DISPOSITIVO]"
        
        log_entry = SystemLog(
            log_type='network',
            level='info' if success else 'warning',
            message=message
        )
        db.session.add(log_entry)
        db.session.commit()
        
        if success:
            flash('Port mapping UPnP abilitato con successo.', 'success')
        else:
            flash('Port mapping aggiornato nel database ma non è stato possibile abilitarlo sul dispositivo.', 'warning')
    except Exception as e:
        flash(f'Errore durante l\'abilitazione del port mapping UPnP: {str(e)}', 'danger')
        logger.error(f"Errore durante l'abilitazione del port mapping UPnP: {str(e)}")
    
    return redirect(url_for('upnp.index'))

@upnp_bp.route('/upnp/mapping/disable/<int:mapping_id>', methods=['POST'])
@login_required
def disable_mapping(mapping_id):
    """Disabilita un port mapping UPnP"""
    if not current_user.is_admin:
        flash('Devi essere amministratore per gestire i port mapping UPnP.', 'danger')
        return redirect(url_for('upnp.index'))
    
    try:
        # Recupera il mapping dal database
        port_mapping = UPnPPortMapping.query.get_or_404(mapping_id)
        
        # Se già disabilitato, non fare nulla
        if not port_mapping.enabled:
            flash('Il port mapping è già disabilitato.', 'info')
            return redirect(url_for('upnp.index'))
        
        # Elimina il port mapping tramite miniupnpc
        success = upnp_manager.delete_port_mapping(port_mapping.external_port, port_mapping.protocol)
        
        # Aggiorna il mapping nel database
        port_mapping.enabled = False
        db.session.commit()
        
        # Log di sistema
        message = f"Port mapping UPnP disabilitato: {port_mapping.external_port} ({port_mapping.protocol})"
        if not success:
            message += " [NON RIUSCITO SU DISPOSITIVO]"
        
        log_entry = SystemLog(
            log_type='network',
            level='info' if success else 'warning',
            message=message
        )
        db.session.add(log_entry)
        db.session.commit()
        
        if success:
            flash('Port mapping UPnP disabilitato con successo.', 'success')
        else:
            flash('Port mapping aggiornato nel database ma non è stato possibile disabilitarlo sul dispositivo.', 'warning')
    except Exception as e:
        flash(f'Errore durante la disabilitazione del port mapping UPnP: {str(e)}', 'danger')
        logger.error(f"Errore durante la disabilitazione del port mapping UPnP: {str(e)}")
    
    return redirect(url_for('upnp.index'))

@upnp_bp.route('/upnp/sync', methods=['POST'])
@login_required
def sync_mappings():
    """Sincronizza i port mapping con il dispositivo UPnP"""
    if not current_user.is_admin:
        flash('Devi essere amministratore per sincronizzare i port mapping UPnP.', 'danger')
        return redirect(url_for('upnp.index'))
    
    try:
        # Ottieni i port mapping dal dispositivo
        device_mappings = upnp_manager.get_mapped_ports()
        
        # Recupera i port mapping dal database
        db_mappings = UPnPPortMapping.query.all()
        
        # Ottieni configurazione UPnP
        config = UPnPConfig.query.first()
        if not config:
            config = UPnPConfig(enabled=True)
            db.session.add(config)
            db.session.commit()
        
        # Sincronizza i port mapping tra il database e il dispositivo
        sync_count = 0
        
        # Aggiungi al database i mapping presenti nel dispositivo ma non nel database
        for device_mapping in device_mappings:
            found = False
            for db_mapping in db_mappings:
                if (db_mapping.external_port == device_mapping['external_port'] and 
                    db_mapping.protocol == device_mapping['protocol']):
                    found = True
                    break
            
            if not found:
                # Mapping presente sul dispositivo ma non nel database, aggiungi al database
                new_mapping = UPnPPortMapping(
                    config_id=config.id,
                    description=device_mapping.get('description', 'Imported from device'),
                    external_port=device_mapping['external_port'],
                    internal_port=device_mapping['internal_port'],
                    internal_client=device_mapping['internal_ip'],
                    protocol=device_mapping['protocol'],
                    lease_duration=device_mapping.get('lease_duration', 0),
                    enabled=True,
                    remote_host=device_mapping.get('remote_host', ''),
                    last_seen=datetime.utcnow()
                )
                db.session.add(new_mapping)
                sync_count += 1
        
        # Aggiorna lo stato dei port mapping nel database rispetto al dispositivo
        for db_mapping in db_mappings:
            found = False
            for device_mapping in device_mappings:
                if (db_mapping.external_port == device_mapping['external_port'] and 
                    db_mapping.protocol == device_mapping['protocol']):
                    found = True
                    # Aggiorna i dettagli del mapping se necessario
                    if db_mapping.internal_client != device_mapping['internal_ip'] or \
                       db_mapping.internal_port != device_mapping['internal_port']:
                        db_mapping.internal_client = device_mapping['internal_ip']
                        db_mapping.internal_port = device_mapping['internal_port']
                        sync_count += 1
                    
                    db_mapping.last_seen = datetime.utcnow()
                    break
            
            # Se il mapping è abilitato nel database ma non presente sul dispositivo,
            # prova a crearlo sul dispositivo
            if not found and db_mapping.enabled:
                success = upnp_manager.add_port_mapping(
                    db_mapping.external_port, 
                    db_mapping.internal_port, 
                    db_mapping.internal_client, 
                    db_mapping.protocol, 
                    db_mapping.description, 
                    db_mapping.lease_duration
                )
                if success:
                    sync_count += 1
        
        db.session.commit()
        
        # Log di sistema
        log_entry = SystemLog(
            log_type='network',
            level='info',
            message=f"Sincronizzazione port mapping UPnP completata: {sync_count} modifiche effettuate"
        )
        db.session.add(log_entry)
        db.session.commit()
        
        flash(f'Sincronizzazione port mapping UPnP completata: {sync_count} modifiche effettuate.', 'success')
    except Exception as e:
        flash(f'Errore durante la sincronizzazione dei port mapping UPnP: {str(e)}', 'danger')
        logger.error(f"Errore durante la sincronizzazione dei port mapping UPnP: {str(e)}")
    
    return redirect(url_for('upnp.index'))