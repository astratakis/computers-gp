from flask import request
from apiflask import APIBlueprint
from auth import security_doc, token_active
from sqlalchemy.orm import Session
import logging 
import schema
from db.crud import operators_db
from db.db_schemas import OperatorSchema
from db.database import database_exception_handler

"""
    This .py file contains the endpoints attached to the blueprint
    responsible for all operations related to the database management
    of all helpdesk operators

    Follows the REST logic.
"""

logging.basicConfig(level=logging.DEBUG)

# The users operations blueprint for all operations related to the lifecycle of a user
operators_bp = APIBlueprint('operators_blueprint', __name__, tag={'name':'Helpdesk Operators Management','description':'Operations related to management of helpdesk members (CRUD)'})

@operators_bp.route('/', methods=['GET'])
@operators_bp.doc(tags=['Helpdesk Operators Management'], security=security_doc)
@operators_bp.output(schema.ResponseAmbiguous, status_code=200, example={"result":{"count":3,"operators":[{"fname":"ΑΝΔΡΕΑΣ","id":13,"lname":"ΣΤΡΑΤΑΚΗΣ","rank":"ΣΤΡ"},{"fname":"ΑΛΛΟΣ","id":14,"lname":"ΚΑΠΟΙΟΣ","rank":"ΣΤΡ"},{"fname":"BILL","id":15,"lname":"SMITH","rank":"CEO"}]},"success":True,"url":"http://192.168.1.86:3000/api/v1/operators/"})
@token_active
@database_exception_handler
def get_operators(db: Session):
    """
        Returns a JSON of all helpdesk operators. Requires active token.

        Returns:
            - dict():  The JSON containing the operators
    """

    operators = operators_db.read_all_operators(db=db)

    return {
        'url': request.url,
        'result':  { 
            'operators': operators,
            'count': len(operators)
        },
        'success': True
    }, 200

@operators_bp.route('/<id>', methods=['GET'])
@operators_bp.doc(tags=['Helpdesk Operators Management'], security=security_doc)
@operators_bp.output(schema.ResponseAmbiguous, status_code=200, example={"result":{"operator":{"fname":"BILL","id":15,"lname":"SMITH","rank":"CEO"}},"success":True,"url":"http://192.168.1.86:3000/api/v1/operators/15"})
@token_active
@database_exception_handler
def get_operator_by_id(db: Session, id: str):
    """
        Returns a JSON of a specific helpdesk operator (id). Requires active token.

        Returns:
            - dict():  The JSON containing the operator
    """

    operator = operators_db.read_operator(db=db, operator_id=int(id))

    return {
        'url': request.url,
        'result':  { 
            'operator': operator
        },
        'success': True
    }, 200

@operators_bp.route('/', methods=['POST'])
@operators_bp.doc(tags=['Helpdesk Operators Management'], security=security_doc)
@operators_bp.input(schema.NewOperator, location='json')
@operators_bp.output(schema.ResponseAmbiguous, status_code=200, example={"result":{"id":16},"success":True,"url":"http://192.168.1.86:3000/api/v1/operators/"})
@token_active
@database_exception_handler
def post_operator(db: Session, json_data: dict):
    """
        Creates a new helpdesk operator. Requires active token.

        Returns:
            - dict():  The JSON containing the status
    """

    operator = OperatorSchema.model_validate(json_data)
    id = operators_db.create_operator(db=db, operator=operator)

    return {
        'url': request.url,
        'result':  { 
            'id': id
        },
        'success': True
    }, 200

@operators_bp.route('/<id>', methods=['PATCH'])
@operators_bp.doc(tags=['Helpdesk Operators Management'], security=security_doc)
@operators_bp.input(schema.UpdatedOperator, location='json')
@operators_bp.output(schema.ResponseAmbiguous, status_code=200, example={"result":{"affected":1},"success":True,"url":"http://192.168.1.86:3000/api/v1/operators/15"})
@token_active
@database_exception_handler
def patch_operator(db: Session, id: str, json_data: dict):
    """
        Updates an existing helpdesk operator. Requires active token.

        Returns:
            - dict():  The JSON containing the status
    """
    if json_data == {}:
        raise ValueError("Expected a json, got nothing")

    updated_operator = OperatorSchema.model_validate(json_data)
    affected = operators_db.update_operator(db=db, operator_id=int(id), new_data=updated_operator)

    return {
        'url': request.url,
        'result':  { 
            'affected': affected
        },
        'success': True
    }, 200

@operators_bp.route('/<id>', methods=['DELETE'])
@operators_bp.doc(tags=['Helpdesk Operators Management'], security=security_doc)
@operators_bp.output(schema.ResponseAmbiguous, status_code=200, example={"result":{"affected":1},"success":True,"url":"http://192.168.1.86:3000/api/v1/operators/15"})
@token_active
@database_exception_handler
def delete_operator(db: Session, id: str):
    """
        Deletes an existing helpdesk operator. Requires active token.

        Returns:
            - dict():  The JSON containing the status
    """
    affected = operators_db.delete_operator(db=db, operator_id=int(id))

    return {
        'url': request.url,
        'result':  { 
            'affected': affected
        },
        'success': True
    }, 200
