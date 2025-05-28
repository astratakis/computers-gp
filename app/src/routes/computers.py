from flask import request
from apiflask import APIBlueprint
from auth import security_doc, token_active
from sqlalchemy.orm import Session
import logging 
import schema
from db.crud import computers_db
from db.db_schemas import ComputerSchema, EntrySchema
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
computers_bp = APIBlueprint('computers_blueprint', __name__, tag={'name':'Computer Management','description':'Operations related to management of computers (CRUD)'})

@computers_bp.route('/count', methods=['GET'])
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_computers_count(db: Session):
    """
        Returns:
            - dict():  The JSON containing the computers

        Args optionally:
            - limit: Maximum number of computers returned per request, if limit is 0 all computers are returned.
            - offset: Offset of the result by #offset computer.
    """
    
    count = computers_db.count_computers(db=db)
    
    return {
        'url': request.url,
        'result':  { 
            'count': count
        },
        'success': True
    }, 200

@computers_bp.route('/generic/count', methods=['GET'])
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.input(schema.GenericSearch, location='query')
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_searched_computers_count(db: Session, query_data: dict):
    """
        Returns:
            - dict():  The JSON containing the computers

        Args optionally:
            - limit: Maximum number of computers returned per request, if limit is 0 all computers are returned.
            - offset: Offset of the result by #offset computer.
    """

    data_to_search = query_data.get("search")
    
    count = computers_db.count_searched(db=db, data=data_to_search)
    
    return {
        'url': request.url,
        'result':  { 
            'count': count
        },
        'success': True
    }, 200

@computers_bp.route('/classes', methods=['GET'])
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_computer_classes(db: Session):
    """
        Returns:
            - dict():  The JSON containing the computers

        Args optionally:
            - limit: Maximum number of computers returned per request, if limit is 0 all computers are returned.
            - offset: Offset of the result by #offset computer.
    """
    
    output = computers_db.read_computer_classes(db=db)
    
    return {
        'url': request.url,
        'result':  output,
        'success': True
    }, 200


@computers_bp.route('/label/<uuid_label>', methods=['GET'])
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.input(schema.PaginationParameters, location='query')
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_computer_by_label(db: Session, uuid_label: str, query_data: dict):

    offset = query_data.get('offset', 0)
    limit = query_data.get('limit', 0)

    computer = computers_db.read_computer_by_label(db=db, uuid_label=int(uuid_label))

    if computer is None:
        raise ValueError(f"Computer with label {uuid_label} does not exist...")
    
    if offset < 0 or limit < 0:
        raise ValueError(f'Pagination paramteres offset and limit must be non negative...')

    entries = entries_db.read_all_entries_by_label(db=db, uuid_label=computer.get("uuid_label"), offset=offset, limit=limit)


    return {
        'url': request.url,
        'result':  { 
            'computer': computer,
            'entries': {
                'count': len(entries),
                'history': entries
            }
        },
        'success': True
    }, 200    

@computers_bp.route('/', methods=['GET'])
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.input(schema.PaginationParameters, location='query')
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_computers(db: Session, query_data: dict):
    """
        Returns:
            - dict():  The JSON containing the computers

        Args optionally:
            - limit: Maximum number of computers returned per request, if limit is 0 all computers are returned.
            - offset: Offset of the result by #offset computer.
    """
    
    offset = query_data.get('offset', 0)
    limit = query_data.get('limit', 0)

    if limit < 0 or offset < 0:
        raise ValueError('Pagination parameters limit and offset must be non negative...')
    
    computers = computers_db.read_all_computers(db=db, offset=offset, limit=limit)
    
    return {
        'url': request.url,
        'result':  { 
            'computers': computers,
            'count': len(computers)
        },
        'success': True
    }, 200

@computers_bp.route('/', methods=['POST'])
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.input(schema.NewComputerRegistration, location='json')
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def create_computer(db: Session, json_data: dict):
    """
        Creates a new computer and returns a JSON with it's information. Requires active token

        Returns:
            - dict():  The JSON containing the computer and it's entries
    """

    operator = json_data.get("created_by")
    uuid_label = json_data.get("uuid_label")
    json_data.pop("created_by")
    computer = ComputerSchema.model_validate(json_data)

    entry = EntrySchema.model_validate({
        "created_by": operator,
        "uuid_label": uuid_label,
        "reason": "Registration"
    })

    output = computers_db.create_computer(db=db, computer=computer, entry=entry)

    logging.debug(output)

    return {
        "url": request.url,
        "success": True,
        "result": {
            "computer": output[0],
            "entry": output[1]
        }
    }, 200

@computers_bp.route('/<host_name>', methods=['GET'], strict_slashes=False)
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.input(schema.PaginationParameters, location='query')
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_computer_by_hostname(db: Session, host_name: str, query_data: dict):
    """
        Returns a JSON of all the details of the computer with a specific hostname. It also returns a list of all entries tied to this computer. Requires active token. Supports pagination

        Returns:
            - dict():  The JSON containing the computer and it's entries
    """

    offset = query_data.get('offset', 0)
    limit = query_data.get('limit', 0)

    computer = computers_db.read_computer(db=db, host_name=host_name)

    if computer is None:
        raise ValueError(f"Computer with hostname {host_name} does not exist...")
    
    if offset < 0 or limit < 0:
        raise ValueError(f'Pagination paramteres offset and limit must be non negative...')

    entries = entries_db.read_all_entries_by_label(db=db, uuid_label=computer.get("uuid_label"), offset=offset, limit=limit)

    return {
        'url': request.url,
        'result':  { 
            'computer': computer,
            'entries': {
                'count': len(entries),
                'history': entries
            }
        },
        'success': True
    }, 200    

@computers_bp.route('/generic', methods=['GET'])
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.input(schema.GenericSearch, location='query')
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def generic_search(db: Session, query_data: dict):

    data_to_search = query_data.get("search")
    limit = query_data.get("limit", 0)
    offset = query_data.get("offset", 0)

    computers = computers_db.generic_search(db=db, data=data_to_search, limit=int(limit), offset=int(offset))

    return {
        'url': request.url,
        'result':  { 
            'computers': computers,
            'count': len(computers)
        },
        'success': True
    }, 200 

@computers_bp.route('/<uuid_label>', methods=['PATCH'])
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.input(schema.UpdatedComputer, location='json')
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def update_computer_by_hostname(db: Session, uuid_label: str, json_data: dict):
    """
        Updates the information of a computer. and Returns a JSON of the new data. Requires active token

        Returns:
            - dict():  The JSON containing the computer and it's entries
    """
    operator = json_data.get("created_by")
    uuid_label = json_data.get("uuid_label")
    json_data.pop("created_by")
    computer = ComputerSchema.model_validate(json_data)

    affected = computers_db.update_computer(db=db, uuid_label=uuid_label, new_computer=computer)

    return {
        "url": request.url,
        "success": True,
        "result": {
            "affected": affected
        }
    }, 200



@computers_bp.route('/<uuid_label>', methods=['DELETE'])
@computers_bp.doc(tags=['Computer Management'], security=security_doc)
@computers_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def delete_computer_by_label(db: Session, uuid_label: str):
    """
        Deletes a computer. Requires active token

        Returns:
            - dict():  The JSON containing the status of the process.
    """

    result = computers_db.delete_computer(db=db, uuid_label=uuid_label)

    return {
        "url": request.url,
        "success": True,
        "result": {
            "count": result
        }
    }, 200