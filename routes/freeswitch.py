import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from utils.freeswitch import (
    get_freeswitch_status, restart_freeswitch, 
    get_extensions, add_extension, update_extension, delete_extension,
    get_trunks, add_trunk, update_trunk, delete_trunk
)
from forms.freeswitch import ExtensionForm, TrunkForm, FreeswitchWizardForm
from models import PbxConfig, SipExtension, SipTrunk, db

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint
freeswitch_bp = Blueprint('freeswitch', __name__)

@freeswitch_bp.route('/')
@login_required
def index():
    """FreeSWITCH dashboard overview page"""
    try:
        fs_status = get_freeswitch_status()
        return render_template('freeswitch/index.html', 
                               active_page="freeswitch",
                               fs_status=fs_status)
    except Exception as e:
        logger.error(f"Error loading FreeSWITCH dashboard: {str(e)}")
        flash("Si è verificato un errore nel caricamento delle informazioni di FreeSWITCH.", "danger")
        return render_template('freeswitch/index.html', 
                               active_page="freeswitch",
                               error=True)

@freeswitch_bp.route('/extensions')
@login_required
def list_extensions():
    """List all SIP extensions"""
    try:
        extensions = get_extensions()
        return render_template('freeswitch/extensions.html', 
                               active_page="freeswitch",
                               extensions=extensions)
    except Exception as e:
        logger.error(f"Error loading extensions: {str(e)}")
        flash("Si è verificato un errore nel caricamento delle estensioni.", "danger")
        return render_template('freeswitch/extensions.html', 
                               active_page="freeswitch",
                               error=True)

@freeswitch_bp.route('/extensions/add', methods=['GET', 'POST'])
@login_required
def add_extension_route():
    """Add a new SIP extension"""
    form = ExtensionForm()
    
    if form.validate_on_submit():
        try:
            result = add_extension(
                extension_number=form.extension_number.data,
                name=form.name.data,
                password=form.password.data,
                voicemail_enabled=form.voicemail_enabled.data,
                voicemail_pin=form.voicemail_pin.data if form.voicemail_enabled.data else None
            )
            
            if result:
                flash(f"Estensione {form.extension_number.data} aggiunta con successo.", "success")
                return redirect(url_for('freeswitch.list_extensions'))
            else:
                flash("Errore nell'aggiunta dell'estensione.", "danger")
        except Exception as e:
            logger.error(f"Error adding extension: {str(e)}")
            flash(f"Errore nell'aggiunta dell'estensione: {str(e)}", "danger")
    
    return render_template('freeswitch/extensions.html',
                          active_page="freeswitch",
                          form=form,
                          action="add")

@freeswitch_bp.route('/extensions/edit/<extension_id>', methods=['GET', 'POST'])
@login_required
def edit_extension_route(extension_id):
    """Edit an existing SIP extension"""
    form = ExtensionForm()
    
    # Get extension information
    try:
        extensions = get_extensions()
        extension = next((e for e in extensions if str(e.get('id')) == str(extension_id)), None)
        
        if not extension:
            flash("Estensione non trovata.", "danger")
            return redirect(url_for('freeswitch.list_extensions'))
        
        if form.validate_on_submit():
            result = update_extension(
                extension_id=extension_id,
                extension_number=form.extension_number.data,
                name=form.name.data,
                password=form.password.data if form.password.data else extension.get('password'),
                voicemail_enabled=form.voicemail_enabled.data,
                voicemail_pin=form.voicemail_pin.data if form.voicemail_enabled.data else None
            )
            
            if result:
                flash(f"Estensione {form.extension_number.data} aggiornata con successo.", "success")
                return redirect(url_for('freeswitch.list_extensions'))
            else:
                flash("Errore nell'aggiornamento dell'estensione.", "danger")
        
        # Pre-fill the form with current values
        if not form.is_submitted():
            form.extension_number.data = extension.get('extension_number')
            form.name.data = extension.get('name')
            form.voicemail_enabled.data = extension.get('voicemail_enabled', False)
            form.voicemail_pin.data = extension.get('voicemail_pin', '')
        
        return render_template('freeswitch/extensions.html',
                              active_page="freeswitch",
                              form=form,
                              extension=extension,
                              action="edit")
                              
    except Exception as e:
        logger.error(f"Error editing extension {extension_id}: {str(e)}")
        flash(f"Errore nella modifica dell'estensione: {str(e)}", "danger")
        return redirect(url_for('freeswitch.list_extensions'))

@freeswitch_bp.route('/extensions/delete/<extension_id>', methods=['POST'])
@login_required
def delete_extension_route(extension_id):
    """Delete a SIP extension"""
    try:
        result = delete_extension(extension_id)
        
        if result:
            flash("Estensione eliminata con successo.", "success")
        else:
            flash("Errore nell'eliminazione dell'estensione.", "danger")
            
        return redirect(url_for('freeswitch.list_extensions'))
    except Exception as e:
        logger.error(f"Error deleting extension {extension_id}: {str(e)}")
        flash(f"Errore nell'eliminazione dell'estensione: {str(e)}", "danger")
        return redirect(url_for('freeswitch.list_extensions'))

@freeswitch_bp.route('/trunks')
@login_required
def list_trunks():
    """List all SIP trunks"""
    try:
        trunks = get_trunks()
        return render_template('freeswitch/trunks.html', 
                               active_page="freeswitch",
                               trunks=trunks)
    except Exception as e:
        logger.error(f"Error loading trunks: {str(e)}")
        flash("Si è verificato un errore nel caricamento dei trunk SIP.", "danger")
        return render_template('freeswitch/trunks.html', 
                               active_page="freeswitch",
                               error=True)

@freeswitch_bp.route('/trunks/add', methods=['GET', 'POST'])
@login_required
def add_trunk_route():
    """Add a new SIP trunk"""
    form = TrunkForm()
    
    if form.validate_on_submit():
        try:
            result = add_trunk(
                name=form.name.data,
                host=form.host.data,
                port=form.port.data,
                username=form.username.data,
                password=form.password.data,
                enabled=form.enabled.data
            )
            
            if result:
                flash(f"Trunk SIP {form.name.data} aggiunto con successo.", "success")
                return redirect(url_for('freeswitch.list_trunks'))
            else:
                flash("Errore nell'aggiunta del trunk SIP.", "danger")
        except Exception as e:
            logger.error(f"Error adding trunk: {str(e)}")
            flash(f"Errore nell'aggiunta del trunk SIP: {str(e)}", "danger")
    
    return render_template('freeswitch/trunks.html',
                          active_page="freeswitch",
                          form=form,
                          action="add")

@freeswitch_bp.route('/trunks/edit/<trunk_id>', methods=['GET', 'POST'])
@login_required
def edit_trunk_route(trunk_id):
    """Edit an existing SIP trunk"""
    form = TrunkForm()
    
    # Get trunk information
    try:
        trunks = get_trunks()
        trunk = next((t for t in trunks if str(t.get('id')) == str(trunk_id)), None)
        
        if not trunk:
            flash("Trunk SIP non trovato.", "danger")
            return redirect(url_for('freeswitch.list_trunks'))
        
        if form.validate_on_submit():
            result = update_trunk(
                trunk_id=trunk_id,
                name=form.name.data,
                host=form.host.data,
                port=form.port.data,
                username=form.username.data,
                password=form.password.data if form.password.data else trunk.get('password'),
                enabled=form.enabled.data
            )
            
            if result:
                flash(f"Trunk SIP {form.name.data} aggiornato con successo.", "success")
                return redirect(url_for('freeswitch.list_trunks'))
            else:
                flash("Errore nell'aggiornamento del trunk SIP.", "danger")
        
        # Pre-fill the form with current values
        if not form.is_submitted():
            form.name.data = trunk.get('name')
            form.host.data = trunk.get('host')
            form.port.data = trunk.get('port')
            form.username.data = trunk.get('username')
            form.enabled.data = trunk.get('enabled', True)
        
        return render_template('freeswitch/trunks.html',
                              active_page="freeswitch",
                              form=form,
                              trunk=trunk,
                              action="edit")
                              
    except Exception as e:
        logger.error(f"Error editing trunk {trunk_id}: {str(e)}")
        flash(f"Errore nella modifica del trunk SIP: {str(e)}", "danger")
        return redirect(url_for('freeswitch.list_trunks'))

@freeswitch_bp.route('/trunks/delete/<trunk_id>', methods=['POST'])
@login_required
def delete_trunk_route(trunk_id):
    """Delete a SIP trunk"""
    try:
        result = delete_trunk(trunk_id)
        
        if result:
            flash("Trunk SIP eliminato con successo.", "success")
        else:
            flash("Errore nell'eliminazione del trunk SIP.", "danger")
            
        return redirect(url_for('freeswitch.list_trunks'))
    except Exception as e:
        logger.error(f"Error deleting trunk {trunk_id}: {str(e)}")
        flash(f"Errore nell'eliminazione del trunk SIP: {str(e)}", "danger")
        return redirect(url_for('freeswitch.list_trunks'))

@freeswitch_bp.route('/restart', methods=['POST'])
@login_required
def restart_freeswitch_service():
    """Restart FreeSWITCH service"""
    try:
        result = restart_freeswitch()
        if result:
            return jsonify({'success': True, 'message': 'FreeSWITCH riavviato con successo.'})
        else:
            return jsonify({'success': False, 'message': 'Errore nel riavvio di FreeSWITCH.'}), 500
    except Exception as e:
        logger.error(f"Error restarting FreeSWITCH: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore nel riavvio di FreeSWITCH: {str(e)}'}), 500

@freeswitch_bp.route('/save_wizard', methods=['POST'])
@login_required
def save_wizard():
    """Endpoint for the wizard form submission"""
    # This is a simple redirect to the wizard route
    # The actual form processing happens in the wizard route
    return redirect(url_for('freeswitch.wizard'))

@freeswitch_bp.route('/wizard', methods=['GET', 'POST'])
@login_required
def wizard():
    """FreeSWITCH configuration wizard"""
    form = FreeswitchWizardForm()
    
    # Pre-fill with existing configuration if available
    if not form.is_submitted():
        fs_config = PbxConfig.query.first()
        if fs_config:
            form.enabled.data = fs_config.enabled
            form.sip_port.data = fs_config.sip_port
            form.rtp_port_start.data = fs_config.rtp_port_start
            form.rtp_port_end.data = fs_config.rtp_port_end
    
    if form.validate_on_submit():
        try:
            # Process submitted form
            # 1. Save PbxConfig
            pbx_config = PbxConfig.query.first()
            if not pbx_config:
                pbx_config = PbxConfig()
                db.session.add(pbx_config)
            
            pbx_config.enabled = form.enabled.data
            pbx_config.sip_port = form.sip_port.data
            pbx_config.rtp_port_start = form.rtp_port_start.data
            pbx_config.rtp_port_end = form.rtp_port_end.data
            
            # 2. Process extensions
            # Get all extension data from the dynamic form fields
            extension_data = []
            for key, value in request.form.items():
                if key.startswith('ext_number_'):
                    idx = key.split('_')[-1]
                    extension_data.append({
                        'number': request.form.get(f'ext_number_{idx}', ''),
                        'name': request.form.get(f'ext_name_{idx}', ''),
                        'password': request.form.get(f'ext_password_{idx}', '')
                    })
            
            # Create or update extensions
            for ext_data in extension_data:
                # Check if extension already exists
                existing = SipExtension.query.filter_by(extension_number=ext_data['number']).first()
                
                if existing:
                    # Update existing extension
                    existing.name = ext_data['name']
                    if ext_data['password']:  # Don't update password if not provided
                        existing.password = ext_data['password']
                    
                    # Set advanced features based on form data
                    existing.voicemail_enabled = form.voicemail_enabled.data
                    existing.voicemail_email = form.voicemail_email.data
                    existing.voicemail_attach_file = form.voicemail_attach_file.data
                    existing.voicemail_delete_after_email = form.voicemail_delete_after_email.data
                    existing.record_inbound = form.record_inbound.data if form.call_recording_enabled.data else False
                    existing.record_outbound = form.record_outbound.data if form.call_recording_enabled.data else False
                else:
                    # Create new extension
                    new_extension = SipExtension(
                        extension_number=ext_data['number'],
                        name=ext_data['name'],
                        password=ext_data['password'],
                        voicemail_enabled=form.voicemail_enabled.data,
                        voicemail_email=form.voicemail_email.data,
                        voicemail_attach_file=form.voicemail_attach_file.data,
                        voicemail_delete_after_email=form.voicemail_delete_after_email.data,
                        record_inbound=form.record_inbound.data if form.call_recording_enabled.data else False,
                        record_outbound=form.record_outbound.data if form.call_recording_enabled.data else False
                    )
                    db.session.add(new_extension)
            
            # 3. Process trunk if configured
            if form.configure_trunk.data:
                # Create a new SIP trunk
                new_trunk = SipTrunk(
                    name=form.trunk_name.data,
                    host=form.trunk_host.data,
                    port=form.trunk_port.data,
                    username=form.trunk_username.data if form.trunk_username.data else None,
                    password=form.trunk_password.data if form.trunk_password.data else None,
                    enabled=True
                )
                db.session.add(new_trunk)
            
            # Save all changes
            db.session.commit()
            
            # Restart PBX service with new configuration
            restart_freeswitch()
            
            flash("Configurazione del centralino completata con successo!", "success")
            return redirect(url_for('freeswitch.index'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving PBX wizard configuration: {str(e)}")
            flash(f"Errore durante il salvataggio della configurazione: {str(e)}", "danger")
    
    # If GET request or form validation failed, render the wizard template
    return render_template('freeswitch/wizard.html', 
                           active_page="freeswitch",
                           form=form)
