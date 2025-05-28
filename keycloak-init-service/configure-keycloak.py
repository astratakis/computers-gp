
from keycloak import KeycloakAdmin, KeycloakPostError
import os

OK = "\033[92m      OK      \033[0m"
FAILED = "\033[91m****FAILED****\033[0m"
SKIP = "\033[96m     SKIP     \033[0m"

KEYCLOAK_ADMIN_USERNAME = os.getenv("KEYCLOAK_ADMIN")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
KEYCLOAK_TOKEN_LIFESPAN = int(os.getenv("KEYCLOAK_TOKEN_LIFESPAN"))
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_REALM_ROLES = os.getenv("KEYCLOAK_REALM_ROLES")

# Function to create a client
def create_client(keycloak_admin: KeycloakAdmin, client_name: str, home_url: str = "", root_url: str = ""):
    client_representation = {
        "clientId": client_name,
        "enabled": True,
        "rootUrl": root_url,
        "baseUrl": home_url,
        "redirectUris": ["*"],
        "attributes": {
            "post.logout.redirect.uris": "+"
        },
        "directAccessGrantsEnabled": True
        
    }
    
    client_id = keycloak_admin.create_client(client_representation, skip_exists=True)
    return client_id

# Enables service account to a client in keycloak
def enable_service_account(keycloak_admin: KeycloakAdmin, client_id):
    try:
        # Retrieve the client configuration
        client_representation = keycloak_admin.get_client(client_id)
        
        # Update the configuration to enable service accounts
        client_representation["serviceAccountsEnabled"] = True
        client_representation["authorizationServicesEnabled"] = True
        
        # Update the client with the modified configuration
        keycloak_admin.update_client(client_id, client_representation)
        print(f"Service account enabled for client with ID: {client_id}")

        role = keycloak_admin.get_realm_role("admin")
        print(f"Retrieved existing role: {role}")

        service_account_user = keycloak_admin.get_client_service_account_user(client_id)
        service_account_user_id = service_account_user["id"]

        # Assign the admin role to the service account user
        keycloak_admin.assign_realm_roles(service_account_user_id, [role])
        print(f"Admin role assigned to service account for client ID: {client_id}")
        
    except KeycloakPostError as e:
        print(f"Failed to enable service account: {e}")
        raise

def update_token_lifespan(keycloak_admin: KeycloakAdmin, lifespan: int):
    # Get the current settings of the realm
    realm = keycloak_admin.get_realm(KEYCLOAK_REALM)

    # Update the access token lifespan (e.g., 3600 seconds = 1 hour)
    realm["accessTokenLifespan"] = lifespan

    # Apply the updated settings
    keycloak_admin.update_realm(KEYCLOAK_REALM, realm)
    
if __name__ == "__main__":
    print('=========================== < KEYCLOAK CONFIGURATION > ===========================')
    
    kc_admin = KeycloakAdmin(server_url=KEYCLOAK_URL,
                             username=KEYCLOAK_ADMIN_USERNAME,
                             password=KEYCLOAK_ADMIN_PASSWORD,
                             realm_name=KEYCLOAK_REALM,
                             verify=True)
    
    print(f"[{OK}] Creating Keycloak Client ... ")
    
    try: 
        client_id = create_client(kc_admin, client_name='computers-gp')
        print(f"[{OK}] Creating client id ... ")
    except Exception:
        print(f"[{FAILED}] Creating client id ... ")
        exit(1)

    print('Parsing client secret ... ', end="\t")
    try:
        client_secret_info = kc_admin.get_client_secrets(client_id)
        client_secret = client_secret_info['value']
        print(f"[{OK}] Parsing clinet secret ... ")
    except Exception:
        print(f"[{FAILED}] Parsing clinet secret ... ")
        exit(1)

    for role in KEYCLOAK_REALM_ROLES:
        try:
            kc_admin.create_realm_role({'name': role})
            print(f"[{OK}] Created {role} role ... ")
        except Exception:
            print(f"[{SKIP}] Role {role} already exists ... ")

    try:
        update_token_lifespan(kc_admin, KEYCLOAK_TOKEN_LIFESPAN)
        print(f"[{OK}] Updating token lifespan ... ")
    except Exception:
        print(f"[{FAILED}] Updating token lifespan ... ")
        exit(1)

    try:
        enable_service_account(kc_admin, client_id)
        print(f"[{OK}] Enabling service account ... ")
    except Exception:
        print(f"[{FAILED}] Enabling service account ... ")
        exit(1)

    try:
        file = open("/usr/shared/client-secret.txt", "w")
        file.write(client_secret)
        file.close()
        print(f"[{OK}] Saving client secret ... ")
    except Exception:
        print(f"[{FAILED}] Saving client secret ... ")

    print('==================================================================================')

    print('My job is done, now im going to kill myself... byeee!')
    exit(0)