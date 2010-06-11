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

from django.db.models import ForeignKey
from django.utils.translation import ugettext_lazy as _

from base import Base
from other_models import InvoiceStatus
from product_line import ProductLine
from service_line import ServiceLine


class Invoice(Base):
    status = ForeignKey(InvoiceStatus, verbose_name=_(u'Status de la facture'), blank=False, null=False)

    research_fields = Base.research_fields + ['status__name']
    excluded_fields_in_html_output = Base.excluded_fields_in_html_output + ['base_ptr']

    def get_absolute_url(self):
        return "/billing/invoice/%s" % self.id

    def get_edit_absolute_url(self):
        return "/billing/invoice/edit/%s" % self.id

    @staticmethod
    def get_lv_absolute_url():
        """url for list_view """
        return "/billing/invoices"

    def get_delete_absolute_url(self):
        return "/billing/invoice/delete/%s" % self.id

    def get_products_price_inclusive_of_tax(self):
        total = 0
        for line in ProductLine.objects.filter(document=self):
            total += line.get_price_inclusive_of_tax()
        return total

    def get_services_price_inclusive_of_tax(self):
        #debug("GET TOTAL SERVICE TTC")
        total = 0
        for line in ServiceLine.objects.filter(document=self):
            total += line.get_price_inclusive_of_tax()
        return total

    def get_products_price_exclusive_of_tax(self):
        total = 0
        for line in ProductLine.objects.filter(document=self):
            total += line.get_price_exclusive_of_tax()
        return total

    def get_services_price_exclusive_of_tax(self):
        #debug("GET TOTAL SERVICE HT")
        total = 0
        for line in ServiceLine.objects.filter(document=self):
            total += line.get_price_exclusive_of_tax()
        return total

    def remaining_payment_for_products(self):
        total = 0
        for line in ProductLine.objects.filter(document=self):
            if not line.is_paid:
                total += line.get_price_inclusive_of_tax()
        return total

    def remaining_payment_for_services(self):
        total = 0
        for line in ServiceLine.objects.filter(document=self):
            if not line.is_paid:
                total += line.get_price_inclusive_of_tax()
        return total

    def build(self, template):
        # Specific recurrent generation rules
        self.status = InvoiceStatus.objects.get(pk = template.status_id)
        return super(Invoice, self).build(template)

    class Meta:
        app_label = "billing"
        verbose_name = _(u'Facture')
        verbose_name_plural = _(u'Factures')
