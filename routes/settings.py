from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User, ApiClient
from forms import ChangePasswordForm, ApiClientForm
from app import db
from utils.security import generate_api_key
from werkzeug.security import check_password_hash, generate_password_hash
import logging

logger = logging.getLogger(__name__)
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def index():
    password_form = ChangePasswordForm()
    api_form = ApiClientForm()
    api_clients = ApiClient.query.all()
    
    return render_template('settings.html', 
                          password_form=password_form,
                          api_form=api_form,
                          api_clients=api_clients)

@settings_bp.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.get(current_user.id)
        
        if not check_password_hash(user.password_hash, form.current_password.data):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('settings.index'))
        
        user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        
        flash('Your password has been updated', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/api/add', methods=['POST'])
@login_required
def add_api_client():
    form = ApiClientForm()
    if form.validate_on_submit():
        client = ApiClient(
            name=form.name.data,
            api_key=generate_api_key(),
            enabled=form.enabled.data,
            ip_whitelist=form.ip_whitelist.data
        )
        db.session.add(client)
        db.session.commit()
        flash(f'API client "{form.name.data}" created successfully', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/api/<int:id>/delete', methods=['POST'])
@login_required
def delete_api_client(id):
    client = ApiClient.query.get_or_404(id)
    client_name = client.name
    db.session.delete(client)
    db.session.commit()
    flash(f'API client "{client_name}" deleted successfully', 'success')
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/api/<int:id>/regenerate', methods=['POST'])
@login_required
def regenerate_api_key(id):
    client = ApiClient.query.get_or_404(id)
    client.api_key = generate_api_key()
    db.session.commit()
    flash(f'API key for "{client.name}" regenerated successfully', 'success')
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/backup', methods=['GET'])
@login_required
def backup():
    # Logic to create and download a backup of the router configuration
    try:
        # This would be implemented to create a backup file
        return render_template('settings.html', backup_message='Backup functionality will be implemented here')
    except Exception as e:
        logger.error(f"Backup error: {str(e)}")
        flash(f'Error creating backup: {str(e)}', 'danger')
        return redirect(url_for('settings.index'))

@settings_bp.route('/settings/restore', methods=['POST'])
@login_required
def restore():
    # Logic to restore a router configuration from a backup file
    try:
        # This would be implemented to restore from a backup file
        flash('Restore functionality will be implemented here', 'info')
    except Exception as e:
        logger.error(f"Restore error: {str(e)}")
        flash(f'Error restoring from backup: {str(e)}', 'danger')
    
    return redirect(url_for('settings.index'))
