# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2013  Hybird
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

from django.template import Library
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.utils.meta import get_model_field_info
from creme.creme_core.models.header_filter import (HFI_FIELD, HFI_RELATION, HFI_FUNCTION,
                                                   HFI_CUSTOM, HFI_CALCULATED, HFI_RELATED)
from creme.creme_core.registry import creme_registry

from ..constants import DATETIME_FILTER_FORMAT


register = Library()

HFI_TYPE_VERBOSE = {
    HFI_FIELD      : _(u"Regular field"),
    HFI_RELATION   : _(u"Relation"),
    HFI_FUNCTION   : _(u"Function"),
    HFI_CUSTOM     : _(u"Custom field"),
    HFI_CALCULATED : _(u"Calculated value"),
    HFI_RELATED    : _(u"Related field"),
}

@register.filter(name="is_field_is_linkable")
def is_linkable(field, ct):
    field_infos = get_model_field_info(ct.model_class(), field.name)
    registred_models = creme_registry.iter_entity_models()

    for field_dict in field_infos:
        if isinstance(field_dict.get('field'), (ForeignKey, ManyToManyField)) and \
           field_dict.get('model') in registred_models:
            return True

    return False

@register.filter(name="get_verbose_type")
def get_verbose_type(type_id):
    return HFI_TYPE_VERBOSE.get(type_id)

#@register.inclusion_tag('reports/templatetags/column_header.html')
#def get_column_header(column):
#    return {'data' : column.get_children_fields_with_hierarchy()}

@register.inclusion_tag('reports/frags/html_column_value.html')
def get_html_column_value(column, line, index, add_index=0):
    return {'line' : line, 'column': column, 'index': index+add_index}

#Here because of try except, but when this will be fixed in reports, remove try except and move to creme_core_tags
@register.filter(name="get_value_at")
def get_value_at(iterable, index):
    try:
        return iterable[index]
    except IndexError:
        return u''

@register.inclusion_tag('reports/plot/barchart.json', takes_context=True)
def report_barchart_json(context, report):
    context['report'] = report;
    return context

@register.inclusion_tag('reports/plot/small_barchart.json', takes_context=True)
def report_small_barchart_json(context, report):
    context['report'] = report;
    return context

@register.inclusion_tag('reports/plot/piechart.json', takes_context=True)
def report_piechart_json(context, report, legendRows=None):
    context['report'] = report;
    context['reportLegendRows'] = legendRows;
    return context

@register.inclusion_tag('reports/plot/tubechart.json', takes_context=True)
def report_tubechart_json(context, report, legendRows=1):
    context['report'] = report;
    context['reportLegendRows'] = legendRows;
    return context

@register.inclusion_tag('reports/templatetags/report_chart.html', takes_context=True)
def get_report_chart(context, report):
    context['report'] = report;
    return context

@register.inclusion_tag('reports/templatetags/report_chart_selectors.html', takes_context=True)
def get_report_chart_selectors(context):
    return context

@register.filter
def to_filter_format(date):
    return date.strftime(DATETIME_FILTER_FORMAT)
