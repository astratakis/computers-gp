from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Operator(Base):
    __tablename__ = 'operators'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    rank = Column(String, nullable=False)
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)

class Computer(Base):
    __tablename__ = 'computers'
    
    uuid_label = Column(Integer, primary_key=True, autoincrement=True, index=True)
    host_name = Column(String(50), unique=True, nullable=False)
    mac_address = Column(String(20), unique=True, nullable=False)
    ipv4_address = Column(String(20), unique=True, nullable=False)
    network = Column(String(20), nullable=False)
    os = Column(String(20), nullable=False)
    network_adapter = Column(String(20), nullable=False)
    secseal = Column(Integer, unique=True, nullable=False)
    make = Column(String(20))
    model = Column(String(50))
    pc_serialnumber = Column(String(50))
    net_adapter_serialnumber = Column(String(50))
    user_name = Column(String(100))
    yat = Column(String(100))
    office_number = Column(String(20))
    telephone = Column(String(20))
    office_location = Column(String(20))

class Entry(Base):
    __tablename__ = 'entries'

    uuid = Column(Integer, primary_key=True, autoincrement=True)
    uuid_label = Column(Integer, nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, default=func.current_timestamp(), nullable=False)
    reason = Column(String(100), nullable=False)
    status = Column(String(100), nullable=False)
    signed_by = Column(String(100))
    signed_at = Column(TIMESTAMP)

class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_by = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=func.current_timestamp(), nullable=False)
    status = Column(String, nullable=False, default='open')
    priority = Column(String, nullable=False)
    division = Column(String, nullable=True)
    office_number = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    client_name = Column(String, nullable=True)
    descr = Column(String, nullable=True)
    title = Column(String, nullable=False)
