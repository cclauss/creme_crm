# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2015-2022  Hybird
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

from typing import TYPE_CHECKING, Type

from django.conf import settings

from creme.creme_core import get_concrete_model

if TYPE_CHECKING:
    from .models import AbstractAddress, AbstractContact, AbstractOrganisation


def address_model_is_custom() -> bool:
    return (
        settings.PERSONS_ADDRESS_MODEL != 'persons.Address'
        and not settings.PERSONS_ADDRESS_FORCE_NOT_CUSTOM
    )


def contact_model_is_custom() -> bool:
    return (
        settings.PERSONS_CONTACT_MODEL != 'persons.Contact'
        and not settings.PERSONS_CONTACT_FORCE_NOT_CUSTOM
    )


def organisation_model_is_custom() -> bool:
    return (
        settings.PERSONS_ORGANISATION_MODEL != 'persons.Organisation'
        and not settings.PERSONS_ORGANISATION_FORCE_NOT_CUSTOM
    )


def get_address_model() -> Type['AbstractAddress']:
    """Returns the Address model that is active in this project."""
    return get_concrete_model('PERSONS_ADDRESS_MODEL')


def get_contact_model() -> Type['AbstractContact']:
    """Returns the Contact model that is active in this project."""
    return get_concrete_model('PERSONS_CONTACT_MODEL')


def get_organisation_model() -> Type['AbstractOrganisation']:
    """Returns the Organisation model that is active in this project."""
    return get_concrete_model('PERSONS_ORGANISATION_MODEL')
