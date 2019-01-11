# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
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

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _, pgettext_lazy

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.models import RelationType, SemiFixedRelationType
from creme.creme_core.views.generic import BricksView
from creme.creme_core.utils import get_from_POST_or_404

from ..forms import relation_type as rtype_forms

from . import base


class Portal(BricksView):
    template_name = 'creme_config/relation_type_portal.html'


class RelationTypeCreation(base.ConfigModelCreation):
    model = RelationType
    form_class = rtype_forms.RelationTypeCreateForm
    title = _('New custom type')


class SemiFixedRelationTypeCreation(base.ConfigModelCreation):
    model = SemiFixedRelationType
    form_class = rtype_forms.SemiFixedRelationTypeCreateForm


class RelationTypeEdition(base.ConfigModelEdition):
    # model = RelationType
    queryset = RelationType.objects.filter(is_custom=True)
    form_class = rtype_forms.RelationTypeEditForm
    pk_url_kwarg = 'rtype_id'
    title = pgettext_lazy('creme_config-relationship', 'Edit the type «{object}»')


@login_required
@permission_required('creme_core.can_admin')
def delete(request):
    relation_type = get_object_or_404(RelationType, pk=get_from_POST_or_404(request.POST, 'id'))

    if not relation_type.is_custom:
        raise Http404("Can't delete a standard RelationType")

    relation_type.delete()

    return HttpResponse()


@login_required
@permission_required('creme_core.can_admin')
def delete_semi_fixed(request):
    get_object_or_404(SemiFixedRelationType,
                      pk=get_from_POST_or_404(request.POST, 'id'),
                     ).delete()

    return HttpResponse()
