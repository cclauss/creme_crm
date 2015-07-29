# -*- coding: utf-8 -*-

try:
    from functools import partial
    from os.path import join

    from django.conf import settings
    from django.contrib.contenttypes.models import ContentType
    from django.core.exceptions import ValidationError
    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext as _

    from creme.creme_core.tests.views.base import CSVImportBaseTestCaseMixin
    from creme.creme_core.auth.entity_credentials import EntityCredentials
    from creme.creme_core.forms.widgets import Label, TextInput
    from creme.creme_core.gui.quick_forms import quickforms_registry
    from creme.creme_core.models import RelationType, Relation, SetCredentials

    from creme.media_managers.models import Image

    from .base import (_BaseTestCase, skipIfCustomAddress, skipIfCustomContact,
            skipIfCustomOrganisation)
    from ..models import Contact, Organisation, Address, Position, Civility, Sector
    from ..constants import REL_OBJ_EMPLOYED_BY, REL_SUB_EMPLOYED_BY
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


__all__ = ('ContactTestCase',)


@skipIfCustomContact
class ContactTestCase(_BaseTestCase, CSVImportBaseTestCaseMixin):
#    ADD_URL = '/persons/contact/add'
#    ADD_RELATED_URL = "/persons/contact/add_with_relation/%(orga_id)s/%(rtype_id)s?callback_url=%(url)s"

    lv_import_data = {
            'step': 1,
            #'document': doc.id, 'user': self.user.id,

            'first_name_colselect': 1,
            'last_name_colselect':  2,

            'civility_colselect':    0,
            'description_colselect': 0,
            'skype_colselect':       0,
            'phone_colselect':       0,
            'mobile_colselect':      0,
            'fax_colselect':         0,
            'position_colselect':    0,
            'sector_colselect':      0,
            'email_colselect':       0,
            'url_site_colselect':    0,
            'birthday_colselect':    0,
            'image_colselect':       0,

            #'property_types', 'fixed_relations', 'dyn_relations',

            #TODO: factorise with OrganisationTestCase
            'billaddr_address_colselect':    0,  'shipaddr_address_colselect':    0,
            'billaddr_po_box_colselect':     0,  'shipaddr_po_box_colselect':     0,
            'billaddr_city_colselect':       0,  'shipaddr_city_colselect':       0,
            'billaddr_state_colselect':      0,  'shipaddr_state_colselect':      0,
            'billaddr_zipcode_colselect':    0,  'shipaddr_zipcode_colselect':    0,
            'billaddr_country_colselect':    0,  'shipaddr_country_colselect':    0,
            'billaddr_department_colselect': 0,  'shipaddr_department_colselect': 0,
        }

    #def _build_addrelated_uri(self, orga_id, rtype_id, url):
        #return reverse('persons__create_related_contact', args=(orga_id, rtype_id)) \
               #+ '?callback_url=' + url
    def _build_addrelated_uri(self, orga_id, rtype_id=None, url='/'):
        #return reverse('persons__create_related_contact',
                       #kwargs={'orga_id': orga_id, 'rtype_id': rtype_id},
                      #) + '?callback_url=' + url
        kwargs = {'orga_id': orga_id}

        if rtype_id:
            kwargs['rtype_id'] = rtype_id

        return reverse('persons__create_related_contact', kwargs=kwargs) + '?callback_url=' + url

    #TODO: in creme_core ??
    def _build_delete_url(self, entity):
        return '/creme_core/entity/delete/%s' % entity.id

#    def _build_edit_url(self, contact):
#        return '/persons/contact/edit/%s' % contact.id

    def test_unicode(self):
        first_name = 'Spike'
        last_name  = 'Spiegel'
        build_contact = partial(Contact, last_name=last_name)
        self.assertEqual(last_name, unicode(build_contact()))
        self.assertEqual(last_name, unicode(build_contact(first_name='')))
        self.assertEqual(_('%(first_name)s %(last_name)s') % {
                                'first_name': first_name,
                                'last_name':  last_name,
                            },
                         unicode(build_contact(first_name=first_name))
                        )

        captain = Civility.objects.create(title='Captain') #no shortcut
        self.assertEqual(_('%(first_name)s %(last_name)s') % {
                                'first_name': first_name,
                                'last_name':  last_name,
                            },
                         unicode(build_contact(first_name=first_name, civility=captain))
                        )

        captain.shortcut = shortcut = 'Cpt'
        captain.save()
        self.assertEqual(_('%(civility)s %(first_name)s %(last_name)s') % {
                            'civility':   shortcut,
                            'first_name': first_name,
                            'last_name':  last_name,
                            },
                         unicode(build_contact(first_name=first_name, civility=captain))
                        )

    def test_createview01(self):
        user = self.login()

#        url = self.ADD_URL
        url = reverse('persons__create_contact')
        self.assertGET200(url)

        count = Contact.objects.count()
        first_name = 'Spike'
        last_name  = 'Spiegel'
        response = self.client.post(url, follow=True,
                                    data={'user':       user.pk,
                                          'first_name': first_name,
                                          'last_name':  last_name,
                                         }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(count + 1, Contact.objects.count())

        contact = self.get_object_or_fail(Contact, first_name=first_name)
        self.assertEqual(last_name,  contact.last_name)
        self.assertIsNone(contact.billing_address)
        self.assertIsNone(contact.shipping_address)

        abs_url = contact.get_absolute_url()
        self.assertEqual('/persons/contact/%s' % contact.id, abs_url)
        self.assertRedirects(response, abs_url)

    @skipIfCustomAddress
    def test_createview02(self):
        "With addresses"
        user = self.login()

        first_name = 'Spike'
        b_address = 'In the Bebop.'
        s_address = 'In the Bebop (bis).'
#        response = self.client.post(self.ADD_URL, follow=True,
        response = self.client.post(reverse('persons__create_contact'), follow=True,
                                    data={'user':                     user.pk,
                                          'first_name':               first_name,
                                          'last_name':                'Spiegel',
                                          'billing_address-address':  b_address,
                                          'shipping_address-address': s_address,
                                         }
                                   )
        self.assertNoFormError(response)

        contact = self.get_object_or_fail(Contact, first_name=first_name)
        self.assertIsNotNone(contact.billing_address)
        self.assertEqual(b_address, contact.billing_address.address)

        self.assertIsNotNone(contact.shipping_address)
        self.assertEqual(s_address, contact.shipping_address.address)

        self.assertContains(response, b_address)
        self.assertContains(response, s_address)

    def test_editview01(self):
        user = self.login()
        first_name = 'Faye'
        contact = Contact.objects.create(user=user, first_name=first_name, last_name='Valentine')

#        url = self._build_edit_url(contact)
        url = contact.get_edit_absolute_url()
        self.assertGET200(url)

        last_name = 'Spiegel'
        response = self.assertPOST200(url, follow=True,
                                      data={'user':       user.pk,
                                            'first_name': first_name,
                                            'last_name':  last_name,
                                           }
                                     )

        contact = self.refresh(contact)
        self.assertEqual(last_name, contact.last_name)
        self.assertIsNone(contact.billing_address)
        self.assertIsNone(contact.shipping_address)

        self.assertRedirects(response, contact.get_absolute_url())

    @skipIfCustomAddress
    def test_editview02(self):
        "Edit addresses"
        user = self.login()

        first_name = 'Faye'
        last_name  = 'Valentine'
#        self.assertPOST200(self.ADD_URL, follow=True,
        self.assertPOST200(reverse('persons__create_contact'), follow=True,
                           data={'user':                     user.pk,
                                 'first_name':               first_name,
                                 'last_name':                last_name,
                                 'billing_address-address':  'In the Bebop.',
                                 'shipping_address-address': 'In the Bebop. (bis)',
                                }
                          )
        contact = Contact.objects.get(first_name=first_name)
        billing_address_id  = contact.billing_address_id
        shipping_address_id = contact.shipping_address_id

        state   = 'Solar system'
        country = 'Mars'
#        self.assertNoFormError(self.client.post(self._build_edit_url(contact), follow=True,
        self.assertNoFormError(self.client.post(contact.get_edit_absolute_url(), follow=True,
                                                data={'user':                     user.pk,
                                                      'first_name':               first_name,
                                                      'last_name':                last_name,
                                                      'billing_address-state':    state,
                                                      'shipping_address-country': country,
                                                     }
                                               )
                              )

        contact = self.refresh(contact)
        self.assertEqual(billing_address_id,  contact.billing_address_id)
        self.assertEqual(shipping_address_id, contact.shipping_address_id)

        self.assertEqual(state,   contact.billing_address.state)
        self.assertEqual(country, contact.shipping_address.country)

    def test_editview03(self):
        "Contact is a user => sync"
        user = self.login()
        contact = self.get_object_or_fail(Contact, is_user=user)

#        url = self._build_edit_url(contact)
        url = contact.get_edit_absolute_url()
        response = self.assertPOST200(url, follow=True,
                                      data={'user':      user.id,
                                            'last_name': contact.last_name,
                                           }
                                     )
        msg = _('This field is required.')
        self.assertFormError(response, 'form', 'first_name', msg)
        self.assertFormError(response, 'form', 'email',      msg)

        first_name = contact.first_name.lower(); self.assertNotEqual(first_name, user.first_name)
        last_name  = contact.last_name.upper();  self.assertNotEqual(last_name,  user.last_name)
        email      = '%s.%s@noir.org' % (user.first_name, user.last_name)
        self.assertNotEqual(email, user.email)

        response = self.client.post(url, follow=True,
                                    data={'user':       user.id,
                                          'last_name':  last_name,
                                          'first_name': first_name,
                                          'email':      email,
                                         }
                                   )
        self.assertNoFormError(response)

        contact = self.refresh(contact)
        self.assertEqual(first_name, contact.first_name)
        self.assertEqual(last_name,  contact.last_name)
        self.assertEqual(email,      contact.email)

        user = self.refresh(user)
        self.assertEqual(first_name, user.first_name)
        self.assertEqual(last_name,  user.last_name)
        self.assertEqual(email,      user.email)

    def test_is_user01(self):
        "Property 'linked_contact'"
        user = self.login()

        with self.assertNumQueries(0):
            rel_contact = user.linked_contact

        contact = self.get_object_or_fail(Contact, is_user=user)
        self.assertEqual(contact, rel_contact)

        user = self.refresh(user) #clean cache

        with self.assertNumQueries(1):
            #rel_contact1 = 
            user.linked_contact

        with self.assertNumQueries(0):
            #rel_contact2 = 
            user.linked_contact

    def test_is_user02(self):
        """Contact.clean() + integrity of User.
        first_name = NULL (not nullable in User)
        email = NULL (not nullable in User)
        """
        user = self.login()
        contact = user.linked_contact
        last_name = contact.last_name
        first_name = contact.first_name

        contact.email = None
        contact.first_name = None
        contact.save()

        user = self.refresh(user)
        self.assertEqual('',         user.first_name)
        self.assertEqual(last_name,  user.last_name)
        self.assertEqual('',         user.email)

        with self.assertRaises(ValidationError) as cm:
            contact.full_clean()

        #self.assertIsInstance(cm.exception, ValidationError)
        self.assertEqual([_('This Contact is related to a user and must have a first name.')],
                         cm.exception.messages
                        )

        contact.first_name = first_name

        with self.assertRaises(ValidationError) as cm:
            contact.full_clean()

        #self.assertIsInstance(cm.exception, ValidationError)
        self.assertEqual([_('This Contact is related to a user and must have an e-mail address.')],
                         cm.exception.messages
                        )

    def test_listview(self):
        user = self.login()

        count = Contact.objects.filter(is_deleted=False).count()

        create_contact = partial(Contact.objects.create, user=user)
        faye    = create_contact(first_name='Faye',    last_name='Valentine')
        spike   = create_contact(first_name='Spike',   last_name='Spiegel')
        vicious = create_contact(first_name='Vicious', last_name='Badguy', is_deleted=True)

#        response = self.assertGET200('/persons/contacts')
        response = self.assertGET200(Contact.get_lv_absolute_url())

        with self.assertNoException():
            contacts_page = response.context['entities']

        #self.assertEqual(3, contacts_page.paginator.count) #3: Creme user
        self.assertEqual(count + 2, contacts_page.paginator.count)

        contacts_set = set(contacts_page.object_list)
        self.assertIn(faye,  contacts_set)
        self.assertIn(spike, contacts_set)
        self.assertNotIn(vicious, contacts_set)

    @skipIfCustomOrganisation
    def test_create_linked_contact01(self):
        user = self.login()

        orga = Organisation.objects.create(user=user, name='Acme')
        redir = orga.get_absolute_url()
#        uri = self.ADD_RELATED_URL % {'orga_id':  orga.id,
#                                      'rtype_id': REL_OBJ_EMPLOYED_BY,
#                                      'url':      redir,
#                                     }
        uri = self._build_addrelated_uri(orga.id, REL_OBJ_EMPLOYED_BY, redir)
        self.assertGET200(uri)

        first_name = 'Bugs'
        last_name = 'Bunny'
        response = self.client.post(uri, follow=True,
                                    data={'orga_overview': 'dontcare',
                                          'relation':      'dontcare',
                                          'user':          user.pk,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                         }
                                   )
        self.assertNoFormError(response)
        self.assertRedirects(response, redir)

        contact = self.get_object_or_fail(Contact, first_name=first_name)
        self.assertRelationCount(1, orga, REL_OBJ_EMPLOYED_BY, contact)
        self.assertEqual(last_name, contact.last_name)

    @skipIfCustomOrganisation
    def test_create_linked_contact02(self):
        "RelationType not fixed"
        user = self.login()

        orga = Organisation.objects.create(user=user, name='Acme')
        uri = self._build_addrelated_uri(orga.id, url=orga.get_absolute_url())
        self.assertGET200(uri)

        first_name = 'Bugs'
        last_name = 'Bunny'
        response = self.client.post(uri, follow=True,
                                    data={'orga_overview': 'dontcare',
                                          'relation':      REL_SUB_EMPLOYED_BY,
                                          'user':          user.pk,
                                          'first_name':    first_name,
                                          'last_name':     last_name,
                                         }
                                   )
        self.assertNoFormError(response)

        contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)
        self.assertRelationCount(1, orga, REL_OBJ_EMPLOYED_BY, contact)

    @skipIfCustomOrganisation
    def test_create_linked_contact03(self):
        "No LINK credentials"
        user = self.login(is_superuser=False, creatable_models=[Contact])

        create_sc = partial(SetCredentials.objects.create, role=self.role,
                            set_type=SetCredentials.ESET_OWN,
                           )
        create_sc(value=EntityCredentials.VIEW   | EntityCredentials.CHANGE |
                        EntityCredentials.DELETE | EntityCredentials.UNLINK, #no LINK
                 )

        orga = Organisation.objects.create(user=user, name='Acme')
        self.assertTrue(user.has_perm_to_view(orga))
        self.assertFalse(user.has_perm_to_link(orga))

#        uri = self.ADD_RELATED_URL % {'orga_id':  orga.id,
#                                      'rtype_id': REL_OBJ_EMPLOYED_BY,
#                                      'url':      orga.get_absolute_url(),
#                                     }
        uri = self._build_addrelated_uri(orga.id, REL_OBJ_EMPLOYED_BY, orga.get_absolute_url())
        self.assertGET403(uri)

        get_ct = ContentType.objects.get_for_model
        create_sc(value=EntityCredentials.LINK, ctype=get_ct(Organisation))
        self.assertGET403(uri)

        create_sc(value=EntityCredentials.LINK, ctype=get_ct(Contact))
        self.assertGET200(uri)

        response = self.assertPOST200(uri, follow=True,
                                      data={'orga_overview': 'dontcare',
                                            'relation':      'dontcare',
                                            'user':          self.other_user.pk,
                                            'first_name':    'Bugs',
                                            'last_name':     'Bunny',
                                           }
                                     )
        self.assertFormError(response, 'form', 'user',
                             _(u'You are not allowed to link with the «%s» of this user.') % 
                                _(u'Contacts')
                            )

    @skipIfCustomOrganisation
    def test_create_linked_contact04(self):
        user = self.login()

        orga = Organisation.objects.create(user=user, name='Acme')
#        url = self.ADD_RELATED_URL
#
#        self.assertGET404(url % {'orga_id':  1024, #doesn't exist
#                                 'rtype_id': REL_OBJ_EMPLOYED_BY,
#                                 'url':      orga.get_absolute_url(),
#                                }
#                         )
#        self.assertGET404(url % {'orga_id':  orga.id,
#                                 'rtype_id': 'IDONOTEXIST',
#                                 'url':      orga.get_absolute_url(),
#                                }
#                        )
        self.assertGET404(self._build_addrelated_uri(1024, #doesn't exist
                                                     REL_OBJ_EMPLOYED_BY,
                                                     orga.get_absolute_url(),
                                                   )
                         )
        self.assertGET404(self._build_addrelated_uri(orga.id,
                                                     'IDONOTEXIST',
                                                     orga.get_absolute_url(),
                                                    )
                        )

        create_rtype = RelationType.create
        rtype1 = create_rtype(('persons-subject_test_rtype1', u'RType #1',     [Organisation]),
                              ('persons-object_test_rtype1',  u'Rtype sym #1', [Contact]),
                             )[0]
        self.assertGET200(self._build_addrelated_uri(orga.id, rtype1.id))

        rtype2 = create_rtype(('persons-subject_test_badrtype1', u'Bad RType #1',     [Organisation]),
                              ('persons-object_test_badrtype1',  u'Bad RType sym #1', [Image]), # <==
                             )[0]
        self.assertGET409(self._build_addrelated_uri(orga.id, rtype2.id))

        rtype3 = create_rtype(('persons-subject_test_badrtype2', u'Bad RType #2',     [Image]), # <==
                              ('persons-object_test_badrtype2',  u'Bad RType sym #2', [Contact]),
                              #is_internal=True,
                             )[0]
        self.assertGET409(self._build_addrelated_uri(orga.id, rtype3.id))

        rtype4 = create_rtype(('persons-subject_test_badrtype3', u'Bad RType #3',     [Organisation]),
                              ('persons-object_test_badrtype3',  u'Bad RType sym #3', [Contact]),
                              is_internal=True,  # <==
                             )[0]
        self.assertGET409(self._build_addrelated_uri(orga.id, rtype4.id))

    @skipIfCustomOrganisation
    def test_create_linked_contact05(self):
        "Avoid internal RelationType"
        user = self.login()

        orga = Organisation.objects.create(user=user, name='Acme')
        rtype = RelationType.create(('persons-subject_test_linked', u'is the employee of the month at', [Contact]),
                                    ('persons-object_test_linked',  u'has the employee of the month',   [Organisation]),
                                    is_internal=True,
                                   )[0]

        response = self.assertPOST200(self._build_addrelated_uri(orga.id),
                                      follow=True,
                                      data={'orga_overview': 'dontcare',
                                            'relation':      rtype.id,
                                            'user':          user.pk,
                                            'first_name':    'Bugs',
                                            'last_name':     'Bunny',
                                            }
                                    )
        self.assertFormError(response, 'form', 'relation',
                             _(u'Select a valid choice. That choice is not one of the available choices.')
                            )

    @skipIfCustomAddress
    def test_clone(self):
        "Addresses & is_user are problematic"
        user = self.login()

        #naruto = Contact.objects.create(user=user, is_user=user,
                                        #first_name='Naruto', last_name='Uzumaki'
                                       #)
        naruto = self.get_object_or_fail(Contact, is_user=user)

        create_address = partial(Address.objects.create,
                                 city='Konoha', state='Konoha', zipcode='111',
                                 country='The land of fire', department="Ninjas' homes",
                                 content_type=ContentType.objects.get_for_model(Contact),
                                 object_id=naruto.id,
                                )
        naruto.billing_address  = create_address(name="Naruto's", address='Home', po_box='000')
        naruto.shipping_address = create_address(name="Naruto's", address='Home (second entry)', po_box='001')
        naruto.save()

        for i in xrange(5):
            create_address(name='Secret Cave #%s' % i, address='Cave #%s' % i, po_box='XXX')

        kage_bunshin = naruto.clone()

        self.assertEqual(naruto.first_name, kage_bunshin.first_name)
        self.assertEqual(naruto.last_name, kage_bunshin.last_name)
        self.assertIsNone(kage_bunshin.is_user) #<====

        self.assertEqual(naruto.id, naruto.billing_address.object_id)
        self.assertEqual(naruto.id, naruto.shipping_address.object_id)

        self.assertEqual(kage_bunshin.id, kage_bunshin.billing_address.object_id)
        self.assertEqual(kage_bunshin.id, kage_bunshin.shipping_address.object_id)

        addresses   = list(Address.objects.filter(object_id=naruto.id))
        c_addresses = list(Address.objects.filter(object_id=kage_bunshin.id))
        self.assertEqual(7, len(addresses))
        self.assertEqual(7, len(c_addresses))

        addresses_map   = {a.address: a for a in addresses}
        c_addresses_map = {a.address: a for a in c_addresses}
        self.assertEqual(7, len(addresses_map))
        self.assertEqual(7, len(c_addresses_map))

        for ident, address in addresses_map.iteritems():
            address2 = c_addresses_map.get(ident)
            self.assertIsNotNone(address2, ident)
            self.assertAddressOnlyContentEqual(address, address2)

    def test_delete01(self):
        user = self.login()
        naruto = Contact.objects.create(user=user, first_name='Naruto', last_name='Uzumaki')
        url = self._build_delete_url(naruto)
        self.assertPOST200(url, follow=True)

        with self.assertNoException():
            naruto = self.refresh(naruto)

        self.assertIs(naruto.is_deleted, True)

        self.assertPOST200(url, follow=True)
        self.assertDoesNotExist(naruto)

    def test_delete02(self):
        "Can not delete if the Contact corresponds to an user"
        user = self.login()
        #naruto = Contact.objects.create(user=user, is_user=user, is_deleted=True,
                                        #first_name='Naruto', last_name='Uzumaki'
                                       #)
        #self.assertPOST403(self._build_delete_url(naruto), follow=True)
        #contact = self.get_object_or_fail(Contact, is_user=user)
        contact = user.linked_contact
        self.assertPOST403(self._build_delete_url(contact), follow=True)

    def test_delete03(self):
        "Can not trash if the Contact corresponds to an user"
        user = self.login()
        #naruto = Contact.objects.create(user=user, is_user=user,
                                        #first_name='Naruto', last_name='Uzumaki'
                                       #)
        #self.assertPOST403(self._build_delete_url(naruto), follow=True)
        #contact = self.get_object_or_fail(Contact, is_user=user)
        contact = user.linked_contact
        self.assertPOST403(self._build_delete_url(contact), follow=True)

    def _build_quickform_url(self, count):
        ct = ContentType.objects.get_for_model(Contact)
        return '/creme_core/quickforms/%s/%s' % (ct.id, count)

    def test_quickform01(self):
        "2 Contacts created"
        user = self.login()

        contact_count = Contact.objects.count()
        orga_count = Organisation.objects.count()

        models = set(quickforms_registry.iter_models())
        self.assertIn(Contact, models)
        self.assertIn(Organisation, models)

        data = [('Faye', 'Valentine'), ('Spike', 'Spiegel')]

        url = self._build_quickform_url(len(data))
        response = self.assertGET200(url)

        with self.assertNoException():
            orga_f = response.context['formset'][0].fields['organisation']

        self.assertEqual(_(u'If no organisation is found, a new one will be created.'),
                         orga_f.help_text
                        )
        self.assertIsInstance(orga_f.widget, TextInput)
        self.assertFalse(isinstance(orga_f.widget, Label))
        self.assertFalse(orga_f.initial)

        response = self.client.post(url, data={'form-TOTAL_FORMS':   len(data),
                                               'form-INITIAL_FORMS': 0,
                                               'form-MAX_NUM_FORMS': u'',
                                               'form-0-user':        user.id,
                                               'form-0-first_name':  data[0][0],
                                               'form-0-last_name':   data[0][1],
                                               'form-1-user':        user.id,
                                               'form-1-first_name':  data[1][0],
                                               'form-1-last_name':   data[1][1],
                                              }
                                   )
        self.assertNoFormError(response)

        #self.assertEqual(3, Contact.objects.count())
        self.assertEqual(contact_count + 2, Contact.objects.count())
        self.assertEqual(orga_count, Organisation.objects.count())

        for first_name, last_name in data:
            self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)

    @skipIfCustomOrganisation
    def test_quickform02(self):
        "2 Contacts & 1 Organisation created"
        self.login(is_superuser=False, creatable_models=[Contact, Organisation])
        count = Contact.objects.count()

        create_sc = partial(SetCredentials.objects.create, role=self.role,
                            set_type=SetCredentials.ESET_OWN,
                           )
        create_sc(value=EntityCredentials.VIEW)
        create_sc(value=EntityCredentials.LINK)

        orga_name = 'Bebop'
        self.assertFalse(Organisation.objects.filter(name=orga_name).exists())
        existing_orga = Organisation.objects.create(user=self.other_user, name=orga_name) #not viewable

        data = [('Faye', 'Valentine', orga_name), ('Spike', 'Spiegel', orga_name)]
        response = self.client.post(self._build_quickform_url(len(data)),
                                    data={'form-TOTAL_FORMS':      len(data),
                                          'form-INITIAL_FORMS':    0,
                                          'form-MAX_NUM_FORMS':    u'',
                                          'form-0-user':           self.user.id,
                                          'form-0-first_name':     data[0][0],
                                          'form-0-last_name':      data[0][1],
                                          'form-0-organisation':   data[0][2],
                                          'form-1-user':           self.user.id,
                                          'form-1-first_name':     data[1][0],
                                          'form-1-last_name':      data[1][1],
                                          'form-1-organisation':   data[1][2],
                                         }
                                   )
        self.assertNoFormError(response)

        #self.assertEqual(3, Contact.objects.count())
        self.assertEqual(count + 2, Contact.objects.count())

        orgas = Organisation.objects.filter(name=orga_name)
        self.assertEqual(2, len(orgas))

        created_orga = next(o for o in orgas if o != existing_orga)

        for first_name, last_name, orga_name in data:
            contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)
            self.assertRelationCount(1, contact, REL_SUB_EMPLOYED_BY, created_orga)

    @skipIfCustomOrganisation
    def test_quickform03(self):
        "2 Contacts created and link with an existing Organisation"
        user = self.login(is_superuser=False, creatable_models=[Contact, Organisation])
        count = Contact.objects.count()

        SetCredentials.objects.create(role=self.role,
                                      value=EntityCredentials.VIEW | EntityCredentials.LINK,
                                      set_type=SetCredentials.ESET_OWN,
                                     )

        orga_name = 'Bebop'
        self.assertFalse(Organisation.objects.filter(name=orga_name))

        create_orga = partial(Organisation.objects.create, name=orga_name)
        orga1 = create_orga(user=user)
        orga2 = create_orga(user=self.other_user) #this one can not be seen by user

        data = [('Faye', 'Valentine', orga_name), ('Spike', 'Spiegel', orga_name)]
        response = self.client.post(self._build_quickform_url(len(data)),
                                    data={'form-TOTAL_FORMS':      len(data),
                                          'form-INITIAL_FORMS':    0,
                                          'form-MAX_NUM_FORMS':    u'',
                                          'form-0-user':           user.id,
                                          'form-0-first_name':     data[0][0],
                                          'form-0-last_name':      data[0][1],
                                          'form-0-organisation':   data[0][2],
                                          'form-1-user':           user.id,
                                          'form-1-first_name':     data[1][0],
                                          'form-1-last_name':      data[1][1],
                                          'form-1-organisation':   data[1][2],
                                         }
                                    )
        self.assertNoFormError(response)

        #self.assertEqual(3, Contact.objects.count())
        self.assertEqual(count + 2, Contact.objects.count())
        self.assertEqual(2, Organisation.objects.filter(name=orga_name).count())

        for first_name, last_name, orga_name in data:
            contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)
            self.assertRelationCount(1, contact, REL_SUB_EMPLOYED_BY, orga1)
            self.assertRelationCount(0, contact, REL_SUB_EMPLOYED_BY, orga2)

    def test_quickform04(self):
        "No permission to create Organisation"
        user = self.login(is_superuser=False, creatable_models=[Contact]) #<== no Organisation

        SetCredentials.objects.create(role=self.role,
                                      value=EntityCredentials.VIEW | EntityCredentials.LINK,
                                      set_type=SetCredentials.ESET_ALL
                                     )

        orga_name = 'Bebop'
        self.assertFalse(Organisation.objects.filter(name=orga_name).exists())

        contact_count = Contact.objects.count()
        orga_count = Organisation.objects.count()

        url = self._build_quickform_url(1)
        response = self.assertGET200(url)

        with self.assertNoException():
            orga_f = response.context['formset'][0].fields['organisation']

        self.assertEqual(_(u'Enter the name of an existing Organisation.'),
                         unicode(orga_f.help_text)
                        )

        response = self.client.post(url,
                                    data={'form-TOTAL_FORMS':      1,
                                          'form-INITIAL_FORMS':    0,
                                          'form-MAX_NUM_FORMS':    u'',
                                          'form-0-user':           user.id,
                                          'form-0-first_name':     'Faye',
                                          'form-0-last_name':      'Valentine',
                                          'form-0-organisation':   orga_name,
                                         }
                                   )
        #self.assertFormSetError(response, 'formset', 0, 'organisation',
        self.assertFormsetError(response, 'formset', 0, 'organisation',
                                [_(u'You are not allowed to create an Organisation.')]
                               )
        self.assertEqual(contact_count, Contact.objects.count())
        self.assertEqual(orga_count, Organisation.objects.count())

    def test_quickform05(self):
        "No permission to link Organisation"
        user = self.login(is_superuser=False, creatable_models=[Contact])

        create_sc = partial(SetCredentials.objects.create, role=self.role,
                            set_type=SetCredentials.ESET_ALL
                           )
        create_sc(value=EntityCredentials.VIEW)
        create_sc(value=EntityCredentials.LINK,
                  ctype=ContentType.objects.get_for_model(Contact),
                 )

        orga_count = Organisation.objects.count()

        url = self._build_quickform_url(1)
        response = self.assertGET200(url)

        with self.assertNoException():
            orga_f = response.context['formset'][0].fields['organisation']

        self.assertIsInstance(orga_f.widget, Label)
        self.assertFalse(unicode(orga_f.help_text))
        self.assertEqual(_(u'You are not allowed to link with an Organisation'),
                         orga_f.initial
                        )

        first_name = 'Faye'
        last_name = 'Valentine'
        self.client.post(url,
                         data={'form-TOTAL_FORMS':      1,
                               'form-INITIAL_FORMS':    0,
                               'form-MAX_NUM_FORMS':    u'',
                               'form-0-user':           user.id,
                               'form-0-first_name':     first_name,
                               'form-0-last_name':      last_name,
                               'form-0-organisation':   'Bebop',
                              }
                        )
        #self.assertFormSetError(response, 'formset', 0, 'organisation', None)
        self.assertFormsetError(response, 'formset', 0, 'organisation', None)

        contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)
        self.assertEqual(orga_count, Organisation.objects.count())
        self.assertFalse(Relation.objects.filter(subject_entity=contact))

    def test_quickform06(self):
        "No permission to link Contact in general"
        self.login(is_superuser=False, creatable_models=[Contact, Organisation])

        create_sc = partial(SetCredentials.objects.create, role=self.role,
                            set_type=SetCredentials.ESET_ALL,
                           )
        create_sc(value=EntityCredentials.VIEW)
        create_sc(value=EntityCredentials.LINK,
                  ctype=ContentType.objects.get_for_model(Organisation),
                 )

        response = self.assertGET200(self._build_quickform_url(1))

        with self.assertNoException():
            orga_f = response.context['formset'][0].fields['organisation']

        self.assertIsInstance(orga_f.widget, Label)
        self.assertEqual(_(u'You are not allowed to link with a Contact'),
                         orga_f.initial
                        )

    def test_quickform07(self):
        "No permission to link Contact with a specific owner"
        self.login(is_superuser=False, creatable_models=[Contact, Organisation])

        get_ct = ContentType.objects.get_for_model
        create_sc = partial(SetCredentials.objects.create, role=self.role)
        create_sc(value=EntityCredentials.VIEW, set_type=SetCredentials.ESET_ALL)
        create_sc(value=EntityCredentials.LINK, set_type=SetCredentials.ESET_ALL, ctype=get_ct(Organisation))
        create_sc(value=EntityCredentials.LINK, set_type=SetCredentials.ESET_OWN, ctype=get_ct(Contact))

        url = self._build_quickform_url(1)
        response = self.assertGET200(url)

        with self.assertNoException():
            orga_f = response.context['formset'][0].fields['organisation']

        self.assertIsNone(orga_f.initial)

        first_name = 'Faye'
        last_name = 'Valentine'
        data = {'form-TOTAL_FORMS':     1,
                'form-INITIAL_FORMS':   0,
                'form-MAX_NUM_FORMS':   u'',
                'form-0-user':          self.other_user.id,
                'form-0-first_name':    'Faye',
                'form-0-last_name':     'Valentine',
               }
        response = self.client.post(url, data=dict(data, **{'form-0-organisation': 'Bebop'}))
        #self.assertFormSetError(response, 'formset', 0, None,
        self.assertFormsetError(response, 'formset', 0, None,
                                [_(u'You are not allowed to link with the «%s» of this user.') %
                                    _(u'Contacts')
                                ]
                               )

        response = self.client.post(url, data=data)
        #self.assertFormSetError(response, 'formset', 0, None, expected_errors=None)
        self.assertFormsetError(response, 'formset', 0, field=None, errors=None)
        self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)

    @skipIfCustomOrganisation
    def test_quickform08(self):
        "Multiple Organisations found"
        user = self.login()

        orga_name = 'Bebop'
        create_orga = partial(Organisation.objects.create, name=orga_name)
        create_orga(user=user)
        create_orga(user=self.other_user)

        response = self.client.post(self._build_quickform_url(1),
                                    data={'form-TOTAL_FORMS':      1,
                                          'form-INITIAL_FORMS':    0,
                                          'form-MAX_NUM_FORMS':    u'',
                                          'form-0-user':           user.id,
                                          'form-0-first_name':     'Faye',
                                          'form-0-last_name':      'Valentine',
                                          'form-0-organisation':   orga_name,
                                         }
                                   )
        #self.assertFormSetError(response, 'formset', 0, 'organisation',
        self.assertFormsetError(response, 'formset', 0, 'organisation',
                                [_(u'Several Organisations with this name have been found.')]
                               )

    @skipIfCustomOrganisation
    def test_quickform09(self):
        "Multiple Organisations found, only one linkable (so we use it)"
        user = self.login(is_superuser=False, creatable_models=[Contact, Organisation])

        create_sc = partial(SetCredentials.objects.create, role=self.role)
        create_sc(value=EntityCredentials.VIEW, set_type=SetCredentials.ESET_ALL)
        create_sc(value=EntityCredentials.LINK, set_type=SetCredentials.ESET_OWN)

        orga_name = 'Bebop'
        create_orga = partial(Organisation.objects.create, name=orga_name)
        orga1 = create_orga(user=user)
        create_orga(user=self.other_user) #can not be linked by user

        first_name = 'Faye'
        last_name = 'Valentine'
        response = self.client.post(self._build_quickform_url(1),
                                    data={'form-TOTAL_FORMS':      1,
                                          'form-INITIAL_FORMS':    0,
                                          'form-MAX_NUM_FORMS':    u'',
                                          'form-0-user':           user.id,
                                          'form-0-first_name':     first_name,
                                          'form-0-last_name':      last_name,
                                          'form-0-organisation':   orga_name,
                                         }
                                   )
        #self.assertFormSetError(response, 'formset', 0, 'organisation', None)
        self.assertFormsetError(response, 'formset', 0, 'organisation', None)

        contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)
        self.assertRelationCount(1, contact, REL_SUB_EMPLOYED_BY, orga1)

    @skipIfCustomOrganisation
    def test_quickform10(self):
        "Multiple Organisations found, but none of them is linkable"
        user = self.login(is_superuser=False, creatable_models=[Contact, Organisation])

        create_sc = partial(SetCredentials.objects.create, role=self.role)
        create_sc(value=EntityCredentials.VIEW, set_type=SetCredentials.ESET_ALL)
        create_sc(value=EntityCredentials.LINK, set_type=SetCredentials.ESET_OWN)

        orga_name = 'Bebop'

        for i in xrange(2):
            Organisation.objects.create(user=self.other_user, name=orga_name)

        response = self.client.post(self._build_quickform_url(1),
                                    data={'form-TOTAL_FORMS':      1,
                                          'form-INITIAL_FORMS':    0,
                                          'form-MAX_NUM_FORMS':    u'',
                                          'form-0-user':           user.id,
                                          'form-0-first_name':     'Faye',
                                          'form-0-last_name':      'Valentine',
                                          'form-0-organisation':   orga_name,
                                         }
                                   )
        #self.assertFormSetError(response, 'formset', 0, 'organisation',
        self.assertFormsetError(response, 'formset', 0, 'organisation',
                                [_(u'No linkable Organisation found.')]
                               )

    def test_quickform11(self):
        "Have to create an Organisations, but can not link to it"
        self.login(is_superuser=False, creatable_models=[Contact, Organisation])

        create_sc = partial(SetCredentials.objects.create, role=self.role)
        create_sc(value=EntityCredentials.VIEW, set_type=SetCredentials.ESET_ALL)
        create_sc(value=EntityCredentials.LINK, set_type=SetCredentials.ESET_ALL,
                  ctype=ContentType.objects.get_for_model(Contact),
                 )
        create_sc(value=EntityCredentials.LINK, set_type=SetCredentials.ESET_OWN)

        orga_name = 'Bebop'
        self.assertFalse(Organisation.objects.filter(name=orga_name).exists())

        response = self.client.post(self._build_quickform_url(1),
                                    data={'form-TOTAL_FORMS':      1,
                                          'form-INITIAL_FORMS':    0,
                                          'form-MAX_NUM_FORMS':    u'',
                                          'form-0-user':           self.other_user.id,
                                          'form-0-first_name':     'Faye',
                                          'form-0-last_name':      'Valentine',
                                          'form-0-organisation':   orga_name,
                                         }
                                   )
        #self.assertFormSetError(response, 'formset', 0, None,
        self.assertFormsetError(response, 'formset', 0, None,
                                [_(u'You are not allowed to link with the «%s» of this user.') % 
                                    _(u'Organisations')
                                ]
                               )

    @skipIfCustomOrganisation
    def test_quickform12(self):
        "Multiple Organisations found, only one is not deleted (so we use it)"
        user = self.login()

        orga_name = 'Bebop'
        create_orga = partial(Organisation.objects.create, name=orga_name, user=user)
        create_orga(is_deleted=True)
        orga2 = create_orga()

        first_name = 'Faye'
        last_name = 'Valentine'
        response = self.client.post(self._build_quickform_url(1),
                                    data={'form-TOTAL_FORMS':    1,
                                          'form-INITIAL_FORMS':  0,
                                          'form-MAX_NUM_FORMS':  u'',
                                          'form-0-user':         user.id,
                                          'form-0-first_name':   first_name,
                                          'form-0-last_name':    last_name,
                                          'form-0-organisation': orga_name,
                                         }
                                   )
        #self.assertFormSetError(response, 'formset', 0, 'organisation', None)
        self.assertFormsetError(response, 'formset', 0, 'organisation', None)

        contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)
        self.assertRelationCount(1, contact, REL_SUB_EMPLOYED_BY, orga2)

    @skipIfCustomAddress
    def test_merge01(self):
        "Merging addresses"
        user = self.login()

        create_contact = partial(Contact.objects.create, user=user)
        contact01 = create_contact(first_name='Faye', last_name='Valentine')
        contact02 = create_contact(first_name='FAYE', last_name='VALENTINE')

        create_address = Address.objects.create
        bill_addr01 = create_address(name="Billing address 01",
                                     address="BA1 - Address", po_box="BA1 - PO box",
                                     zipcode="BA1 - Zip code", city="BA1 - City",
                                     department="BA1 - Department",
                                     state="BA1 - State", country="BA1 - Country",
                                     owner=contact01,
                                    )
        #NB: no shipping address for contact01
        contact01.billing_address = bill_addr01
        contact01.save()

        #NB: no billing address for contact02
        ship_addr02 = create_address(name="Shipping address 02",
                                     address="SA2 - Address", po_box="SA2 - PO box",
                                     zipcode="SA2 - Zip code", city="SA2 - City",
                                     department="SA2 - Department",
                                     state="SA2 - State", country="SA2 - Country",
                                     owner=contact02,
                                    )
        other_addr02 = create_address(name="Other address 02", owner=contact02)

        contact02.shipping_address = ship_addr02
        contact02.save()

        url = self.build_merge_url(contact01, contact02)
        context = self.client.get(url).context

        with self.assertNoException():
            f_baddr = context['form'].fields['billaddr_address']

        self.assertEqual([bill_addr01.address, '', bill_addr01.address], f_baddr.initial)

        response = self.client.post(url, follow=True,
                                    data={'user_1':      user.id,
                                          'user_2':      user.id,
                                          'user_merged': user.id,

                                          'first_name_1':      contact01.first_name,
                                          'first_name_2':      contact02.first_name,
                                          'first_name_merged': contact01.first_name,

                                          'last_name_1':      contact01.last_name,
                                          'last_name_2':      contact02.last_name,
                                          'last_name_merged': contact01.last_name,

                                           #Billing address
                                          'billaddr_address_1':      bill_addr01.address,
                                          'billaddr_address_2':      '',
                                          'billaddr_address_merged': bill_addr01.address,

                                          'billaddr_po_box_1':      bill_addr01.po_box,
                                          'billaddr_po_box_2':      '',
                                          'billaddr_po_box_merged': 'Merged PO box',

                                          'billaddr_city_1':      bill_addr01.city,
                                          'billaddr_city_2':      '',
                                          'billaddr_city_merged': 'Merged city',

                                          'billaddr_state_1':      bill_addr01.state,
                                          'billaddr_state_2':      '',
                                          'billaddr_state_merged': 'Merged state',

                                          'billaddr_zipcode_1':      bill_addr01.zipcode,
                                          'billaddr_zipcode_2':      '',
                                          'billaddr_zipcode_merged': 'Merged zipcode',

                                          'billaddr_country_1':      bill_addr01.country,
                                          'billaddr_country_2':      '',
                                          'billaddr_country_merged': 'Merged country',

                                          'billaddr_department_1':      bill_addr01.department,
                                          'billaddr_department_2':      '',
                                          'billaddr_department_merged': 'Merged department',

                                          #Shipping address
                                          'shipaddr_address_1':      '',
                                          'shipaddr_address_2':      ship_addr02.address,
                                          'shipaddr_address_merged': ship_addr02.address,

                                          'shipaddr_po_box_1':      '',
                                          'shipaddr_po_box_2':      ship_addr02.po_box,
                                          'shipaddr_po_box_merged': 'Merged PO box 2',

                                          'shipaddr_city_1':      '',
                                          'shipaddr_city_2':      ship_addr02.city,
                                          'shipaddr_city_merged': 'Merged city 2',

                                          'shipaddr_state_1':      '',
                                          'shipaddr_state_2':      ship_addr02.state,
                                          'shipaddr_state_merged': 'Merged state 2',

                                          'shipaddr_zipcode_1':      '',
                                          'shipaddr_zipcode_2':      ship_addr02.zipcode,
                                          'shipaddr_zipcode_merged': 'Merged zipcode 2',

                                          'shipaddr_country_1':      '',
                                          'shipaddr_country_2':      ship_addr02.country,
                                          'shipaddr_country_merged': 'Merged country 2',

                                          'shipaddr_department_1':      '',
                                          'shipaddr_department_2':      ship_addr02.department,
                                          'shipaddr_department_merged': 'Merged department 2',
                                         }
                                   )
        self.assertNoFormError(response)
        self.assertDoesNotExist(contact02)

        with self.assertNoException():
            contact01 = self.refresh(contact01)

        addresses = Address.objects.filter(object_id=contact01.id)
        self.assertEqual(3, len(addresses))

        self.assertIn(bill_addr01,  addresses)
        self.assertIn(ship_addr02,  addresses)
        self.assertIn(other_addr02, addresses)

        billing_address = contact01.billing_address
        self.assertEqual(bill_addr01,         billing_address)
        self.assertEqual(bill_addr01.address, billing_address.address)
        self.assertEqual('Merged PO box',     billing_address.po_box)
        self.assertEqual('Merged city',       billing_address.city)
        self.assertEqual('Merged state',      billing_address.state)
        self.assertEqual('Merged zipcode',    billing_address.zipcode)
        self.assertEqual('Merged country',    billing_address.country)
        self.assertEqual('Merged department', billing_address.department)

        shipping_address = contact01.shipping_address
        self.assertEqual(ship_addr02,           shipping_address)
        self.assertEqual(contact01,             shipping_address.owner)
        self.assertEqual('Merged PO box 2',     shipping_address.po_box)
        self.assertEqual('Merged city 2',       shipping_address.city)
        self.assertEqual('Merged state 2',      shipping_address.state)
        self.assertEqual('Merged zipcode 2',    shipping_address.zipcode)
        self.assertEqual('Merged country 2',    shipping_address.country)
        self.assertEqual('Merged department 2', shipping_address.department)

    @skipIfCustomAddress
    def test_merge02(self):
        "Merging addresses -> empty addresses"
        user = self.login()

        create_contact = partial(Contact.objects.create, user=user)
        contact01 = create_contact(first_name='Faye', last_name='Valentine')
        contact02 = create_contact(first_name='FAYE', last_name='VALENTINE')

        ship_addr02 = Address.objects.create(name="Shipping address 02",
                                             address="SA2 - Address", po_box="SA2 - PO box",
                                             zipcode="SA2 - Zip code", city="SA2 - City",
                                             department="SA2 - Department",
                                             state="SA2 - State", country="SA2 - Country",
                                             owner=contact02,
                                            )
        contact02.shipping_address = ship_addr02
        contact02.save()

        response = self.client.post(self.build_merge_url(contact01, contact02),
                                    follow=True,
                                    data={'user_1':      user.id,
                                          'user_2':      user.id,
                                          'user_merged': user.id,

                                          'first_name_1':      contact01.first_name,
                                          'first_name_2':      contact02.first_name,
                                          'first_name_merged': contact01.first_name,

                                          'last_name_1':      contact01.last_name,
                                          'last_name_2':      contact02.last_name,
                                          'last_name_merged': contact01.last_name,

                                           #Billing address
                                          'billaddr_name_1':      '',
                                          'billaddr_name_2':      '',
                                          'billaddr_name_merged': '',

                                          'billaddr_address_1':      '',
                                          'billaddr_address_2':      '',
                                          'billaddr_address_merged': '',

                                          'billaddr_po_box_1':      '',
                                          'billaddr_po_box_2':      '',
                                          'billaddr_po_box_merged': '',

                                          'billaddr_city_1':      '',
                                          'billaddr_city_2':      '',
                                          'billaddr_city_merged': '',

                                          'billaddr_state_1':      '',
                                          'billaddr_state_2':      '',
                                          'billaddr_state_merged': '',

                                          'billaddr_zipcode_1':      '',
                                          'billaddr_zipcode_2':      '',
                                          'billaddr_zipcode_merged': '',

                                          'billaddr_country_1':      '',
                                          'billaddr_country_2':      '',
                                          'billaddr_country_merged': '',

                                          'billaddr_department_1':      '',
                                          'billaddr_department_2':      '',
                                          'billaddr_department_merged': '',

                                          #Shipping address
                                          'shipaddr_name_1':      '',
                                          'shipaddr_name_2':      ship_addr02.name,
                                          'shipaddr_name_merged': '',

                                          'shipaddr_address_1':      '',
                                          'shipaddr_address_2':      ship_addr02.address,
                                          'shipaddr_address_merged': '',

                                          'shipaddr_po_box_1':      '',
                                          'shipaddr_po_box_2':      ship_addr02.po_box,
                                          'shipaddr_po_box_merged': '',

                                          'shipaddr_city_1':      '',
                                          'shipaddr_city_2':      ship_addr02.city,
                                          'shipaddr_city_merged': '',

                                          'shipaddr_state_1':      '',
                                          'shipaddr_state_2':      ship_addr02.state,
                                          'shipaddr_state_merged': '',

                                          'shipaddr_zipcode_1':      '',
                                          'shipaddr_zipcode_2':      ship_addr02.zipcode,
                                          'shipaddr_zipcode_merged': '',

                                          'shipaddr_country_1':      '',
                                          'shipaddr_country_2':      ship_addr02.country,
                                          'shipaddr_country_merged': '',

                                          'shipaddr_department_1':      '',
                                          'shipaddr_department_2':      ship_addr02.department,
                                          'shipaddr_department_merged': '',
                                         }
                                   )
        self.assertNoFormError(response)
        self.assertDoesNotExist(contact02)

        with self.assertNoException():
            contact01 = self.refresh(contact01)

        self.assertFalse(Address.objects.filter(object_id=contact01.id))
        self.assertIsNone(contact01.billing_address)
        self.assertIsNone(contact01.shipping_address)

    def test_merge03(self):
        "Merge 1 Contact which represents a user with another Contact"
        user = self.login()

        contact01 = user.linked_contact
        first_name1 = contact01.first_name
        last_name2 = 'VALENTINE'
        contact02 = Contact.objects.create(user=user, first_name='FAYE', last_name=last_name2)

        url = self.build_merge_url(contact01, contact02)
        self.assertGET200(url)

        data = {'user_1':      user.id,
                'user_2':      user.id,
                'user_merged': user.id,

                'first_name_1':      first_name1,
                'first_name_2':      contact02.first_name,
                'first_name_merged': first_name1,

                'last_name_1':      contact01.last_name,
                'last_name_2':      last_name2,
                'last_name_merged': last_name2,

                'email_1':      contact01.email,
                'email_2':      contact02.email,
                'email_merged': '',
               }
        response = self.assertPOST200(url, follow=True, data=data)
        self.assertFormError(response, 'form', None,
                             _('This Contact is related to a user and must have an e-mail address.')
                            )

        response = self.client.post(url, follow=True,
                                    data=dict(data,
                                              email_merged=contact01.email,
                                             )
                                   )
        self.assertNoFormError(response)

        self.assertDoesNotExist(contact02)

        with self.assertNoException():
            contact01 = self.refresh(contact01)
            user = self.refresh(user)

        self.assertEqual(user,        contact01.is_user)
        self.assertEqual(first_name1, user.first_name)
        self.assertEqual(last_name2,  user.last_name)

    def test_merge04(self):
        "Merge 1 Contact with another one which represents a user (entity swap)"
        user = self.login()

        first_name1 = 'FAYE'
        contact01 = Contact.objects.create(user=user, first_name=first_name1, last_name='VALENTINE')
        contact02 = user.linked_contact

        url = self.build_merge_url(contact01, contact02)
        response = self.assertGET200(url)

        with self.assertNoException():
            first_name_f = response.context['form'].fields['first_name']

        self.assertEqual([contact02.first_name, #the entities have been swapped (to keep the user-contact first)
                          contact01.first_name,
                          contact02.first_name,
                         ],
                         first_name_f.initial
                        )

        data = {'user_1':      user.id,
                'user_2':      user.id,
                'user_merged': user.id,

                'first_name_1':      contact02.first_name,
                'first_name_2':      first_name1,
                'first_name_merged': first_name1,

                'last_name_1':      contact02.last_name,
                'last_name_2':      contact01.last_name,
                'last_name_merged': contact01.last_name,
               }
        response = self.assertPOST200(url, follow=True, data=data)
        self.assertFormError(response, 'form', None,
                             _('This Contact is related to a user and must have an e-mail address.')
                            )

        response = self.client.post(url, follow=True,
                                    data=dict(data,
                                              email_1=contact02.email,
                                              email_2=contact01.email,
                                              email_merged=contact02.email,
                                             )
                                   )
        self.assertNoFormError(response)

        self.assertDoesNotExist(contact01)

        with self.assertNoException():
            contact02 = self.refresh(contact02)

        self.assertEqual(user,        contact02.is_user)
        self.assertEqual(first_name1, contact02.first_name)

    def test_merge05(self):
        "Cannot merge 2 Contacts that represent 2 users"
        user = self.login()

        contact01 = user.linked_contact
        contact02 = self.other_user.linked_contact

        self.assertGET409(self.build_merge_url(contact01, contact02))
        self.assertGET409(self.build_merge_url(contact02, contact01))

    def test_delete_civility(self):
        "Set to null"
        user = self.login()
        captain = Civility.objects.create(title='Captain')
        harlock = Contact.objects.create(user=user, first_name='Harlock',
                                         last_name='Matsumoto', civility=captain,
                                        )

        self.assertPOST200('/creme_config/persons/civility/delete', data={'id': captain.pk})
        self.assertDoesNotExist(captain)

        harlock = self.get_object_or_fail(Contact, pk=harlock.pk)
        self.assertIsNone(harlock.civility)

    def test_delete_position(self):
        "Set to null"
        user = self.login()
        captain = Position.objects.create(title='Captain')
        harlock = Contact.objects.create(user=user, first_name='Harlock',
                                         last_name='Matsumoto', position=captain,
                                        )

        self.assertPOST200('/creme_config/persons/position/delete', data={'id': captain.pk})
        self.assertDoesNotExist(captain)

        harlock = self.get_object_or_fail(Contact, pk=harlock.pk)
        self.assertIsNone(harlock.position)

    def test_delete_sector(self):
        "Set to null"
        user = self.login()
        piracy = Sector.objects.create(title='Piracy')
        harlock = Contact.objects.create(user=user, first_name='Harlock',
                                         last_name='Matsumoto', sector=piracy,
                                        )

        self.assertPOST200('/creme_config/persons/sector/delete', data={'id': piracy.pk})
        self.assertDoesNotExist(piracy)

        harlock = self.get_object_or_fail(Contact, pk=harlock.pk)
        self.assertIsNone(harlock.sector)

    def test_delete_image(self):
        "Set to null"
        user = self.login()

        path = join(settings.CREME_ROOT, 'static', 'chantilly', 'images', 'creme_22.png')

        image_name = 'My image'
        self.client.post('/media_managers/image/add', follow=True,
                         data={'user':        user.pk,
                               'name':        image_name,
                               'description': 'Blabala',
                               'image':       open(path, 'rb'),
                              }
                        )

        with self.assertNoException():
            image = Image.objects.get(name=image_name)

        harlock = Contact.objects.create(user=self.user, last_name='Matsumoto', image=image)

        image.delete()

        self.assertDoesNotExist(image)
        self.assertIsNone(self.refresh(harlock).image)

    @skipIfCustomAddress
    def test_csv_import01(self):
        user = self.login()

        count = Contact.objects.count()
        lines = [("Rei",   "Ayanami"),
                 ("Asuka", "Langley"),
                ]

        doc = self._build_csv_doc(lines)
        response = self.client.post(self._build_import_url(Contact),
                                    data=dict(self.lv_import_data,
                                              document=doc.id,
                                              user=user.id,
                                              first_name_colselect=1,
                                              last_name_colselect=2,
                                             ),
                                   )
        self.assertNoFormError(response)

        with self.assertNoException():
            form = response.context['form']

        lines_count = len(lines)
        self.assertFalse(list(form.import_errors))
        self.assertEqual(lines_count, form.imported_objects_count)
        self.assertEqual(lines_count, form.lines_count)

        self.assertEqual(count + lines_count, Contact.objects.count())

        for first_name, last_name in lines:
            contact = self.get_object_or_fail(Contact, first_name=first_name, last_name=last_name)
            self.assertEqual(user, contact.user)
            self.assertIsNone(contact.billing_address)

    @skipIfCustomAddress
    def test_csv_import02(self):
        "Address"
        user = self.login()

        contact_count = Contact.objects.count()

        city = 'Tokyo'
        lines = [('First name', 'Last name', 'City'),
                 ('Rei',        'Ayanami',   city),
                 ('Asuka',      'Langley',   ''),
                ]

        doc = self._build_csv_doc(lines)
        response = self.client.post(
                         #url,
                        self._build_import_url(Contact),
                        data=dict(self.lv_import_data,
                                  document=doc.id, has_header=True,
                                  user=user.id,
                                  first_name_colselect=1,
                                  last_name_colselect=2,
                                  billaddr_city_colselect=3,
                                 )
                   )
        self.assertNoFormError(response)

        with self.assertNoException():
            form = response.context['form']
 
        lines_count = len(lines) - 1 # '-1' for header
        self.assertEqual(0, len(form.import_errors))
        self.assertEqual(lines_count, form.imported_objects_count)
        self.assertEqual(lines_count, form.lines_count)
        self.assertEqual(contact_count + lines_count, Contact.objects.count())

        rei = self.get_object_or_fail(Contact, last_name=lines[1][1], first_name=lines[1][0])
        address = rei.billing_address
        self.assertIsInstance(address, Address)
        self.assertEqual(city, address.city)

        asuka = self.get_object_or_fail(Contact, last_name=lines[2][1], first_name=lines[2][0])
        self.assertIsNone(asuka.billing_address)

    @skipIfCustomAddress
    def test_csv_import03(self):
        "Update (with address)"
        user = self.login()

        last_name = 'Ayanami'
        first_name = 'Rei'
        rei = Contact.objects.create(user=user, last_name=last_name, first_name=first_name)

        city1 = 'Kyoto'
        city2 = 'Tokyo'
        create_address = partial(Address.objects.create, address='XXX', country='Japan',
                                 owner=rei,
                                )
        rei.billing_address  = addr1 = create_address(name='Hideout #1', city=city1)
        rei.shipping_address = addr2 = create_address(name='Hideout #2', city=city2)
        rei.save()

        addr_count = Address.objects.count()

        address_val1 = '213 Gauss Street'
        address_val2 = '56 Einstein Avenue'
        email = 'contact@bebop.mrs'
        doc = self._build_csv_doc([(first_name, last_name, address_val1, address_val2, email)])
        response = self.client.post(self._build_import_url(Contact),
                                    data=dict(self.lv_import_data,
                                                document=doc.id,
                                                user=user.id,
                                                key_fields=['first_name', 'last_name'],
                                                email_colselect=5,
                                                billaddr_address_colselect=3,
                                                shipaddr_address_colselect=4,
                                            )
                                    )
        self.assertNoFormError(response)

        rei = self.refresh(rei)
        self.assertEqual(email, rei.email)

        self.assertEqual(addr_count, Address.objects.count())

        addr1 = self.refresh(addr1)
        self.assertEqual(city1, addr1.city)
        self.assertEqual(address_val1, addr1.address)

        addr2 = self.refresh(addr2)
        self.assertEqual(city2, addr2.city)

    def test_user_delete_is_user(self):
        "Manage Contact.is_user field : Contact is no more related to deleted user."
        user = self.login()
        other_user = self.other_user

        contact = user.linked_contact
        other_contact = other_user.linked_contact

        create_contact = Contact.objects.create
        deunan   = create_contact(user=user,       first_name='Deunan',   last_name='Knut')
        briareos = create_contact(user=other_user, first_name='Briareos', last_name='Hecatonchires')

        self.assertNoFormError(self.client.post('/creme_config/user/delete/%s' % other_user.id,
                                                {'to_user': user.id}
                                               )
                              )
        self.assertDoesNotExist(other_user)
        self.assertStillExists(contact)

        other_contact = self.assertStillExists(other_contact)
        self.assertIsNone(other_contact.is_user)
        self.assertEqual(user, other_contact.user)

        self.assertStillExists(deunan)
        self.assertEqual(user, self.assertStillExists(briareos).user)
