from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required
from models import FreeswitchConfig, FreeswitchExtension
from forms import FreeswitchConfigForm, FreeswitchExtensionForm
from app import db
from utils.freeswitch import (
    restart_freeswitch, 
    get_freeswitch_status, 
    apply_freeswitch_config,
    generate_extension_config,
    get_registrations
)
import logging

logger = logging.getLogger(__name__)
freeswitch_bp = Blueprint('freeswitch', __name__)

@freeswitch_bp.route('/freeswitch')
@login_required
def index():
    # Get FreeSWITCH configuration
    config = FreeswitchConfig.query.first()
    if not config:
        config = FreeswitchConfig()
        db.session.add(config)
        db.session.commit()
    
    # Get all extensions
    extensions = FreeswitchExtension.query.all()
    
    # Get current status
    status = get_freeswitch_status()
    
    config_form = FreeswitchConfigForm(obj=config)
    extension_form = FreeswitchExtensionForm()
    
    return render_template('freeswitch.html', 
                          config=config, 
                          extensions=extensions, 
                          status=status,
                          config_form=config_form,
                          extension_form=extension_form)

@freeswitch_bp.route('/freeswitch/config', methods=['POST'])
@login_required
def update_config():
    config = FreeswitchConfig.query.first()
    if not config:
        config = FreeswitchConfig()
        db.session.add(config)
    
    form = FreeswitchConfigForm(obj=config)
    
    if form.validate_on_submit():
        form.populate_obj(config)
        db.session.commit()
        
        try:
            apply_freeswitch_config(config)
            restart_freeswitch()
            flash('FreeSWITCH configuration updated successfully', 'success')
        except Exception as e:
            logger.error(f"Failed to apply FreeSWITCH config: {str(e)}")
            flash(f'Error applying FreeSWITCH configuration: {str(e)}', 'danger')
        
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('freeswitch.index'))

@freeswitch_bp.route('/freeswitch/extension/add', methods=['POST'])
@login_required
def add_extension():
    form = FreeswitchExtensionForm()
    
    if form.validate_on_submit():
        # Check if extension already exists
        if FreeswitchExtension.query.filter_by(extension=form.extension.data).first():
            flash(f'Extension {form.extension.data} already exists', 'danger')
            return redirect(url_for('freeswitch.index'))
        
        extension = FreeswitchExtension()
        form.populate_obj(extension)
        db.session.add(extension)
        db.session.commit()
        
        try:
            generate_extension_config(extension)
            restart_freeswitch()
            flash(f'Extension {extension.extension} created successfully', 'success')
        except Exception as e:
            logger.error(f"Failed to generate extension config: {str(e)}")
            flash(f'Error creating extension: {str(e)}', 'danger')
    
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('freeswitch.index'))

@freeswitch_bp.route('/freeswitch/extension/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_extension(id):
    extension = FreeswitchExtension.query.get_or_404(id)
    form = FreeswitchExtensionForm(obj=extension)
    
    if request.method == 'POST' and form.validate_on_submit():
        form.populate_obj(extension)
        db.session.commit()
        
        try:
            generate_extension_config(extension)
            restart_freeswitch()
            flash(f'Extension {extension.extension} updated successfully', 'success')
        except Exception as e:
            logger.error(f"Failed to update extension config: {str(e)}")
            flash(f'Error updating extension: {str(e)}', 'danger')
        
        return redirect(url_for('freeswitch.index'))
    
    return render_template('freeswitch.html', extension_form=form, edit_extension=extension)

@freeswitch_bp.route('/freeswitch/extension/<int:id>/delete', methods=['POST'])
@login_required
def delete_extension(id):
    extension = FreeswitchExtension.query.get_or_404(id)
    ext_number = extension.extension
    
    try:
        db.session.delete(extension)
        db.session.commit()
        restart_freeswitch()
        flash(f'Extension {ext_number} deleted successfully', 'success')
    except Exception as e:
        logger.error(f"Failed to delete extension: {str(e)}")
        flash(f'Error deleting extension: {str(e)}', 'danger')
    
    return redirect(url_for('freeswitch.index'))

@freeswitch_bp.route('/freeswitch/restart', methods=['POST'])
@login_required
def restart():
    try:
        restart_freeswitch()
        flash('FreeSWITCH restarted successfully', 'success')
    except Exception as e:
        logger.error(f"Failed to restart FreeSWITCH: {str(e)}")
        flash(f'Error restarting FreeSWITCH: {str(e)}', 'danger')
    
    return redirect(url_for('freeswitch.index'))

@freeswitch_bp.route('/freeswitch/registrations', methods=['GET'])
@login_required
def registrations():
    try:
        registrations = get_registrations()
        return jsonify({'success': True, 'registrations': registrations})
    except Exception as e:
        logger.error(f"Failed to get registrations: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
