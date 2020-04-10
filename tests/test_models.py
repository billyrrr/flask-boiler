from collections import OrderedDict

import pytest

from flask_boiler import schema
from flask_boiler.models import ModelBase
from flask_boiler.models import base
from flask_boiler.attributes import attribute


class G(ModelBase):
    i = attribute.AttributeBase()


def test__collect_attrs():
    assert isinstance(G.i, attribute.AttributeBase)

    assert list(base._collect_attrs(G)) == [("i", G.i)]


def test__schema_cls_from_attributed_class():
    res = base._schema_cls_from_attributed_class(G)

    assert isinstance(res, schema.Schema.__class__)
    schema_obj: schema.Schema = res()
    assert isinstance(schema_obj.fields, OrderedDict)

    desc = "OrderedDict([('obj_type', <fields.Function(" \
           "default=<marshmallow.missing>, attribute='obj_type', " \
           "validate=None, required=False, load_only=False, dump_only=False, " \
           "missing=<marshmallow.missing>, allow_none=False, " \
           "error_messages={'required': 'Missing data for required field.', " \
           "'null': 'Field may not be null.', 'validator_failed': 'Invalid " \
           "value.'})>), ('doc_id', <fields.String(" \
           "default=<marshmallow.missing>, attribute='doc_id', " \
           "validate=None, required=False, load_only=False, dump_only=True, " \
           "missing=<class 'str'>, allow_none=False, error_messages={" \
           "'required': 'Missing data for required field.', 'null': 'Field " \
           "may not be null.', 'validator_failed': 'Invalid value.', " \
           "'invalid': 'Not a valid string.', 'invalid_utf8': 'Not a valid " \
           "utf-8 string.'})>), ('doc_ref', <fields.String(" \
           "default=<marshmallow.missing>, attribute='doc_ref_str', " \
           "validate=None, required=False, load_only=False, dump_only=True, " \
           "missing=<class 'str'>, allow_none=False, error_messages={" \
           "'required': 'Missing data for required field.', 'null': 'Field " \
           "may not be null.', 'validator_failed': 'Invalid value.', " \
           "'invalid': 'Not a valid string.', 'invalid_utf8': 'Not a valid " \
           "utf-8 string.'})>), ('_remainder', <fields.Remainder(" \
           "default=<marshmallow.missing>, attribute='_remainder', " \
           "validate=None, required=False, load_only=False, dump_only=False, " \
           "missing=<marshmallow.missing>, allow_none=False, " \
           "error_messages={'required': 'Missing data for required field.', " \
           "'null': 'Field may not be null.', 'validator_failed': 'Invalid " \
           "value.', 'invalid': 'Not a valid mapping type.'})>), ('i', " \
           "<fields.Field(default=<marshmallow.missing>, attribute='i', " \
           "validate=None, required=False, load_only=False, dump_only=False, " \
           "missing=None, allow_none=True, error_messages={'required': " \
           "'Missing data for required field.', 'null': 'Field may not be " \
           "null.', 'validator_failed': 'Invalid value.'})>)]) "
    assert str(schema_obj.fields) == desc
