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

from creme.creme_core.models import (RelationType, SearchConfigItem, HeaderFilterItem, HeaderFilter,
                               BlockDetailviewLocation, RelationBlockItem, ButtonMenuItem)
from creme.creme_core.utils import create_if_needed
from creme.creme_core.blocks import properties_block, relations_block, customfields_block, history_block
from creme.creme_core.management.commands.creme_populate import BasePopulator

from .models import *
from .models.status import BASE_STATUS
from .constants import REL_SUB_LINKED_2_TICKET, REL_OBJ_LINKED_2_TICKET


logger = logging.getLogger(__name__)


class Populator(BasePopulator):
    dependencies = ['creme_core']

    def populate(self, *args, **kwargs):
        RelationType.create((REL_SUB_LINKED_2_TICKET, _(u'is linked to the ticket')),
                            (REL_OBJ_LINKED_2_TICKET, _(u'(ticket) linked to the entitity'), [Ticket]))

        for pk, name in BASE_STATUS:
            create_if_needed(Status, {'pk': pk}, name=unicode(name), is_custom=False)

        for i, name in enumerate([_('Low'), _('Normal'), _('High'), _('Urgent'), _('Blocking')], start=1):
            create_if_needed(Priority, {'pk': i}, name=name)

        for i, name in enumerate([_('Minor'), _('Major'), _('Feature'), _('Critical'), _('Enhancement'), _('Error')], start=1):
            create_if_needed(Criticity, {'pk': i}, name=name)

        hf = HeaderFilter.create(pk='tickets-hf_ticket', name=_(u'Ticket view'), model=Ticket)
        hf.set_items([HeaderFilterItem.build_4_field(model=Ticket, name='title'),
                      HeaderFilterItem.build_4_field(model=Ticket, name='status__name'),
                      HeaderFilterItem.build_4_field(model=Ticket, name='priority__name'),
                      HeaderFilterItem.build_4_field(model=Ticket, name='criticity__name'),
                      HeaderFilterItem.build_4_field(model=Ticket, name='closing_date'),
                     ])

        hf = HeaderFilter.create(pk='tickets-hf_template', name=_(u'Ticket template view'), model=TicketTemplate)
        hf.set_items([HeaderFilterItem.build_4_field(model=TicketTemplate, name='title'),
                      HeaderFilterItem.build_4_field(model=TicketTemplate, name='status__name'),
                      HeaderFilterItem.build_4_field(model=TicketTemplate, name='priority__name'),
                      HeaderFilterItem.build_4_field(model=TicketTemplate, name='criticity__name'),
                     ])

        SearchConfigItem.create_if_needed(Ticket, ['title', 'description', 'status__name', 'priority__name', 'criticity__name'])

        rbi = RelationBlockItem.create(REL_OBJ_LINKED_2_TICKET)

        BlockDetailviewLocation.create_4_model_block(order=5, zone=BlockDetailviewLocation.LEFT, model=Ticket)
        BlockDetailviewLocation.create(block_id=customfields_block.id_, order=40,  zone=BlockDetailviewLocation.LEFT,  model=Ticket)
        BlockDetailviewLocation.create(block_id=properties_block.id_,   order=450, zone=BlockDetailviewLocation.LEFT,  model=Ticket)
        BlockDetailviewLocation.create(block_id=relations_block.id_,    order=500, zone=BlockDetailviewLocation.LEFT,  model=Ticket)
        BlockDetailviewLocation.create(block_id=rbi.block_id,           order=1,   zone=BlockDetailviewLocation.RIGHT, model=Ticket)
        BlockDetailviewLocation.create(block_id=history_block.id_,      order=20,  zone=BlockDetailviewLocation.RIGHT, model=Ticket)

        if 'creme.assistants' in settings.INSTALLED_APPS:
            logger.info('Assistants app is installed => we use the assistants blocks on detail view')

            from creme.assistants.blocks import alerts_block, memos_block, todos_block, messages_block

            BlockDetailviewLocation.create(block_id=todos_block.id_,    order=100, zone=BlockDetailviewLocation.RIGHT, model=Ticket)
            BlockDetailviewLocation.create(block_id=memos_block.id_,    order=200, zone=BlockDetailviewLocation.RIGHT, model=Ticket)
            BlockDetailviewLocation.create(block_id=alerts_block.id_,   order=300, zone=BlockDetailviewLocation.RIGHT, model=Ticket)
            BlockDetailviewLocation.create(block_id=messages_block.id_, order=400, zone=BlockDetailviewLocation.RIGHT, model=Ticket)

        if 'creme.persons' in settings.INSTALLED_APPS:
            try:
                from creme.persons.models import Contact, Organisation
            except ImportError as e:
                logger.info(str(e))
            else:
                from creme.tickets.buttons import linked_2_ticket_button

                ButtonMenuItem.create_if_needed(pk='tickets-linked_contact_button', model=Contact,      button=linked_2_ticket_button, order=50)
                ButtonMenuItem.create_if_needed(pk='tickets-linked_orga_button',    model=Organisation, button=linked_2_ticket_button, order=50)

                logger.info("'Persons' app is installed => add button 'Linked to a ticket' to Contact & Organisation")
