"""
Routes per la gestione del Quality of Service (QoS).
"""
import json
import logging
from typing import List, Dict, Any, Optional
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc

from app import db
from models import QoSConfig, QoSClass, QoSRule, NetworkConfig
from forms.qos import QoSConfigForm, QoSClassForm, QoSRuleForm
from utils.qos import (setup_qos, add_qos_class, add_qos_rule, remove_qos_rule,
                     remove_qos_class, disable_qos, get_qos_status, get_bandwidth_usage,
                     get_interfaces, apply_all_qos_rules)

# Configurazione del logger
logger = logging.getLogger(__name__)

qos = Blueprint('qos', __name__)

@qos.route('/')
@login_required
def index():
    """Pagina principale del QoS"""
    # Ottenere la configurazione QoS
    qos_config = QoSConfig.query.first()
    
    if not qos_config:
        # Creazione di una configurazione predefinita se non esiste
        network_interfaces = get_interfaces()
        default_interface = next((i["name"] for i in network_interfaces if "wan" in i["name"].lower()), "eth0")
        
        qos_config = QoSConfig(
            enabled=False,
            interface=default_interface,
            download_bandwidth=10000,  # 10 Mbps
            upload_bandwidth=1000,     # 1 Mbps
            default_class="default",
            hierarchical=True
        )
        db.session.add(qos_config)
        
        # Creazione delle classi di traffico predefinite
        classes = [
            QoSClass(
                config=qos_config,
                name="high",
                priority=1,
                min_bandwidth=30,
                max_bandwidth=100,
                description="Traffico ad alta priorità (VoIP, videoconferenza)"
            ),
            QoSClass(
                config=qos_config,
                name="medium",
                priority=3,
                min_bandwidth=20,
                max_bandwidth=80,
                description="Traffico a media priorità (navigazione web, email)"
            ),
            QoSClass(
                config=qos_config,
                name="default",
                priority=4,
                min_bandwidth=10,
                max_bandwidth=60,
                description="Traffico normale non classificato"
            ),
            QoSClass(
                config=qos_config,
                name="low",
                priority=6,
                min_bandwidth=5,
                max_bandwidth=30,
                description="Traffico a bassa priorità (download, peer-to-peer)"
            )
        ]
        db.session.add_all(classes)
        db.session.commit()
    
    # Ottenere tutte le classi e regole
    classes = QoSClass.query.filter_by(config_id=qos_config.id).order_by(QoSClass.priority).all()
    class_counts = {c.id: QoSRule.query.filter_by(class_id=c.id).count() for c in classes}
    
    # Ottenere lo stato attuale
    qos_status = get_qos_status(qos_config.id) if qos_config.enabled else None
    bandwidth_usage = get_bandwidth_usage(qos_config.interface) if qos_config.enabled else None
    
    return render_template('qos/index.html',
                          qos_config=qos_config,
                          classes=classes,
                          class_counts=class_counts,
                          qos_status=qos_status,
                          bandwidth_usage=bandwidth_usage)

@qos.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    """Configurazione QoS"""
    qos_config = QoSConfig.query.first()
    
    if not qos_config:
        flash("La configurazione QoS non è stata trovata. Inizializzare la pagina QoS principale.", "warning")
        return redirect(url_for('qos.index'))
    
    form = QoSConfigForm(obj=qos_config)
    
    # Popolare il campo interface con le interfacce disponibili
    network_interfaces = get_interfaces()
    form.interface.choices = [(i["name"], f"{i['name']} - {i['description']}") for i in network_interfaces]
    
    if form.validate_on_submit():
        try:
            # Salvataggio dei dati del form
            old_enabled = qos_config.enabled
            old_interface = qos_config.interface
            
            # Aggiornamento della configurazione dal form
            qos_config.enabled = form.enabled.data
            qos_config.interface = form.interface.data
            qos_config.download_bandwidth = form.download_bandwidth.data
            qos_config.upload_bandwidth = form.upload_bandwidth.data
            qos_config.default_class = form.default_class.data
            qos_config.hierarchical = form.hierarchical.data
            
            db.session.commit()
            
            # Se il QoS è stato abilitato o è cambiata l'interfaccia, configurare il sistema
            if qos_config.enabled and (not old_enabled or old_interface != qos_config.interface):
                success = setup_qos(
                    qos_config.id,
                    qos_config.interface,
                    qos_config.download_bandwidth,
                    qos_config.upload_bandwidth,
                    qos_config.default_class,
                    qos_config.hierarchical
                )
                
                if success:
                    # Applicare tutte le regole
                    apply_all_qos_rules()
                    flash("Configurazione QoS salvata e applicata con successo!", "success")
                else:
                    flash("Configurazione QoS salvata ma errore durante l'applicazione.", "warning")
            elif not qos_config.enabled and old_enabled:
                # Disabilitare il QoS
                success = disable_qos(qos_config.id)
                if success:
                    flash("QoS disabilitato con successo!", "success")
                else:
                    flash("Errore durante la disabilitazione del QoS.", "warning")
            else:
                flash("Configurazione QoS salvata con successo!", "success")
            
            return redirect(url_for('qos.index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Errore durante il salvataggio della configurazione QoS: {str(e)}")
            flash(f"Errore durante il salvataggio: {str(e)}", "danger")
    
    return render_template('qos/config_form.html', form=form, qos_config=qos_config)

@qos.route('/classes')
@login_required
def classes():
    """Visualizzazione classi di traffico QoS"""
    qos_config = QoSConfig.query.first()
    
    if not qos_config:
        flash("La configurazione QoS non è stata trovata. Inizializzare la pagina QoS principale.", "warning")
        return redirect(url_for('qos.index'))
    
    # Ottenere tutte le classi
    qos_classes = QoSClass.query.filter_by(config_id=qos_config.id).order_by(QoSClass.priority).all()
    
    # Contare le regole per ogni classe
    class_counts = {c.id: QoSRule.query.filter_by(class_id=c.id).count() for c in qos_classes}
    
    return render_template('qos/classes.html', 
                          qos_config=qos_config,
                          classes=qos_classes,
                          class_counts=class_counts)

@qos.route('/classes/new', methods=['GET', 'POST'])
@login_required
def new_class():
    """Creazione di una nuova classe di traffico QoS"""
    qos_config = QoSConfig.query.first()
    
    if not qos_config:
        flash("La configurazione QoS non è stata trovata. Inizializzare la pagina QoS principale.", "warning")
        return redirect(url_for('qos.index'))
    
    form = QoSClassForm()
    
    if form.validate_on_submit():
        try:
            # Creazione della nuova classe
            qos_class = QoSClass(
                config_id=qos_config.id,
                name=form.name.data,
                priority=form.priority.data,
                min_bandwidth=form.min_bandwidth.data,
                max_bandwidth=form.max_bandwidth.data,
                description=form.description.data
            )
            db.session.add(qos_class)
            db.session.commit()
            
            # Se il QoS è abilitato, applicare la classe
            if qos_config.enabled:
                success = add_qos_class(
                    qos_config.id,
                    qos_class.id,
                    qos_class.name,
                    qos_class.priority,
                    qos_class.min_bandwidth,
                    qos_class.max_bandwidth
                )
                
                if success:
                    flash(f"Classe '{qos_class.name}' creata e applicata con successo!", "success")
                else:
                    flash(f"Classe '{qos_class.name}' creata ma errore durante l'applicazione.", "warning")
            else:
                flash(f"Classe '{qos_class.name}' creata con successo! Abilitare il QoS per applicarla.", "success")
            
            return redirect(url_for('qos.classes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Errore durante la creazione della classe QoS: {str(e)}")
            flash(f"Errore durante la creazione: {str(e)}", "danger")
    
    return render_template('qos/class_form.html', form=form, title='Nuova Classe QoS')

@qos.route('/classes/<int:class_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_class(class_id):
    """Modifica di una classe di traffico QoS"""
    qos_class = QoSClass.query.get_or_404(class_id)
    qos_config = QoSConfig.query.get(qos_class.config_id)
    
    form = QoSClassForm(obj=qos_class)
    
    if form.validate_on_submit():
        try:
            # Aggiornamento della classe
            qos_class.name = form.name.data
            qos_class.priority = form.priority.data
            qos_class.min_bandwidth = form.min_bandwidth.data
            qos_class.max_bandwidth = form.max_bandwidth.data
            qos_class.description = form.description.data
            
            db.session.commit()
            
            # Se il QoS è abilitato, aggiornare la classe
            if qos_config.enabled:
                # Rimuovere e ricreare la classe
                remove_qos_class(qos_class.id)
                success = add_qos_class(
                    qos_config.id,
                    qos_class.id,
                    qos_class.name,
                    qos_class.priority,
                    qos_class.min_bandwidth,
                    qos_class.max_bandwidth
                )
                
                if success:
                    flash(f"Classe '{qos_class.name}' aggiornata e applicata con successo!", "success")
                else:
                    flash(f"Classe '{qos_class.name}' aggiornata ma errore durante l'applicazione.", "warning")
            else:
                flash(f"Classe '{qos_class.name}' aggiornata con successo! Abilitare il QoS per applicarla.", "success")
            
            return redirect(url_for('qos.classes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Errore durante l'aggiornamento della classe QoS: {str(e)}")
            flash(f"Errore durante l'aggiornamento: {str(e)}", "danger")
    
    return render_template('qos/class_form.html', form=form, qos_class=qos_class, 
                          title='Modifica Classe QoS')

@qos.route('/classes/<int:class_id>/delete', methods=['POST'])
@login_required
def delete_class(class_id):
    """Eliminazione di una classe di traffico QoS"""
    qos_class = QoSClass.query.get_or_404(class_id)
    qos_config = QoSConfig.query.get(qos_class.config_id)
    
    try:
        # Controllo se è la classe predefinita
        if qos_config.default_class == qos_class.name:
            flash("Non è possibile eliminare la classe predefinita.", "danger")
            return redirect(url_for('qos.classes'))
        
        # Se il QoS è abilitato, rimuovere la classe
        if qos_config.enabled:
            remove_qos_class(qos_class.id)
        
        # Eliminare la classe
        class_name = qos_class.name
        db.session.delete(qos_class)
        db.session.commit()
        
        flash(f"Classe '{class_name}' eliminata con successo!", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Errore durante l'eliminazione della classe QoS: {str(e)}")
        flash(f"Errore durante l'eliminazione: {str(e)}", "danger")
    
    return redirect(url_for('qos.classes'))

@qos.route('/rules')
@login_required
def rules():
    """Visualizzazione regole QoS"""
    qos_config = QoSConfig.query.first()
    
    if not qos_config:
        flash("La configurazione QoS non è stata trovata. Inizializzare la pagina QoS principale.", "warning")
        return redirect(url_for('qos.index'))
    
    # Ottenere tutte le classi e regole
    classes = QoSClass.query.filter_by(config_id=qos_config.id).all()
    class_dict = {c.id: c for c in classes}
    
    rules = QoSRule.query.join(QoSClass).filter(QoSClass.config_id == qos_config.id).order_by(
        QoSRule.priority, QoSClass.priority).all()
    
    return render_template('qos/rules.html', 
                          qos_config=qos_config,
                          rules=rules,
                          classes=class_dict)

@qos.route('/rules/new', methods=['GET', 'POST'])
@login_required
def new_rule():
    """Creazione di una nuova regola QoS"""
    qos_config = QoSConfig.query.first()
    
    if not qos_config:
        flash("La configurazione QoS non è stata trovata. Inizializzare la pagina QoS principale.", "warning")
        return redirect(url_for('qos.index'))
    
    form = QoSRuleForm()
    
    # Popolare il campo class_id con le classi disponibili
    classes = QoSClass.query.filter_by(config_id=qos_config.id).order_by(QoSClass.priority).all()
    form.class_id.choices = [(c.id, f"{c.name} (Priorità: {c.priority})") for c in classes]
    
    if form.validate_on_submit():
        try:
            # Creazione della nuova regola
            rule = QoSRule(
                class_id=form.class_id.data,
                name=form.name.data,
                description=form.description.data,
                source=form.source.data,
                destination=form.destination.data,
                protocol=form.protocol.data,
                src_port=form.src_port.data,
                dst_port=form.dst_port.data,
                dscp=form.dscp.data,
                direction=form.direction.data,
                priority=form.priority.data,
                enabled=form.enabled.data
            )
            db.session.add(rule)
            db.session.commit()
            
            # Se il QoS è abilitato e la regola è abilitata, applicare la regola
            if qos_config.enabled and rule.enabled:
                success = add_qos_rule(
                    rule.id,
                    rule.class_id,
                    rule.source,
                    rule.destination,
                    rule.protocol,
                    rule.src_port,
                    rule.dst_port,
                    rule.dscp,
                    rule.direction
                )
                
                if success:
                    flash(f"Regola '{rule.name}' creata e applicata con successo!", "success")
                else:
                    flash(f"Regola '{rule.name}' creata ma errore durante l'applicazione.", "warning")
            else:
                flash(f"Regola '{rule.name}' creata con successo! Abilitare il QoS per applicarla.", "success")
            
            return redirect(url_for('qos.rules'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Errore durante la creazione della regola QoS: {str(e)}")
            flash(f"Errore durante la creazione: {str(e)}", "danger")
    
    return render_template('qos/rule_form.html', form=form, title='Nuova Regola QoS')

@qos.route('/rules/<int:rule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rule(rule_id):
    """Modifica di una regola QoS"""
    rule = QoSRule.query.get_or_404(rule_id)
    qos_class = QoSClass.query.get(rule.class_id)
    qos_config = QoSConfig.query.get(qos_class.config_id)
    
    form = QoSRuleForm(obj=rule)
    
    # Popolare il campo class_id con le classi disponibili
    classes = QoSClass.query.filter_by(config_id=qos_config.id).order_by(QoSClass.priority).all()
    form.class_id.choices = [(c.id, f"{c.name} (Priorità: {c.priority})") for c in classes]
    
    if form.validate_on_submit():
        try:
            # Aggiornamento della regola
            old_enabled = rule.enabled
            
            rule.class_id = form.class_id.data
            rule.name = form.name.data
            rule.description = form.description.data
            rule.source = form.source.data
            rule.destination = form.destination.data
            rule.protocol = form.protocol.data
            rule.src_port = form.src_port.data
            rule.dst_port = form.dst_port.data
            rule.dscp = form.dscp.data
            rule.direction = form.direction.data
            rule.priority = form.priority.data
            rule.enabled = form.enabled.data
            
            db.session.commit()
            
            # Se il QoS è abilitato, aggiornare la regola
            if qos_config.enabled:
                # Se la regola era abilitata, rimuoverla
                if old_enabled:
                    remove_qos_rule(rule.id)
                
                # Se la regola è abilitata, applicarla
                if rule.enabled:
                    success = add_qos_rule(
                        rule.id,
                        rule.class_id,
                        rule.source,
                        rule.destination,
                        rule.protocol,
                        rule.src_port,
                        rule.dst_port,
                        rule.dscp,
                        rule.direction
                    )
                    
                    if success:
                        flash(f"Regola '{rule.name}' aggiornata e applicata con successo!", "success")
                    else:
                        flash(f"Regola '{rule.name}' aggiornata ma errore durante l'applicazione.", "warning")
                else:
                    flash(f"Regola '{rule.name}' aggiornata e disabilitata con successo!", "success")
            else:
                flash(f"Regola '{rule.name}' aggiornata con successo! Abilitare il QoS per applicarla.", "success")
            
            return redirect(url_for('qos.rules'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Errore durante l'aggiornamento della regola QoS: {str(e)}")
            flash(f"Errore durante l'aggiornamento: {str(e)}", "danger")
    
    return render_template('qos/rule_form.html', form=form, rule=rule, 
                          title='Modifica Regola QoS')

@qos.route('/rules/<int:rule_id>/delete', methods=['POST'])
@login_required
def delete_rule(rule_id):
    """Eliminazione di una regola QoS"""
    rule = QoSRule.query.get_or_404(rule_id)
    qos_class = QoSClass.query.get(rule.class_id)
    qos_config = QoSConfig.query.get(qos_class.config_id)
    
    try:
        # Se il QoS è abilitato e la regola è abilitata, rimuovere la regola
        if qos_config.enabled and rule.enabled:
            remove_qos_rule(rule.id)
        
        # Eliminare la regola
        rule_name = rule.name
        db.session.delete(rule)
        db.session.commit()
        
        flash(f"Regola '{rule_name}' eliminata con successo!", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Errore durante l'eliminazione della regola QoS: {str(e)}")
        flash(f"Errore durante l'eliminazione: {str(e)}", "danger")
    
    return redirect(url_for('qos.rules'))

@qos.route('/rules/<int:rule_id>/toggle', methods=['POST'])
@login_required
def toggle_rule(rule_id):
    """Attivazione/disattivazione di una regola QoS"""
    rule = QoSRule.query.get_or_404(rule_id)
    qos_class = QoSClass.query.get(rule.class_id)
    qos_config = QoSConfig.query.get(qos_class.config_id)
    
    try:
        # Cambiare lo stato della regola
        rule.enabled = not rule.enabled
        db.session.commit()
        
        # Se il QoS è abilitato, applicare o rimuovere la regola
        if qos_config.enabled:
            if rule.enabled:
                success = add_qos_rule(
                    rule.id,
                    rule.class_id,
                    rule.source,
                    rule.destination,
                    rule.protocol,
                    rule.src_port,
                    rule.dst_port,
                    rule.dscp,
                    rule.direction
                )
                
                if success:
                    flash(f"Regola '{rule.name}' attivata con successo!", "success")
                else:
                    flash(f"Errore durante l'attivazione della regola '{rule.name}'.", "warning")
            else:
                success = remove_qos_rule(rule.id)
                
                if success:
                    flash(f"Regola '{rule.name}' disattivata con successo!", "success")
                else:
                    flash(f"Errore durante la disattivazione della regola '{rule.name}'.", "warning")
        else:
            state = "attivata" if rule.enabled else "disattivata"
            flash(f"Regola '{rule.name}' {state} con successo! Abilitare il QoS per applicare le modifiche.", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Errore durante la modifica dello stato della regola QoS: {str(e)}")
        flash(f"Errore durante la modifica dello stato: {str(e)}", "danger")
    
    return redirect(url_for('qos.rules'))

@qos.route('/apply', methods=['POST'])
@login_required
def apply_all_qos():
    """Applica tutte le configurazioni QoS"""
    qos_config = QoSConfig.query.first()
    
    if not qos_config:
        flash("La configurazione QoS non è stata trovata. Inizializzare la pagina QoS principale.", "warning")
        return redirect(url_for('qos.index'))
    
    try:
        if not qos_config.enabled:
            flash("Il QoS è disabilitato. Abilitare il QoS prima di applicare le configurazioni.", "warning")
            return redirect(url_for('qos.index'))
        
        success = apply_all_qos_rules()
        
        if success:
            flash("Tutte le configurazioni QoS sono state applicate con successo!", "success")
        else:
            flash("Errore durante l'applicazione delle configurazioni QoS.", "danger")
    except Exception as e:
        logger.error(f"Errore durante l'applicazione delle configurazioni QoS: {str(e)}")
        flash(f"Errore durante l'applicazione: {str(e)}", "danger")
    
    return redirect(url_for('qos.index'))

@qos.route('/api/stats')
@login_required
def api_stats():
    """API per ottenere le statistiche QoS in tempo reale"""
    qos_config = QoSConfig.query.first()
    
    if not qos_config or not qos_config.enabled:
        return jsonify({"error": "QoS not enabled"}), 400
    
    try:
        bandwidth_usage = get_bandwidth_usage(qos_config.interface)
        return jsonify(bandwidth_usage)
    except Exception as e:
        logger.error(f"Errore durante l'ottenimento delle statistiche QoS: {str(e)}")
        return jsonify({"error": str(e)}), 500