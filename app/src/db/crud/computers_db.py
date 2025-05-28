from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import insert, update, delete, func, or_, cast, String, Integer
from db.models import Computer, Entry
from typing import List
from db.db_schemas import ComputerSchema, EntrySchema

def generate_next_uuid_label(db: Session) -> int:
    stmt = select(func.max(Computer.uuid_label))
    result = db.execute(stmt).scalar_one_or_none()
    return -1 if result is None else result + 1

def generate_next_hostname(db: Session) -> int:
    stmt = select(Computer.host_name).where(
        Computer.host_name.like('HOST-%')
    ).order_by(Computer.host_name.desc()).limit(1)
    max_number = db.execute(stmt).scalar_one_or_none()
    if max_number is not None:
        max_number = int(max_number.split('-')[1])
    else:
        max_number = 0
    next_number = max_number + 1
    return f"HOST-{next_number:05d}"

def count_computers(db: Session) -> int:

    stmt = select(func.count()).select_from(Computer)
    result = db.execute(stmt).scalar()
    return result

def read_all_computers(db: Session, offset: int = 0, limit: int = 0) -> List[ComputerSchema]:
    
    stmt = select(Computer).offset(offset).limit(limit=(limit if limit > 0 else None)).order_by(Computer.uuid_label.desc())
    result = db.execute(stmt).scalars().all()
    return [ComputerSchema(**computer.__dict__).model_dump() for computer in result]

def read_computer_classes(db: Session) -> dict:

    stmt = select(Computer.network, func.count(Computer.network)).group_by(Computer.network)
    result = db.execute(stmt).all()
    return result

def read_computer(db: Session, host_name: str) -> ComputerSchema:
    
    stmt = select(Computer).where(Computer.host_name == host_name)
    result = db.execute(stmt).scalar_one_or_none()
    return ComputerSchema(**result.__dict__).model_dump() if result is not None else None

def read_computer_by_label(db: Session, uuid_label: int) -> ComputerSchema:
    
    stmt = select(Computer).where(Computer.uuid_label == uuid_label)
    result = db.execute(stmt).scalar_one_or_none()
    return ComputerSchema(**result.__dict__).model_dump() if result is not None else None


def create_computer(db: Session, computer: ComputerSchema, entry: EntrySchema) -> tuple[int, int]:
    stmt = insert(Computer).values(computer.model_dump(exclude_none=True)).returning(Computer.uuid_label)
    computer_id = db.execute(stmt).scalar_one()

    stmt = insert(Entry).values(entry.model_dump(exclude_none=True)).returning(Entry.uuid)
    entry_id = db.execute(stmt).scalar_one()

    db.commit()
    return computer_id, entry_id

def update_computer(db: Session, new_computer: ComputerSchema, uuid_label: int) -> int:
    stmt = update(Computer).where(Computer.uuid_label == uuid_label).values(new_computer.model_dump(exclude_none=True))
    result = db.execute(stmt).rowcount
    db.commit()
    return result

def delete_computer(db: Session, uuid_label: int = None, host_name: str = None) -> int:

    if uuid_label is not None:
        stmt = delete(Computer).where(Computer.uuid_label == uuid_label)
        result = db.execute(stmt).rowcount
        db.commit()
    elif host_name is not None:
        stmt = delete(Computer).where(Computer.host_name == host_name)
        result = db.execute(stmt).rowcount
        db.commit()
    else:
        raise ValueError("Either uuid_label or host_name must be provided")
    return result

def generic_search(db: Session, data: str, limit: int, offset: int) -> List[ComputerSchema]:
    like_pattern = f"%{data}%"
    
    stmt = select(Computer).where(
        or_(
            # Case-insensitive search on the hostname
            Computer.host_name.ilike(like_pattern),
            # Convert integer columns to strings and search for the substring
            cast(Computer.uuid_label, String).like(like_pattern),
            cast(Computer.secseal, String).like(like_pattern),

            Computer.ipv4_address.like(like_pattern),
            # Case-insensitive search on the MAC address
            func.replace(Computer.mac_address, ":", "").ilike(like_pattern)
        )
    ).order_by(Computer.uuid_label.desc()).limit(limit if limit > 0 else None).offset(offset)
    
    result = db.execute(stmt).scalars().all()
    return [ComputerSchema(**computer.__dict__).model_dump() for computer in result]

def count_searched(db: Session, data: str) -> int:
    like_pattern = f"%{data}%"
    
    stmt = select(func.count()).select_from(Computer).where(
        or_(
            # Case-insensitive search on the hostname
            Computer.host_name.ilike(like_pattern),
            # Convert integer columns to strings and search for the substring
            cast(Computer.uuid_label, String).like(like_pattern),
            cast(Computer.secseal, String).like(like_pattern),

            Computer.ipv4_address.like(like_pattern),
            # Case-insensitive search on the MAC address
            func.replace(Computer.mac_address, ":", "").ilike(like_pattern)
        )
    )
    
    result = db.execute(stmt).scalar_one()
    return result