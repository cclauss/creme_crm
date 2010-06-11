# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns


urlpatterns = patterns('persons.views',
    (r'^$', 'portal.portal'),

    (r'^contacts$',                                           'contact.listview'),
    (r'^leads_customers$',                                    'contact.list_my_leads_my_customers'),
    (r'^contact/add$',                                        'contact.add'),
    (r'^contact/add_with_relation/(?P<organisation_id>\d+)$', 'contact.add_with_relation'),
    (r'^contact/edit/(?P<contact_id>\d+)$',                   'contact.edit'),
    (r'^contact/(?P<contact_id>\d+)$',                        'contact.detailview'),

    (r'^organisations$',                                           'organisation.listview'),
    (r'^organisation/add$',                                        'organisation.add'),
    (r'^organisation/edit/(?P<organisation_id>\d+)$',              'organisation.edit'),
    (r'^organisation/(?P<organisation_id>\d+)$',                   'organisation.detailview'),
    (r'^organisation/(?P<organisation_id>\d+)/managers/reload/$',  'organisation.reload_managers'),
    (r'^organisation/(?P<organisation_id>\d+)/employees/reload/$', 'organisation.reload_employees'),

    (r'^(?P<entity_id>\d+)/become_customer/(?P<mngd_orga_id>\d+)$',          'crud_relations.become_customer'),
    (r'^(?P<entity_id>\d+)/become_prospect/(?P<mngd_orga_id>\d+)$',          'crud_relations.become_prospect'),
    (r'^(?P<entity_id>\d+)/become_suspect/(?P<mngd_orga_id>\d+)$',           'crud_relations.become_suspect'),
    (r'^(?P<entity_id>\d+)/become_inactive_customer/(?P<mngd_orga_id>\d+)$', 'crud_relations.become_inactive'),
    (r'^(?P<entity_id>\d+)/become_supplier/(?P<mngd_orga_id>\d+)$',          'crud_relations.become_supplier'),

    (r'^address/from_organisation$', 'address.get_org_addresses'),
    (r'^address/add$',               'address.add'),
)

urlpatterns += patterns('creme_core.views',
    (r'^contact/edit_js/$',                                'ajax.edit_js'),
    (r'^contact/delete/(?P<object_id>\d+)$',               'generic.delete_entity'),
    (r'^contact/delete_js/(?P<entities_ids>([\d]+[,])+)$', 'generic.delete_entities_js'),

    (r'^organisation/edit_js/$',                                'ajax.edit_js'),
    (r'^organisation/delete/(?P<object_id>\d+)$',               'generic.delete_entity'),
    (r'^organisation/delete_js/(?P<entities_ids>([\d]+[,])+)$', 'generic.delete_entities_js'),
)
