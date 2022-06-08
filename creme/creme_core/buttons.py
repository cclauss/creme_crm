# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2022  Hybird
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

from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from .constants import UUID_SANDBOX_SUPERUSERS
from .gui.button_menu import Button


class Restrict2SuperusersButton(Button):
    # id_ = Button.generate_id('creme_core', 'restrict_2_superusers')
    id = Button.generate_id('creme_core', 'restrict_2_superusers')
    verbose_name = _('Restrict to superusers')
    description = _(
        'This button moves the current entity within a sandbox reserved to the '
        'superusers, so the regular users cannot see it. If the current is '
        'already restricted to superusers, the button can be used to move the '
        'entity out of the sandbox.\n'
        'The button is only viewable by superusers.\n'
        'App: Core'
    )
    template_name = 'creme_core/buttons/restrict-to-superusers.html'

    def render(self, context):
        sandbox = context['object'].sandbox
        context['sandbox_uuid'] = str(sandbox.uuid) if sandbox else None
        context['UUID_SANDBOX_SUPERUSERS'] = UUID_SANDBOX_SUPERUSERS

        return super().render(context)


class ActionButton(Button):
    template_name = 'creme_core/buttons/action.html'
    action = ''
    action_icon = 'view'
    action_icon_title = None

    def get_action_url(self, context) -> str:
        return ''

    def get_action_data(self, context) -> dict:
        return {}

    def get_action_options(self, context) -> dict:
        return {}

    def get_html_attrs(self, context) -> dict:
        return {}

    def is_valid(self, context) -> bool:
        return True

    def get_action_context(self, context) -> dict:
        return {
            'name': self.action,
            'icon': self.action_icon,
            'icon_title': self.action_icon_title,
            'url': self.get_action_url(context),

            'data': {
                'options': self.get_action_options(context),
                'data': self.get_action_data(context),
            },
        }

    def get_button_context(self, context) -> dict:
        return {
            'verbose_name': self.verbose_name,
            'description': self.description,
            'attrs': self.get_html_attrs(context),
            'has_perm': self.has_perm(context),
            'is_valid': self.is_valid(context),
        }

        return context

    def render(self, context) -> str:
        context['button'] = self.get_button_context(context)
        context['action'] = self.get_action_context(context)
        return get_template(self.template_name).render(context)


class ViewButton(ActionButton):
    action = 'creme_core-hatmenubar-view'

    def get_action_data(self):
        return {
            'title': self.verbose_name
        }


class FormButton(ActionButton):
    action = 'creme_core-hatmenubar-form'
    redirect = True

    def extra_submit_data(self, context):
        return {}

    def get_action_data(self, context):
        return {
            'title': self.verbose_name
        }

    def get_action_options(self, context):
        return {
            'redirectOnSuccess': self.redirect,
            'submitData': self.extra_submit_data(context)
        }


class UpdateButton(ActionButton):
    action = 'creme_core-hatmenubar-update'
    method = 'POST'
    confirm = False
    success_message = ''
    show_error_message = True
    reload_on_error = True
    reload_on_success = True

    def get_action_options(self, context):
        return {
            'confirm': self.confirm,
            'action': self.method,
            'warnOnFail': self.show_error_message,
            'warnOnFailTitle': self.verbose_name,
            'messageOnSuccess': self.success_message,
            'reloadOnFail': self.reload_on_error,
            'reloadOnSuccess': self.reload_on_success,
        }
