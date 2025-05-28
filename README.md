# Computers GP

A web application for ticketing and managing a database of computers. Created using Flask for backend api and plain javascript and html for the frontend.

<div align="center">
  <img src="./app/src/static/computers-gp-logo.svg" width="600" height="180" alt="Computers GP">
</div>

## Environmental Variables

You need to create a **.env** file which contains all the environmental variables for the docker-compose.yml file. All the variables are listed in the following table. For reference see the **environment-example.txt**.

| Variable | Service | Description |
| ---------- | -------- | ----------------- |
| POSTGRES_USER | postgres | Login user via the pgadmin for the postgres database |
| POSTGRES_PASSWORD | postgres | Password of the database |
| POSTGRES_DB | postgres | Name of the database |
| KEYCLOAK_DB_USER | postgres | Keycloak user for keycloak's database |
| KEYCLOAK_DB_PASSWORD | postgres | Keycloak's password for keycloak's database |
| KC_HEALTH_ENABLED | keycloak | Enables health reports from keycloak |
| KEYCLOAK_ADMIN | keycloak | The username of Keycloak's administrator account |
| KEYCLOAK_ADMIN_PASSWORD | keycloak | The password of Keycloak's administrator |
| KC_DB | keycloak | Database service for keycloak |
| KC_HOSTNAME | keycloak | Keycloak's URL |
| KC_RELATIVE_HTTP_PATH | keycloak | Relative path for keycloak |
| KC_HOSTNAME_DEBUG | keycloak | If enabled it shows debug data |
| KC_HOSTNAME_STRICT | keycloak | |
| KC_HTTP_ENABLED | keycloak | |
| KC_DB_URL | keycloak | Keycloak's database URL |
| KC_DB_USERNAME | keycloak | Keycloak's database username |
| KC_DB_PASSWORD | keycloak | Keycloak's database password |
| JDBC_PARAMS | keycloak | Keycloak's database JDBC parameters |
| PGADMIN_DEFAULT_EMAIL | pgadmin | Email of default login account |
| PGADMIN_DEFAULT_PASSWORD | pgadmin | Password of default login account |
| SCRIPT_NAME | pgadmin | Relative path for pgadmin |

## How to build and run

In order to run this application you need to initialize the containers in a specific order. First create the database, keycloak and pgadmin (optional) and then run the keycloak-init service. After this you can start the Flask API and the nginx. **Before deploying the services make sure you have the necessary certifications for https and all environmental variables set.**

1. docker compose --env-file ./.env up -d postgres keycloak pgadmin
2. docker compose --env-file ./.env up keycloak-init
3. docker compose --env-file ./.env up flask nginx
