# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from creme_core.entities_access.functions_for_permissions import get_view_or_die, add_view_or_die, edit_object_or_die
from creme_core.views.generic import add_entity, edit_entity, view_entity_with_template, list_view, inner_popup

from sms.models import SendList
from sms.forms.sendlist import (SendListForm,
                                AddContactsForm,
                                AddContactsFromFilterForm,)
from sms.blocks import contacts_block


@login_required
@get_view_or_die('sms')
@add_view_or_die(ContentType.objects.get_for_model(SendList), None, 'sms')
def add(request):
    return add_entity(request, SendListForm)

def edit(request, id):
    return edit_entity(request, id, SendList, SendListForm, 'sms')

@login_required
@get_view_or_die('sms')
def detailview(request, id):
    return view_entity_with_template(request,
                                     id,
                                     SendList,
                                     '/sms/sendlist',
                                     'sms/view_sendlist.html')

@login_required
@get_view_or_die('sms')
def listview(request):
    return list_view(request, SendList, extra_dict={'add_url': '/sms/sendlist/add'})

@login_required
@get_view_or_die('sms')
def _add_aux(request, id, form_class, title):
    sendlist = get_object_or_404(SendList, pk=id)

    die_status = edit_object_or_die(request, sendlist)
    if die_status:
        return die_status

    if request.POST:
        recip_add_form = form_class(sendlist, request.POST)

        if recip_add_form.is_valid():
            recip_add_form.save()
    else:
        recip_add_form = form_class(sendlist=sendlist)

    return inner_popup(request, 'creme_core/generics/blockform/add_popup2.html',
                       {
                        'form':  recip_add_form,
                        'title': title % sendlist,
                       },
                       is_valid=recip_add_form.is_valid(),
                       reload=False,
                       delegate_reload=True,
                       context_instance=RequestContext(request))

def add_contacts(request, id):
    return _add_aux(request, id, AddContactsForm, 'Nouveaux contacts pour <%s>')

def add_contacts_from_filter(request, id):
    return _add_aux(request, id, AddContactsFromFilterForm, 'Nouveaux contacts pour <%s>')

#def add_organisations(request, ml_id):
#    return _add_aux(request, ml_id, AddOrganisationsForm, 'Nouvelles organisations pour <%s>')
#
#def add_organisations_from_filter(request, ml_id):
#    return _add_aux(request, ml_id, AddOrganisationsFromFilterForm, 'Nouvelles organisations pour <%s>')
#
#def add_children(request, ml_id):
#    return _add_aux(request, ml_id, AddChildForm, 'Nouvelles listes filles pour <%s>')

@login_required
@get_view_or_die('sms')
def _delete_aux(request, sendlist_id, subobject_id, deletor):
    sendlist = get_object_or_404(SendList, pk=sendlist_id)

    die_status = edit_object_or_die(request, sendlist)
    if die_status:
        return die_status

    deletor(sendlist, subobject_id)

    return HttpResponseRedirect(sendlist.get_absolute_url())

def delete_contact(request, sendlist_id, id):
    return _delete_aux(request, sendlist_id, id, lambda ml, contact_id: ml.contacts.remove(contact_id))

#def delete_organisation(request, sendlist_id, orga_id):
#    return _delete_aux(request, sendlist_id, orga_id, lambda ml, orga_id: ml.organisations.remove(orga_id))
#
#def delete_child(request, sendlist_id, child_id):
#    return _delete_aux(request, sendlist_id, child_id, lambda ml, child_id: ml.children.remove(child_id))

@login_required
def reload_block_contacts(request, id):
    return contacts_block.detailview_ajax(request, id)

#@login_required
#def reload_block_organisations(request, ml_id):
#    return organisations_block.detailview_ajax(request, ml_id)
#
#@login_required
#def reload_block_child_lists(request, ml_id):
#    return child_lists_block.detailview_ajax(request, ml_id)
#
#@login_required
#def reload_block_parent_lists(request, ml_id):
#    return parent_lists_block.detailview_ajax(request, ml_id)
