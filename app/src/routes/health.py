from apiflask import APIBlueprint
from flask import request
import logging 
import schema
import time

import os

POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')

"""
    This .py file contains the endpoints attached to the blueprint
    responsible for all operations related to the database management
    of all the computers

    Follows the REST logic.
"""

logging.basicConfig(level=logging.DEBUG)

# The users operations blueprint for all operations related to the lifecycle of a user
health_bp = APIBlueprint('health_bp', __name__, tag={'name':'Health','description':'Operations related to the monitoring of the app'})

import requests
import psycopg2

@health_bp.route('/', methods=['GET'])
@health_bp.doc(tags=['Health'])
@health_bp.output(schema.ResponseAmbiguous, status_code=200, example={"result":{"keycloak":{"active":True,"time":8.2},"pgadmin":{"active":True,"time":25.9},"postgres":{"active":True,"time":23.7}},"success":True,"url":"http://pgadmin:80/login?next=/"})
def health():
    results = {}
    
    # Check Keycloak
    keycloak_response_time_start = time.perf_counter_ns()
    try:
        response = requests.get("http://keycloak:8080/auth/health")
        results['keycloak'] = response.status_code == 404
    except Exception:
        results['keycloak'] = False
    keycloak_response_time_end = time.perf_counter_ns()

    # Check pgadmin
    pgadmin_response_time_start = time.perf_counter_ns()
    try:
        response = requests.get("http://pgadmin:80")
        results['pgadmin'] = response.status_code == 200
    except Exception:
        results['pgadmin'] = False
    pgadmin_response_time_end = time.perf_counter_ns()

    # Check Postgres (using psycopg2)
    postgres_response_time_start = time.perf_counter_ns()
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB, user=POSTGRES_USER,
            host=POSTGRES_HOST, password=POSTGRES_PASSWORD
        )
        results['postgres'] = True
        conn.close()
    except Exception:
        results['postgres'] = False
    postgres_response_time_end = time.perf_counter_ns()

    return {
        "url": request.url,
        "success": True,
        "result": {
            "keycloak": {
                "active": results['keycloak'],
                "time": round((keycloak_response_time_end - keycloak_response_time_start) / 1000000, 1)
            },
            "pgadmin": {
                "active": results['pgadmin'],
                "time": round((pgadmin_response_time_end - pgadmin_response_time_start) / 1000000, 1)
            },
            "postgres": {
                "active": results['postgres'],
                "time": round((postgres_response_time_end - postgres_response_time_start) / 1000000, 1)
            }
        }
    }, 200
