from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import insert, update, delete
from db.models import Operator
from db.db_schemas import OperatorSchema
from typing import List

import logging

def create_operator(db: Session, operator: OperatorSchema) -> int:
    stmt = insert(Operator).values(**operator.model_dump(exclude={"id"})).returning(Operator.id)
    result = db.execute(stmt).scalar_one()
    db.commit()
    return result

def read_operator(db: Session, operator_id: int) -> OperatorSchema:
    stmt = select(Operator).where(Operator.id == operator_id)
    result = db.execute(stmt).scalar_one_or_none()
    if result is None:
        raise AttributeError(f"Operator with id={operator_id} was not found...")
    return OperatorSchema(**result.__dict__).model_dump()

def read_all_operators(db: Session) -> List[OperatorSchema]:
    stmt = select(Operator).order_by(Operator.id.asc())
    result = db.execute(stmt).scalars().all()
    return [OperatorSchema(**operator.__dict__).model_dump() for operator in result]

def update_operator(db: Session, operator_id: int, new_data: OperatorSchema) -> int:
    stmt = update(Operator).where(Operator.id == operator_id).values(**new_data.model_dump(exclude_none=True, exclude={"id"}))
    result = db.execute(stmt).rowcount
    db.commit()
    return result

def delete_operator(db: Session, operator_id: int) -> int:
    stmt = delete(Operator).where(Operator.id == operator_id)
    result = db.execute(stmt).rowcount
    db.commit()
    return result