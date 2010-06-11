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

from logging import debug
from django.utils.encoding import smart_str, force_unicode

from django.db.models import ForeignKey, CharField, TextField, PositiveIntegerField, BooleanField, DateField
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.auth.models import User

from creme_core.models import CremeEntity, Relation, CremePropertyType, CremeProperty
from creme_core.constants import PROP_IS_MANAGED_BY_CREME

from media_managers.models import Image

from address import Address
from contact import Contact
from other_models import StaffSize, LegalForm, Sector
from persons.constants import REL_SUB_EMPLOYED_BY, REL_SUB_MANAGES


class Organisation (CremeEntity):
    name            = CharField(_(u'Nom'), max_length=100)
    phone           = CharField(_(u'Téléphone'), max_length=100 , blank=True, null=True)
    fax             = CharField(_(u'Fax'), max_length=100 , blank=True, null=True)
    email           = CharField(_(u'E-mail'), max_length=100 , blank=True, null=True)
    url_site        = CharField(_(u'URL Site'), max_length=100, blank=True, null=True)
    sector          = ForeignKey(Sector, verbose_name=_(u'Secteur'), blank=True, null=True)    
    capital         = PositiveIntegerField(_(u'Capital'), blank=True, null=True)
    siren           = CharField(_(u'SIREN'), max_length=100, blank=True, null=True)
    naf             = CharField(_(u'Code NAF'), max_length=100 , blank=True, null=True)
    siret           = CharField(_(u'SIRET'), max_length=100, blank=True, null=True)
    rcs             = CharField(_(u'RCS/RM'), max_length=100, blank=True, null=True)
    tvaintra        = CharField(_(u'Numéro TVA'), max_length=100, blank=True, null=True)
    subject_to_vat  = BooleanField(_(u'Assujetti à la TVA'), default=True)
    legal_form      = ForeignKey(LegalForm, verbose_name=_(u'Forme Juridique'), blank=True, null=True)
    employees       = ForeignKey(StaffSize, verbose_name=_(u'Effectif'), blank=True, null=True)
    billing_adress  = ForeignKey(Address, verbose_name=_(u'Adresse de facturation'), blank=True, null=True, related_name='AdressefactuOrganisation_set')
    shipping_adress = ForeignKey(Address, verbose_name=_(u'Adresse de livraison'), blank=True, null=True, related_name='AdresselivraisonOrganisation_set')
    annual_revenue  = CharField(_(u'Revenu annuel'), max_length=100, blank=True, null=True)
    description     = TextField(_(u'Description'), blank=True, null=True)
    creation_date   = DateField(_(u"Date de création de l'entreprise"), blank=True, null=True)
    image           = ForeignKey(Image, verbose_name=_(u'Logo'), blank=True, null=True)

#    addresses = ManyToManyField (Address, verbose_name = _(u'Adresse(s)'),blank=True, null=True, related_name='AdressesOrganisation_set')

    research_fields = CremeEntity.research_fields + ['name']

    class Meta:
        app_label = "persons"
        ordering = ('name',)
        verbose_name = _(u'Société')
        verbose_name_plural = _(u'Sociétés')

    def save(self):
        self.header_filter_search_field = self.name
        super(Organisation, self).save()

    def __unicode__(self):
        return force_unicode (self.name)

    def get_absolute_url(self):
        return "/persons/organisation/%s" % self.id

    def get_edit_absolute_url(self):
        return "/persons/organisation/edit/%s" % self.id

    @staticmethod
    def get_lv_absolute_url():
        """url for list_view """
        return "/persons/organisations"

    def get_delete_absolute_url(self):
        return "/persons/organisation/delete/%s" % self.id

    def get_managers_relations(self):
        return Relation.objects.filter(object_id=self.id, type__id=REL_SUB_MANAGES)

    def get_employed_relations(self):
        return Relation.objects.filter(object_id=self.id, type__id=REL_SUB_EMPLOYED_BY)

    #TODO: used ???
    def zipcode(self):
        if self.billing_adress is not None:
            return self.billing_adress.zipcode
        return 'Non renseigné'

    @staticmethod
    def get_all_managed_by_creme():
#        managed_by_creme = CremePropertyType.objects.get(pk=PROP_IS_MANAGED_BY_CREME)
#        return Organisation.objects.filter(properties__type=managed_by_creme).
        ct_orga = ContentType.objects.get_for_model(Organisation)
        pk_list = CremeProperty.objects.filter(type__id=PROP_IS_MANAGED_BY_CREME, subject_ct=ct_orga).distinct().values_list('subject_id',flat=True)
        return Organisation.objects.filter(pk__in=pk_list)







