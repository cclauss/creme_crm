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

from creme_core.forms import CremeModelForm
from creme_core.forms.fields import MultiCremeEntityField

from media_managers.models import Image
from media_managers.forms.widgets import ImageM2MWidget

from products.models import Service


#class ServiceListViewForm(CremeModelForm):
    #class Meta:
        #model = Service


class ServiceCreateForm(CremeModelForm):
    class Meta:
        model = Service
        exclude = CremeModelForm.exclude

    images = MultiCremeEntityField(required=False, model=Image,
                                   widget=ImageM2MWidget())
