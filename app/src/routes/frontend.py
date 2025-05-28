from flask import request, jsonify, current_app, url_for, render_template, url_for, redirect, session, flash
from apiflask import APIBlueprint
import requests
from auth import auth, security_doc, admin_required, token_active
# Auxiliary custom functions & SQL query templates for ranking
#import utils
import logging 
# Input schema for validating and structuring several API requests
import schema
import kutils
from functools import wraps

from db.database import *
from db.models import *
from db.db_schemas import *
import logging
import time
from server import START_TIME
from db.crud.operators_db import read_all_operators
from db.crud.computers_db import generate_next_uuid_label, generate_next_hostname
from db.crud.tickets_db import count_open
from db.crud.entries_db import count_all_jobs
from db.database import database_exception_handler
from sqlalchemy.orm import Session

def session_required(f):
    """
    Custom decorator to check if the session is active and the token is valid.
    If the session is invalid or token is expired, redirect to login with a default message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Retrieve token from session
        access_token = session.get('access_token')

        # If token doesn't exist or is invalid, clear session and redirect to login with a message
        if not access_token or not kutils.introspect_token(access_token):
            
            keycloak_openid = kutils.initialize_keycloak_openid()
            # Revoke refresh token to log out
            try:
                keycloak_openid.logout(session['refresh_token'])
            except Exception as e:
                pass

            session.clear()
            # Clear local session and redirect to the login page
            flash("Session Expired, Please Login Again","warning") 
            return redirect(url_for('frontend_blueprint.login_page', next=request.url))

        # If token is valid, continue with the requested function
        return f(*args, **kwargs)
    
    return decorated_function

"""
    This .py file contains the endpoints attached to the blueprint
    responsible for all operations related to the lifecycle of
    users in the ecosystem.

    Follows the REST logic.
"""

logging.basicConfig(level=logging.DEBUG)

frontend_bp = APIBlueprint('frontend_blueprint', __name__, enable_openapi=False)

@frontend_bp.route("/login", methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template("sign-in.html")
    elif request.method == 'POST':
        try:
            username = request.form.get("username")
            password = request.form.get("password")

            print('username:', username, 'password:', password)

            token = kutils.get_token(username, password)

            session['access_token'] = token['access_token']
            session['refresh_token'] = token['refresh_token']

            return redirect(url_for('frontend_blueprint.home_page'))

        except:
            
            return redirect(url_for('frontend_blueprint.login_page'))
        
@frontend_bp.route("/logout", methods=['POST'])
def logout():
        
    keycloak_openid = kutils.initialize_keycloak_openid()
    # Revoke refresh token to log out
    try:
        keycloak_openid.logout(session['refresh_token'])
    except Exception as e:
        pass

    session.clear()
    return redirect(url_for('frontend_blueprint.login_page'))

@frontend_bp.route("/", methods=['GET'])
@session_required
@database_exception_handler
def home_page(db: Session):
    user_data = kutils.load_user_metadata()
    uptime_seconds = int(time.time() - START_TIME)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60

    uptime_str = f"{days} days {hours} hours {minutes} mins"

    open_tickets_count = count_open(db=db)
    open_jobs_count = count_all_jobs(db=db, filter='recent')

    return render_template("home.html", open_tickets_count=open_tickets_count, open_jobs_count=open_jobs_count,
                            role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), 
                            fullname=user_data.get("fullname", "Undefined"), uptime=uptime_str)

@frontend_bp.route("/computers", methods=['GET'])
@session_required
def computers_page():
    user_data = kutils.load_user_metadata()
    return render_template("computers.html", role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), fullname=user_data.get("fullname", "Undefined"))

@frontend_bp.route("/computers/new", methods=['GET'])
@session_required
@database_exception_handler
def new_computer_page(db: Session):
    user_data = kutils.load_user_metadata()
    operators_list = read_all_operators(db=db)

    operators = []
    for element in operators_list:
        operators.append({'id': element['id'], 'name': str(element['rank'] + " " + element['lname'] + " " + element['fname'])})

    next_label = generate_next_uuid_label(db=db)
    next_hostname = generate_next_hostname(db=db)

    return render_template("new-computer.html", next_label=next_label, next_hostname=next_hostname, operators=operators, role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), fullname=user_data.get("fullname", "Undefined"))

@frontend_bp.route("/computers/edit/<uuid_label>", methods=['GET'])
@session_required
@database_exception_handler
def edit_computer_page(db: Session, uuid_label: str):
    user_data = kutils.load_user_metadata()
    operators_list = read_all_operators(db=db)

    operators = []
    for element in operators_list:
        operators.append({'id': element['id'], 'name': str(element['rank'] + " " + element['lname'] + " " + element['fname'])})

    return render_template("edit-computer.html", operators=operators, role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), fullname=user_data.get("fullname", "Undefined"))


@frontend_bp.route("/computers/<label>", methods=['GET'])
@session_required
def specific_computer_page(label: str):
    user_data = kutils.load_user_metadata()
    return render_template("datagrid.html", uuid_label=label, role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), fullname=user_data.get("fullname", "Undefined"))

@frontend_bp.route("/jobs", methods=['GET'])
@session_required
def jobs_page():
    user_data = kutils.load_user_metadata()
    return render_template("jobs.html", role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), fullname=user_data.get("fullname", "Undefined"))

@frontend_bp.route("/tickets", methods=['GET'])
@session_required
def tickets_page():
    user_data = kutils.load_user_metadata()
    return render_template("tickets.html", role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), fullname=user_data.get("fullname", "Undefined"))

@frontend_bp.route("/tickets/new", methods=['GET'])
@session_required
@database_exception_handler
def new_ticket_page(db: Session):
    user_data = kutils.load_user_metadata()
    operators_list = read_all_operators(db=db)

    operators = []
    for element in operators_list:
        operators.append({'id': element['id'], 'name': str(element['rank'] + " " + element['lname'] + " " + element['fname'])})

    return render_template("new-ticket.html", operators=operators, role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), fullname=user_data.get("fullname", "Undefined"))

@frontend_bp.route("/tickets/<ticket_id>", methods=['GET'])
@session_required
@database_exception_handler
def ticket_page(db: Session, ticket_id: str):
    user_data = kutils.load_user_metadata()
    operators_list = read_all_operators(db=db)

    operators = []
    for element in operators_list:
        operators.append({'id': element['id'], 'name': str(element['rank'] + " " + element['lname'] + " " + element['fname'])})

    return render_template("specific-ticket.html", operators=operators, role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), fullname=user_data.get("fullname", "Undefined"))

@frontend_bp.route("/operators", methods=['GET'])
@session_required
def operators_page():
    user_data = kutils.load_user_metadata()
    return render_template("operators.html", role=user_data.get("role", "Undefined"), username=user_data.get("username", "undefined"), fullname=user_data.get("fullname", "Undefined"))

@frontend_bp.route("/403", methods=['GET'])
def auth_error():
    custom_message = request.args.get('message', default="You are not authorized to enter this page...")
    return render_template('error-auth.html', msg=custom_message), 403
