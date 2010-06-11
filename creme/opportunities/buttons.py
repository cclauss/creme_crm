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

from django.utils.translation import ugettext_lazy as _

from creme_core.gui.button_menu import Button


class LinkedOpportunityButton(Button):
    id_           = Button.generate_id('opportunities', 'linked_opportunity')
    verbose_name  = _(u'Ajouter une opportunité liée à une société')
    template_name = 'opportunities/templatetags/button_linked_opp.html'

    def get_ctypes(self):
        from persons.models import Organisation
        return (Organisation,)


linked_opportunity_button = LinkedOpportunityButton()
