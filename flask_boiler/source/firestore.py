from flask_boiler.source.base import Source


class FirestoreSource(Source):

    def __init__(self, query):
        """ Initializes a ViewMediator to declare protocols that
                are called when the results of a query change. Note that
                mediator.start must be called later.

        :param query: a listener will be attached to this query
        """
        super().__init__()
        self.query = query

    def start(self):
        self._register()

    def _register(self):
        from flask_boiler.context import Context as CTX
        CTX.listener.register(query=self.query, source=self)

    @classmethod
    def delta(cls, container):
        start = container._read_times[-2]
        end = container._read_times[-1]
        for key in container.d.keys():
            for snapshot in container.get_with_range(key, start, end):
                from flask_boiler.database import Snapshot
                prev: Snapshot = snapshot.prev
                cur: Snapshot = snapshot
                if not prev.exists:
                    yield ("on_create", key, cur)
                else:
                    yield ("on_update", key, cur)

    def _call(self, container):
        for func_name, ref, snapshot in self.delta(container):
            fname = self.protocol.fname_of(func_name)
            f = getattr(self.parent()(), fname)
            f(ref=ref, snapshot=snapshot)