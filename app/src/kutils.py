from keycloak import KeycloakOpenID, KeycloakAdmin, KeycloakAuthenticationError, KeycloakGetError
from flask import current_app, session
import datetime
import uuid
import re
import logging

def load_user_metadata() -> dict:
    user_data = get_user_by_token(session['access_token'])

    if "Helpdesk" in user_data.get("realm_access").get("roles"):
        role = "Helpdesk"
    elif "GPolicy" in user_data.get("realm_access").get("roles"):
        role = "GPolicy"
    elif "admin" in user_data.get("realm_access").get("roles"):
        role = "Administrator"
    else:
        role = "Undefined"

    username = user_data.get("username")
    fullname = user_data.get("name")

    return {"role": role, "username": username, "fullname": fullname}

def initialize_admin_client() -> KeycloakAdmin:
    """
    Initializes and returns a KeycloakAdmin client using the client service account. (If Enabled)

    Returns:
        KeycloakAdmin: An initialized KeycloakAdmin client
    """
    config = current_app.config['settings']
    
    try:
        keycloak_admin = KeycloakAdmin(
            server_url=config['KEYCLOAK_URL'],
            realm_name=config['REALM_NAME'],
            client_id=config['KEYCLOAK_CLIENT_ID'],
            client_secret_key=config['KEYCLOAK_CLIENT_SECRET'],
            verify=True
        )
        return keycloak_admin
    except Exception as e:
        raise RuntimeError(f'Failed to generate token and initialize KeycloakAdmin: {str(e)}')

def get_user_roles(user_id: str, keycloak_admin: KeycloakAdmin):
    """
    Fetches the roles assigned to a user with the given user_id using KeycloakAdmin object.

    Args:
        user_id (str): The ID of the user whose roles are to be fetched.
        keycloak_admin (KeycloakAdmin): The keycloak admin object that is already initialized.

    Returns:
        A list of roles assigned to the user.
    
    Raises:
        Exception: If an error occurs.
    """
    try:
        realm_roles = keycloak_admin.get_realm_roles_of_user(user_id) 

        if not realm_roles:
            return []

        filtered_roles = [
            role['name'] for role in realm_roles
            if role.get('name') and role['name'] != 'default-roles-master'
        ]

        return filtered_roles
    
    except Exception as e:
        return []

def get_users_from_keycloak(offset: int, limit: int) -> list:
    """
    Retrieves a list of users from Keycloak with pagination and additional user details.

    Args:
        offset (int): The starting index for the users to retrieve (default is 0).
        limit (int): The maximum number of users to retrieve (default is 50).

    Returns:
        A list of user dictionaries containing user details.
    
    Raises:
        ValueError: If invalid values for offset or limit are provided.
        RuntimeError: If there is an issue with the Keycloak connection or API interaction.
    """
    try:
        # Initialize KeycloakAdmin client with credentials
        keycloak_admin = initialize_admin_client()

        if limit < 0 or offset < 0:
            raise ValueError("Limit and offset must be greater than 0.")
        
        if limit == 0:
            query={"first": offset}
        else:
            query={"first": offset, "max": limit}

        users = keycloak_admin.get_users(query=query)

        result = []
        for user in users:
            creation_date = convert_iat_to_date(user['createdTimestamp'])
            filtered_roles = get_user_roles(user_id=user['id'], keycloak_admin=keycloak_admin)
            
            active_status = user.get('enabled', False)
            user_info = {
                "username": user.get("username"),
                "fullname": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
                "joined_date": creation_date,
                "id": user.get("id"),
                "roles": filtered_roles,
                "active": active_status  
            }
            result.append(user_info)
        
        return result

    except ValueError as ve:
        raise ValueError(f"Invalid parameter: {str(ve)}")
    except RuntimeError as re:
        raise RuntimeError(f"Failed to fetch users from Keycloak: {str(re)}")

def is_valid_uuid(s: str) -> bool:
    try:
        # Try converting the string to a UUID object
        uuid_obj = uuid.UUID(s)
        # Check if the string matches the canonical form of the UUID (with lowercase hexadecimal and hyphens)
        return str(uuid_obj) == s
    except ValueError:
        return False

def convert_iat_to_date(timestamp: float) -> datetime:
    if timestamp:
        return datetime.datetime.fromtimestamp(timestamp / 1000.0).strftime('%d-%m-%Y')
    else:
        return None

def username_unique(username):
    keycloak_admin = initialize_admin_client()
    # Check for existing users with the same username
    existing_users = keycloak_admin.get_users({
        "username": username
    })

    if existing_users:
        raise ValueError(f"A user with the username '{username}' already exists.")

def initialize_keycloak_openid() -> KeycloakOpenID:
    config = current_app.config['settings']
    return KeycloakOpenID(
        server_url=config['KEYCLOAK_URL'],
        client_id=config['KEYCLOAK_CLIENT_ID'],
        realm_name=config['REALM_NAME'],
        client_secret_key=config['KEYCLOAK_CLIENT_SECRET'],
        verify=True
    )

def introspect_admin_token(access_token) -> bool:
    """
    Introspects the given access token to check if it's valid and active.
    It also checks if the user has admin role.

    Returns:
        True if the token is valid and admin, False if the token is invalid or expired or not admin or an exception occurs.
    """
    try:
        keycloak_openid = initialize_keycloak_openid()
        introspect_response = keycloak_openid.introspect(access_token)
        
        # Check if the token is active and user has admin role
        if introspect_response.get("active", False):
            if (introspect_response.get("realm_access", False)):
                if ("admin" in introspect_response["realm_access"]["roles"]):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    except Exception as e:
        return False
    
def introspect_gpolicy_token(access_token) -> bool:
    """
    Introspects the given access token to check if it's valid and active.
    It also checks if the user has admin role.

    Returns:
        True if the token is valid and admin, False if the token is invalid or expired or not admin or an exception occurs.
    """
    try:
        keycloak_openid = initialize_keycloak_openid()
        introspect_response = keycloak_openid.introspect(access_token)
        
        # Check if the token is active and user has admin role
        if introspect_response.get("active", False):
            if (introspect_response.get("realm_access", False)):
                if ("admin" in introspect_response["realm_access"]["roles"] or "GPolicy" in introspect_response["realm_access"]["roles"]):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    except Exception as e:
        return False

def get_user_by_token(access_token):
    """
    Introspects the given access token to return the user information if the token is active
    Returns the user json if the token is valid, False if the token is invalid or expired.
    """
    try:
        keycloak_openid = initialize_keycloak_openid()
        introspect_response = keycloak_openid.introspect(access_token)
        if introspect_response.get("active", False):
            return introspect_response
        else:
            return {}
    except Exception as e:
        return False

def introspect_token(access_token):
    """
    Introspects the given access token to check if it's valid and active.
    Returns True if the token is valid, False if the token is invalid or expired.
    """
    try:
        keycloak_openid = initialize_keycloak_openid()
        introspect_response = keycloak_openid.introspect(access_token)
        # Check if the token is active
        if introspect_response.get("active", False):
            return True
        else:
            return False
    except Exception as e:
        return False

def refresh_access_token(refresh_token):
    """
    Refreshes the access token using the refresh token given as args.

    This function initializes the Keycloak OpenID client and uses the stored refresh token 
    to obtain a new access token. If successful, it updates the session with the new 
    access token and refresh token. In case of failure, it returns an appropriate error message.

    Args:
        - refresh_token: The refresh token to use.

    Returns:
        tuple: A tuple containing:
            - str or None: The refreshed access token if successful, otherwise None.
            - str or None: An error message if the refresh fails, otherwise None.

    Raises:
        Exception: If an error occurs during the token refresh process.
    """

    keycloak_openid = initialize_keycloak_openid()
    
    if not refresh_token:
        return None

    try:
        token = keycloak_openid.refresh_token(refresh_token, grant_type='refresh_token')
        return token
    except Exception as e:
        return None, str(e)
    
def get_token(username, password):
    """ 
    Returns a token for a user in Keycloak by using username and password. 

    Args:
        username: The username of the user in Keycloak
        password The secret password of the user in Keycloak

    Returns:
        str: The access_token
        null: Error return  
   
    """
    kopenid = initialize_keycloak_openid()
    try:
        token = kopenid.token(username, password)
        return token
    except Exception as e:
        return None

def initialize_admin_client_with_admin_token(admin_token):
    """
    Initializes and returns a KeycloakAdmin client using a pre-obtained admin token.

    Args:
        admin_token: An OAuth2.0 admin token

    Returns:
        KeycloakAdmin: An initialized KeycloakAdmin client with admin token.
    
    Raises:
        RuntimeError: If initialization fails due to an error.
    """
    config = current_app.config['settings']
    

    
    try:
        
        # Initialize KeycloakAdmin using the token
        admin_client = KeycloakAdmin(
            server_url=config['KEYCLOAK_URL'],
            realm_name=config['REALM_NAME'],
            client_id=config['KEYCLOAK_CLIENT_ID'],
            verify=True,
            token=admin_token
        )
        
        return admin_client
    except Exception as e:
        raise RuntimeError(f'Failed to initialize KeycloakAdmin with admin token: {str(e)}')

def init_admin_client(username, password):
    """
    Initializes and returns a KeycloakAdmin client using the admin username and password.
    
    This function authenticates an admin user using their username and password to obtain a new
    access token. It then uses this access token to initialize a KeycloakAdmin client. The access 
    token is not stored in the session in this case, since it is generated dynamically for each 
    login request.

    Args:
        username (str): The username of the admin user.
        password (str): The password of the admin user.

    Returns:
        KeycloakAdmin: An initialized KeycloakAdmin client with a valid access token.

    Raises:
        ValueError: If the username or password is invalid or the authentication fails.
        RuntimeError: If the token generation or client initialization fails.
    """
    config = current_app.config['settings']

    keycloak_openid = initialize_keycloak_openid()

    try:
        # Generate token by authenticating using username and password
        token = keycloak_openid.token(username, password)

        # Initialize KeycloakAdmin client with the new access token
        keycloak_admin = KeycloakAdmin(
            server_url=config['KEYCLOAK_URL'],
            realm_name=config['REALM_NAME'],
            token=token,  
            verify=True
        )

        return keycloak_admin

    except Exception as e:
        raise RuntimeError(f'Failed to generate token and initialize KeycloakAdmin: {str(e)}')

def get_role(role_id):
    """
    Fetches the role by ID from the Realm

    :param user_id: The ID or the name of the role to be fetched.
    :return: The role representation
    """
    try:
        keycloak_admin = initialize_admin_client()  

        if is_valid_uuid(role_id):
            role_rep = keycloak_admin.get_realm_role_by_id(role_id)
        else:
            role_rep = keycloak_admin.get_realm_role(role_id)
            
        if not role_rep:
            return None

        return role_rep
    
    except Exception as e:
        return None

def get_realm_roles():
    """
        Returns the realm roles exluding the Keycloak default roles. 
    """
    
    try:
        keycloak_admin = initialize_admin_client()

        roles = keycloak_admin.get_realm_roles(brief_representation=True)

        for role in roles:
            logging.debug(role)

        # Define a set of roles to exclude
        roles_to_exclude = {'offline_access', 'uma_authorization', 'create-realm', 'default-roles-master'}

        # Filter the roles, excluding those in the roles_to_exclude set
        filtered_roles = [role for role in roles if role['name'] not in roles_to_exclude]

        return filtered_roles

    except Exception as e:
        raise Exception(str(e))

def create_user_with_password(
    username,
    first_name,
    last_name,
    password,
    enabled=True,
    temporary_password=False,
    attributes=None
):
    """
    Create a new user in Keycloak and set a password, ensuring username and email are unique.

    :param username: Username for the new user
    :param first_name: First name of the user
    :param last_name: Last name of the user
    :param password: Password for the new user
    :param enabled: Whether the user account should be enabled (default: True)
    :param temporary_password: If True, the password is marked as temporary
    :param attributes: Additional attributes to add to the user
    :param emailVerified: Boolean to mark the verification state of the email
    :return: The ID of the created user, or None if creation failed

    Raises:
    - ValueError if the username or the email are not unique

    """
    try:
        # Initialize the Keycloak admin client
        keycloak_admin = initialize_admin_client()

        # Will raise ValueError if the username or email already exist.
        username_unique(username=username)

        user_payload = {
            "username": username,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": enabled,
            "attributes": attributes or {}
        }

        user_id = keycloak_admin.create_user(payload=user_payload, exist_ok=False)

        if user_id:
            keycloak_admin.set_user_password(user_id=user_id, password=password, temporary=temporary_password)
        
        return user_id
    except KeycloakAuthenticationError as e:
        logging.error('Authentication Error')
        return None
    except ValueError as ve:
        logging.error('Value Error')
        raise ValueError(ve)
    except Exception as e:
        logging.error('Exception occured')
        logging.error(e)
        return None

def update_user(
        user_id, 
        first_name=None, 
        last_name=None, 
        enabled=None
    ):
    """
    Updates a user in the Keycloak realm by the given user ID.
    
    Parameters:
    - first_name (str, optional): The new first name for the user.
    - last_name (str, optional): The new last name for the user.
    - email (str, optional): The new email for the user.
    - enabled (bool, optional): Whether the user account should be enabled or disabled.
    
    Returns:
    - dict: The updated user data if successful, otherwise raises an exception.
    
    Raises:
    - ValueError: if the username or the email are not unique
    """
    try:
        keycloak_admin = initialize_admin_client()
       
        # Prepare the update data dictionary with only the fields that are not None
        user_data = {}
        user_repr = get_user(user_id=user_id)

        if user_repr['username'] == 'admin':
            return {"warning":"Modifications to administrator account are not allowed"}

        if first_name:
            user_data['firstName'] = first_name
        if last_name:
            user_data['lastName'] = last_name
        if enabled is not None:
            user_data['enabled'] = enabled
        
        # Support both selecting user by UUID and by Username
        if not is_valid_uuid(user_id):
            user_id = keycloak_admin.get_user_id(user_id)

        keycloak_admin.update_user(user_id, user_data)

        updated_user_json = get_user(user_id=user_id)
        
        return updated_user_json
    
    except KeycloakAuthenticationError as e:
        return None
    except ValueError as ve:
        raise ValueError(ve)
    except Exception as e:
        return None

def get_user(user_id=None):
    """
    Retrieve a user from Keycloak by user ID.
    It also returns the roles

    :param user_id: The ID of the user to retrieve (str). If None, returns None.
    :return: A dictionary representation of the user if found, otherwise None.
    """
    if not user_id or not isinstance(user_id, str):
        return None
    
    try:
        keycloak_admin = initialize_admin_client()

        #Support both searching by UUID and by Username
        if is_valid_uuid(user_id):
            user_representation = keycloak_admin.get_user(user_id)
        else:
            id= keycloak_admin.get_user_id(user_id)
            user_representation= keycloak_admin.get_user(id)

        if user_representation:
          
            creation_date = convert_iat_to_date(user_representation['createdTimestamp'])

            filtered_roles = get_user_roles(user_representation['id'])
            
            active_status = user_representation.get('enabled', False)
            email_verified = user_representation.get('emailVerified', False)

            user_info = {
                "username": user_representation.get("username"),
                "email": user_representation.get("email"),
                "fullname": f"{user_representation.get('firstName', '')} {user_representation.get('lastName', '')}".strip(),
                "joined_date": creation_date,
                "id": user_representation.get("id"),
                "roles": filtered_roles,
                "active": active_status,
                "email_verified": email_verified
            }

            return user_info
        return None
    
    except Exception as e:
        return None
    
def delete_user(user_id=None):
    """
    Delete a user from Keycloak by user UUID.

    :param user_id: The UUID of the user to delete (str). If None, returns None.
    :return: The UUID of the deleted user.
    :raises AttributeError: If the user is not found.

    """
    if not user_id or not isinstance(user_id, str):
        return None

    try:
        keycloak_admin = initialize_admin_client()

        # Support both searching by UUID and by Username
        if not is_valid_uuid(user_id):
            id = keycloak_admin.get_user_id(user_id)
            user_id = keycloak_admin.get_user(id)['id']
            
        keycloak_admin.delete_user(user_id)
        return user_id

    except KeycloakGetError as e:
        if e.response_code == 404:
            raise AttributeError(f"User with ID '{user_id}' not found.") from e
        else:
            raise

    except Exception as e:
        raise

def fetch_user_creation_date(user_id):
    """
    Fetches user creation date from Keycloak Admin API using client credentials access token.

    """    
    keycloak_admin = initialize_admin_client()

    try:
        user = keycloak_admin.get_user(user_id)
        data = convert_iat_to_date(user.get("creadedTimestamp"))
        if data:
            return data
    except Exception as e:
        return None
    
def assign_role_to_user(user_id, role_id):
    """
        Assigns realm role to user.

        Args:
        - user_id: The UUID of the user or the username.
        - role_id: The UUID of the realm role or the name of it.

        Returns:
        - dict(): The updated user represantation containing the new role
    """
    
    try:
        keycloak_admin = initialize_admin_client()

        # Fetch the user representation
        user_rep = get_user(user_id)

        if not user_rep:
            raise ValueError(f"User with ID: {user_id} was not found.")
        
        user_roles = get_user_roles(user_rep.get('id'))
        
        role_rep = get_role(role_id)
        if not role_rep:
            raise ValueError(f"Role with ID: {role_id} was not found")

        # Assign the role to the user if it is not already assigned
        if role_rep['name'] not in user_roles:
            keycloak_admin.assign_realm_roles(user_rep['id'],[role_rep])
            return get_user(user_id)
        else:
            raise AttributeError(f"Role with ID: {role_id} already assigned to user with ID: {user_id}")

    except ValueError as ve:
        raise ValueError(str(ve))
    except AttributeError as ae:
        raise AttributeError(str(ae))
    except Exception as e:
        pass

def assign_roles_to_user(user_id, role_ids):
    """
    Assign multiple realm roles to a user.

    Args:
    - user_id: The UUID of the user or the username.
    - role_ids: A list of UUIDs or names of the realm roles to be assigned.

    Returns:
    - dict: The updated user representation containing the new roles.
    
    Raises:
    - ValueError: If the user or any role is not found.
    - AttributeError: If any role is already assigned to the user.
    """
    if not isinstance(role_ids, list):
        raise ValueError("role_ids must be a list of role UUIDs or names.")

    try:
        # Initialize Keycloak admin client
        keycloak_admin = initialize_admin_client()

        # Fetch the user representation
        user_rep = get_user(user_id)
        if not user_rep:
            raise ValueError(f"User with ID: {user_id} was not found.")

        user_roles = get_user_roles(user_rep.get('id'))

        # Fetch all roles representations
        roles_to_assign = []
        already_assigned_roles = []
        for role_id in role_ids:
            role_rep = get_role(role_id)
            if not role_rep:
                raise ValueError(f"Role with ID: {role_id} was not found.")
            
            # Check if the role is already assigned
            if role_rep['name'] not in user_roles:
                roles_to_assign.append(role_rep)
            else:
                already_assigned_roles.append(role_rep['name'])

        # Assign roles to the user if there are new roles to assign
        if roles_to_assign:
            keycloak_admin.assign_realm_roles(user_rep['id'], roles_to_assign)

        return get_user(user_id)

    except ValueError as ve:
        raise
    except AttributeError as ae:
        raise
    except Exception as e:
        raise

def patch_user_roles(user_id, role_ids):
    """
    Patch the roles of the user with new roles. Any roles not specified in the list will be removed.

    Args:
    - user_id: The UUID of the user or the username.
    - role_ids: A list of UUIDs or names of the realm roles to be assigned.

    Returns:
    - dict: The updated user representation containing the new roles.
    
    Raises:
    - ValueError: If the user or any role is not found.
    - AttributeError: If any role is already assigned to the user.
    """
    if not isinstance(role_ids, list):
        raise ValueError("role_ids must be a list of role UUIDs or names.")

    try:
        # Initialize Keycloak admin client
        keycloak_admin = initialize_admin_client()

        # Fetch the user representation
        user_rep = get_user(user_id)
        if not user_rep:
            raise ValueError(f"User with ID: {user_id} was not found.")

        # Fetch and validate roles
        roles = []
        for role in role_ids:
            rep = get_role(role)
            if rep is None:
                raise ValueError(f"The following role was not found: {role}")
            else:
                roles.append(rep.get('name'))

        current_roles = keycloak_admin.get_realm_roles_of_user(user_rep.get('id'))
        current_role_names = get_user_roles(user_rep.get('id'))

        if roles is not None:
            if not roles:
                # No roles specified: Unassign all non-default roles
                roles_to_remove = [role for role in current_roles if role['name'] != 'default-roles-master']
                if roles_to_remove:
                    keycloak_admin.delete_realm_roles_of_user(user_rep.get('id'), roles_to_remove)
            else:
                # Unassign roles not in the request
                roles_to_remove = [role for role in current_roles if role['name'] not in roles and role['name'] != 'default-roles-master']
                if roles_to_remove:
                    keycloak_admin.delete_realm_roles_of_user(user_rep.get('id'), roles_to_remove)

                # Assign new roles that are not already assigned
                available_realm_roles = keycloak_admin.get_realm_roles()
                roles_to_add = []
                for role in roles:
                    if role not in current_role_names:
                        role_info = next((r for r in available_realm_roles if r['name'] == role), None)
                        if role_info:
                            roles_to_add.append(role_info)
                        else:
                            raise ValueError(f"Role '{role}' not found in realm roles")

                if roles_to_add:
                    keycloak_admin.assign_realm_roles(user_rep.get('id'), roles_to_add)

        return get_user(user_id)

    except ValueError as ve:
        raise
    except AttributeError as ae:
        raise
    except Exception as e:
        raise

def unassign_role_from_user(user_id, role_id):
    """
        Unassigns a realm role from a user.

        Args:
        - user_id: The UUID of the user or the username.
        - role_id: The UUID of the realm role or the name of it.

        Returns:
        - dict(): The updated user representation without the removed role.
    """
    try:
        keycloak_admin = initialize_admin_client()

        # Fetch the user representation
        user_rep = get_user(user_id)
        if not user_rep:
            raise ValueError(f"User with ID: {user_id} was not found.")

        user_roles = get_user_roles(user_rep.get('id'))

        role_rep = get_role(role_id)
        if not role_rep:
            raise ValueError(f"Role with ID: {role_id} was not found.")

        # Unassign the role if it is currently assigned to the user
        if role_rep['name'] in user_roles:
            keycloak_admin.delete_realm_roles_of_user(user_rep['id'], [role_rep])
            return get_user(user_id)
        else:
            raise AttributeError(f"Role with ID: {role_id} is not assigned to user with ID: {user_id}")

    except ValueError as ve:
        raise ValueError(str(ve))
    except AttributeError as ae:
        raise AttributeError(str(ae))
    except Exception as e:
        pass

def create_client_role(keycloak_admin, client_name, client_id, role_name):
    print(client_id)
    keycloak_admin.create_client_role(client_id, {'name': role_name},skip_exists=True)
    print(f'Role "{role_name}" created successfully for client "{client_name}".')
    return role_name

def create_realm_role(keycloak_admin, role_name):
    config = current_app.config['settings']
    realm_role = {
        "name": role_name,
        "composite": True,
        "clientRole": False,
        "containerId": config['REALM_NAME']
    }
    keycloak_admin.create_realm_role(realm_role,skip_exists=True)

    return role_name

def delete_realm_roles(keycloak_admin,roles_to_delete):
# Delete the roles that are no longer needed
    for role in roles_to_delete:
        print("realm role to delete: ",role)
        role_id = keycloak_admin.get_realm_role(role)["id"]
        keycloak_admin.delete_role_by_id(role_id)

def delete_client_roles(keycloak_admin,client_roles_to_delete):
    for client_role in client_roles_to_delete:
        keycloak_admin.delete_client_role(keycloak_admin.get_client_id('minio'),client_role)