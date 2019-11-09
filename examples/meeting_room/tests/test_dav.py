import time

from google.cloud.firestore_v1 import Watch, DocumentSnapshot, \
    DocumentReference

from examples.meeting_room.domain_models import Meeting, User
from examples.meeting_room.view_models import UserView
from examples.meeting_room.view_models.meeting_session import \
    MeetingSessionMutation, MeetingSessionMixin
from examples.meeting_room.view_models.user_view import UserViewMixin
from flask_boiler.mutation import Mutation
from flask_boiler.view import DocumentAsView
from flask_boiler.view_mediator_dav import ViewMediatorDAV
from ..views import meeting_session_ops
from flask_boiler import view_mediator
# Import the fixtures used by fixtures
from tests.fixtures import CTX, setup_app
from .fixtures import users, tickets, location, meeting
from flask_boiler.context import Context


class MeetingSessionDAV(MeetingSessionMixin, DocumentAsView):

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.get_from_meeting_id(*args, **kwargs)

    @classmethod
    def get_from_meeting_id(cls, meeting_id, once=False, user=None):
        doc_ref = user.doc_ref.collection(cls.__name__).document(meeting_id)
        return super().get_from_meeting_id(
            meeting_id, once=once, doc_ref=doc_ref)


class MeetingSessionViewMediatorDAV(ViewMediatorDAV):

    def __init__(self, *args, meeting_cls=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meeting_cls = meeting_cls

    def _listen_to_view_model(self, meeting_id, user_id):
        obj: MeetingSessionDAV = self.instances[(meeting_id, user_id)]

        def on_snapshot(snapshots, changes, timestamp):
            if len(snapshots) != 1:
                raise ValueError
            doc = snapshots[0]
            data = obj.diff(doc.to_dict())
            if data:
                self.mutation_cls.mutate_patch_one(obj=obj, data=data)

        watch = Watch.for_document(
            document_ref=obj.doc_ref,
            snapshot_callback=on_snapshot,
            snapshot_class_instance=DocumentSnapshot,
            reference_class_instance=DocumentReference)

    def start(self):
        self.generate_entries()
        for meeting_id, user_id in self.instances:
            self._listen_to_view_model(
                meeting_id=meeting_id,
                user_id=user_id)

    def generate_entries(self):

        meetings = self.meeting_cls.all()
        for meeting in meetings:
            assert isinstance(meeting, Meeting)
            for user_ref in meeting.users:
                user = User.get(doc_ref=user_ref)
                obj = self.view_model_cls.new(
                    meeting_id=meeting.doc_id,
                    once=False,
                    user=user
                )
                self.instances[(meeting.doc_id, user.doc_id)] = obj


def test_start(users, tickets, location, meeting):
    mediator = MeetingSessionViewMediatorDAV(
        view_model_cls=MeetingSessionDAV,
        meeting_cls=Meeting,
    )

    mediator.start()

    time.sleep(5)

    ref = Context.db.collection("users").document(users[0].doc_id) \
        .collection(MeetingSessionDAV.__name__).document(meeting.doc_id)
    assert ref.get().to_dict() == {'latitude': 32.880361,
                                   'obj_type': 'MeetingSessionDAV',
                                   'numHearingAidRequested': 2,
                                   'attending': [
                                       {'hearing_aid_requested': True,
                                        'name': 'Joshua Pendergrast',
                                        'organization': 'SDSU'},
                                       {'organization': 'UCSD',
                                        'hearing_aid_requested': False,
                                        'name': 'Thomasina Manes'},
                                       {'organization': 'UCSD',
                                        'hearing_aid_requested': True,
                                        'name': 'Tijuana Furlong'}],
                                   'longitude': -117.242929,
                                   'doc_ref': 'users/tijuana/MeetingSessionDAV/meeting_1',
                                   'inSession': True,
                                   'address': '9500 Gilman Drive, La Jolla, CA'}

    for user in users:
        Context.db.collection("users").document(user.doc_id) \
            .collection(MeetingSessionDAV.__name__).document(meeting.doc_id)\
            .delete()


def test_mutate(users, tickets, location, meeting):
    mediator = MeetingSessionViewMediatorDAV(
        view_model_cls=MeetingSessionDAV,
        meeting_cls=Meeting,
        mutation_cls=MeetingSessionMutation
    )

    mediator.start()

    time.sleep(5)

    ref = Context.db.collection("users").document(users[0].doc_id) \
        .collection(MeetingSessionDAV.__name__).document(meeting.doc_id)
    assert ref.get().to_dict() == {'latitude': 32.880361,
                                   'obj_type': 'MeetingSessionDAV',
                                   'numHearingAidRequested': 2,
                                   'attending': [
                                       {'hearing_aid_requested': True,
                                        'name': 'Joshua Pendergrast',
                                        'organization': 'SDSU'},
                                       {'organization': 'UCSD',
                                        'hearing_aid_requested': False,
                                        'name': 'Thomasina Manes'},
                                       {'organization': 'UCSD',
                                        'hearing_aid_requested': True,
                                        'name': 'Tijuana Furlong'}],
                                   'longitude': -117.242929,
                                   'doc_ref': 'users/tijuana/MeetingSessionDAV/meeting_1',
                                   'inSession': True,
                                   'address': '9500 Gilman Drive, La Jolla, CA'}

    for user in users:
        Context.db.collection("users").document(user.doc_id) \
            .collection(MeetingSessionDAV.__name__).document(meeting.doc_id)\
            .delete()


def test_domain_model_changes(users, tickets, location, meeting):
    """ Tests that view model updates when domain model is changed

    :param users:
    :param tickets:
    :param location:
    :param meeting:
    :return:
    """
    mediator = MeetingSessionViewMediatorDAV(
        view_model_cls=MeetingSessionDAV,
        meeting_cls=Meeting,
    )

    mediator.start()

    time.sleep(5)

    ref = Context.db.collection("users").document(users[0].doc_id) \
        .collection(MeetingSessionDAV.__name__).document(meeting.doc_id)

    assert ref.get().to_dict() == {'latitude': 32.880361,
                                   'obj_type': 'MeetingSessionDAV',
                                   'numHearingAidRequested': 2,
                                   'attending': [
                                       {'hearing_aid_requested': True,
                                        'name': 'Joshua Pendergrast',
                                        'organization': 'SDSU'},
                                       {'organization': 'UCSD',
                                        'hearing_aid_requested': False,
                                        'name': 'Thomasina Manes'},
                                       {'organization': 'UCSD',
                                        'hearing_aid_requested': True,
                                        'name': 'Tijuana Furlong'}],
                                   'longitude': -117.242929,
                                   'doc_ref': 'users/tijuana/MeetingSessionDAV/meeting_1',
                                   'inSession': True,
                                   'address': '9500 Gilman Drive, La Jolla, CA'}

    # User Tijuana Furlong sets their attendance to False
    tickets[0].attendance = False
    tickets[0].save()

    time.sleep(3)

    """
    Expect the document to be updated to exclude Tijuana Furlong from a
      list of people attending the meeting session and the hearing aid
      counter.
    """
    assert ref.get().to_dict() == {'latitude': 32.880361,
                                   'obj_type': 'MeetingSessionDAV',
                                   'numHearingAidRequested': 1,
                                   'attending': [
                                       {
                                           'name': 'Joshua Pendergrast',
                                           'organization': 'SDSU',
                                           'hearing_aid_requested': True},
                                       {
                                           'name': 'Thomasina Manes',
                                           'organization': 'UCSD',
                                           'hearing_aid_requested': False}
                                   ],
                                   'longitude': -117.242929,
                                   'doc_ref': 'users/tijuana/MeetingSessionDAV/meeting_1',
                                   'inSession': True,
                                   'address': '9500 Gilman Drive, La Jolla, CA'}

    for user in users:
        Context.db.collection("users").document(user.doc_id) \
            .collection(MeetingSessionDAV.__name__).document(meeting.doc_id)\
            .delete()


def test_view_model(users, tickets, location, meeting):
    meeting_session = MeetingSessionDAV \
        .get_from_meeting_id(meeting_id=meeting.doc_id,
                             once=True,
                             user=users[0])

    assert meeting_session._export_as_view_dict() == \
           {'inSession': True,
            'longitude': -117.242929,
            'latitude': 32.880361,
            'address': '9500 Gilman Drive, La Jolla, CA',
            'attending': [
                {
                    'name': 'Joshua Pendergrast',
                    'organization': 'SDSU',
                    'hearing_aid_requested': True},
                {
                    'name': 'Thomasina Manes',
                    'organization': 'UCSD',
                    'hearing_aid_requested': False},
                {
                    'name': 'Tijuana Furlong',
                    'organization': 'UCSD',
                    'hearing_aid_requested': True},
            ],
            'numHearingAidRequested': 2}


class UserViewDAV(UserViewMixin, DocumentAsView):

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.get_from_user_id(*args, **kwargs)

    @classmethod
    def get_from_user_id(cls, user_id, once=False):
        doc_ref = Context.db.collection(UserViewDAV.__name__).document(user_id)
        return super().get_from_user_id(user_id, once=once, doc_ref=doc_ref)

    def propagate_change(self):
        self.user.save()


class UserViewMediatorDAV(ViewMediatorDAV):

    def __init__(self, *args, user_cls=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_cls = user_cls

    def _listen_to_view_model(self, user_id):
        obj: UserViewDAV = self.instances[user_id]

        def on_snapshot(snapshots, changes, timestamp):
            if len(snapshots) != 1:
                raise ValueError
            doc = snapshots[0]
            data = obj.diff(doc.to_dict(), allowed={"lastName"})
            data = {
                self.view_model_cls.get_schema_cls().g(key): val
                for key, val in data.items()
            }
            self.mutation_cls.mutate_patch_one(obj=obj, data=data)

        watch = Watch.for_document(
            document_ref=obj.doc_ref,
            snapshot_callback=on_snapshot,
            snapshot_class_instance=DocumentSnapshot,
            reference_class_instance=DocumentReference)

    def start(self):
        self.generate_entries()
        time.sleep(3)  # TODO: delete after implementing sync
        for user_id in self.instances:
            self._listen_to_view_model(
                user_id=user_id)

    def generate_entries(self):

        users = self.user_cls.all()
        for user in users:
            assert isinstance(user, User)
            obj = self.view_model_cls.new(
                    user_id=user.doc_id,
                    once=False,
                )
            self.instances[user.doc_id] = obj


def test_user_view(users, tickets, location, meeting):

    user_view = UserViewDAV.new(user_id="thomasina", )

    time.sleep(3)  # TODO: delete after implementing sync

    assert user_view._export_as_view_dict() == {'meetings': [
        {'status': 'in-session', 'users': [
            {'lastName': 'Furlong', 'firstName': 'Tijuana',
             'hearingAidRequested': True, 'organization': 'UCSD'},
            {'lastName': 'Manes', 'firstName': 'Thomasina',
             'hearingAidRequested': False, 'organization': 'UCSD'},
            {'lastName': 'Pendergrast', 'firstName': 'Joshua',
             'hearingAidRequested': True, 'organization': 'SDSU'}],
         'location': {'latitude': 32.880361,
                      'address': '9500 Gilman Drive, La Jolla, CA',
                      'longitude': -117.242929},
         'tickets': [
            {'attendance': True, 'role': 'Participant',
             'user': {'lastName': 'Furlong', 'firstName': 'Tijuana',
                      'hearingAidRequested': True, 'organization': 'UCSD'}},
            {'attendance': True, 'role': 'Organizer',
             'user': {'lastName': 'Manes', 'firstName': 'Thomasina',
                      'hearingAidRequested': False, 'organization': 'UCSD'}},
            {'attendance': True, 'role': 'Participant',
             'user': {'lastName': 'Pendergrast', 'firstName': 'Joshua',
                      'hearingAidRequested': True, 'organization': 'SDSU'}}]}],
        'lastName': 'Manes',
        'firstName': 'Thomasina',
        'hearingAidRequested': False,
        'organization': 'UCSD'}


def test_user_view_diff(users, tickets, location, meeting):

    user_view = UserViewDAV.new(user_id="thomasina", )

    time.sleep(3)  # TODO: delete after implementing sync

    updated_dict = user_view._export_as_view_dict().copy()
    updated_dict["lastName"] = 'M.'

    res = user_view.diff(
        updated_dict
    )
    assert res == {'lastName': 'M.'}


def test_propagate_change(users, tickets, location, meeting):

    user_id = users[1].doc_id

    user_view = UserViewDAV.new(user_id=user_id, )

    time.sleep(3)

    user_view.user.last_name = "M."
    user_view.propagate_change()

    user_ref = Context.db.collection("users").document(user_id)
    assert user_ref.get().to_dict()["lastName"] == "M."


class UserViewMutationDAV(Mutation):
    pass


def test_mutation(users, tickets, location, meeting):

    user_id = users[1].doc_id

    mediator = UserViewMediatorDAV(
        view_model_cls=UserViewDAV,
        user_cls=User,
        mutation_cls=UserViewMutationDAV
    )

    mediator.start()

    user_view = mediator.instances[user_id]

    time.sleep(3)  # TODO: delete after implementing sync

    ref = Context.db.collection("UserViewDAV").document(user_id)
    ref.update({
        "lastName": "M."
    })

    time.sleep(3)

    updated_user = User.get(doc_id=user_id)

    assert updated_user.last_name == "M."

    res = user_view._export_as_view_dict()

    assert res['lastName'] == 'M.'
