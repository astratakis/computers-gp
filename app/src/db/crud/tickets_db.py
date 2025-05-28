from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import insert, update, delete, func
from db.models import Ticket
from db.db_schemas import TicketSchema
from typing import List
import logging

def count_open(db: Session) -> int:
    stmt = select(func.count(Ticket.id)).where(Ticket.status == "open")
    result = db.execute(stmt).scalar_one_or_none()
    return result if result is not None else 0

def create_ticket(db: Session, ticket: TicketSchema) -> int:
    stmt = insert(Ticket).values(ticket.model_dump(exclude_none=True, exclude={"id", "created_at"})).returning(Ticket.id)
    result = db.execute(stmt).scalar_one()
    db.commit()
    return result

def read_ticket(db: Session, ticket_id: int) -> TicketSchema:
    stmt = select(Ticket).where(Ticket.id == ticket_id)
    result = db.execute(stmt).scalar_one_or_none()
    if result is None:
        raise ValueError(f"Ticket with id={ticket_id} was not found...")
    return TicketSchema(**result.__dict__).model_dump()

def read_all_tickets(db: Session, offset: int, limit: int, status: list[str]) -> List[TicketSchema]:
    stmt = select(Ticket).where(Ticket.status.in_(status) if len(status) > 0 else True).offset(offset).limit(limit if limit > 0 else None).order_by(Ticket.created_at.desc())
    result = db.execute(stmt).scalars().all()
    return [TicketSchema(**ticket.__dict__).model_dump() for ticket in result]

def update_ticket(db: Session, ticket_id: int, values: dict) -> int:
    stmt = update(Ticket).where(Ticket.id == ticket_id).values(values)
    result = db.execute(stmt).rowcount
    db.commit()
    return result


def delete_ticket(db: Session, ticket_id) -> int:
    stmt = delete(Ticket).where(Ticket.id == ticket_id)
    result = db.execute(stmt).rowcount
    db.commit()
    return result