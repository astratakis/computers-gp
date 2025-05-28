import flask
import requests
import json
import re
import sys
import psycopg2
import os
import uuid
import os
import urllib
import time

#for keycloak integration with the api
from requests.models import Response
import logging
from auth import auth, security_doc, token_active

from psycopg2.extras import RealDictCursor
from flask import request, jsonify, current_app, redirect, session, url_for
from apiflask import APIFlask
from apiflask.fields import Dict, Nested

from datetime import datetime as datetime
from datetime import date

# Auxiliary custom functions & SQL query templates for ranking
#import utils
#import sql_utils

# Input schemata for validating several API requests
import schema

START_TIME = time.time()

#################### BLUEPRINT IMPORTS #####################
# Import the blueprints for the logical parts of the API

from routes.users import users_bp
from routes.frontend import frontend_bp
from routes.computers import computers_bp
from routes.entries import entries_bp
from routes.operators import operators_bp
from routes.tickets import tickets_bp
from routes.health import health_bp

############################################################

# Create an instance of this API; by default, its OpenAPI-compliant specification will be generated under folder /specs
app = APIFlask(__name__, spec_path='/specs', docs_path ='/docs')

app.secret_key = 'secretkey123'

app.config.from_prefixed_env()

################## BLUEPRINT REGISTRATION ##################

# Blueprints are used to split the API into logical parts, 
# such as User Management, Catalog Management,
# Workflow/Execution management etc.

app.register_blueprint(users_bp, url_prefix='/api/v1/users')
app.register_blueprint(frontend_bp, url_prefix='/')
app.register_blueprint(computers_bp, url_prefix='/api/v1/computers')
app.register_blueprint(entries_bp, url_prefix='/api/v1/entries')
app.register_blueprint(operators_bp, url_prefix='/api/v1/operators')
app.register_blueprint(tickets_bp, url_prefix='/api/v1/tickets/')
app.register_blueprint(health_bp, url_prefix='/api/v1/health')
############################################################

def main(app):

    app.config['settings'] = {
        'FLASK_RUN_HOST': os.getenv('FLASK_RUN_HOST', '0.0.0.0'),
        'FLASK_RUN_PORT': os.getenv('FLASK_RUN_PORT', '80'),
        'FLASK_DEBUG': os.getenv('FLASK_DEBUG', 'True') == 'True',

        'API_TITLE': os.getenv('API_TITLE', 'Computers GP'),
        'API_VERSION': os.getenv('API_VERSION', '1.0.0'),
        'SPEC_FORMAT': os.getenv('API_SPEC_FORMAT', 'json'),

        'AUTO_SERVERS': os.getenv('API_AUTO_SERVERS', 'True') == 'True',
        'AUTO_TAGS': os.getenv('API_AUTO_TAGS', 'False') == 'True',
        'AUTO_OPERATION_SUMMARY': os.getenv('API_AUTO_OPERATION_SUMMARY', 'True') == 'True',
        'AUTO_OPERATION_DESCRIPTION': os.getenv('API_AUTO_OPERATION_DESCRIPTION', 'True') == 'True',

        'dbname': os.getenv('POSTGRES_DB', '<DB-NAME>'),
        'dbuser': os.getenv('POSTGRES_USER', '<DB-USERNAME>'),
        'dbpass': os.getenv('POSTGRES_PASSWORD', '<DB-PASSWORD>'),
        'dbhost': os.getenv('POSTGRES_HOST', '<DB-HOST>'),
        'dbport': os.getenv('POSTGRES_PORT', '5432'),

        'KEYCLOAK_URL': os.getenv('KEYCLOAK_URL', 'http://keycloak:8080'),
        'KEYCLOAK_CLIENT_ID': os.getenv('KEYCLOAK_CLIENT_ID', 'stelar'),
        'KEYCLOAK_CLIENT_SECRET': os.getenv('KEYCLOAK_CLIENT_SECRET', 'none'),
        'REALM_NAME': os.getenv('REALM_NAME','master')
    }

    secret_file = open("/usr/shared/client-secret.txt", "r")
    client_secret = secret_file.read()
    app.config['settings']['KEYCLOAK_CLIENT_SECRET'] = client_secret

    print('This is the client secret:', client_secret)

    # Apply configuration settings for this API
    app.title = app.config['settings']['API_TITLE']
    app.version = app.config['settings']['API_VERSION']
    app.config['SECURITY_SCHEMES'] = {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT'
        }
    }  

# This entry point is used with gunicorn -b -w ....
def create_app():
    main(app)
    # Return the application instance so that gunicorn can run it.
    return app