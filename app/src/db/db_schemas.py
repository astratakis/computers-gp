from pydantic import BaseModel, field_validator, field_serializer
from typing import Optional
from datetime import datetime, date
import re

class OperatorSchema(BaseModel):
    id: Optional[int] = None
    rank: Optional[str] = None
    fname: Optional[str] = None
    lname: Optional[str] = None

    class Config:
        from_attributes = True

class ComputerSchema(BaseModel):
    uuid_label: Optional[int] = None
    host_name: str
    mac_address: str
    ipv4_address: Optional[str] = None
    network: str
    os: str
    network_adapter: str
    secseal: int
    make: Optional[str] = None
    model: Optional[str] = None
    pc_serialnumber: Optional[str] = None
    net_adapter_serialnumber: Optional[str] = None
    user_name: Optional[str] = None
    yat: Optional[str] = None
    office_number: Optional[str] = None
    telephone: Optional[str] = None
    office_location: Optional[str] = None

    class Config:
        from_attributes = True

class EntrySchema(BaseModel):

    uuid: Optional[int] = None
    uuid_label: Optional[int] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    signed_by: Optional[str] = None
    signed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TrafficSchema(BaseModel):
    date: str
    network: str
    count: int

    class Config:
        from_attributes = True

class JobSchema(BaseModel):

    uuid: int
    uuid_label: int
    host_name: str
    created_by: str
    created_at: datetime
    signed_by: Optional[str] = None
    signed_at: Optional[datetime] = None
    status: str
    reason: str

    class Config:
        from_attributes = True

class PolicySchema(BaseModel):

    uuid_label: int
    host_name: str
    mac_address: str
    ipv4_address: str
    user_name: Optional[str]
    office_location: Optional[str]
    telephone: Optional[str]

    class Config:
        from_attributes = True


class TicketSchema(BaseModel):

    id: Optional[int] = None
    created_by: str
    created_at: Optional[datetime] = None
    priority: str
    status: Optional[str] = None
    division : Optional[str] = None
    office_number: Optional[str] = None
    phone: Optional[str] = None
    client_name: Optional[str] = None
    descr: Optional[str] = None
    title: str
