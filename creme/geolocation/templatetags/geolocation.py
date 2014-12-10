# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2014  Hybird
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
from django.utils.translation import ungettext

register = Library()


@register.inclusion_tag('geolocation/templatetags/googleapi.html', takes_context=True)
def load_googleapi_once(context):
    if context.get('google_loaded_once', False):
        context['google_loaded'] = True

    context['google_loaded_once'] = True

    return context

@register.filter
def format_distance(value):
    if value < 1000:
        return ungettext('%(distance)d meter', '%(distance)d meters', value) % {'distance': value}

    value = value / 1000.0
    return ungettext('%(distance).1f Km', '%(distance).1f Km', value) % {'distance': value}

@register.filter
def format_location(location):
    return '%3.6f, %3.6f' % (location.latitude, location.longitude)