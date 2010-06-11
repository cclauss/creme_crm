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


class Algo(object):
    def generate_number(self, organisation, ct, *args, **kwargs):
        pass


class AlgoRegistry(object):
    def __init__(self):
        self._algos = {}

    def register(self, *to_register):
        algos = self._algos

        for name, algo in to_register:
            if algos.has_key(name):
                warning("Duplicate algo's id or algo registered twice : %s", name) #exception instead ???

            algos[name] = algo

    def get_algo(self, name):
        algos = self._algos
        if algos.has_key(name):
            return algos[name]

        return None

    def __iter__(self):
        return self._algos.iteritems()

    def itervalues(self):
        return self._algos.itervalues() 


algo_registry = AlgoRegistry()
