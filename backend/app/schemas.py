from marshmallow import Schema, fields, validate

from .models import Role


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1, max=128))


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Email(dump_only=True)
    name = fields.String(dump_only=True)
    role = fields.Enum(Role, by_value=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)