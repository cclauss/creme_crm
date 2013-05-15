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

import logging

from django.utils.translation import ugettext as _
from django.conf import settings

from creme.creme_core.models import SearchConfigItem, RelationType, HeaderFilterItem, HeaderFilter, BlockDetailviewLocation
from creme.creme_core.blocks import properties_block, relations_block, customfields_block, history_block
from creme.creme_core.utils import create_if_needed
from creme.creme_core.management.commands.creme_populate import BasePopulator

from creme.persons.models import Contact

from creme.opportunities.models import Opportunity

from .models import EventType, Event
from .blocks import resuts_block
from .constants import *


logger = logging.getLogger(__name__)


class Populator(BasePopulator):
    dependencies = ['creme_core']

    def populate(self, *args, **kwargs):
        create_rtype = RelationType.create
        create_rtype((REL_SUB_IS_INVITED_TO,       _(u'is invited to the event'),               [Contact]),
                     (REL_OBJ_IS_INVITED_TO,       _(u'has invited'),                           [Event]),
                     is_internal=True,
                    )
        create_rtype((REL_SUB_ACCEPTED_INVITATION, _(u'accepted the invitation to the event'),  [Contact]),
                     (REL_OBJ_ACCEPTED_INVITATION, _(u'prepares to receive'),                   [Event]),
                     is_internal=True,
                     )
        create_rtype((REL_SUB_REFUSED_INVITATION,  _(u'refused the invitation to the event'),   [Contact]),
                     (REL_OBJ_REFUSED_INVITATION,  _(u'do not prepare to receive any more'),    [Event]),
                     is_internal=True,
                    )
        create_rtype((REL_SUB_CAME_EVENT,          _(u'came to the event'),                     [Contact]),
                     (REL_OBJ_CAME_EVENT,          _(u'received'),                              [Event]),
                     is_internal=True,
                    )
        create_rtype((REL_SUB_NOT_CAME_EVENT,      _(u'did not come to the event'),             [Contact]),
                     (REL_OBJ_NOT_CAME_EVENT,      _(u'did not receive'),                       [Event]),
                     is_internal=True,
                    )
        create_rtype((REL_SUB_GEN_BY_EVENT,        _(u'generated by the event'),                [Opportunity]),
                     (REL_OBJ_GEN_BY_EVENT,        _(u'(event) has generated the opportunity'), [Event]),
                     is_internal=True,
                    )

        for i, name in enumerate([_('Show'), _('Conference'), _('Breakfast'), _('Brunch')], start=1):
            create_if_needed(EventType, {'pk': i}, name=name)

        hf = HeaderFilter.create(pk='events-hf', name=_(u'Event view'), model=Event)
        hf.set_items([HeaderFilterItem.build_4_field(model=Event, name='name'),
                      HeaderFilterItem.build_4_field(model=Event, name='type__name'),
                      HeaderFilterItem.build_4_field(model=Event, name='start_date'),
                      HeaderFilterItem.build_4_field(model=Event, name='end_date'),
                     ])

        BlockDetailviewLocation.create_4_model_block(order=5, zone=BlockDetailviewLocation.LEFT, model=Event)
        BlockDetailviewLocation.create(block_id=customfields_block.id_, order=40,  zone=BlockDetailviewLocation.LEFT,  model=Event)
        BlockDetailviewLocation.create(block_id=properties_block.id_,   order=450, zone=BlockDetailviewLocation.LEFT,  model=Event)
        BlockDetailviewLocation.create(block_id=relations_block.id_,    order=500, zone=BlockDetailviewLocation.LEFT,  model=Event)
        BlockDetailviewLocation.create(block_id=resuts_block.id_,       order=2,   zone=BlockDetailviewLocation.RIGHT, model=Event)
        BlockDetailviewLocation.create(block_id=history_block.id_,      order=20,  zone=BlockDetailviewLocation.RIGHT, model=Event)

        if 'creme.assistants' in settings.INSTALLED_APPS:
            logger.info('Assistants app is installed => we use the assistants blocks on detail view')

            from creme.assistants.blocks import alerts_block, memos_block, todos_block, messages_block

            BlockDetailviewLocation.create(block_id=todos_block.id_,    order=100, zone=BlockDetailviewLocation.RIGHT, model=Event)
            BlockDetailviewLocation.create(block_id=memos_block.id_,    order=200, zone=BlockDetailviewLocation.RIGHT, model=Event)
            BlockDetailviewLocation.create(block_id=alerts_block.id_,   order=300, zone=BlockDetailviewLocation.RIGHT, model=Event)
            BlockDetailviewLocation.create(block_id=messages_block.id_, order=400, zone=BlockDetailviewLocation.RIGHT, model=Event)

        SearchConfigItem.create_if_needed(Event, ['name', 'description', 'type__name'])
