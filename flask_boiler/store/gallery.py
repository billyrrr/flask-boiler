from typing import List
from flask_boiler.database import Reference, Snapshot
from flask_boiler.store.snapshot_container import SnapshotContainer
from flask_boiler.context import Context as CTX


class Gallery:

    def __init__(self):
        self.tasks = dict()  # TODO: Watch out for when (doc_ref, obj_type_super) and (doc_ref, obj_type_sub) are both in the set; the objects will be equivalent, but initialized twice under the current plan
        self.visited = set()
        self.container = SnapshotContainer()
        self.object_container = dict()
        self.save_tasks = dict()

    def insert(self, *, doc_ref, obj_type) -> None:
        """
        TODO: implement obj_type kwarg or toss it
        :param doc_ref:
        :param obj_type:
        :return:
        """
        if doc_ref in self.tasks or doc_ref in self.visited:
            return
        self.tasks[doc_ref] = obj_type
        self.visited.add(doc_ref)

    def save_later(self, obj, transaction=None, **kwargs):
        forward_kwargs = dict(kwargs, transaction=transaction)
        if obj.doc_ref not in self.save_tasks:
            self.save_tasks[obj.doc_ref] = (obj, forward_kwargs)
        else:
            # TODO: implement
            # TODO: add logic for checking changes
            pass

    def save(self):
        for _, (obj, kwargs) in self.save_tasks.items():
            d = obj._export_as_dict(**kwargs)
            snapshot = Snapshot(d)
            CTX.db.set(snapshot=snapshot, ref=obj.doc_ref, transaction=kwargs['transaction'])

    @staticmethod
    def _get_snapshots_with_listener(refs: List[Reference]):
        raise NotImplementedError
        # from flask_boiler.context import Context as CTX
        #
        # def cb(*args, **kwargs):
        #     print(f"{args} {kwargs}")
        # CTX.listener.from_refs(refs, cb=cb)


    @staticmethod
    def _get_snapshots_with_batch(transaction, **kwargs):
        """ needed because transactional wrapper uses specific argument
            ordering

        :param transaction:
        :param kwargs:
        :return:
        """
        from flask_boiler.context import Context as CTX
        return CTX.db.get_many(transaction=transaction, **kwargs)

    def refresh(self, transaction, get_snapshots=None):

        if get_snapshots is None:
            get_snapshots = self._get_snapshots_with_batch

        while len(self.tasks) != 0:

            refs = list()
            for doc_ref in self.tasks:
                refs.append(doc_ref)

            res = get_snapshots(refs=refs, transaction=transaction)
            for ref, doc in res:
                self.container.set(key=ref, val=doc)

                # for doc in res:
                obj_type = self.tasks[ref]
                del self.tasks[ref]
                instance = obj_type.from_snapshot(
                    ref=ref, snapshot=doc, _store=self)

                # d = doc.to_dict()
                # obj_cls = resolve_obj_cls(cls=obj_type, d=d)
                #
                # schema_obj = obj_cls.get_schema_obj()
                # d = schema_obj.load(d)
                # d = obj_cls._import_from_dict(d, transaction=transaction,
                #                               _store=self)
                #
                # instance = obj_cls.new(
                #     **d, transaction=transaction)
                self.object_container[ref] = instance

    def retrieve(self, *, doc_ref, obj_type):
        if doc_ref not in self.object_container:
            snapshot = self.container.get(key=doc_ref)
            self.object_container[doc_ref] = obj_type.from_snapshot(ref=doc_ref, snapshot=snapshot)
        return self.object_container[doc_ref]