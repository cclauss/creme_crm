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

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from creme_core.entities_access.functions_for_permissions import add_view_or_die, get_view_or_die, read_object_or_die
from creme_core.views.generic import add_entity, view_entity_with_template, edit_entity, list_view

from reports.models import Graph
from reports.forms.graph import GraphForm


@login_required
@get_view_or_die('reports')
@add_view_or_die(ContentType.objects.get_for_model(Graph), None, 'reports')
def add(request):
    return add_entity(request, GraphForm)

@login_required
@get_view_or_die('reports')
def dl_png(request, graph_id):
    graph = get_object_or_404(Graph, pk=graph_id)

    die_status = read_object_or_die(request, graph)
    if die_status:
        return die_status

    return graph.generate_png()

def edit(request, graph_id):
    return edit_entity(request, graph_id, Graph, GraphForm, 'reports')

@login_required
@get_view_or_die('reports')
def detailview(request, graph_id):
    return view_entity_with_template(request, graph_id, Graph, '/reports/graph', 'reports/view_graph.html')

@login_required
@get_view_or_die('reports')
def listview(request):
    return list_view(request, Graph, extra_dict={'add_url':'/reports/graph/add'})
