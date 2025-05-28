from flask import request
from apiflask import APIBlueprint
from auth import security_doc, token_active, gpolicy_required
from sqlalchemy.orm import Session
import logging 
import schema
from db.db_schemas import EntrySchema
from db.crud import entries_db
from db.database import database_exception_handler

"""
    This .py file contains the endpoints attached to the blueprint
    responsible for all operations related to the database management
    of all the computers

    Follows the REST logic.
"""

logging.basicConfig(level=logging.DEBUG)

# The users operations blueprint for all operations related to the lifecycle of a user
entries_bp = APIBlueprint('entries_blueprint', __name__, tag={'name':'Entry (History) Management','description':'Operations related to management of entries (CRUD)'})

@entries_bp.route('/', methods=['GET'])
@entries_bp.doc(tags=['Entry (History) Management'], security=security_doc)
@entries_bp.input(schema.PaginationParameters, location='query')
@entries_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def read_entries(db: Session, query_data: dict):
    """
        Returns a JSON of all entries (jobs). Requires active token. Supports pagination.

        Returns:
            - dict():  The JSON containing the computers
    """
    
    offset = query_data.get('offset', 0)
    limit = query_data.get('limit', 0)

    if limit < 0 or offset < 0:
        raise ValueError('Pagination parameters limit and offset must be non negative...')
    
    entries = entries_db.read_all_entries(db=db, offset=offset, limit=limit)
    
    return {
        'url': request.url,
        'result':  { 
            'entries': entries,
            'count': len(entries)
        },
        'success': True
    }, 200

@entries_bp.route('/jobs', methods=['GET'])
@entries_bp.doc(tags=['Entry (History) Management'], security=security_doc)
@entries_bp.input(schema.JobQueryPatameters, location='query')
@entries_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def read_jobs(db: Session, query_data: dict):
    """
        Returns a JSON of all jobs. Requires active token. Supports pagination.

        Returns:
            - dict():  The JSON containing the computers
    """

    limit = query_data.get('limit', 0)
    offset = query_data.get('offset', 0)
    filter = query_data.get('filter')
    sort = query_data.get('sort')
    
    jobs = entries_db.get_jobs(db=db, limit=limit, offset=offset, filter=filter, sort=sort)
        
    return {
        'url': request.url,
        'result':  { 
            'jobs': jobs,
            'count': len(jobs)
        },
        'success': True
    }, 200

@entries_bp.route('/policy/<uuid>', methods=['GET'])
@entries_bp.doc(tags=['Entry (History) Management'], security=security_doc)
@entries_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_policy_by_id(db: Session, uuid: str):
    """
        Returns a JSON of all jobs. Requires active token. Supports pagination.

        Returns:
            - dict():  The JSON containing the computers
    """
    
    policy = entries_db.get_job_by_id(db=db, id=int(uuid))
        
    return {
        'url': request.url,
        'result':  { 
            'policy': policy,
        },
        'success': True
    }, 200

@entries_bp.route('/jobs/count', methods=['GET'])
@entries_bp.doc(tags=['Entry (History) Management'], security=security_doc)
@entries_bp.input(schema.JobCountParameters, location='query')
@entries_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def count_jobs(db: Session, query_data: dict):
    """
        Returns a JSON of all jobs. Requires active token. Supports pagination.

        Returns:
            - dict():  The JSON containing the computers
    """
    
    filter = query_data.get('filter')

    count = entries_db.count_all_jobs(db=db, filter=filter)
    
    return {
        'url': request.url,
        'result':  { 
            'count': count
        },
        'success': True
    }, 200

@entries_bp.route('/', methods=['POST'])
@entries_bp.doc(tags=['Entry (History) Management'], security=security_doc)
@entries_bp.input(schema.NewEntry, location='json')
@entries_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def create_entry(db: Session, json_data: dict):

    entry = EntrySchema.model_validate(json_data)

    result = entries_db.create_entry(db=db, entry=entry)

    return {
        'url': request.url,
        'result': {
            'value': result
        },
        'success': True
    }, 200

@entries_bp.route('/<entry_id>', methods=['PATCH'])
@entries_bp.doc(tags=['Entry (History) Management'], security=security_doc)
@entries_bp.input(schema.UpdatedEntry, location='json')
@entries_bp.output(schema.ResponseAmbiguous, status_code=200)
@gpolicy_required
@database_exception_handler
def update_entry(db: Session, entry_id: str, json_data: dict):

    entry = EntrySchema.model_validate(json_data)

    result = entries_db.update_entry(db=db, entry=entry, entry_id=int(entry_id))

    return {
        'url': request.url,
        'result': {
            'value': result
        },
        'success': True
    }, 200

@entries_bp.route('/traffic', methods=['GET'])
@entries_bp.doc(tags=['Entry (History) Management'], security=security_doc)
@entries_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_traffic(db: Session):

    result = entries_db.get_traffic(db=db)

    return {
        'url': request.url,
        'result': {
            'hist': result,
            'length': len(result)
        },
        'success': True
    }, 200