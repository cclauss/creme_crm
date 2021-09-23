# -*- coding: utf-8 -*-

# from functools import partial
#
# from django.contrib.auth import get_user_model
# from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
# from django.utils.timezone import now
from django.test.utils import override_settings

# from creme.creme_core.models import CremeEntity
from creme.creme_core.tests.fake_models import FakeContact

from ..core import RegularFieldExtractor
from ..fetchers.filesystem import NEWFileSystemFetcher
from ..fetchers.pop import NEWPopFetcher
from ..models import FetcherConfigItem, MachineConfigItem  # WaitingAction
from .base import CrudityTestCase


class FetcherConfigItemTestCase(CrudityTestCase):
    def test_no_class(self):
        item = FetcherConfigItem(class_id='')
        self.assertIsNone(item.fetcher)

    @override_settings(CRUDITY_FETCHERS=[
        'creme.crudity.fetchers.filesystem.NEWFileSystemFetcher',
    ])
    def test_invalid_class(self):
        self.assertIsNone(FetcherConfigItem(class_id='invalid').fetcher)
        self.assertIsNone(FetcherConfigItem(class_id='crudity-pop').fetcher)

    @override_settings(CRUDITY_FETCHERS=[
        'creme.crudity.fetchers.invalid.InvalidFetcher',  # Does not exist
    ])
    def test_bad_config01(self):
        with self.assertRaises(ImproperlyConfigured) as cm:
            _ = FetcherConfigItem(class_id='crudity-pop').fetcher

        self.assertEqual(
            '"creme.crudity.fetchers.invalid.InvalidFetcher" is an invalid path '
            'of <CrudityFetcher> (see CRUDITY_FETCHERS).',
            str(cm.exception),
        )

    @override_settings(CRUDITY_FETCHERS=[
        'creme.crudity.decoders.ini.IniDecoder',  # Not a fetcher
    ])
    def test_bad_config02(self):
        with self.assertRaises(ImproperlyConfigured) as cm:
            _ = FetcherConfigItem(class_id='crudity-pop').fetcher

        self.assertEqual(
            '"creme.crudity.decoders.ini.IniDecoder" is not a <CrudityFetcher> '
            'sub-class (see CRUDITY_FETCHERS).',
            str(cm.exception),
        )

    @override_settings(CRUDITY_FETCHERS=[
        'creme.crudity.fetchers.pop.NEWPopFetcher',
    ])
    def test_pop(self):
        options = {
            'url': 'pop.cremecrm.org',
            'username': 'creme_crudity',
            'password': '123456',
            'port': 110,
            # TODO: 'use_ssl'....
        }
        item = FetcherConfigItem.objects.create(class_id='crudity-pop', options=options)

        fetcher = self.refresh(item).fetcher
        self.assertIsInstance(fetcher, NEWPopFetcher)
        self.assertDictEqual(options, fetcher.options)

    @override_settings(CRUDITY_FETCHERS=[
        'creme.crudity.fetchers.pop.NEWPopFetcher',
        'creme.crudity.fetchers.filesystem.NEWFileSystemFetcher',
    ])
    def test_filesystem(self):
        options = {'path': '/home/creme/crud_import/ini/'}
        item = FetcherConfigItem.objects.create(
            class_id='crudity-filesystem',
            options=options
        )

        fetcher = self.refresh(item).fetcher
        self.assertIsInstance(fetcher, NEWFileSystemFetcher)
        self.assertDictEqual(options, fetcher.options)


class MachinesConfigItemTestCase(CrudityTestCase):
    def test_extractors01(self):
        fetcher_item = FetcherConfigItem.objects.create(
            class_id='crudity-filesystem',
            options={'path': '/home/creme/crud_import/ini/'},
        )
        item = MachineConfigItem(
            action_type=MachineConfigItem.CRUDAction.CREATE,
            content_type=FakeContact,
            fetcher_item=fetcher_item,
            # json_extractors=[],
        )
        self.assertListEqual([], item.extractors)

    def test_extractors02(self):
        fetcher_item = FetcherConfigItem.objects.create(
            class_id='crudity-filesystem',
            options={'path': '/home/creme/crud_import/ini/'},
        )
        item = MachineConfigItem.objects.create(
            action_type=MachineConfigItem.CRUDAction.CREATE,
            content_type=FakeContact,
            fetcher_item=fetcher_item,
            extractors=[
                RegularFieldExtractor(model=FakeContact, value='last_name'),
                RegularFieldExtractor(model=FakeContact, value='first_name'),
            ],
        )
        self.assertListEqual(
            [
                RegularFieldExtractor(model=FakeContact, value='last_name'),
                RegularFieldExtractor(model=FakeContact, value='first_name'),
            ],
            self.refresh(item).extractors,
        )


# class WaitingActionTestCase(CrudityTestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#
#         get_ct = ContentType.objects.get_for_model
#         cls.ct_entity  = get_ct(CremeEntity)
#         cls.ct_contact = get_ct(FakeContact)
#
#         cls.User = get_user_model()
#         cls._staff_user_ids_backup = [
#             *cls.User.objects.filter(is_staff=True).values_list('id')
#         ]
#
#     @classmethod
#     def tearDownClass(cls):
#         super().tearDownClass()
#         cls.User.objects.exclude(id__in=cls._staff_user_ids_backup).update(is_staff=False)
#
#     def test_can_validate_or_delete01(self):
#         "Sandbox for everyone."
#         user = self.login()
#         action = WaitingAction.objects.create(
#             user=None, source='unknown',
#             action='create', subject='',
#             ct=self.ct_entity,
#         )
#         self.assertTrue(action.can_validate_or_delete(user)[0])
#         self.assertTrue(action.can_validate_or_delete(self.other_user)[0])
#
#     def test_can_validate_or_delete02(self):
#         "Sandbox by user."
#         user = self.login()
#         other_user = self.other_user
#
#         self._set_sandbox_by_user()
#
#         create_waction = partial(
#             WaitingAction.objects.create,
#             source='unknown', action='create', subject='', ct=self.ct_entity,
#         )
#         action = create_waction(user=user)
#         self.assertTrue(action.can_validate_or_delete(user)[0])
#         self.assertFalse(action.can_validate_or_delete(other_user)[0])
#
#         action2 = create_waction(user=self.other_user)
#         self.assertTrue(action2.can_validate_or_delete(user)[0])
#         self.assertTrue(action2.can_validate_or_delete(other_user)[0])
#
#     def test_auto_assignation01(self):
#         """If the sandbox was not by user, but now it is all WaitingAction has
#         to be assigned to someone.
#         """
#         action = WaitingAction.objects.create(
#             source='unknown', action='create', subject='', ct=self.ct_entity,
#         )
#         self.assertIsNone(action.user)
#
#         self.assertTrue(self.User.objects.filter(is_superuser=True, is_staff=False))
#
#         # Sandbox will be by user
#         self._set_sandbox_by_user()
#         self.assertFalse(WaitingAction.objects.filter(user=None))
#
#         action = self.refresh(action)
#         self.assertTrue(action.user.is_superuser)
#         self.assertFalse(action.user.is_staff)
#
#     def test_auto_assignation02(self):
#         action = WaitingAction.objects.create(
#             source='unknown', action='create', subject='', ct=self.ct_entity,
#         )
#         self.assertIsNone(action.user)
#
#         self.User.objects.filter(is_superuser=True).update(is_staff=True)
#
#         superuser = self.User.objects.create(username='Kirika2', is_superuser=True)
#
#         self._set_sandbox_by_user()
#         self.assertFalse(WaitingAction.objects.filter(user=None))
#         self.assertEqual(superuser, self.refresh(action).user)
#
#     def test_data_property01(self):
#         expected_data = {'first_name': 'Mario', 'last_name': 'Bros'}
#         action = WaitingAction.objects.create(ct=self.ct_contact, data=expected_data)
#         self.assertDictEqual(expected_data, self.refresh(action).data)
#
#     def test_data_property02(self):
#         action = WaitingAction(ct=self.ct_contact)
#         expected_data = {
#             'first_name': 'Mario',
#             'last_name': 'Bros',
#             'friends': ['Yoshi', 'Toad'],
#             'lives': 99,
#             'enemies': {'Bowser': 1, 'Koopa': 50},
#             'epoch': now(),
#         }
#         action.data = expected_data
#         action.save()
#
#         self.assertDictEqual(expected_data, self.refresh(action).data)
