# -*- coding: utf-8 -*-

from datetime import date, datetime
from decimal import Decimal
from tempfile import NamedTemporaryFile

from django.core.serializers.json import simplejson
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from creme_core.models import *
from creme_core.forms.base import _CUSTOM_NAME
from creme_core.gui.bulk_update import bulk_update_registry
from creme_core.tests.views.base import ViewsTestCase

from media_managers.models.image import Image

from persons.models import Contact, Organisation, Position, Sector


class EntityViewsTestCase(ViewsTestCase):
    def test_get_fields(self):
        self.login()

        ct_id = ContentType.objects.get_for_model(CremeEntity).id
        response = self.client.post('/creme_core/entity/get_fields', data={'ct_id': ct_id})
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        content = simplejson.loads(response.content)
        self.assertEqual(7, len(content))
        self.assertEqual(content[0],    ["created",          "Creme entity - " + _('Creation date')])
        self.assertEqual(content[1],    ["modified",         "Creme entity - " + _("Last modification")])
        self.assertEqual(content[2],    ["user__username",   _("User") + " - " + _("Username")])
        self.assertEqual(content[3],    ["user__first_name", _("User") + " - " + _("First name")])
        self.assertEqual(content[4],    ["user__last_name",  _("User") + " - " + _("Last name")])
        self.assertEqual(content[5][0], "user__email")
        self.assertEqual(content[6][0], "user__is_team")

        response = self.client.post('/creme_core/entity/get_fields', data={'ct_id': 0})
        self.assertEqual(404,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        response = self.client.post('/creme_core/entity/get_fields', data={'ct_id': 'notint'})
        self.assertEqual(400,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        response = self.client.post('/creme_core/entity/get_fields', data={'ct_id': ct_id, 'deep': 'notint'})
        self.assertEqual(400,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

    def test_get_function_fields(self):
        self.login()

        ct_id = ContentType.objects.get_for_model(CremeEntity).id
        response = self.client.post('/creme_core/entity/get_function_fields', data={'ct_id': ct_id})
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        content = simplejson.loads(response.content)
        self.assertEqual(content, [['get_pretty_properties', _('Properties')]])

        response = self.client.post('/creme_core/entity/get_function_fields', data={'ct_id': 0})
        self.assertEqual(404,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        response = self.client.post('/creme_core/entity/get_function_fields', data={'ct_id': 'notint'})
        self.assertEqual(400,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

    def test_get_custom_fields(self):
        self.login()

        ct = ContentType.objects.get_for_model(CremeEntity)
        response = self.client.post('/creme_core/entity/get_custom_fields', data={'ct_id': ct.id})
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])
        self.assertEqual([], simplejson.loads(response.content))

        CustomField.objects.create(name='cf01', content_type=ct, field_type=CustomField.INT)
        CustomField.objects.create(name='cf02', content_type=ct, field_type=CustomField.FLOAT)

        response = self.client.post('/creme_core/entity/get_custom_fields', data={'ct_id': ct.id})
        self.assertEqual([['cf01', 'cf01'], ['cf02', 'cf02']], simplejson.loads(response.content))

        response = self.client.post('/creme_core/entity/get_custom_fields', data={'ct_id': 0})
        self.assertEqual(404,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        response = self.client.post('/creme_core/entity/get_custom_fields', data={'ct_id': 'notint'})
        self.assertEqual(400,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

    def test_get_creme_entity_as_json01(self):
        self.login()

        try:
            entity = CremeEntity.objects.create(user=self.user)
        except Exception, e:
            self.fail(str(e))

        response = self.client.post('/creme_core/entity/json', data={'pk': entity.id})
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        json_data = simplejson.loads(response.content)
        #[{'pk': 1,
        #  'model': 'creme_core.cremeentity',
        #  'fields': {'is_actived': False,
        #             'is_deleted': False,
        #             'created': '2010-11-09 14:34:04',
        #             'header_filter_search_field': '',
        #             'entity_type': 100,
        #             'modified': '2010-11-09 14:34:04',
        #             'user': 1
        #            }
        #}]
        try:
            dic = json_data[0]
            pk     = dic['pk']
            model  = dic['model']
            fields = dic['fields']
            user = fields['user']
        except Exception, e:
            self.fail(str(e))

        self.assertEqual(entity.id, pk)
        self.assertEqual('creme_core.cremeentity', model)
        self.assertEqual(self.user.id, user)

    def test_get_creme_entity_as_json02(self):
        self.login()

        try:
            entity = CremeEntity.objects.create(user=self.user)
        except Exception, e:
            self.fail(str(e))

        response = self.client.post('/creme_core/entity/json', data={'pk': entity.id, 'fields': ['user', 'entity_type']})
        self.assertEqual(200, response.status_code)

        json_data = simplejson.loads(response.content)
        #[{'pk': 1,
        #  'model': 'creme_core.cremeentity',
        #  'fields': {'user': 1, 'entity_type': 100}}
        #]
        try:
            fields = json_data[0]['fields']
            user = fields['user']
            entity_type = fields['entity_type']
        except Exception, e:
            self.fail(str(e))

            self.assertEqual(self.user.id, user)
            self.assertEqual(ContentType.objects.get_for_model(CremeEntity).id, entity_type)

    def test_get_creme_entities_repr(self):
        self.login()

        try:
            entity = CremeEntity.objects.create(user=self.user)
        except Exception, e:
            self.fail(str(e))

        response = self.client.get('/creme_core/entity/get_repr/%s' % entity.id)
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])
        json_data = simplejson.loads(response.content)
        self.assertEqual('Creme entity: %s' % entity.id, json_data[0]['text'])

    def test_delete_entity01(self):
        self.login()

        entity = Organisation.objects.create(user=self.user, name='Nerv') #to get a get_lv_absolute_url() method

        response = self.client.post('/creme_core/entity/delete/%s' % entity.id)
        self.assertEqual(302, response.status_code)
        self.assertEqual(0,   Organisation.objects.filter(pk=entity.id).count())

    def test_delete_entity02(self):
        self.login(is_superuser=False)

        entity = Organisation.objects.create(user=self.other_user, name='Nerv')

        response = self.client.post('/creme_core/entity/delete/%s' % entity.id)
        self.assertEqual(403, response.status_code)
        self.assertEqual(1,   Organisation.objects.filter(pk=entity.id).count())

    def test_delete_entity03(self):
        self.login()

        entity01 = Organisation.objects.create(user=self.other_user, name='Nerv')
        entity02 = Organisation.objects.create(user=self.other_user, name='Seele')

        rtype, srtype = RelationType.create(('test-subject_linked', 'is linked to'),
                                            ('test-object_linked',  'is linked to')
                                           )
        Relation.objects.create(user=self.user, type=rtype, subject_entity=entity01, object_entity=entity02)

        response = self.client.post('/creme_core/entity/delete/%s' % entity01.id)
        #self.assertEqual(400, response.status_code)
        self.assertEqual(2,   Organisation.objects.filter(pk__in=[entity01.id, entity02.id]).count())

    def test_delete_entities01(self):
        self.login()

        entity01 = CremeEntity.objects.create(user=self.user)
        entity02 = CremeEntity.objects.create(user=self.user)
        entity03 = CremeEntity.objects.create(user=self.user)

        response = self.client.post('/creme_core/delete_js',
                                    data={'ids': '%s,%s,' % (entity01.id, entity02.id)}
                                   )
        self.assertEqual(200, response.status_code)
        self.assertEqual(0,   CremeEntity.objects.filter(pk__in=[entity01.id, entity02.id]).count())
        self.assertEqual(1,   CremeEntity.objects.filter(pk=entity03.id).count())

    def test_delete_entities02(self):
        self.login()

        entity01 = CremeEntity.objects.create(user=self.user)
        entity02 = CremeEntity.objects.create(user=self.user)

        response = self.client.post('/creme_core/delete_js',
                                    data={'ids': '%s,%s,' % (entity01.id, entity02.id + 1)}
                                   )
        self.assertEqual(404, response.status_code)
        self.assertEqual(0,   CremeEntity.objects.filter(pk=entity01.id).count())
        self.assertEqual(1,   CremeEntity.objects.filter(pk=entity02.id).count())

    def test_delete_entities03(self):
        self.login(is_superuser=False)

        forbidden = CremeEntity.objects.create(user=self.other_user)
        allowed   = CremeEntity.objects.create(user=self.user)
        response = self.client.post('/creme_core/delete_js',
                                    data={'ids': '%s,%s,' % (forbidden.id, allowed.id)}
                                   )
        self.assertEqual(403, response.status_code)
        self.assertEqual(0,   CremeEntity.objects.filter(pk=allowed.id).count())
        self.assertEqual(1,   CremeEntity.objects.filter(pk=forbidden.id).count())

    def test_delete_entities04(self):
        self.login()

        entity01 = CremeEntity.objects.create(user=self.user)
        entity02 = CremeEntity.objects.create(user=self.user)
        entity03 = CremeEntity.objects.create(user=self.user) #not linked => can be deleted

        rtype, srtype = RelationType.create(('test-subject_linked', 'is linked to'),
                                            ('test-object_linked',  'is linked to')
                                           )
        Relation.objects.create(user=self.user, type=rtype, subject_entity=entity01, object_entity=entity02)

        response = self.client.post('/creme_core/delete_js',
                                    data={'ids': '%s,%s,%s,' % (entity01.id, entity02.id, entity03.id)}
                                   )
        self.assertEqual(400, response.status_code)
        self.assertEqual(2,   CremeEntity.objects.filter(pk__in=[entity01.id, entity02.id]).count())
        self.assertEqual(0,   CremeEntity.objects.filter(pk=entity03.id).count())

    def test_get_info_fields01(self):
        self.login()

        furl = '/creme_core/entity/get_info_fields/%s/json'
        ct = ContentType.objects.get_for_model(Contact)
        response = self.client.get(furl % ct.id)
        self.assertEqual(200, response.status_code)

        json_data = simplejson.loads(response.content)
        #print json_data
        self.assert_(isinstance(json_data, list))
        self.assert_(all(isinstance(elt, list) for elt in json_data))
        self.assert_(all(len(elt) == 2 for elt in json_data))

        names = ['created', 'modified', 'first_name', 'last_name', 'description',
                 'skype', 'phone', 'mobile', 'fax', 'email', 'url_site', 'birthday'
                ]
        diff = set(names) - set(name for name, vname in json_data)
        self.failIf(diff, diff)

        self.assertEqual(len(names), len(json_data))

    def test_get_info_fields02(self):
        self.login()

        furl = '/creme_core/entity/get_info_fields/%s/json'
        ct = ContentType.objects.get_for_model(Organisation)
        json_data = simplejson.loads(self.client.get(furl % ct.id).content)
        #print json_data

        names = ['created', 'modified', 'name', 'description', 'annual_revenue',
                 'url_site', 'fax', 'naf', 'siren', 'phone', 'siret', 'rcs', 'email',
                 'creation_date',  'tvaintra', 'subject_to_vat', 'capital'
                ]
        self.assertEqual(set(names), set(name for name, vname in json_data))
        self.assertEqual(len(names), len(json_data))

        json_dict = dict(json_data)
        translation = _(u'Name')
        self.assert_(json_dict['name'].startswith(translation))
        self.assertNotEqual(translation, json_dict['name'])

    def test_clone01(self):
        self.login()
        url = '/creme_core/entity/clone'

        mario = Contact.objects.create(user=self.user, first_name="Mario", last_name="Bros")

        response = self.client.post(url, data={'id': mario.id}, follow=True)
        self.assertEqual(200, response.status_code)

        response = self.client.post(url, data={})
        self.assertEqual(404, response.status_code)

        response = self.client.post(url, data={'id': 0})
        self.assertEqual(404, response.status_code)

    def test_clone02(self):
        self.login(is_superuser=False)
        url = '/creme_core/entity/clone'

        mario = Contact.objects.create(user=self.other_user, first_name="Mario", last_name="Bros")

        response = self.client.post(url, data={'id': mario.id}, follow=True)
        self.assertEqual(403, response.status_code)

    def test_clone03(self):
        self.login(is_superuser=False, creatable_models=[ct.model_class() for ct in ContentType.objects.all()])
        self._set_all_creds_except_one(SetCredentials.CRED_VIEW)
        url = '/creme_core/entity/clone'

        mario = Contact.objects.create(user=self.other_user, first_name="Mario", last_name="Bros")

        response = self.client.post(url, data={'id': mario.id}, follow=True)
        self.assertEqual(403, response.status_code)

    def test_clone04(self):
        self.login(is_superuser=False, creatable_models=[ct.model_class() for ct in ContentType.objects.all()], allowed_apps=('creme_core', 'persons'))
        self._set_all_creds_except_one(None)
        url = '/creme_core/entity/clone'

        mario = Contact.objects.create(user=self.user, first_name="Mario", last_name="Bros")

        response = self.client.post(url, data={'id': mario.id}, follow=True)
        self.assertEqual(200, response.status_code)

    def test_clone05(self):
        self.login()
        url = '/creme_core/entity/clone'

        first_name = "Mario"
        mario = Contact.objects.create(user=self.other_user, first_name=first_name, last_name="Bros")

        count = Contact.objects.count()
        response = self.client.post(url, data={'id': mario.id}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(count + 1, Contact.objects.count())

        try:
            mario = Contact.objects.filter(first_name=first_name).order_by('created')[0]
            oiram = Contact.objects.filter(first_name=first_name).order_by('created')[1]
        except Exception, e:
            self.fail(str(e))

        self.assertEqual(mario.last_name,  oiram.last_name)

        self.assert_(response.redirect_chain)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assert_(response.redirect_chain[0][0].endswith('/persons/contact/%s' % oiram.id))

        response = self.client.get('/persons/contact/%s' % oiram.id)
        self.assertEqual(response.status_code, 200)

    def _assert_detailview(self, response, entity):
        self.assertEqual(200, response.status_code)
        self.assertEqual(1,   len(response.redirect_chain))
        self.assert_(response.redirect_chain[0][0].endswith(entity.get_absolute_url()))

    def test_search_and_view01(self):
        self.login()

        phone = '123456789'
        url = '/creme_core/entity/search_n_view'
        data = {
                'models': 'persons-contact',
                'fields': 'phone',
                'value':  phone,
               }
        self.assertEqual(404, self.client.get(url, data=data).status_code)

        create_contact = Contact.objects.create
        onizuka = create_contact(user=self.user, first_name='Eikichi', last_name='Onizuka')
        ryuji   = create_contact(user=self.user, first_name='Ryuji',   last_name='Danma', phone='987654', mobile=phone)
        self.assertEqual(404, self.client.get(url, data=data).status_code)

        onizuka.phone = phone
        onizuka.save()
        self._assert_detailview(self.client.get(url, data=data, follow=True), onizuka)

    def test_search_and_view02(self):
        self.login()

        phone = '999999999'
        url = '/creme_core/entity/search_n_view'
        data = {
                'models': 'persons-contact',
                'fields': 'phone,mobile',
                'value':  phone,
               }
        self.assertEqual(404, self.client.get(url, data=data).status_code)

        create_contact = Contact.objects.create
        onizuka  = create_contact(user=self.user, first_name='Eikichi', last_name='Onizuka', mobile=phone)
        ryuji    = create_contact(user=self.user, first_name='Ryuji',   last_name='Danma', phone='987654')
        self._assert_detailview(self.client.get(url, data=data, follow=True), onizuka)

    def test_search_and_view03(self):
        self.login()

        phone = '696969'
        url = '/creme_core/entity/search_n_view'
        data = {
                'models':  'persons-contact,persons-organisation',
                'fields': 'phone,mobile',
                'value': phone,
               }
        self.assertEqual(404, self.client.get(url, data=data).status_code)

        create_contact = Contact.objects.create
        onizuka = create_contact(user=self.user, first_name='Eikichi', last_name='Onizuka', mobile='55555')
        ryuji   = create_contact(user=self.user, first_name='Ryuji',   last_name='Danma', phone='987654')
        onibaku = Organisation.objects.create(user=self.user, name='Onibaku', phone=phone)
        self._assert_detailview(self.client.get(url, data=data, follow=True), onibaku)

        onizuka.mobile = phone
        onizuka.save()
        self._assert_detailview(self.client.get(url, data=data, follow=True), onizuka)

    def test_search_and_view04(self): #errors
        self.login()

        url = '/creme_core/entity/search_n_view'
        base_data = {
                        'models': 'persons-contact,persons-organisation',
                        'fields': 'mobile,phone',
                        'value':  '696969',
                    }
        create_contact = Contact.objects.create
        onizuka = create_contact(user=self.user, first_name='Eikichi', last_name='Onizuka', mobile='55555')
        ryuji   = create_contact(user=self.user, first_name='Ryuji',   last_name='Danma', phone='987654')
        onibaku = Organisation.objects.create(user=self.user, name='Onibaku', phone='54631357')

        data = dict(base_data); data['models'] = 'foo-bar'
        self.assertEqual(404, self.client.get(url, data=data).status_code)

        data = dict(base_data); data['models'] = 'foobar'
        self.assertEqual(404, self.client.get(url, data=data).status_code)

        data = dict(base_data); data['values'] = ''
        self.assertEqual(404, self.client.get(url, data=data).status_code)

        data = dict(base_data); data['models'] = ''
        self.assertEqual(404, self.client.get(url, data=data).status_code)

        data = dict(base_data); data['fields'] = ''
        self.assertEqual(404, self.client.get(url, data=data).status_code)

        data = dict(base_data); data['models'] = 'persons-civility' #not CremeEntity
        self.assertEqual(404, self.client.get(url, data=data).status_code)

    def test_search_and_view05(self): #creds
        self.login(is_superuser=False)
        self.role.allowed_apps = ['creme_core', 'persons']
        self.role.save()

        phone = '44444'
        url = '/creme_core/entity/search_n_view'
        data = {
                'models': 'persons-contact,persons-organisation',
                'fields': 'phone,mobile',
                'value':  phone,
               }
        user = self.user
        create_contact = Contact.objects.create
        onizuka = create_contact(user=self.other_user, first_name='Eikichi', last_name='Onizuka', mobile=phone) #phone Ok and but not readable
        ryuji   = create_contact(user=user,            first_name='Ryuji',   last_name='Danma',   phone='987654') #phone KO
        onibaku = Organisation.objects.create(user=user, name='Onibaku', phone=phone) #phone Ok and readable

        self.failIf(onizuka.can_view(user))
        self.assert_(ryuji.can_view(user))
        self.assert_(onibaku.can_view(user))
        self._assert_detailview(self.client.get(url, data=data, follow=True), onibaku)

    def test_search_and_view06(self): #app creds
        self.login(is_superuser=False)
        self.role.allowed_apps = ['creme_core'] #not 'persons'
        self.role.save()

        phone = '31337'
        data = {
                'models': 'persons-contact',
                'fields': 'phone',
                'value':  phone,
               }
        onizuka = Contact.objects.create(user=self.user, first_name='Eikichi', last_name='Onizuka', phone=phone)#would match if apps was allowed
        self.assertEqual(403, self.client.get('/creme_core/entity/search_n_view', data=data).status_code)


class BulkEditTestCase(ViewsTestCase):
    def setUp(self):
        self.contact_ct = ContentType.objects.get_for_model(Contact)
        self.url = '/creme_core/entity/bulk_update/%s/%s'

    def create_contact(self, user, **kwargs):
        return Contact.objects.create(user=user, **kwargs)

    def refresh_contact(self, contact):
        return Contact.objects.get(pk=contact.id)

    def get_cf_values(self, cf, entity):
        return cf.get_value_class().objects.get(custom_field=cf, entity=entity)

    def test_edit_entities_bulk01(self):
        self.login()
        contact_ct_id = self.contact_ct.id

        self.assertEqual(404, self.client.get('/creme_core/entity/bulk_update/%s/'  % contact_ct_id).status_code)
        self.assertEqual(404, self.client.get('/creme_core/entity/bulk_update/%s/%s' % (contact_ct_id, 0)).status_code)

        response = self.client.get('/creme_core/entity/bulk_update/%s/%s' % (contact_ct_id, ",".join([str(i) for i in xrange(10)])))
        self.assertEqual(404, response.status_code)

        mario = self.create_contact(user=self.user, first_name="Mario", last_name="Bros")
        self.assertEqual(200, self.client.get('/creme_core/entity/bulk_update/%s/%s' % (contact_ct_id, mario.id)).status_code)

    def test_edit_entities_bulk02(self):
        self.login()

        unemployed   = Position.objects.create(title='unemployed')
        plumber      = Position.objects.create(title='plumber')
        ghost_hunter = Position.objects.create(title='ghost hunter')

        mario = self.create_contact(user=self.user, first_name="Mario", last_name="Bros", position=plumber)
        luigi = self.create_contact(user=self.user, first_name="Luigi", last_name="Bros", position=ghost_hunter)

        url = self.url % (self.contact_ct.id, ",".join([str(mario.id), str(luigi.id)]))
        self.assertEqual(200, self.client.get(url).status_code)

        response = self.client.post(url, data={
                                                'field_name':   'position',
                                                'field_value':  unemployed.id,
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(unemployed, self.refresh_contact(mario).position)
        self.assertEqual(unemployed, self.refresh_contact(luigi).position)

    def test_edit_entities_bulk03(self):
        self.login()

        plumbing    = Sector.objects.create(title='Plumbing')
        games       = Sector.objects.create(title='Games')

        mario = self.create_contact(user=self.user, first_name="Mario", last_name="Bros", sector=games)
        luigi = self.create_contact(user=self.user, first_name="Luigi", last_name="Bros", sector=games)
        nintendo = Organisation.objects.create(user=self.user, name='Nintendo', sector=games)

        url = self.url % (self.contact_ct.id, ",".join([str(mario.id), str(luigi.id), str(nintendo.id)]))
        self.assertEqual(200, self.client.get(url).status_code)

        response = self.client.post(url, data={
                                                'field_name':   'sector',
                                                'field_value':  plumbing.id,
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(plumbing, self.refresh_contact(mario).sector)
        self.assertEqual(plumbing, self.refresh_contact(luigi).sector)
        self.assertEqual(games, Organisation.objects.get(pk=nintendo).sector)

    def test_edit_entities_bulk04(self):
        self.login()

        mario = self.create_contact(user=self.user, first_name="Mario", last_name="Bros")
        luigi = self.create_contact(user=self.user, first_name="Luigi", last_name="Bros")

        url = self.url % (self.contact_ct.id, ",".join([str(mario.id), str(luigi.id)]))
        self.assertEqual(200, self.client.get(url).status_code)

        response = self.client.post(url, data={
                                                'field_name':   'last_name',
                                                'field_value':  '',
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertFormError(response, 'form', None, [_(u'This field is required.')])

    def test_edit_entities_bulk05(self):
        self.login()

        bulk_update_registry.register((Contact, ['position', ]))

        unemployed   = Position.objects.create(title='unemployed')

        mario = self.create_contact(user=self.user, first_name="Mario", last_name="Bros")
        luigi = self.create_contact(user=self.user, first_name="Luigi", last_name="Bros")

        url = self.url % (self.contact_ct.id, ",".join([str(mario.id), str(luigi.id)]))
        self.assertEqual(200, self.client.get(url).status_code)

        response = self.client.post(url, data={
                                                'field_name':   'position',
                                                'field_value':  unemployed.id,
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assert_(response.context['form'].errors)
#        self.assertFormError(response, 'form', 'field_name', [_(u'Select a valid choice. %s is not one of the available choices.') % 'position'])

    def test_edit_entities_bulk06(self):
        self.login()

        mario = self.create_contact(user=self.user, first_name="Mario", last_name="Bros", description="Luigi's brother")
        luigi = self.create_contact(user=self.user, first_name="Luigi", last_name="Bros", description="Mario's brother")

        url = self.url % (self.contact_ct.id, ",".join([str(mario.id), str(luigi.id)]))
        self.assertEqual(200, self.client.get(url).status_code)

        response = self.client.post(url, data={
                                                'field_name':      'description',
                                                'field_value':     '',
                                                'entities_lbl':    'whatever',
                                                'bad_entities_lbl':'whatever',
                                              }
                                   )
        self.assertNoFormError(response)

        mario    = self.refresh_contact(mario)
        luigi    = self.refresh_contact(luigi)
        self.assertEqual('', mario.description)
        self.assertEqual('', luigi.description)

    def test_edit_entities_bulk07(self):
        self.login(is_superuser=False, allowed_apps=('creme_core', 'persons'))

        mario_desc = u"Luigi's brother"
        mario = self.create_contact(user=self.other_user, first_name="Mario", last_name="Bros", description=mario_desc)
        luigi = self.create_contact(user=self.user,       first_name="Luigi", last_name="Bros", description="Mario's brother")
        url = self.url % (self.contact_ct.id, ",".join([str(mario.id), str(luigi.id)]))

        response = self.client.post(url, data={
                                                'field_name':      'description',
                                                'field_value':     '',
                                                'entities_lbl':    'whatever',
                                                'bad_entities_lbl':'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(mario_desc, self.refresh_contact(mario).description)
        self.assertEqual('',         self.refresh_contact(luigi).description)

    def test_edit_entities_bulk08(self):
        self.login()

        mario = self.create_contact(user=self.user, first_name="Mario", last_name="Bros")
        luigi = self.create_contact(user=self.user, first_name="Luigi", last_name="Bros")
        url = self.url % (self.contact_ct.id, ",".join([str(mario.id), str(luigi.id)]))

        response = self.client.post(url, data={
                                                'field_name':   'birthday',
                                                'field_value':  'bad date',
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assert_(response.context['form'].errors)

        settings.DATE_INPUT_FORMATS += ("-%dT%mU%Y-",) #This weird format have few chances to be present in settings
        self.client.post(url, data={
                                    'field_name':   'birthday',
                                    'field_value':  '-31T01U2000-',
                                    'entities_lbl': 'whatever',
                                   }
                       )
        birthday = date(2000, 01, 31)
        self.assertEqual(birthday, self.refresh_contact(mario).birthday)
        self.assertEqual(birthday, self.refresh_contact(luigi).birthday)

    def test_edit_entities_bulk09(self):
        self.login(is_superuser=False, allowed_apps=('creme_core', 'persons', 'media_managers'))

        mario_desc = u"Luigi's brother"
        mario = self.create_contact(user=self.other_user, first_name="Mario", last_name="Bros", description=mario_desc)
        luigi = self.create_contact(user=self.user,       first_name="Luigi", last_name="Bros", description="Mario's brother")

        tmpfile = NamedTemporaryFile()
        tmpfile.width = tmpfile.height = 0
        tmpfile._committed = True

        unallowed = Image.objects.create(user=self.other_user, image=tmpfile)
        allowed   = Image.objects.create(user=self.user, image=tmpfile)

        url = self.url % (self.contact_ct.id, ",".join([str(mario.id), str(luigi.id)]))
        self.assertEqual(200, self.client.get(url).status_code)

        response = self.client.post(url, data={
                                                'field_name':      'image',
                                                'field_value':     unallowed.id,
                                                'entities_lbl':    'whatever',
                                                'bad_entities_lbl':'whatever',
                                              }
                                   )
        self.assert_(response.context['form'].errors)

        self.client.post(url, data={
                                    'field_name':       'image',
                                    'field_value':      allowed.id,
                                    'entities_lbl':     'whatever',
                                    'bad_entities_lbl': 'whatever',
                                   }
                        )
        self.assertNotEqual(allowed, self.refresh_contact(mario).image)
        self.assertEqual(allowed,    self.refresh_contact(luigi).image)

    def get_2_contacts_n_url(self):
        mario = self.create_contact(user=self.user, first_name="Mario", last_name="Bros")
        luigi = self.create_contact(user=self.user, first_name="Luigi", last_name="Bros")
        url   = self.url % (self.contact_ct.id, ",".join([str(mario.id), str(luigi.id)]))

        return mario, luigi, url

    def test_edit_entities_bulk_cf01(self):
        self.login()
        contact_ct    = ContentType.objects.get_for_id(self.contact_ct.id)
        get_cf_values = self.get_cf_values
        cf_int        = CustomField.objects.create(name='int', content_type=contact_ct, field_type=CustomField.INT)
        mario, luigi, url = self.get_2_contacts_n_url()

        #Int
        response = self.client.post(url, data={
                                                'field_name': _CUSTOM_NAME % cf_int.id,
                                                'field_value': 10,
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(10, get_cf_values(cf_int, self.refresh_contact(mario)).value)
        self.assertEqual(10, get_cf_values(cf_int, self.refresh_contact(luigi)).value)

        #Int empty
        response = self.client.post(url, data={
                                                'field_name': _CUSTOM_NAME % cf_int.id,
                                                'field_value': '',
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertRaises(CustomFieldInteger.DoesNotExist, get_cf_values, cf_int, self.refresh_contact(mario))
        self.assertRaises(CustomFieldInteger.DoesNotExist, get_cf_values, cf_int, self.refresh_contact(luigi))

    def test_edit_entities_bulk_cf02(self):
        self.login()
        contact_ct    = ContentType.objects.get_for_id(self.contact_ct.id)
        get_cf_values = self.get_cf_values
        mario, luigi, url = self.get_2_contacts_n_url()

        cf_float = CustomField.objects.create(name='float', content_type=contact_ct, field_type=CustomField.FLOAT)

        #Float
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_float.id,
                                                'field_value':  '10.2',
                                                'entities_lbl': 'whatever',
                                            }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(Decimal("10.2"), get_cf_values(cf_float, self.refresh_contact(mario)).value)
        self.assertEqual(Decimal("10.2"), get_cf_values(cf_float, self.refresh_contact(luigi)).value)

        #Float empty
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_float.id,
                                                'field_value':  '',
                                                'entities_lbl': 'whatever',
                                             }
                                   )
        self.assertNoFormError(response)
        self.assertRaises(CustomFieldFloat.DoesNotExist, get_cf_values, cf_float, self.refresh_contact(mario))
        self.assertRaises(CustomFieldFloat.DoesNotExist, get_cf_values, cf_float, self.refresh_contact(luigi))

    def test_edit_entities_bulk_cf03(self):
        self.login()
        get_cf_values = self.get_cf_values
        mario, luigi, url = self.get_2_contacts_n_url()

        cf_bool = CustomField.objects.create(name='bool', content_type=self.contact_ct, field_type=CustomField.BOOL)

        #Bool
        response = self.client.post(url, data={
                                                'field_name': _CUSTOM_NAME % cf_bool.id,
                                                'field_value': True,
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(True, get_cf_values(cf_bool, self.refresh_contact(mario)).value)
        self.assertEqual(True, get_cf_values(cf_bool, self.refresh_contact(luigi)).value)

        #Bool false
        response = self.client.post(url, data={
                                                'field_name': _CUSTOM_NAME % cf_bool.id,
                                                'field_value': False,
                                                'entities_lbl': 'whatever',
                                            }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(False, get_cf_values(cf_bool, self.refresh_contact(mario)).value)
        self.assertEqual(False, get_cf_values(cf_bool, self.refresh_contact(luigi)).value)

        #Bool empty
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_bool.id,
                                                'field_value':  None,
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertRaises(CustomFieldBoolean.DoesNotExist, get_cf_values, cf_bool, self.refresh_contact(mario))
        self.assertRaises(CustomFieldBoolean.DoesNotExist, get_cf_values, cf_bool, self.refresh_contact(luigi))

    def test_edit_entities_bulk_cf04(self):
        self.login()
        get_cf_values = self.get_cf_values
        mario, luigi, url = self.get_2_contacts_n_url()

        cf_str  = CustomField.objects.create(name='str', content_type=self.contact_ct, field_type=CustomField.STR)
        #Str
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_str.id,
                                                'field_value':  'str',
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual('str', get_cf_values(cf_str, self.refresh_contact(mario)).value)
        self.assertEqual('str', get_cf_values(cf_str, self.refresh_contact(luigi)).value)

        #Str empty
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_str.id,
                                                'field_value':  '',
                                                'entities_lbl': 'whatever',
                                              }
                           )
        self.assertNoFormError(response)
        self.assertRaises(CustomFieldString.DoesNotExist, get_cf_values, cf_str, self.refresh_contact(mario))
        self.assertRaises(CustomFieldString.DoesNotExist, get_cf_values, cf_str, self.refresh_contact(luigi))

    def test_edit_entities_bulk_cf05(self):
        self.login()
        get_cf_values = self.get_cf_values
        mario, luigi, url = self.get_2_contacts_n_url()

        cf_date = CustomField.objects.create(name='date', content_type=self.contact_ct, field_type=CustomField.DATE)

        #Date
        settings.DATETIME_INPUT_FORMATS += ("-%dT%mU%Y-",) #This weird format have few chances to be present in settings
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_date.id,
                                                'field_value':  '-31T01U2000-',
                                                'entities_lbl': 'whatever',
                                             }
                                   )
        self.assertNoFormError(response)

        dt = datetime(2000, 01, 31)
        self.assertEqual(dt, get_cf_values(cf_date, self.refresh_contact(mario)).value)
        self.assertEqual(dt, get_cf_values(cf_date, self.refresh_contact(luigi)).value)

        #Date
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_date.id,
                                                'field_value':  '',
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertRaises(CustomFieldDateTime.DoesNotExist, get_cf_values, cf_date, self.refresh_contact(mario))
        self.assertRaises(CustomFieldDateTime.DoesNotExist, get_cf_values, cf_date, self.refresh_contact(luigi))

    def test_edit_entities_bulk_cf06(self):
        self.login()
        get_cf_values = self.get_cf_values
        mario, luigi, url = self.get_2_contacts_n_url()

        cf_enum = CustomField.objects.create(name='enum', content_type=self.contact_ct, field_type=CustomField.ENUM)
        enum1 = CustomFieldEnumValue.objects.create(custom_field= cf_enum, value=u"Enum1")
        enum2 = CustomFieldEnumValue.objects.create(custom_field= cf_enum, value=u"Enum2")

        #Enum
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_enum.id,
                                                'field_value':  enum1.id,
                                                'entities_lbl': 'whatever',
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(enum1, get_cf_values(cf_enum, self.refresh_contact(mario)).value)
        self.assertEqual(enum1, get_cf_values(cf_enum, self.refresh_contact(luigi)).value)

        #Enum empty
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_enum.id,
                                                'field_value':  '',
                                                'entities_lbl': 'whatever',
                                              }
                           )
        self.assertNoFormError(response)
        self.assertRaises(CustomFieldEnum.DoesNotExist, get_cf_values, cf_enum, self.refresh_contact(mario))
        self.assertRaises(CustomFieldEnum.DoesNotExist, get_cf_values, cf_enum, self.refresh_contact(luigi))

    def test_edit_entities_bulk_cf07(self):
        self.login()
        get_cf_values = self.get_cf_values

        cf_multi_enum = CustomField.objects.create(name='multi_enum', content_type=self.contact_ct, field_type=CustomField.MULTI_ENUM)
        m_enum1 = CustomFieldEnumValue.objects.create(custom_field= cf_multi_enum, value=u"MEnum1")
        m_enum2 = CustomFieldEnumValue.objects.create(custom_field= cf_multi_enum, value=u"MEnum2")
        m_enum3 = CustomFieldEnumValue.objects.create(custom_field= cf_multi_enum, value=u"MEnum3")

        mario, luigi, url = self.get_2_contacts_n_url()
        self.assertEqual(200, self.client.get(url).status_code)

        #Multi-Enum
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_multi_enum.id,
                                                'field_value':  [m_enum1.id, m_enum3.id],
                                                'entities_lbl': 'whatever',
                                              }
                           )
        self.assertNoFormError(response)

        mario = self.refresh_contact(mario)
        luigi = self.refresh_contact(luigi)

        self.failUnless(m_enum1.id in get_cf_values(cf_multi_enum, mario).value.values_list('pk', flat=True))
        self.failUnless(m_enum3.id in get_cf_values(cf_multi_enum, mario).value.values_list('pk', flat=True))

        self.failUnless(m_enum1.id in get_cf_values(cf_multi_enum, luigi).value.values_list('pk', flat=True))
        self.failUnless(m_enum3.id in get_cf_values(cf_multi_enum, luigi).value.values_list('pk', flat=True))

        #Multi-Enum empty
        response = self.client.post(url, data={
                                                'field_name':   _CUSTOM_NAME % cf_multi_enum.id,
                                                'field_value':  [],
                                                'entities_lbl': 'whatever',
                                              }
                           )
        self.assertNoFormError(response)
        self.assertRaises(CustomFieldMultiEnum.DoesNotExist, get_cf_values, cf_multi_enum, self.refresh_contact(mario))
        self.assertRaises(CustomFieldMultiEnum.DoesNotExist, get_cf_values, cf_multi_enum, self.refresh_contact(luigi))

    def test_get_widget(self):#Bulk edition uses this widget
        self.login()

        url = '/creme_core/entity/get_widget/%s'

        response = self.client.post(url % self.contact_ct.id,
                                    data={
                                            'field_name':       'first_name',
                                            'field_value_name': 'field_value',
                                         }
                                   )
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])
        self.assert_(simplejson.loads(response.content)['rendered'])

        response = self.client.post(url % 0, data={})
        self.assertEqual(404,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        self.assertEqual(404, self.client.post(url % 'notint', data={}).status_code)
