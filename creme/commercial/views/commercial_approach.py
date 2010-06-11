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
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required

from creme_core.entities_access.functions_for_permissions import edit_object_or_die
from creme_core.models import CremeEntity
from creme_core.views.generic import inner_popup

from commercial.forms.commercial_approach import ComAppCreateForm
from commercial.blocks import approaches_block


#TODO: use generic add_model ??
@login_required
def add(request, entity_id):
    """
        @Permissions : Edit on entity that's will be linked to the alert
    """
    entity = get_object_or_404(CremeEntity, pk=entity_id).get_real_entity()

    die_status = edit_object_or_die(request, entity)
    if die_status:
        return die_status

    if request.POST:
        comapp_form = ComAppCreateForm(request.POST)

        if comapp_form.is_valid():
            comapp_form.save()
    else:
        comapp_form = ComAppCreateForm(initial={'entity_id': entity_id})

    return inner_popup(request, 'creme_core/generics/blockform/add_popup2.html',
                       {
                        'form':   comapp_form,
                        'title':  u"Nouvelle démarche commerciale pour <%s>" % entity,
                       },
                       is_valid=comapp_form.is_valid(),
                       reload=False,
                       delegate_reload=True,
                       context_instance=RequestContext(request))

@login_required
def reload_approaches(request, entity_id):
    return approaches_block.detailview_ajax(request, entity_id)

@login_required
def reload_home_approaches(request):
    return approaches_block.home_ajax(request)

@login_required
def reload_portal_approaches(request, ct_id):
    return approaches_block.portal_ajax(request, ct_id)
