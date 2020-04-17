from google.cloud.firestore_v1 import Transaction

from flask_boiler.collection_mixin import CollectionMixin
from flask_boiler.firestore_object import FirestoreObject
from flask_boiler.query.query_mixin import QueryMixin
from flask_boiler.serializable import SerializableMeta
from flask_boiler.utils import random_id, doc_ref_from_str

from flask_boiler.schema import Schema


class PrimaryObjectMeta(SerializableMeta):

    def __new__(mcs, name, bases, attrs):
        klass = super().__new__(mcs, name, bases, attrs)
        if hasattr(klass, "Meta"):
            meta = klass.Meta
            if hasattr(meta, "collection_name"):
                klass._collection_name = meta.collection_name
        return klass


class PrimaryObject(FirestoreObject, QueryMixin, CollectionMixin,
                    metaclass=PrimaryObjectMeta):
    """
    Primary Object is placed in a collection in root directory only.
    the document will be stored in and accessed from
            self.collection.document(doc_id)

    """

    _collection_name = None

    @classmethod
    def get_schema_cls(cls):
        """ Returns schema_cls or the union of all schemas of subclasses.
                Should only be used on the root DomainModel. Does not
                cache the result.

        """
        d = dict()
        if super().get_schema_cls() is None:
            for child in cls._get_children():
                for key, val in child.get_schema_obj().fields.items():
                    field_cls = val.__class__

                    if key in d and d[key] != field_cls:
                        raise ValueError

                    d[key] = field_cls
            tmp_schema = Schema.from_dict(d)
            return tmp_schema
        else:
            return super().get_schema_cls()

    def __init__(self, doc_id=None, doc_ref=None, **kwargs):
        if doc_ref is None:
            doc_ref = self._doc_ref_from_id(doc_id=doc_id)
        super().__init__(doc_ref=doc_ref, **kwargs)

    @property
    def doc_id(self):
        """ Returns Document ID
        """
        return self.doc_ref.id

    @property
    def doc_ref(self):
        """ Returns Document Reference
        """
        if self._doc_ref is None:
            self._doc_ref = self.collection.document(random_id())
        return self._doc_ref

    random_id = random_id

    @classmethod
    def new(cls, doc_id=None, doc_ref=None, **kwargs):
        """ Creates an instance of object and assign a firestore reference
        with random id to the instance. This is similar to the use
        of "new" in Java. It is recommended that you use "new" to
        initialize an object, rather than the native initializer.
        Values are initialized based on the order that they are
        declared in the schema.

        :param: doc_id: Document ID
        :param: doc_ref: Document Reference
        :param allow_default: if set to False, an error will be
            raised if value is not provided for a field.
        :param kwargs: keyword arguments to pass to the class
            initializer.
        :return: the instance created
        """
        if doc_ref is None:
            if doc_id is None:
                doc_id = cls.random_id()
            doc_ref = cls._get_collection().document(doc_id)
        obj = super().new(doc_ref=doc_ref, **kwargs)
        return obj

    @classmethod
    def get(cls, *, doc_ref_str=None, doc_ref=None, doc_id=None,
            transaction: Transaction=None):
        """ Returns the instance from doc_id.

        :param doc_ref_str: DocumentReference path string
        :param doc_ref: DocumentReference
        :param doc_id: gets the instance from self.collection.document(doc_id)
        :param transaction: firestore transaction
        """

        if doc_ref_str is not None:
            doc_ref = doc_ref_from_str(doc_ref_str)

        if doc_ref is None:
            doc_ref = cls._get_collection().document(doc_id)

        return super().get(doc_ref=doc_ref, transaction=transaction)
