import json
import logging
from apiflask import Schema, abort
from apiflask.fields import Boolean, Integer, String, DateTime, Dict, List, URL
from apiflask.validators import Length, OneOf, Regexp, Range
from marshmallow import pre_load, fields, INCLUDE, validates, post_dump, ValidationError, validate, validates_schema

optional_basic_metadata = ['version', 'url', 'author', 'author_email', 'maintainer', 'maintainer_email', 'license_id', 'type', 'private']

class ResponseOK(Schema):
    url = URL(required=True)
    result = Dict(required=True)
    success = Boolean(required=True)

class ResponseError(Schema):
    url = URL(required=True)
    error = Dict(required=True)
    success = Boolean(required=True)

class ResponseAmbiguous(Schema):
    url = fields.URL(required=True)
    success = fields.Boolean(required=True)
    
    # Use fields that are conditionally required depending on success
    result = fields.Dict(required=False)
    error = fields.Dict(required=False)

    class Meta:
        unknown = INCLUDE  # This allows extra fields not explicitly defined in the schema

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, data):
        """
        Custom validation to ensure either 'result' or 'error' is present
        based on the 'success' value.
        """
        if data.get('success'):
            if not data.get('result'):
                raise ValueError("'result' field is required when success is True.")
        else:
            if not data.get('error'):
                raise ValueError("'error' field is required when success is False.")
        return data

class Identifier(Schema):
    id = String(required=False, validate=Length(0, 64))

class PaginationParameters(Schema):
    limit = Integer(required=False)
    offset = Integer(required=False)

class ComputerQueryParameters(Schema):
    label = Integer(required=True)

class JobQueryPatameters(Schema):
    limit = Integer(required=False)
    offset = Integer(required=False)
    filter = String(required=True, validate=OneOf(["all", "recent"]))
    sort = String(required=True, validate=OneOf(["signed_at", "created_at"]))

class JobCountParameters(Schema):
    filter = String(required=True, validate=OneOf(["all", "recent"]))

class RolesInput(Schema):
    roles = List(String, required=True)

class GenericSearch(Schema):
    search = String(required=True)
    limit = String(required=False)
    offset = String(required=False)

class NewUser(Schema):
    username = String(required=True, validate=Length(3, 25))
    firstName = String(required=True, validate=Length(0, 100))
    lastName = String(required=True, validate=Length(0, 100))
    password = String(required=True, validate=Length(8, 25))
    enabled = Boolean(required=True)

class NewComputerRegistration(Schema):
    created_by = String(required=True, validate=Length(max=50))
    uuid_label = Integer(required=False, validate=Range(min=100))
    host_name = String(required=True, validate=Length(max=30))
    mac_address = String(
        required=True,
        validate=[
        Length(equal=17),
        Regexp(
                r'^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$',
                error="Invalid MAC address format (expecting XX:XX:XX:XX:XX:XX)."
            )
        ]
    )
    ipv4_address = String(
        required=True,
        validate=Regexp(
            r'^(25[0-5]|2[0-4]\d|[01]?\d?\d)\.'
            r'(25[0-5]|2[0-4]\d|[01]?\d?\d)\.'
            r'(25[0-5]|2[0-4]\d|[01]?\d?\d)\.'
            r'(25[0-5]|2[0-4]\d|[01]?\d?\d)$',
            error="Invalid IPv4 address"
        )
    )
    network = String(required=True, validate=Length(max=20))
    os = String(required=True, validate=Length(max=20))
    network_adapter = String(required=True, validate=Length(max=20))
    secseal = Integer(required=True)
    make = String(validate=Length(max=20))
    model = String(validate=Length(max=50))
    pc_serialnumber = String(validate=Length(max=50))
    net_adapter_serialnumber = String(validate=Length(max=50))
    user_name = String(validate=Length(max=50))
    yat = String(validate=Length(max=50))
    office_number = String(validate=Length(max=20))
    telephone = String(validate=Length(max=20))
    office_location = String(validate=Length(max=20))

class UpdatedComputer(Schema):
    created_by = String(required=True, validate=Length(max=50))
    uuid_label = Integer(required=False, validate=Range(min=100))
    host_name = String(required=True, validate=Length(max=30))
    mac_address = String(
        required=True,
        validate=[
        Length(equal=17),
        Regexp(
                r'^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$',
                error="Invalid MAC address format (expecting XX:XX:XX:XX:XX:XX)."
            )
        ]
    )
    ipv4_address = String(
        required=True,
        validate=Regexp(
            r'^(25[0-5]|2[0-4]\d|[01]?\d?\d)\.'
            r'(25[0-5]|2[0-4]\d|[01]?\d?\d)\.'
            r'(25[0-5]|2[0-4]\d|[01]?\d?\d)\.'
            r'(25[0-5]|2[0-4]\d|[01]?\d?\d)$',
            error="Invalid IPv4 address"
        )
    )
    network = String(required=True, validate=Length(max=20))
    os = String(required=True, validate=Length(max=20))
    network_adapter = String(required=True, validate=Length(max=20))
    secseal = Integer(required=True)
    make = String(validate=Length(max=20))
    model = String(validate=Length(max=50))
    pc_serialnumber = String(validate=Length(max=50))
    net_adapter_serialnumber = String(validate=Length(max=50))
    user_name = String(validate=Length(max=50))
    yat = String(validate=Length(max=50))
    office_number = String(validate=Length(max=20))
    telephone = String(validate=Length(max=20))
    office_location = String(validate=Length(max=20))


class NewEntry(Schema):
    uuid = Integer()
    uuid_label = Integer(required=True)
    created_by = String(required=True)
    created_at = DateTime()
    reason = String(required=True)
    status = String()
    signed_by = String()
    signed_at = DateTime()

class UpdatedEntry(Schema):
    created_by = String()
    created_at = DateTime()
    reason = String()
    status = String()
    signed_by = String()
    signed_at = DateTime()

class NewOperator(Schema):
    rank = String(required=True, validate=Length(max=100))
    lname = String(required=True, validate=Length(max=100))
    fname = String(required=True, validate=Length(max=100))

class UpdatedOperator(Schema):
    rank = String(required=False, validate=Length(max=100))
    lname = String(required=False, validate=Length(max=100))
    fname = String(required=False, validate=Length(max=100))

class NewTicket(Schema):
    created_by = String(required=True, validate=Length(max=100))
    priority = String(required=True)
    division = String(required=False, validate=Length(0, 30))
    office_number = String(required=False, validate=Length(0, 30))
    phone = String(required=False, validate=Length(0, 10))
    client_name = String(required=False, validate=Length(0, 100))
    title = String(required=True, validate=Length(0, 100))
    descr = String(required=False, validate=Length(0, 500))

class UpdatedTicket(Schema):
    priority = String(required=True)
    division = String(required=False, validate=Length(0, 30))
    office_number = String(required=False, validate=Length(0, 30))
    phone = String(required=False, validate=Length(0, 10))
    status= String(required=False, validate=Length(0, 20))
    client_name = String(required=False, validate=Length(0, 100))
    descr = String(required=False, validate=Length(0, 500))

class TicketSearchParameters(Schema):
    limit = Integer(required=False)
    offset = Integer(required=False)
    status = fields.List(
        fields.Str(
            validate=validate.OneOf(["open", "closed", "in-progress", "awaiting"])
        ),
        required=False
    )

class ActivationInput(Schema):
    id = String(required=True, validate=Length(0, 50))

class UpdatedUser(Schema):
    firstName = String(required=False, validate=Length(0, 100))
    lastName = String(required=False, validate=Length(0, 100))
    enabled = Boolean(required=False)

class UserRole(Schema):
    id = String(required=True, validate=Length(0, 50))
    username = String(required=True, validate=Length(0, 50))
    role = String(required=True, validate=OneOf(['admin', 'Helpdesk', 'GPolicy']))

class NewToken(Schema):
    username = String(required=True, validate=Length(0, 50))
    password = String(required=True, validate=Length(0, 50))

class RefreshToken(Schema):
    refresh_token = String(required=True)
