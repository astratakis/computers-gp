from flask import request, jsonify, current_app, url_for
from apiflask import APIBlueprint
import requests
from auth import auth, security_doc, admin_required, token_active
import logging 
import schema
import xml.etree.ElementTree as ET
import kutils

"""
    This .py file contains the endpoints attached to the blueprint
    responsible for all operations related to the lifecycle of
    users in the ecosystem.

    Follows the REST logic.
"""

logging.basicConfig(level=logging.DEBUG)

# The users operations blueprint for all operations related to the lifecycle of a user
users_bp = APIBlueprint('users_blueprint', __name__, tag={'name':'User Management','description':'Operations related to management of users (CRUD, Authentication)'})

@users_bp.route('/', methods=['GET'])
@users_bp.doc(tags=['User Management'], security=security_doc)
@users_bp.input(schema.PaginationParameters, location='query')
@users_bp.output(schema.ResponseAmbiguous, status_code=200, example={"result":{"count":2,"users":[{"active":True,"fullname":"GP Default","id":"b16d521b-d81c-435d-bc81-11f2491d4280","joined_date":"13-02-2025","roles":[],"username":"gp.default"},{"active":True,"fullname":"Help Desk","id":"337da7e8-7ec4-4bb3-96fa-ca116eeea127","joined_date":"13-02-2025","roles":[],"username":"helpdesk"}]},"success":True,"url":"http://192.168.1.86:3000/api/v1/users/?limit=2&offset=1"})
@token_active
@admin_required
def get_users(query_data: dict):
    """
        Returns a JSON of all users. Requires admin role. Supports pagination.

        Returns:
            - dict():  The JSON containing the users
    """
    try:
        offset = query_data.get('offset', 0)
        limit = query_data.get('limit', 0)
        
        users = kutils.get_users_from_keycloak(offset=offset, limit=limit)
                
        return {
            'url': request.url,
            'result':  { 
                'users': users,
                'count': len(users)
            },
            'success': True
        }, 200    
    except ValueError as ve:
        return {
                'url' : request.url,
                'result': {str(ve)},
                'success': False
        }, 400
    except Exception as e:
        return {
                'url' : request.url,
                'result': {str(e)},
                'success': False
        }, 500

@users_bp.route('/token', methods=['POST'])
@users_bp.input(schema.NewToken, location='json', example={"username": "a.stratakis", "password": "mypassword"})
@users_bp.output(schema.ResponseAmbiguous, example={"result":{"token":"$$$ACCESS_TOKEN$$$","refresh_token":"$$$REFRESH_TOKEN$$$"},"success":True}, status_code=200)
@users_bp.doc(tags=['User Management'])
def api_token_create(json_data: dict):
    """
    Generate an OAuth2.0 token for an existing user.

    Returns:
        - A JSON response with the OAuth2.0 token.
    """

    try:
        username = json_data.get('username')
        password = json_data.get('password')
        token = kutils.get_token(username, password)
        if token:
            return {
                'help' : request.url,
                'result': {
                    'token': token['access_token'],
                    'refresh_token': token['refresh_token']
                },
                'success': True
            }, 200
        else:
            return {
                'help' : request.url,
                'result': {},
                'success': False
            }, 400
    except Exception:
        return {
                'help' : request.url,
                'result': {},
                'success': False
        }, 400

@users_bp.route('/token', methods=['PUT'])
@users_bp.input(schema.RefreshToken, location='json', example={"refresh_token": "$$$REFRESH_TOKEN$$$"})
@users_bp.output(schema.ResponseOK, example={"result":{"token":"$$$ACCESS_TOKEN$$$","refresh_token":"$$$REFRESH_TOKEN$$$"},"success":True}, status_code=200)
@users_bp.doc(tags=['User Management'])
def api_token_refresh(json_data: dict):
    """
    Refresh an OAuth2.0 token using a refresh token.

    Returns:
        - A JSON response with the OAuth2.0 token or an error message.
    """

    try:
        reftoken = json_data.get('refresh_token')

        token = kutils.refresh_access_token(reftoken)

        if token:
            return {
                'help' : request.url,
                'result': {
                    'token': token['access_token'],
                    'refresh_token': token['refresh_token']
                },
                'success': True
            }, 200
        else:
            return {
                'help' : request.url,
                'result': {},
                'success': False
            }, 400
    except Exception as e:
        return {
                'help' : request.url,
                'result': {},
                'success': False
        }, 400

@users_bp.route('/', methods=['POST'])
@users_bp.input(schema.NewUser, location='json')
@users_bp.output(schema.ResponseAmbiguous, status_code=200)
@users_bp.doc(tags=['User Management'], security=security_doc)
@token_active
@admin_required
def api_create_user(json_data: dict):
    """
    Creates a new user. Requires admin role.

    Returns:
        - A JSON response of the reulst.
    """

    try:
        username = json_data["username"]
        first_name = json_data["firstName"]
        last_name = json_data["lastName"]
        password = json_data["password"]
        enabled = json_data.get("enabled", True)  

        user_id = kutils.create_user_with_password(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            enabled=enabled,
            attributes={}
        )

        if not user_id:
            raise RuntimeError("Failed to create user. Please check the logs for details.")

        # Retrieve and return the newly created user representation
        user_rep = kutils.get_user(user_id)

        if user_rep:
            return {
                'help': request.url,
                'result': {
                    'user': user_rep
                },
                'success': True
            }, 200
        else:
            raise AttributeError(f"Failed to find user with identifier: {user_id}")

    except ValueError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Validation error: {ve}",
                '__type': 'User Entity Error',
            },
            "success": False
        }, 400
    
    except AttributeError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'User Entity Not Found',
            },
            "success": False
        }, 404
        
    except Exception as e:
        return {
            "help": request.url,
            "error": {
                "name": f"Error: {e}",
                '__type': 'Unknown Error',
            },
            "success": False
        }, 500

@users_bp.route('/<user_id>', methods=['GET'])
@users_bp.output(schema.ResponseAmbiguous, status_code=200)
@users_bp.doc(tags=['User Management'], security=security_doc)
@token_active
@admin_required
def api_get_user(user_id):
    """Get information about a specific user (id). Requires admin role.
       
        Returns:
            - A JSON response of the reulst.
    """

    try:
        user_rep = kutils.get_user(user_id=user_id)
        if user_rep:
            return {
                'help': request.url,
                'result': {
                    'user': user_rep
                },
                'success': True
            }, 200
        else:
            raise AttributeError(f"Failed to find user with identifier: {user_id}")

    except ValueError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Validation error: {ve}",
                '__type': 'User Entity Error',
            },
            "success": False
        }, 400

    except AttributeError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'User Entity Not Found',
            },
            "success": False
        }, 404

    except Exception as e:
        return {
            "help": request.url,
            "error": {
                "name": f"Error: {e}",
                '__type': 'Unknown Error',
            },
            "success": False
        }, 500

@users_bp.route('/<user_id>', methods=['PATCH'])
@users_bp.input(schema.UpdatedUser, location='json')
@users_bp.output(schema.ResponseAmbiguous, status_code=200)
@users_bp.doc(tags=['User Management'], security=security_doc)
@token_active
@admin_required
def api_put_user(user_id, json_data):
    """
    Updates information of a specific user (id). Requires admin role.
    
    Returns:
        - A JSON response with the updated user.
    """

    try:
        email = json_data.get("email")
        first_name = json_data.get('firstName')
        last_name = json_data.get("lastName")
        enabled = json_data.get("enabled", True)  

        user_upd = kutils.update_user(user_id=user_id,
                                      first_name=first_name,
                                      last_name=last_name,
                                      email=email,
                                      enabled=enabled)
        if user_upd:
            return {
                "success":True, 
                "result":{
                    "user": user_upd
                },
                "help": request.url
            }, 200
        else:
            raise AttributeError(f"User with ID or username: {user_id} not found")
    except ValueError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Validation error: {ve}",
                '__type': 'User Entity Error',
            },
            "success": False
        }, 400
    except AttributeError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'User Entity Not Found',
            },
            "success": False
        }, 404
    except Exception as e:
        return {
            "help": request.url,
            "error": {
                "name": f"Error: {e}",
                '__type': 'Unknown Error',
            },
            "success": False
        }, 500

@users_bp.route('/<user_id>', methods=['DELETE'])
@users_bp.output(schema.ResponseAmbiguous, status_code=200)
@users_bp.doc(tags=['User Management'], security=security_doc)
@token_active
@admin_required
def api_delete_user(user_id):
    """
    Deletes a specific user (id or username). Requires admin role.

    Returns:
     - A JSON response containing the UUID of the deleted user.
    """

    try:
        id = kutils.delete_user(user_id)
        if id:
            return {
                "success":True, 
                "result":{
                    "deleted_id": id
                },
                "help": request.url
            },200

    except AttributeError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'User Entity Not Found',
            },
            "success": False
        }, 404
    except Exception as e:
        return {
            "help": request.url,
            "error": {
                "name": f"Error: {e}",
                '__type': 'Unknown Error',
            },
            "success": False
        }, 500

@users_bp.route('/roles', methods=['GET'])
@users_bp.output(schema.ResponseAmbiguous, status_code=200)
@users_bp.doc(tags=['Authorization Management'], security=security_doc)
@token_active
@admin_required
def api_get_roles():
    """
    Get sll existing roles. Requires admin role.

    Returns:
        - A JSON response containing all the roles.
    """

    try:
        roles = kutils.get_realm_roles()

        return {
            "success":True, 
            "result":{
                "roles": roles
            },
            "help": request.url
        }, 200

    except Exception as e:
        return {
            "help": request.url,
            "error": {
                "name": f"Error: {e}",
                '__type': 'Unknown Error',
            },
            "success": False
        }, 500

@users_bp.route('/<user_id>/roles/<role_id>', methods=['POST'])
@users_bp.output(schema.ResponseAmbiguous, status_code=200)
@users_bp.doc(tags=['Authorization Management'], security=security_doc)
@token_active
@admin_required
def api_assign_role(user_id, role_id):
    """
    Assign role to a specific user by ID and by Role ID. Requires admin role.

    Returns:
        - A JSON response with the updated user description.
    """

    try:
        user = kutils.assign_role_to_user(user_id, role_id)
        return {
            "success":True, 
            "result":{
                "user": user
            },
            "help": request.url
        }, 200
    except AttributeError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Uniqueness error: {ve}",
                '__type': 'Entity Already Present',
            },
            "success": False
        }, 400
    except ValueError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'Entity Not Found',
            },
            "success": False
        }, 404
    except Exception as e:
        return {
            "help": request.url,
            "error": {
                "name": f"Error: {e}",
                '__type': 'Unknown Error',
            },
            "success": False
        }, 500

@users_bp.route('/<user_id>/roles/<role_id>', methods=['DELETE'])
@users_bp.output(schema.ResponseAmbiguous, status_code=200)
@users_bp.doc(tags=['Authorization Management'], security=security_doc)
@token_active
@admin_required
def api_delete_role(user_id, role_id):
    """
    Unassign a role from a specific user by ID. Requires admin role.

    Returns:
        - A JSON response with the updated user description.
    """
    try:
        user = kutils.unassign_role_from_user(user_id, role_id)
        return {
            "success":True, 
            "result":{
                "user": user
            },
            "help": request.url
        }, 200
    except AttributeError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'Entity Not Present',
            },
            "success": False
        }, 400
    except ValueError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'Entity Not Found',
            },
            "success": False
        }, 404
    except Exception as e:
        return {
            "help": request.url,
            "error": {
                "name": f"Error: {e}",
                '__type': 'Unknown Error',
            },
            "success": False
        }, 500

@users_bp.route('/<user_id>/roles', methods=['POST'])
@users_bp.input(schema.RolesInput, location='json')
@users_bp.output(schema.ResponseAmbiguous, status_code=200)
@users_bp.doc(tags=['Authorization Management'], security=security_doc)
@token_active
@admin_required
def api_assign_roles(user_id, json_data):
    """
    Assing lots-of roles to a specific user by ID. Will not remove any roles already assigned to the user. Requires admin role.

    Returns:
        - A JSON response with the updated user description.
    """ 
    try:
        user = kutils.assign_roles_to_user(user_id, json_data.get("roles"))
        return {
            "success":True, 
            "result":{
                "user": user
            },
            "help": request.url
        }, 200
    except AttributeError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'Entity Not Present',
            },
            "success": False
        }, 400
    except ValueError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'Entity Not Found',
            },
            "success": False
        }, 404
    except Exception as e:
        return {
            "help": request.url,
            "error": {
                "name": f"Error: {e}",
                '__type': 'Unknown Error',
            },
            "success": False
        }, 500

@users_bp.route('/<user_id>/roles', methods=['PATCH'])
@users_bp.input(schema.RolesInput, location='json')
@users_bp.output(schema.ResponseAmbiguous, status_code=200)
@users_bp.doc(tags=['Authorization Management'], security=security_doc)
@token_active
@admin_required
def api_patch_roles(user_id, json_data):
    """
        Update the roles of a user. Requires admin role.

        Returns:
        - A JSON response with the updated user description.
    """

    try:
        user = kutils.patch_user_roles(user_id=user_id, role_ids=json_data['roles'])
        return {
            "success":True, 
            "result":{
                "user": user
            },
            "help": request.url
        }, 200
    except AttributeError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'Entity Not Present',
            },
            "success": False
        }, 400
    except ValueError as ve:
        return {
            "help": request.url,
            "error": {
                "name": f"Existence error: {ve}",
                '__type': 'Entity Not Found',
            },
            "success": False
        }, 404
    except Exception as e:
        return {
            "help": request.url,
            "error": {
                "name": f"Error: {e}",
                '__type': 'Unknown Error',
            },
            "success": False
        }, 500
