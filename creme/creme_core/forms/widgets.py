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
from datetime import datetime, time
from itertools import chain

from django.forms.widgets import Textarea, Select, SelectMultiple, FileInput, TextInput
from django.forms.util import flatatt
from django.utils.simplejson.encoder import JSONEncoder
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
#from django.template.loader import render_to_string

from creme_core.models import CremeEntity

def widget_render_context(klass, widget, name, value, attrs, css='', typename='', noinput=False, **kwargs):
    id = attrs.get('id')
    auto = attrs.pop('auto', True)
    
    css = ' '.join((css, 'ui-creme-widget widget-auto' if auto else 'ui-creme-widget', typename))
  
    attrs['class'] = ' '.join([attrs.get('class', ''), 
                               'ui-creme-input', typename])
    
    context= {'MEDIA_URL':  settings.MEDIA_URL,
              'input':      super(klass, widget).render(name, value, attrs) if not noinput else '',
              #'id':         id + '-' + typename if id else '',
              'script':     '',
              'style':      '',
              'typename':   typename,
              'css':        css}
    
#    if auto:
#        context['script'] = """<script type="text/javascript">creme.widget.ready();</script>"""
    
    context.update(kwargs)
    
    return context

def widget_render_context_addclass(context, *args):
    context['class'] = ' '.join([context.get('class', '')] + args)

class DynamicSelect(Select):
    def __init__(self, attrs=None, options=None, url=''):
        super(DynamicSelect, self).__init__(attrs, options if options else ())
        self.url = url
    
    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, name=name)
        attrs['url'] = self.url
        typename='ui-creme-dselect'
        
        context = widget_render_context(DynamicSelect, self, name, value, attrs, 
                                        typename=typename,
                                        noinput=True)
        attrs['class'] = context.get('css', '')
        attrs['widget'] = typename
        
        context['input'] = super(DynamicSelect, self).render(name, value, attrs)
        
        output = """%(input)s %(script)s""" % context
        return mark_safe(output)

class ChainedInput(TextInput):
    
    class Model(object):
        def __init__(self, widget=DynamicSelect, attrs=None, **kwargs):
            self.kwargs = kwargs
            self.attrs = attrs
            self.widget = widget
    
    def __init__(self, attrs=None, **kwargs):
        super(ChainedInput, self).__init__(attrs)
        self.inputs = {}
        self.set(**kwargs)

    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, name=name, type='hidden')

        context = widget_render_context(ChainedInput, self, name, value, attrs,
                                        typename='ui-creme-chainedselect',
                                        style=attrs.pop('style', ''),
                                        selects=self._render_inputs())

        html_output = """
            <div class="%(css)s" style="%(style)s" widget="%(typename)s">
                %(input)s
                %(selects)s
                %(script)s
            </div>
        """ % context;

        return mark_safe(html_output)

    def set(self, **kwargs):
        for name, input in kwargs.iteritems():
            self.put(name, input.widget, input.attrs, **input.kwargs)
        
    def put(self, name, widget=DynamicSelect, attrs=None, **kwargs):
        self.inputs[name] = widget(attrs=attrs, **kwargs)

    def _render_inputs(self):
        output = '<ul class="ui-layout hbox">'
        
        for name, input in self.inputs.iteritems():
            output += '<li chained-name="' + name + '">' + input.render('', '') + '</li>'
        
        output += '</ul>'
        return output

class SelectorList(TextInput):
    def __init__(self, selector, attrs=None):
        super(SelectorList, self).__init__(attrs)
        self.selector = selector
        self.from_python = None # TODO : wait for django 1.2 and new widget api to remove this hack

    def render(self, name, value, attrs=None):
        value = self.from_python(value) if self.from_python is not None else value # TODO : wait for django 1.2 and new widget api to remove this hack
        attrs = self.build_attrs(attrs, name=name, type='hidden')
        
        print 'SelectorList > value', value

        context = widget_render_context(SelectorList, self, name, value, attrs,
                                        typename='ui-creme-selectorlist',
                                        add='Ajouter',
                                        selector=self.selector.render('', '', {'auto':False,}))

        html_output = """
            <div class="%(css)s" style="%(style)s" widget="%(typename)s">
                %(input)s
                <div class="inner-selector-model" style="display:none;">%(selector)s</div>
                <ul class="selectors ui-layout"></ul>
                <div class="add">
                    <ul class="ui-layout hbox">
                        <li><img src="%(MEDIA_URL)s/images/add_16.png" alt="%(add)s" title="%(add)s"/></li>
                        <li><span>%(add)s</span></li>
                    </ul>
                </div>
                %(script)s
            </div>
        """ % context

        return mark_safe(html_output)

class EntitySelector(TextInput):
    def __init__(self, content_type=None, attrs=None):
        super(EntitySelector, self).__init__(attrs)
        self.url = '/creme_core/lv_popup/' + content_type if content_type else '/creme_core/lv_popup/${ctype}'
        self.text_url = '/creme_core/relation/entity/${id}/json'
    
    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, name=name, type='hidden')

        context = widget_render_context(EntitySelector, self, name, value, attrs,
                                        typename='ui-creme-entityselector',
                                        url=self.url,
                                        text_url=self.text_url,
                                        multiple='1' if attrs.pop('multiple', False) else '0',
                                        style=attrs.pop('style', ''),
                                        label='Selectionner...')

        html_output = """
            <span class="%(css)s" style="%(style)s" widget="%(typename)s" url="%(url)s" multiple="%(multiple)s">
                %(input)s
                <button type="button" url="%(text_url)s" label="%(label)s">%(label)s</button>
                %(script)s
            </span>
        """ % context;

        return mark_safe(html_output)

class CTEntitySelector(ChainedInput):
    def __init__(self, content_types, attrs=None):
        super(CTEntitySelector, self).__init__(attrs)
        
        if content_types.__class__ == str:
            ctype = ChainedInput.Model(widget=DynamicSelect, attrs={'auto':False}, url=content_types)
        else:
            ctype = ChainedInput.Model(widget=DynamicSelect, attrs={'auto':False}, options=content_types)
        
        self.set(ctype=ctype,
                 entity=ChainedInput.Model(widget=EntitySelector, attrs={'auto':False}));

    def render(self, name, value, attrs=None):
        return super(CTEntitySelector, self).render(name, value, attrs)
    
class EntitySelectorList(SelectorList):
    def __init__(self, attrs=None):
        super(EntitySelectorList, self).__init__(attrs)
        self.selector = EntitySelector

    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, name=name, type='hidden')

        context = widget_render_context(self, name, value, attrs,
                                        typename='ui-creme-selectorlist',
                                        add='Ajouter',
                                        selector=self.selector.render(name, value, {'auto':False,}))

        html_output = """
            <div id="%(id)s" class="%(css)s" style="%(style)s" widget="%(typename)s">
                %(input)s
                <div class="inner-selector-model" style="display:none;">%(selector)s</div>
                <ul class="selectors ui-layout"></ul>
                <div class="add">
                    <img src="%(MEDIA_URL)s/images/add_16.png" alt="%(add)s" title="%(add)s"/>
                    %(add)s
                </div>
                %(script)s
            </div>
        """ % context

        return mark_safe(html_output)


class RelationListWidget(TextInput):
    def __init__(self, attrs=None, predicates=None, subject=None):
        super(RelationListWidget, self).__init__(attrs)
        self.predicates = predicates or []
        self.subject = subject
        
    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, name=name, type='hidden')

        html_output = """
            %(input)s
            <div id="%(id)s_list" class="ui-creme-rel-selector-list" widget-input="%(id)s">
                %(predicates)s
                <div class="list"></div>
                <div onclick="creme.forms.RelationList.appendSelector($('#%(id)s_list'));" class="add">
                    <img src="%(MEDIA_URL)s/images/add_16.png" alt="%(title)s" title="%(title)s"/>
                    %(title)s
                </div>
            </div>
            <script type="text/javascript">
                $('.ui-creme-rel-selector-list#%(id)s_list').each(function() {
                    creme.forms.RelationList.init($(this)%(subject)s);
                });
            </script>
        """ % {
                'MEDIA_URL':  settings.MEDIA_URL,
                'input':      super(RelationListWidget, self).render(name, value, attrs),
                'title':      'Ajouter',
                'id':         attrs['id'],
                'predicates': self.render_options(self.predicates, 'predicates'),
                'subject':    ', %s' % self.subject if self.subject else '',
              }

        return mark_safe(html_output)

    def render_options(self, options, css):
        output = '<select style="display:none;" class="%s">' % css

        for predicate_id, predicate_label in options: #TODO: use join() ??
            output += '<option value="%s">%s</option>' % (predicate_id, predicate_label)

        output += '</select>'
        return output

    def set_predicates(self, predicates):
        self.predicates = predicates



class DateTimeWidget(TextInput):
    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, name=name, type='hidden')

        html_output = """ 
            <ul id="%(id)s_datetimepicker" class="ui-creme-datetimepicker" style="list-style:none;margin:0;padding:0;">
                %(input)s
                <li>%(date_label)s&nbsp;</li>
                <li class="date"><input class="ui-corner-all" type="text" maxlength="12"/></li>
                <li>&nbsp;%(time_label)s&nbsp;</li>
                <li class="hour"><input class="ui-corner-all" type="text" maxlength="2"/></li>
                <li>&nbsp;%(hour_label)s&nbsp;</li>
                <li class="minute"><input class="ui-corner-all" type="text" maxlength="2"/></li>
                <li>&nbsp;%(minute_label)s</li>
                <li class="clear"><button type="button">%(clear_label)s<button/></li>
                <li class="now last"><button type="button">%(now_label)s<button/></li>
            </ul>
            <script type="text/javascript">
                $('.ui-creme-datetimepicker#%(id)s_datetimepicker').each(function() {creme.forms.DateTimePicker.init($(this));});
            </script>
        """ % {
                'input':        super(DateTimeWidget, self).render(name, value, attrs),
                'date_label':   'Le',
                'time_label':   u'à',
                'hour_label':   'h',
                'minute_label': '',
                'id':           attrs['id'],
                'clear_label':  'Effacer',
                'now_label':    'Maintenant',
              }

        return mark_safe(html_output)


class TimeWidget(TextInput):
    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, name=name, type='hidden')

        html_output = """ 
            <ul id="%(id)s_timepicker" class="ui-creme-timepicker" style="list-style:none;margin:0;padding:0;">
                %(input)s
                <li class="hour"><input class="ui-corner-all" type="text" maxlength="2"/></li>
                <li>&nbsp;%(hour_label)s&nbsp;</li>
                <li class="minute"><input class="ui-corner-all" type="text" maxlength="2"/></li>
                <li>&nbsp;%(minute_label)s</li>
                <li class="last"><button type="button">%(now_label)s<button/></li>
            </ul>
            <script type="text/javascript">
                $('.ui-creme-timepicker#%(id)s_timepicker').each(function() {creme.forms.TimePicker.init($(this));});
            </script>
        """ % {
                'input':        super(TimeWidget, self).render(name, value, attrs),
                'hour_label':   'h',
                'minute_label': '',
                'id':           attrs['id'],
                'now_label':    'Maintenant',
              }

        return mark_safe(html_output)


class CalendarWidget(TextInput):
    def render(self, name, value, attrs=None):
        #be carefull: JS and python date format should be equal (here: date == "yy-mm-dd")
        if isinstance(value, datetime):
            value = value.date()

        attrs = self.build_attrs(attrs, name=name)

        html_output = """
            %(input)s
            <button type="button" onclick="d=new Date();$('#%(id)s').val(d.getFullYear() + '-' + (d.getMonth()+1) + '-' + d.getDate());">
                Aujourd'hui
            </button>
            <script type="text/javascript">
                $("#%(id)s").datepicker({dateFormat: "yy-mm-dd", showOn: "button", buttonImage: "%(MEDIA_URL)s/images/icon_calendar.gif", buttonImageOnly: true });
            </script>
            """ % {
                    'input':     super(CalendarWidget, self).render(name, value, attrs),
                    'id':        attrs['id'],
                    'MEDIA_URL': settings.MEDIA_URL,
                  }

        return mark_safe(html_output)


class DependentSelect(Select):
    def __init__(self, target_id, target_url, attrs=None, choices=()):
        self.target_id = target_id
        self.target_url = target_url
        super(DependentSelect, self).__init__(attrs, choices)

    def set_target(self, target):
        self.target_val = target

    def set_source(self, source):
        self.source_val = source

    def render(self, name, value, attrs=None, choices=()):
        if attrs is not None :
            if attrs.has_key('id') :
                id = attrs['id']
            else :
                id = "id_%s" % name
                attrs['id'] = id
        else :
            id = "id_%s" % name
            attrs = {"id" : id}
        script = '<script>'
        script += "function change_%s () {" % (id)
        script += "var source = $('#%s');" % id
        script += "if(!source || typeof(source) == 'undefined') return;"
        script += "var target = $('#%s');" % self.target_id
        script += "if(!target || typeof(target) == 'undefined') return;"
        script += "$.post('%s', {record_id : source.val()}, " % (self.target_url)
        script += "      function(data){"
        script += "         target.empty();"
        script += "         var result = data['result'];"
        script += "         for(var option in result)"
        script += "         {"
        if not hasattr(self, "source_val") or not hasattr(self, "target_val"): #TODO: un peu beurk...
            script += "             target.append('<option value='+result[option][\"id\"]+'>'+result[option][\"text\"]+'</option>');"
        else :
            script += "             if(result[option]['id'] == %s){" % self.target_val
            script += "                 target.append('<option selected=\"selected\" value='+result[option][\"id\"]+'>'+result[option][\"text\"]+'</option>');"
            script += "             }"
            script += "             else {"
            script += "                     target.append('<option value='+result[option][\"id\"]+'>'+result[option][\"text\"]+'</option>');"
            script += "             }"
        script += "         "
        script += "         "
        script += "         }"
        script += "      }, 'json');"
        script += '} '
#        if not hasattr(self, "source_val") or not hasattr(self, "target_val"):
        script += "$(document).ready(function(){change_%s ();});" % (id)

#        if hasattr(self, "source_val") and self.source_val is not None :
#            logging.debug("\n\n\nid : %s | source_val : %s\n\n\n" % (id,self.source_val))
#            script += "$(document).ready(function(){"
#            script += "$('#%s').val('%s');" % (id, self.source_val)
#            script += "});"
#        if hasattr(self, "target_val") and self.target_val is not None :
##            script += "console.log('avant2');"
##            script += "console.log('%s');" % self.target_val
#            script += "$(document).ready(function(){"
#            script += "$('#%s').val('%s');" % (self.target_id, self.target_val)
#            script += "});"
##            script += "console.log('apres2');"
#            logging.debug("\n\n\n id : %s | target_val : %s\n\n\n" % (self.target_id,self.target_val))

            
        script += '</script>'
        attrs['onchange'] = "change_%s ();" % (id)
        select = super(DependentSelect, self).render(name, value, attrs, choices)

        return mark_safe(select + script)


#TODO: refactor (build_attrs() etc...)
class UploadedFileWidget(FileInput):
    def __init__(self, url=None, attrs=None):
        self.url = url or None #???
        super(UploadedFileWidget, self).__init__(attrs)

    def original_render(self, name, value, attrs=None):
        if self.url is not None :
            input = '<a href="/download_file/%s">%s</a>' % (self.url, self.url)
#            input = mark_safe(u'<a href="/download_file/%s">%s</a>' % (self.url, self.url))
#            input = mark_safe(u'<a href="%s">%s</a>' % (url, url))
        else :
            input = super(UploadedFileWidget, self).render(name, value)
        return input

    def render(self, name, value, attrs=None):
        visual=''
        if self.url is not None :
            #import settings
            visual = '<a href="/download_file/%s">' % (self.url)
            visual += '<img src="%s%s" alt="%s"/></a>' % (settings.MEDIA_URL, self.url, self.url)

            if attrs is not None :
                attrs['type'] = 'hidden'
            else :
                attrs = {'type' : 'hidden'}
        input = super(UploadedFileWidget, self).render(name, value, attrs)
        return mark_safe(input + visual)


class RTEWidget(Textarea):
    css        = settings.MEDIA_URL + '/css/rte.css'
    images_url = settings.MEDIA_URL + '/images/'
    js         = settings.MEDIA_URL + '/js/models/jquery.rte.js'

    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, name=name)

        html_output = """
                <script type="text/javascript">
                    include('%(js)s','js');
                    include('%(css)s','css');
                    $(document).ready(function() {
                        $("#%(id)s").rte({content_css_url: "%(css)s", media_url: "%(url)s" });
                    });
                </script>
                %(textarea)s
                <input type="checkbox" id="%(id)s_is_rte_enabled" name="%(name)s_is_rte_enabled" style="display:none;" checked />
            """ % {
                    'js':       self.js,
                    'css':      self.css,
                    'id':       attrs['id'],
                    'name':     attrs['name'],
                    'url':      self.images_url,
                    'textarea': super(RTEWidget, self).render(name, value, attrs),
                }

        return mark_safe(html_output)


class ColorPickerWidget(TextInput):
    css = settings.MEDIA_URL + '/css/jquery.gccolor.1.0.3/gccolor.css'
    js  = settings.MEDIA_URL +'/js/jquery/extensions/jquery.gccolor.1.0.3/dev/jquery.gccolor.1.0.3.js'

    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, name=name)

        html_output = """
                <script type="text/javascript">
                    include('%(js)s','js');
                    include('%(css)s','css');
                    $(document).ready(function() {
                        $("#%(id)s").gccolor();
                    });
                </script>
                %(input)s
            """ % {
                    'js':    self.js,
                    'css':   self.css,
                    'id':    attrs['id'],
                    'input': super(ColorPickerWidget, self).render(name, value, attrs),
                }

        return mark_safe(html_output)


#TODO: refactor (build_attrs(), model/o2m set by the field etc....)
class ListViewWidget(TextInput):
    """
        A list view many-to-many widget
        Usage in a form definition :

        mailing_list = fields.CremeEntityField(required=False, model=MailingList, q_filter=None)
        For many to many, precise o2m attribute to false :
            mailing_list = fields.MultiCremeEntityField(
                                                        required=False,
                                                        model=MailingList,
                                                        q_filter=None,
                                                        widget=ListViewWidget()
                            )
        q_filter has to be a list of dict => {'pk__in':[1,2], 'name__contains':'toto'} or None
    """
    class Media:
        js = ('js/models/lv_widget.js',)

    def __init__(self, attrs=None, q_filter=None):
        super(ListViewWidget, self).__init__(attrs)
        self.q_filter = q_filter
        print "###--- __init__.q_filter :", self.q_filter," ---###"

    def render(self, name, value, attrs=None):
        print "###--- q_filter :", self.q_filter," ---###"
        id_input = self.attrs.get('id')
        if not id_input:
            id_input = 'id_%s' % name
            if not self.attrs:
                self.attrs = {'id' : id_input}
            else:
                self.attrs['id'] = id_input

        encode = JSONEncoder().encode

        #TODO : Improve me
        if(value and (type(value)==type("") or type(value)==type(u""))):#type(value)!=type([])):
            value = [v for v in value.split(',') if v]

        if(value and (type(value)==type(1) or type(value)==type(1L))):
            value = [value]

        html_output = """
                %(input)s
                %(includes)s
                <script type="text/javascript">
                    $(document).ready(function() {
                        lv_widget.init_widget('%(id)s','%(qfilter)s', %(js_attrs)s);
                        lv_widget.handleSelection(%(value)s, '%(id)s');
                    });
                </script>
            """ % {
                    'input':    super(ListViewWidget, self).render(name, "", self.attrs),
                    'includes': ''.join('<script type="text/javascript" src="/site_media/%s"></script>' % js for js in self.Media.js),
                    'id':       id_input,
                    'qfilter':  encode(self.q_filter),
                    'js_attrs': encode([{'name': k, 'value': v} for k, v in self.attrs.iteritems()]),
                    'value':    encode(value),
                }

        return mark_safe(html_output)


class OrderedMultipleChoiceWidget(SelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ()
        value_dict = dict((opt_value, order + 1) for order, opt_value in enumerate(value))
        attrs = self.build_attrs(attrs, name=name)

        output = [u'<table %s><tbody>' % flatatt(attrs)]

        for i, (opt_value, opt_label) in enumerate(chain(self.choices, choices)):
            order = value_dict.get(opt_value, '')

            output.append(u"""
                <tr name="oms_row_%(i)s">
                    <td><input class="oms_check" type="checkbox" name="%(name)s_check_%(i)s" %(checked)s/></td>
                    <td class="oms_value">%(label)s<input type="hidden" name="%(name)s_value_%(i)s" value="%(value)s" /></td>
                    <td><input class="oms_order" type="text" name="%(name)s_order_%(i)s" value="%(order)s"/></td>
                </tr>""" % {
                                'i':        i,
                                'label':    opt_label,
                                'name':     name,
                                'value':    opt_value,
                                'checked':  'checked' if order else '',
                                'order':    order,
                            })

        output.append(u"""</tbody></table>
                          <script type="text/javascript">
                              $(document).ready(function() {
                                  creme.forms.toOrderedMultiSelect('%s');
                              });
                          </script>""" % attrs['id'])

        return mark_safe(u'\n'.join(output))

    def value_from_datadict(self, data, files, name):
        prefix_check = '%s_check_' % name
        prefix_order = '%s_order_' % name
        prefix_value = '%s_value_' % name

        selected = []
        for key, value in data.iteritems():
            if key.startswith(prefix_check):
                index = key[len(prefix_check):] #in fact not an int...
                order = int(data.get(prefix_order + index) or 0)
                value = data[prefix_value + index]
                selected.append((order, value))

        selected.sort(key=lambda i: i[0])

        return [val for order, val in selected]

class Label(TextInput):
    def render(self, name, value, attrs=None):
        html_output = u"""
            %(input)s<span %(attrs)s>%(content)s</span>
        """ % {
            'input'  : super(Label, self).render(name, value, {'style':'display:none;'}),
            'attrs'  : flatatt(self.build_attrs(attrs, name=name)),
            'content': value
        }
        return mark_safe(html_output)
