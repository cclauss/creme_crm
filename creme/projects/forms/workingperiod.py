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

from django.forms import IntegerField , DateTimeField, ValidationError
from django.utils.translation import ugettext_lazy as _

from creme_core.forms import CremeModelForm
from creme_core.forms.fields import CremeEntityField
from creme_core.forms.widgets import DateTimeWidget

from projects.models import WorkingPeriod, Resource, TaskStatus
from projects import constants


class PeriodEditForms(CremeModelForm):
    resource   = CremeEntityField(label=_(u'Ressource(s) affectée(s) à cette tâche'), required=True, model=Resource)
    start_date = DateTimeField(label=_(u'Entre'), widget=DateTimeWidget(), required=False)
    end_date   = DateTimeField(label=_(u'Et'), widget=DateTimeWidget(), required=False)
    duration   = IntegerField(label=_(u'Durée de la période'), required=True)

    class Meta:
        model = WorkingPeriod
        exclude = ['task']


class PeriodCreateForms(PeriodEditForms):

    def __init__(self, *args, **kwargs):
        self.task = kwargs['initial'].pop('related_task')
        super(PeriodCreateForms, self).__init__(*args, **kwargs)
        self.fields['resource'].widget.q_filter = {'task__id' : self.task.pk}

    def clean_resource(self):
        resource = self.cleaned_data['resource']
        if resource not in self.task.get_resources():
            raise ValidationError(u"Cette ressource n'a pas été affectée au projet")
        return resource

    def save(self):
        self.instance.task = self.task
        if self.task.status.name == constants.TASK_STATUS[constants.NOT_STARTED_PK]:
            self.task.status = TaskStatus.objects.get(id=constants.CURRENT_PK)
            self.task.save()
        super(PeriodCreateForms, self).save()
