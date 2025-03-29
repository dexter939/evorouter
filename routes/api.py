import logging
import secrets
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User, ApiToken, NetworkConfig, FreeswitchConfig, SipExtension, SipTrunk
from utils.network import get_interfaces_status, configure_interface, restart_network
from utils.system import get_system_stats, reboot_system
from utils.freeswitch import get_extensions, add_extension, update_extension, delete_extension

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/token', methods=['POST'])
def get_token():
    """Generate JWT token for API access"""
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Bad username or password"}), 401
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify(access_token=access_token), 200

@api_bp.route('/system/status', methods=['GET'])
@jwt_required()
def api_system_status():
    """API endpoint to get system status"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        system_stats = get_system_stats()
        
        return jsonify({
            "status": "success",
            "data": system_stats
        })
    except Exception as e:
        logger.error(f"API error in system status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/system/reboot', methods=['POST'])
@jwt_required()
def api_system_reboot():
    """API endpoint to reboot the system"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({"error": "Unauthorized"}), 403
        
        reboot_system()
        
        return jsonify({
            "status": "success",
            "message": "System reboot initiated"
        })
    except Exception as e:
        logger.error(f"API error in system reboot: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/network/interfaces', methods=['GET'])
@jwt_required()
def api_network_interfaces():
    """API endpoint to get network interfaces status"""
    try:
        interfaces = get_interfaces_status()
        
        return jsonify({
            "status": "success",
            "data": interfaces
        })
    except Exception as e:
        logger.error(f"API error in network interfaces: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/network/interfaces/<interface_name>', methods=['PUT'])
@jwt_required()
def api_configure_interface(interface_name):
    """API endpoint to configure a network interface"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({"error": "Unauthorized"}), 403
        
        if not request.is_json:
            return jsonify({"error": "Missing JSON in request"}), 400
        
        data = request.json
        
        result = configure_interface(
            interface_name=interface_name,
            ip_mode=data.get('ip_mode', 'dhcp'),
            ip_address=data.get('ip_address'),
            subnet_mask=data.get('subnet_mask'),
            gateway=data.get('gateway'),
            dns_servers=data.get('dns_servers')
        )
        
        if result:
            # Apply network changes
            restart_network()
            return jsonify({
                "status": "success",
                "message": f"Interface {interface_name} configured successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to configure interface {interface_name}"
            }), 500
            
    except Exception as e:
        logger.error(f"API error in configure interface: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/freeswitch/extensions', methods=['GET'])
@jwt_required()
def api_get_extensions():
    """API endpoint to get FreeSWITCH extensions"""
    try:
        extensions = get_extensions()
        
        return jsonify({
            "status": "success",
            "data": extensions
        })
    except Exception as e:
        logger.error(f"API error in get extensions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/freeswitch/extensions', methods=['POST'])
@jwt_required()
def api_add_extension():
    """API endpoint to add a FreeSWITCH extension"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({"error": "Unauthorized"}), 403
        
        if not request.is_json:
            return jsonify({"error": "Missing JSON in request"}), 400
        
        data = request.json
        
        result = add_extension(
            extension_number=data.get('extension_number'),
            name=data.get('name'),
            password=data.get('password'),
            voicemail_enabled=data.get('voicemail_enabled', False),
            voicemail_pin=data.get('voicemail_pin')
        )
        
        if result:
            return jsonify({
                "status": "success",
                "message": "Extension added successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to add extension"
            }), 500
            
    except Exception as e:
        logger.error(f"API error in add extension: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/freeswitch/extensions/<extension_id>', methods=['PUT'])
@jwt_required()
def api_update_extension(extension_id):
    """API endpoint to update a FreeSWITCH extension"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({"error": "Unauthorized"}), 403
        
        if not request.is_json:
            return jsonify({"error": "Missing JSON in request"}), 400
        
        data = request.json
        
        result = update_extension(
            extension_id=extension_id,
            extension_number=data.get('extension_number'),
            name=data.get('name'),
            password=data.get('password'),
            voicemail_enabled=data.get('voicemail_enabled'),
            voicemail_pin=data.get('voicemail_pin')
        )
        
        if result:
            return jsonify({
                "status": "success",
                "message": "Extension updated successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to update extension"
            }), 500
            
    except Exception as e:
        logger.error(f"API error in update extension: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/freeswitch/extensions/<extension_id>', methods=['DELETE'])
@jwt_required()
def api_delete_extension(extension_id):
    """API endpoint to delete a FreeSWITCH extension"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({"error": "Unauthorized"}), 403
        
        result = delete_extension(extension_id)
        
        if result:
            return jsonify({
                "status": "success",
                "message": "Extension deleted successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to delete extension"
            }), 500
            
    except Exception as e:
        logger.error(f"API error in delete extension: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/tokens', methods=['GET'])
@login_required
def list_tokens():
    """List all API tokens for the current user"""
    try:
        if not current_user.is_admin:
            tokens = ApiToken.query.filter_by(created_by_id=current_user.id).all()
        else:
            tokens = ApiToken.query.all()
            
        token_list = []
        for token in tokens:
            token_list.append({
                'id': token.id,
                'name': token.name,
                'created_by': token.created_by.username,
                'created_at': token.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'expires_at': token.expires_at.strftime('%Y-%m-%d %H:%M:%S') if token.expires_at else 'Never',
                'last_used_at': token.last_used_at.strftime('%Y-%m-%d %H:%M:%S') if token.last_used_at else 'Never',
                'is_active': token.is_active
            })
        
        return jsonify({
            "status": "success",
            "data": token_list
        })
    except Exception as e:
        logger.error(f"Error listing API tokens: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/tokens', methods=['POST'])
@login_required
def create_token():
    """Create a new API token"""
    try:
        if not request.is_json:
            return jsonify({"error": "Missing JSON in request"}), 400
        
        data = request.json
        token_name = data.get('name')
        
        if not token_name:
            return jsonify({"error": "Token name is required"}), 400
        
        # Generate token
        token_value = secrets.token_urlsafe(32)
        token_hash = generate_password_hash(token_value)
        
        # Create token record
        new_token = ApiToken(
            name=token_name,
            token_hash=token_hash,
            created_by_id=current_user.id,
            is_active=True
        )
        
        db.session.add(new_token)
        db.session.commit()
        
        logger.info(f"API token '{token_name}' created by {current_user.username}")
        
        return jsonify({
            "status": "success",
            "message": "Token created successfully",
            "data": {
                "id": new_token.id,
                "name": new_token.name,
                "token": token_value  # Only returned once at creation
            }
        })
    except Exception as e:
        logger.error(f"Error creating API token: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/tokens/<token_id>', methods=['DELETE'])
@login_required
def revoke_token(token_id):
    """Revoke an API token"""
    try:
        token = ApiToken.query.get(token_id)
        
        if not token:
            return jsonify({"error": "Token not found"}), 404
        
        # Check if the user is the token creator or an admin
        if token.created_by_id != current_user.id and not current_user.is_admin:
            return jsonify({"error": "Unauthorized"}), 403
        
        token.is_active = False
        db.session.commit()
        
        logger.info(f"API token '{token.name}' revoked by {current_user.username}")
        
        return jsonify({
            "status": "success",
            "message": "Token revoked successfully"
        })
    except Exception as e:
        logger.error(f"Error revoking API token: {str(e)}")
        return jsonify({"error": str(e)}), 500
