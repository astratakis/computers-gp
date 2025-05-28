from flask import request
from apiflask import APIBlueprint
from auth import security_doc, token_active
from sqlalchemy.orm import Session
import logging 
import schema
from db.crud import tickets_db
from db.db_schemas import TicketSchema
from db.database import database_exception_handler

"""
    This .py file contains the endpoints attached to the blueprint
    responsible for all operations related to the database management
    of all tickets

    Follows the REST logic.
"""

logging.basicConfig(level=logging.DEBUG)

tickets_bp = APIBlueprint('tickets_blueprint', __name__, tag={'name':'Ticket Management','description':'Operations related to management of ticketing (CRUD)'})

@tickets_bp.route('/', methods=['GET'])
@tickets_bp.doc(tags=['Ticket Management'], security=security_doc)
@tickets_bp.input(schema.TicketSearchParameters, location='query')
@tickets_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_tickets(db: Session, query_data: dict):
    """
        Reads all tickets. Requires active token.

        Returns:
            - dict():  The JSON containing the status
    """

    limit = query_data.get("limit", 0)
    offset = query_data.get("offset", 0)
    status = query_data.get("status", [])
    
    tickets = tickets_db.read_all_tickets(db=db, offset=int(offset), limit=int(limit), status=status)

    return {
        'url': request.url,
        'result': {
            "count": len(tickets),
            "tickets": tickets
        },
        'success': True
    }, 200

@tickets_bp.route('/<ticket_id>', methods=['GET'])
@tickets_bp.doc(tags=['Ticket Management'], security=security_doc)
@tickets_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def get_ticket_by_id(db: Session, ticket_id: str):

    ticket = tickets_db.read_ticket(db=db, ticket_id=int(ticket_id))

    return {
        'url': request.url,
        'result': {
            "ticket": ticket
        },
        'success': True
    }, 200


@tickets_bp.route('/<ticket_id>', methods=['PATCH'])
@tickets_bp.doc(tags=['Ticket Management'], security=security_doc)
@tickets_bp.input(schema.UpdatedTicket, location='json')
@tickets_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def patch_ticket_by_id(db: Session, ticket_id: str, json_data: dict):

    logging.debug(json_data)

    affected = tickets_db.update_ticket(db=db, ticket_id=int(ticket_id), values=json_data)

    return {
        'url': request.url,
        'result': {
            "affected": affected
        },
        'success': True
    }, 200

@tickets_bp.route('/<ticket_id>', methods=['DELETE'])
@tickets_bp.doc(tags=['Ticket Management'], security=security_doc)
@tickets_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def delete_ticket_by_id(db: Session, ticket_id: str):

    affected = tickets_db.delete_ticket(db=db, ticket_id=int(ticket_id))

    return {
        'url': request.url,
        'result': {
            "affected": affected
        },
        'success': True
    }, 200


@tickets_bp.route('/', methods=['POST'])
@tickets_bp.doc(tags=['Ticket Management'], security=security_doc)
@tickets_bp.input(schema.NewTicket, location='json')
@tickets_bp.output(schema.ResponseAmbiguous, status_code=200)
@token_active
@database_exception_handler
def post_ticket(db: Session, json_data: dict):
    """
        Creates a new ticket. Requires active token.

        Returns:
            - dict():  The JSON containing the status
    """

    ticket = TicketSchema.model_validate(json_data)
    id = tickets_db.create_ticket(db=db, ticket=ticket)

    return {
        'url': request.url,
        'result': {
            "id": id
        },
        'success': True
    }, 200


