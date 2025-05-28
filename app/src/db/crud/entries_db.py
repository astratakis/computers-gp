from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import insert, update, delete, or_, and_, func, text, cast, Date
from db.models import Entry, Computer
from typing import List
from flask import jsonify
from db.db_schemas import EntrySchema, JobSchema, PolicySchema, TrafficSchema

import logging

def count_all_jobs(db: Session, filter: str) -> int:

    if filter == "recent":

        stmt = select(func.count()).select_from(Entry).where(
            or_(
            # 1. Jobs that are not closed
            Entry.status == 'open',
            # 2. Jobs that are closed, but signed_at is within 24h
            and_(
                Entry.status == 'closed',
                Entry.signed_at >= func.now() - text("interval '24 hours'")
            )
            )
        )
    else:
        stmt = select(func.count()).select_from(Entry)
    
    result = db.execute(stmt).scalar_one()
    return result

def get_jobs(db: Session, limit: int, offset: int, filter: str, sort: str) -> List[EntrySchema]:

    if filter == "recent":

        stmt = select(Entry.uuid, Entry.uuid_label, Computer.host_name, Entry.created_by, Entry.created_at, Entry.signed_by, Entry.signed_at, Entry.status, Entry.reason).join(
            Computer, Entry.uuid_label == Computer.uuid_label
        ).where(
            or_(
            # 1. Jobs that are not closed
            Entry.status == 'open',
            # 2. Jobs that are closed, but signed_at is within 24h
            and_(
                Entry.status == 'closed',
                Entry.signed_at >= func.now() - text("interval '24 hours'")
            )
        )
        ).limit(
            limit=(limit if limit > 0 else None)
        ).offset(
            offset
        ).order_by(Entry.created_at.desc() if sort == "created_at" else Entry.signed_at.desc())
    
    else:
        stmt = select(Entry.uuid, Entry.uuid_label, Computer.host_name, Entry.created_by, Entry.created_at, Entry.signed_by, Entry.signed_at, Entry.status, Entry.reason).join(
            Computer, Entry.uuid_label == Computer.uuid_label
        ).limit(
            limit=(limit if limit > 0 else None)
        ).offset(
            offset
        ).order_by(Entry.created_at.desc() if sort == "created_at" else Entry.signed_at.desc())

    result = db.execute(stmt).all()
    return [JobSchema.model_validate(entry).model_dump() for entry in result]

def get_job_by_id(db: Session, id: int) -> PolicySchema:

    stmt = select(Entry.uuid_label, Computer.host_name, Computer.mac_address, Computer.ipv4_address, Computer.user_name, Computer.office_location, Computer.telephone).join(
        Computer, Entry.uuid_label == Computer.uuid_label
    ).where(
        Entry.uuid == id
    )

    result = db.execute(stmt).one()
    return PolicySchema.model_validate(result).model_dump()

def read_all_entries(db: Session, offset: int, limit: int) -> List[EntrySchema]:
    stmt = select(Entry).offset(offset).limit(limit=(limit if limit > 0 else None)).order_by(Entry.created_at.desc())
    result = db.execute(stmt).scalars().all()
    return [EntrySchema(**entry.__dict__).model_dump() for entry in result]
    
def read_all_entries_by_label(db: Session, uuid_label: int, offset: int = 0, limit: int = 0) -> List[EntrySchema]:

    stmt = select(Entry).where(Entry.uuid_label == uuid_label).offset(offset).limit(limit=(limit if limit > 0 else None)).order_by(Entry.created_at.desc())
    result = db.execute(stmt).scalars().all()
    return [EntrySchema(**entry.__dict__).model_dump() for entry in result]

def create_entry(db: Session, entry: EntrySchema) -> int:

    stmt = insert(Entry).values(entry.model_dump(exclude_none=True))
    result = db.execute(stmt).rowcount
    db.commit()

    return result

def update_entry(db: Session, entry: EntrySchema, entry_id: int) -> int:

    entry.signed_at = func.now()
    stmt = update(Entry).where(Entry.uuid == entry_id).values(entry.model_dump(exclude_none=True))

    logging.debug(stmt)
    result = db.execute(stmt).rowcount
    db.commit()

    return result

def delete_entry(db: Session, uuid: int) -> int:

    stmt = delete(Entry).where(Entry.uuid == uuid)
    result = db.execute(stmt).rowcount
    db.commit()
    
    return result

def get_traffic(db: Session) -> List[TrafficSchema]:

    # networks of interest
    NETWORKS = ["__S", "__A", "__D", "__T"]

    stmt = (
        select(
            cast(func.date_trunc('day', Entry.created_at), Date).label("date"),
            Computer.network.label("network"),
            func.count(Entry.uuid).label("total")
        )
        .join(Computer, Entry.uuid_label == Computer.uuid_label)
        .where(
            Computer.network.in_(NETWORKS),
            Entry.created_at >= func.now() - text("interval '40 days'")
        )
        .group_by(
            func.date_trunc('day', Entry.created_at),
            Computer.network
        )
        .order_by(
            func.date_trunc('day', Entry.created_at).asc(),
            Computer.network.asc()
        )
    )

    rows = db.execute(stmt).all()
    logging.error('=====================================')
    logging.error(rows)
    logging.error('=====================================')

    # Option A: Directly construct from row attributes
    traffic_list = []
    for row in rows:
        # row is something like (date=..., network=..., count=...)
        traffic_list.append(
            TrafficSchema(
                date=str(row.date),
                network=row.network,
                count=row.total
            )
        )
    return [traffic.model_dump() for traffic in traffic_list]
