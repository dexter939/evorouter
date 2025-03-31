"""
Routes per la gestione del firewall.
"""
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc

from app import db
from models import FirewallZone, FirewallRule, FirewallPortForwarding, FirewallIPSet, FirewallServiceGroup, FirewallLog
from forms.firewall import (FirewallZoneForm, FirewallRuleForm, FirewallPortForwardingForm, 
                          FirewallIPSetForm, FirewallServiceGroupForm)
from utils.firewall import (get_firewall_status, get_active_connections, apply_zone_config, apply_rule, 
                           apply_port_forwarding, get_firewall_rules, get_port_forwardings, 
                           flush_all_rules, save_firewall_config, load_firewall_config,
                           create_ipset, add_to_ipset)

# Configurazione del logger
logger = logging.getLogger(__name__)

firewall = Blueprint('firewall', __name__)

@firewall.route('/')
@login_required
def index():
    """Pagina principale del firewall"""
    try:
        # Ottieni lo stato del firewall
        firewall_status = get_firewall_status()
        
        # Ottieni le zone di firewall
        zones = FirewallZone.query.all()
        
        # Ottieni le statistiche di base
        rules_count = FirewallRule.query.count()
        forwards_count = FirewallPortForwarding.query.count()
        ipsets_count = FirewallIPSet.query.count()
        service_groups_count = FirewallServiceGroup.query.count()
        
        # Ottieni le connessioni attive (limitato a 10 per performance)
        active_connections = get_active_connections()[:10]
        
        return render_template('firewall/index.html', 
                             firewall_status=firewall_status,
                             zones=zones,
                             rules_count=rules_count,
                             forwards_count=forwards_count,
                             ipsets_count=ipsets_count,
                             service_groups_count=service_groups_count,
                             active_connections=active_connections)
    except Exception as e:
        logger.error(f"Error loading firewall overview: {str(e)}")
        return render_template('firewall/index.html', error=str(e))

@firewall.route('/zones')
@login_required
def zones():
    """Gestione delle zone di firewall"""
    zones = FirewallZone.query.order_by(FirewallZone.priority).all()
    return render_template('firewall/zones.html', zones=zones)

@firewall.route('/zones/new', methods=['GET', 'POST'])
@login_required
def new_zone():
    """Crea una nuova zona di firewall"""
    form = FirewallZoneForm()
    
    if form.validate_on_submit():
        try:
            zone = FirewallZone(
                name=form.name.data,
                description=form.description.data,
                interfaces=form.interfaces.data,
                default_policy=form.default_policy.data,
                masquerade=form.masquerade.data,
                mss_clamping=form.mss_clamping.data,
                priority=form.priority.data
            )
            db.session.add(zone)
            db.session.commit()
            
            # Applica la configurazione al firewall
            interfaces = form.interfaces.data.split(',')
            apply_zone_config(
                zone.id, 
                interfaces, 
                form.default_policy.data, 
                form.masquerade.data
            )
            
            flash(f'Zona di firewall "{form.name.data}" creata con successo!', 'success')
            return redirect(url_for('firewall.zones'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating firewall zone: {str(e)}")
            flash(f'Errore durante la creazione della zona: {str(e)}', 'danger')
    
    return render_template('firewall/zone_form.html', form=form, title='Nuova Zona')

@firewall.route('/zones/<int:zone_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_zone(zone_id):
    """Modifica una zona di firewall esistente"""
    zone = FirewallZone.query.get_or_404(zone_id)
    form = FirewallZoneForm(obj=zone)
    
    if form.validate_on_submit():
        try:
            # Aggiorna i campi della zona
            form.populate_obj(zone)
            db.session.commit()
            
            # Applica la configurazione aggiornata
            interfaces = form.interfaces.data.split(',')
            apply_zone_config(
                zone.id, 
                interfaces, 
                form.default_policy.data, 
                form.masquerade.data
            )
            
            flash(f'Zona di firewall "{zone.name}" aggiornata con successo!', 'success')
            return redirect(url_for('firewall.zones'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating firewall zone: {str(e)}")
            flash(f'Errore durante l\'aggiornamento della zona: {str(e)}', 'danger')
    
    return render_template('firewall/zone_form.html', form=form, title='Modifica Zona', zone=zone)

@firewall.route('/zones/<int:zone_id>/delete', methods=['POST'])
@login_required
def delete_zone(zone_id):
    """Elimina una zona di firewall"""
    zone = FirewallZone.query.get_or_404(zone_id)
    
    try:
        # Controlla se ci sono regole associate
        rules_count = FirewallRule.query.filter_by(zone_id=zone_id).count()
        if rules_count > 0:
            flash(f'Impossibile eliminare la zona: ci sono {rules_count} regole associate.', 'danger')
            return redirect(url_for('firewall.zones'))
        
        # Rimuovi la zona
        db.session.delete(zone)
        db.session.commit()
        flash(f'Zona di firewall "{zone.name}" eliminata con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting firewall zone: {str(e)}")
        flash(f'Errore durante l\'eliminazione della zona: {str(e)}', 'danger')
    
    return redirect(url_for('firewall.zones'))

@firewall.route('/rules')
@login_required
def rules():
    """Gestione delle regole di firewall"""
    # Ottieni le regole dal DB
    rules = FirewallRule.query.order_by(FirewallRule.zone_id, FirewallRule.priority).all()
    
    # Ottieni le zone per il template
    zones = FirewallZone.query.all()
    zones_dict = {zone.id: zone for zone in zones}
    
    return render_template('firewall/rules.html', rules=rules, zones=zones_dict)

@firewall.route('/rules/new', methods=['GET', 'POST'])
@login_required
def new_rule():
    """Crea una nuova regola di firewall"""
    form = FirewallRuleForm()
    
    # Popola le scelte per le zone
    zones = FirewallZone.query.all()
    form.zone_id.choices = [(z.id, z.name) for z in zones]
    
    if form.validate_on_submit():
        try:
            rule = FirewallRule(
                zone_id=form.zone_id.data,
                name=form.name.data,
                description=form.description.data,
                source=form.source.data,
                destination=form.destination.data,
                protocol=form.protocol.data,
                src_port=form.src_port.data,
                dst_port=form.dst_port.data,
                action=form.action.data,
                log=form.log.data,
                enabled=form.enabled.data,
                priority=form.priority.data
            )
            db.session.add(rule)
            db.session.commit()
            
            # Applica la regola se è abilitata
            if rule.enabled:
                zone = FirewallZone.query.get(rule.zone_id)
                apply_rule(
                    rule.id, 
                    zone.name, 
                    rule.source, 
                    rule.destination, 
                    rule.protocol, 
                    rule.src_port, 
                    rule.dst_port, 
                    rule.action
                )
            
            flash(f'Regola di firewall "{form.name.data}" creata con successo!', 'success')
            return redirect(url_for('firewall.rules'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating firewall rule: {str(e)}")
            flash(f'Errore durante la creazione della regola: {str(e)}', 'danger')
    
    return render_template('firewall/rule_form.html', form=form, title='Nuova Regola')

@firewall.route('/rules/<int:rule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rule(rule_id):
    """Modifica una regola di firewall esistente"""
    rule = FirewallRule.query.get_or_404(rule_id)
    form = FirewallRuleForm(obj=rule)
    
    # Popola le scelte per le zone
    zones = FirewallZone.query.all()
    form.zone_id.choices = [(z.id, z.name) for z in zones]
    
    if form.validate_on_submit():
        try:
            # Aggiorna i campi della regola
            form.populate_obj(rule)
            db.session.commit()
            
            # Applica la regola aggiornata se abilitata
            if rule.enabled:
                zone = FirewallZone.query.get(rule.zone_id)
                apply_rule(
                    rule.id, 
                    zone.name, 
                    rule.source, 
                    rule.destination, 
                    rule.protocol, 
                    rule.src_port, 
                    rule.dst_port, 
                    rule.action
                )
            
            flash(f'Regola di firewall "{rule.name}" aggiornata con successo!', 'success')
            return redirect(url_for('firewall.rules'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating firewall rule: {str(e)}")
            flash(f'Errore durante l\'aggiornamento della regola: {str(e)}', 'danger')
    
    return render_template('firewall/rule_form.html', form=form, title='Modifica Regola', rule=rule)

@firewall.route('/rules/<int:rule_id>/delete', methods=['POST'])
@login_required
def delete_rule(rule_id):
    """Elimina una regola di firewall"""
    rule = FirewallRule.query.get_or_404(rule_id)
    
    try:
        # Rimuovi la regola
        db.session.delete(rule)
        db.session.commit()
        
        # Ricrea tutte le regole (semplificazione, in produzione potrebbe essere più efficiente)
        # flush_all_rules()
        # recreate_all_rules()
        
        flash(f'Regola di firewall "{rule.name}" eliminata con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting firewall rule: {str(e)}")
        flash(f'Errore durante l\'eliminazione della regola: {str(e)}', 'danger')
    
    return redirect(url_for('firewall.rules'))

@firewall.route('/port-forwarding')
@login_required
def port_forwarding():
    """Gestione del port forwarding"""
    forwards = FirewallPortForwarding.query.order_by(FirewallPortForwarding.name).all()
    return render_template('firewall/port_forwarding.html', port_forwards=forwards)

@firewall.route('/port-forwarding/new', methods=['GET', 'POST'])
@login_required
def add_port_forwarding():
    """Crea un nuovo port forwarding"""
    form = FirewallPortForwardingForm()
    
    if form.validate_on_submit():
        try:
            forward = FirewallPortForwarding(
                name=form.name.data,
                description=form.description.data,
                source_zone=form.source_zone.data,
                dest_zone=form.dest_zone.data,
                protocol=form.protocol.data,
                src_dip=form.src_dip.data,
                src_port=form.src_port.data,
                dest_ip=form.dest_ip.data,
                dest_port=form.dest_port.data,
                enabled=form.enabled.data
            )
            db.session.add(forward)
            db.session.commit()
            
            # Applica il port forwarding se abilitato
            if forward.enabled:
                apply_port_forwarding(
                    forward.id,
                    forward.source_zone,
                    forward.protocol,
                    forward.src_port,
                    forward.dest_ip,
                    forward.dest_port
                )
            
            flash(f'Port forwarding "{form.name.data}" creato con successo!', 'success')
            return redirect(url_for('firewall.port_forwarding'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating port forwarding: {str(e)}")
            flash(f'Errore durante la creazione del port forwarding: {str(e)}', 'danger')
    
    return render_template('firewall/port_forwarding_form.html', form=form, title='Nuovo Port Forwarding')

@firewall.route('/port-forwarding/<int:forward_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_port_forwarding(forward_id):
    """Modifica un port forwarding esistente"""
    forward = FirewallPortForwarding.query.get_or_404(forward_id)
    form = FirewallPortForwardingForm(obj=forward)
    
    if form.validate_on_submit():
        try:
            # Aggiorna i campi del port forwarding
            form.populate_obj(forward)
            db.session.commit()
            
            # Applica il port forwarding aggiornato se abilitato
            if forward.enabled:
                apply_port_forwarding(
                    forward.id,
                    forward.source_zone,
                    forward.protocol,
                    forward.src_port,
                    forward.dest_ip,
                    forward.dest_port
                )
            
            flash(f'Port forwarding "{forward.name}" aggiornato con successo!', 'success')
            return redirect(url_for('firewall.port_forwarding'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating port forwarding: {str(e)}")
            flash(f'Errore durante l\'aggiornamento del port forwarding: {str(e)}', 'danger')
    
    return render_template('firewall/port_forwarding_form.html', form=form, title='Modifica Port Forwarding', forward=forward)

@firewall.route('/port-forwarding/<int:forward_id>/toggle', methods=['POST'])
@login_required
def toggle_port_forwarding(forward_id):
    """Attiva/disattiva un port forwarding"""
    forward = FirewallPortForwarding.query.get_or_404(forward_id)
    
    try:
        # Inverti lo stato
        forward.enabled = not forward.enabled
        db.session.commit()
        
        if forward.enabled:
            # Applica il port forwarding
            apply_port_forwarding(
                forward.id,
                forward.source_zone,
                forward.protocol,
                forward.src_port,
                forward.dest_ip,
                forward.dest_port
            )
            flash(f'Port forwarding "{forward.name}" attivato con successo!', 'success')
        else:
            # Rimuovi il port forwarding
            # delete_port_forwarding_rule(forward.id)
            flash(f'Port forwarding "{forward.name}" disattivato con successo!', 'warning')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling port forwarding: {str(e)}")
        flash(f'Errore durante la modifica dello stato del port forwarding: {str(e)}', 'danger')
    
    return redirect(url_for('firewall.port_forwarding'))

@firewall.route('/port-forwarding/<int:forward_id>/delete', methods=['POST'])
@login_required
def delete_port_forwarding(forward_id):
    """Elimina un port forwarding"""
    forward = FirewallPortForwarding.query.get_or_404(forward_id)
    
    try:
        # Rimuovi il port forwarding
        db.session.delete(forward)
        db.session.commit()
        
        # Ricrea tutti i port forwarding (semplificazione)
        # flush_all_rules()
        # recreate_all_port_forwardings()
        
        flash(f'Port forwarding "{forward.name}" eliminato con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting port forwarding: {str(e)}")
        flash(f'Errore durante l\'eliminazione del port forwarding: {str(e)}', 'danger')
    
    return redirect(url_for('firewall.port_forwarding'))

@firewall.route('/ipsets')
@login_required
def ipsets():
    """Gestione degli IP set"""
    ipsets = FirewallIPSet.query.order_by(FirewallIPSet.name).all()
    return render_template('firewall/ipsets.html', ipsets=ipsets)

@firewall.route('/ipsets/new', methods=['GET', 'POST'])
@login_required
def new_ipset():
    """Crea un nuovo IP set"""
    form = FirewallIPSetForm()
    
    if form.validate_on_submit():
        try:
            # Verifica gli indirizzi
            addresses_list = [addr.strip() for addr in form.addresses.data.split('\n') if addr.strip()]
            
            ipset = FirewallIPSet(
                name=form.name.data,
                description=form.description.data,
                type=form.type.data,
                addresses=json.dumps(addresses_list)
            )
            db.session.add(ipset)
            db.session.commit()
            
            # Crea l'ipset nel sistema
            create_ipset(ipset.name, ipset.type)
            
            # Aggiungi gli indirizzi
            for addr in addresses_list:
                add_to_ipset(ipset.name, addr)
            
            flash(f'IP set "{form.name.data}" creato con successo!', 'success')
            return redirect(url_for('firewall.ipsets'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating IP set: {str(e)}")
            flash(f'Errore durante la creazione dell\'IP set: {str(e)}', 'danger')
    
    return render_template('firewall/ipset_form.html', form=form, title='Nuovo IP Set')

@firewall.route('/ipsets/<int:ipset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ipset(ipset_id):
    """Modifica un IP set esistente"""
    ipset = FirewallIPSet.query.get_or_404(ipset_id)
    
    # Converti l'elenco JSON in stringa per il form
    addresses_list = json.loads(ipset.addresses) if ipset.addresses else []
    addresses_str = '\n'.join(addresses_list)
    
    form = FirewallIPSetForm(obj=ipset)
    form.addresses.data = addresses_str
    
    if form.validate_on_submit():
        try:
            # Aggiorna i campi dell'IP set
            ipset.name = form.name.data
            ipset.description = form.description.data
            ipset.type = form.type.data
            
            # Aggiorna gli indirizzi
            addresses_list = [addr.strip() for addr in form.addresses.data.split('\n') if addr.strip()]
            ipset.addresses = json.dumps(addresses_list)
            
            db.session.commit()
            
            # Ricrea l'ipset nel sistema
            # In una implementazione reale potrebbe essere più efficiente aggiornare incrementalmente
            create_ipset(ipset.name, ipset.type)
            for addr in addresses_list:
                add_to_ipset(ipset.name, addr)
            
            flash(f'IP set "{ipset.name}" aggiornato con successo!', 'success')
            return redirect(url_for('firewall.ipsets'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating IP set: {str(e)}")
            flash(f'Errore durante l\'aggiornamento dell\'IP set: {str(e)}', 'danger')
    
    return render_template('firewall/ipset_form.html', form=form, title='Modifica IP Set', ipset=ipset)

@firewall.route('/ipsets/<int:ipset_id>/delete', methods=['POST'])
@login_required
def delete_ipset(ipset_id):
    """Elimina un IP set"""
    ipset = FirewallIPSet.query.get_or_404(ipset_id)
    
    try:
        # Rimuovi l'IP set
        db.session.delete(ipset)
        db.session.commit()
        
        # Rimuovi l'ipset dal sistema
        # execute_command(["ipset", "destroy", ipset.name])
        
        flash(f'IP set "{ipset.name}" eliminato con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting IP set: {str(e)}")
        flash(f'Errore durante l\'eliminazione dell\'IP set: {str(e)}', 'danger')
    
    return redirect(url_for('firewall.ipsets'))

@firewall.route('/service-groups')
@login_required
def service_groups():
    """Gestione dei gruppi di servizi"""
    groups = FirewallServiceGroup.query.order_by(FirewallServiceGroup.name).all()
    return render_template('firewall/service_groups.html', groups=groups)

@firewall.route('/service-groups/new', methods=['GET', 'POST'])
@login_required
def new_service_group():
    """Crea un nuovo gruppo di servizi"""
    form = FirewallServiceGroupForm()
    
    if form.validate_on_submit():
        try:
            # Verifica i servizi
            services_list = [service.strip() for service in form.services.data.split('\n') if service.strip()]
            
            group = FirewallServiceGroup(
                name=form.name.data,
                description=form.description.data,
                services=json.dumps(services_list)
            )
            db.session.add(group)
            db.session.commit()
            
            flash(f'Gruppo di servizi "{form.name.data}" creato con successo!', 'success')
            return redirect(url_for('firewall.service_groups'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating service group: {str(e)}")
            flash(f'Errore durante la creazione del gruppo di servizi: {str(e)}', 'danger')
    
    return render_template('firewall/service_group_form.html', form=form, title='Nuovo Gruppo di Servizi')

@firewall.route('/service-groups/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_service_group(group_id):
    """Modifica un gruppo di servizi esistente"""
    group = FirewallServiceGroup.query.get_or_404(group_id)
    
    # Converti l'elenco JSON in stringa per il form
    services_list = json.loads(group.services) if group.services else []
    services_str = '\n'.join(services_list)
    
    form = FirewallServiceGroupForm(obj=group)
    form.services.data = services_str
    
    if form.validate_on_submit():
        try:
            # Aggiorna i campi del gruppo
            group.name = form.name.data
            group.description = form.description.data
            
            # Aggiorna i servizi
            services_list = [service.strip() for service in form.services.data.split('\n') if service.strip()]
            group.services = json.dumps(services_list)
            
            db.session.commit()
            
            flash(f'Gruppo di servizi "{group.name}" aggiornato con successo!', 'success')
            return redirect(url_for('firewall.service_groups'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating service group: {str(e)}")
            flash(f'Errore durante l\'aggiornamento del gruppo di servizi: {str(e)}', 'danger')
    
    return render_template('firewall/service_group_form.html', form=form, title='Modifica Gruppo di Servizi', group=group)

@firewall.route('/service-groups/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_service_group(group_id):
    """Elimina un gruppo di servizi"""
    group = FirewallServiceGroup.query.get_or_404(group_id)
    
    try:
        # Rimuovi il gruppo
        db.session.delete(group)
        db.session.commit()
        
        flash(f'Gruppo di servizi "{group.name}" eliminato con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting service group: {str(e)}")
        flash(f'Errore durante l\'eliminazione del gruppo di servizi: {str(e)}', 'danger')
    
    return redirect(url_for('firewall.service_groups'))

@firewall.route('/logs')
@login_required
def logs():
    """Visualizza i log del firewall"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    
    logs_query = FirewallLog.query.order_by(desc(FirewallLog.timestamp))
    logs_pagination = logs_query.paginate(page=page, per_page=per_page)
    
    return render_template('firewall/logs.html', logs=logs_pagination)

@firewall.route('/api/logs')
@login_required
def api_logs():
    """API per ottenere i log del firewall (per aggiornamenti AJAX)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    
    logs_query = FirewallLog.query.order_by(desc(FirewallLog.timestamp))
    logs_pagination = logs_query.paginate(page=page, per_page=per_page)
    
    logs_data = [{
        'id': log.id,
        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'source_ip': log.source_ip,
        'destination_ip': log.destination_ip,
        'source_port': log.source_port,
        'destination_port': log.destination_port,
        'protocol': log.protocol,
        'action': log.action,
        'interface': log.interface,
        'packets': log.packets,
        'bytes': log.bytes
    } for log in logs_pagination.items]
    
    return jsonify({
        'logs': logs_data,
        'total': logs_pagination.total,
        'pages': logs_pagination.pages,
        'current_page': logs_pagination.page
    })

@firewall.route('/save-config', methods=['POST'])
@login_required
def save_config():
    """Salva la configurazione del firewall"""
    try:
        success = save_firewall_config()
        if success:
            flash('Configurazione del firewall salvata con successo!', 'success')
        else:
            flash('Errore durante il salvataggio della configurazione del firewall.', 'danger')
    except Exception as e:
        logger.error(f"Error saving firewall configuration: {str(e)}")
        flash(f'Errore durante il salvataggio della configurazione: {str(e)}', 'danger')
    
    return redirect(url_for('firewall.index'))

@firewall.route('/load-config', methods=['POST'])
@login_required
def load_config():
    """Carica la configurazione del firewall"""
    try:
        success = load_firewall_config()
        if success:
            flash('Configurazione del firewall caricata con successo!', 'success')
        else:
            flash('Errore durante il caricamento della configurazione del firewall.', 'danger')
    except Exception as e:
        logger.error(f"Error loading firewall configuration: {str(e)}")
        flash(f'Errore durante il caricamento della configurazione: {str(e)}', 'danger')
    
    return redirect(url_for('firewall.index'))

@firewall.route('/flush-rules', methods=['POST'])
@login_required
def flush_rules():
    """Elimina tutte le regole del firewall"""
    try:
        success = flush_all_rules()
        if success:
            flash('Tutte le regole del firewall sono state eliminate con successo!', 'success')
        else:
            flash('Errore durante l\'eliminazione delle regole del firewall.', 'danger')
    except Exception as e:
        logger.error(f"Error flushing firewall rules: {str(e)}")
        flash(f'Errore durante l\'eliminazione delle regole: {str(e)}', 'danger')
    
    return redirect(url_for('firewall.index'))