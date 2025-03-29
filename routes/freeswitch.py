import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from utils.freeswitch import (
    get_freeswitch_status, restart_freeswitch, 
    get_extensions, add_extension, update_extension, delete_extension,
    get_trunks, add_trunk, update_trunk, delete_trunk
)
from forms.freeswitch import ExtensionForm, TrunkForm

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
