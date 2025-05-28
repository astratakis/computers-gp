from apiflask import HTTPTokenAuth
from flask import current_app, session, jsonify, request
from functools import wraps
import kutils

auth = HTTPTokenAuth(scheme="Bearer", header="Authorization", security_scheme_name="BearerAuth", description="An OAuth2 token issued by the STELAR IDP by using endpoint or GUI issuance.")

security_doc = "BearerAuth"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if request.headers.get('Authorization'):
                # Extract the token from the 'Authorization' header
                access_token = request.headers.get('Authorization').split(" ")[1]
            else:
                # Try to extract token from session if not provided.
                access_token = session.get('access_token')
                if access_token is None:
                    response = {
                        'success': False,
                        'help': request.url,
                        'error': {
                            '__type': 'Authentication Error',
                            'name': 'Bearer Token is not Valid'
                        }
                    }
                    return response, 401  
    
            # Check if the token is valid and corresponds to an admin user
            if not kutils.introspect_admin_token(access_token):
                response = {
                    'success': False,
                    'help': request.url,
                    'error': {
                        '__type': 'Authorization Error',
                        'name': 'Bearer Token is not related to an admin user'
                    }
                }
                return response, 403
            
        except (IndexError, ValueError):
            response = {
                'success': False,
                'help': request.url,
                'error': {
                    '__type': 'Authorization Error',
                    'name': 'Authorization Bearer Token is missing or malformed'
                }
            }
            return response, 401
        except Exception as e:
            response = {
                'success': False,
                'help': request.url,
                'error': {
                    '__type': 'Unexpected Error',
                    'name': str(e)
                }
            }
            return response, 500
        
        return f(*args, **kwargs)
    
    return decorated_function

def gpolicy_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if request.headers.get('Authorization'):
                # Extract the token from the 'Authorization' header
                access_token = request.headers.get('Authorization').split(" ")[1]
            else:
                # Try to extract token from session if not provided.
                access_token = session.get('access_token')
                if access_token is None:
                    response = {
                        'success': False,
                        'help': request.url,
                        'error': {
                            '__type': 'Authentication Error',
                            'name': 'Bearer Token is not Valid'
                        }
                    }
                    return response, 401  
    
            # Check if the token is valid and corresponds to an admin user
            if not kutils.introspect_gpolicy_token(access_token):
                response = {
                    'success': False,
                    'help': request.url,
                    'error': {
                        '__type': 'Authorization Error',
                        'name': 'Bearer Token is not related to an admin user'
                    }
                }
                return response, 403
            
        except (IndexError, ValueError):
            response = {
                'success': False,
                'help': request.url,
                'error': {
                    '__type': 'Authorization Error',
                    'name': 'Authorization Bearer Token is missing or malformed'
                }
            }
            return response, 401
        except Exception as e:
            response = {
                'success': False,
                'help': request.url,
                'error': {
                    '__type': 'Unexpected Error',
                    'name': str(e)
                }
            }
            return response, 500
        
        return f(*args, **kwargs)
    
    return decorated_function


def token_active(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:             
            if request.headers.get('Authorization'):
                # Extract the token from the 'Authorization' header
                access_token = request.headers.get('Authorization').split(" ")[1]
            else:
                # Try to extract token from session if not provided.
                access_token = session.get('access_token')
                if access_token is None:
                    response = {
                        'success': False,
                        'help': request.url,
                        'error': {
                            '__type': 'Authentication Error',
                            'name': 'Bearer Token is not Valid'
                        }
                    }
                    return response, 401

            # Check if the token is valid
            if not kutils.introspect_token(access_token):
                response = {
                    'success': False,
                    'help': request.url,
                    'error': {
                        '__type': 'Authorization Error',
                        'name': 'Bearer Token is expired'
                    }
                }
                return response, 403
            
        except (IndexError, ValueError):
            response = {
                'success': False,
                'help': request.url,
                'error': {
                    '__type': 'Authorization Error',
                    'name': 'Authorization Bearer Token is missing or malformed'
                }
            }
            return response, 400
        except Exception as e:
            response = {
                'success': False,
                'help': request.url,
                'error': {
                    '__type': 'Unexpected Error',
                    'name': str(e)
                }
            }
            return response, 500
        
        return f(*args, **kwargs)
    
    
    return decorated_function