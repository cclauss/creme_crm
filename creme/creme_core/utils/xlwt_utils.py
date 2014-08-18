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

from datetime import datetime

from xlwt import Workbook, XFStyle


class XlwtWriter(object):
    def __init__(self, encoding='utf-8'):
        self.nline = 0
        self.wb = wb = Workbook(encoding='utf-8')
        self.ws = wb.add_sheet("sheet 1")
        self.date_format = XFStyle()
        self.date_format.num_format_str = 'dd/mm/yyyy' #TODO: convert from settings.DATE_FORMAT

    def writerow(self, line):
        write = self.ws.write
        nline = self.nline
        for col, cell in enumerate(line):
            if isinstance(cell, datetime):
                write(nline, col, cell, self.date_format)
            else:
                write(nline, col, cell)
        self.nline += 1

    def save(self, filepath):
        self.wb.save(filepath)
