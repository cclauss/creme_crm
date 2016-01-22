# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2015  Hybird
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

from collections import defaultdict
from json import dumps as json_dumps
import logging

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Q, FieldDoesNotExist, ProtectedError
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect
from django.utils.translation import ugettext as _

from ..auth.decorators import login_required
from ..core.exceptions import ConflictError, SpecificProtectedError
from ..forms import CremeEntityForm
from ..forms.bulk import BulkDefaultEditForm
from ..forms.merge import form_factory as merge_form_factory, MergeEntitiesBaseForm
from ..gui.bulk_update import bulk_update_registry, FieldNotAllowed
from ..models import CremeEntity, EntityCredentials, FieldsConfig
from ..models.fields import UnsafeHTMLField
from ..utils import get_ct_or_404, get_from_POST_or_404, get_from_GET_or_404, jsonify
from ..utils.chunktools import iter_as_slices
from ..utils.html import sanitize_html
from ..utils.meta import ModelFieldEnumerator
from ..views.decorators import POST_only
from ..views.generic import inner_popup, list_view_popup_from_widget


logger = logging.getLogger(__name__)


@login_required
@jsonify
def get_creme_entities_repr(request, entities_ids):
    # With the url regexp we are sure that int() will work
    e_ids = [int(e_id) for e_id in entities_ids.split(',') if e_id]

    entities = CremeEntity.objects.in_bulk(e_ids)
    CremeEntity.populate_real_entities(list(entities.itervalues()))  # NB: list + itervalues = Py3K ready

    user = request.user
    has_perm = user.has_perm_to_view

    return [{'id': e_id,
             'text': entity.get_real_entity().get_entity_summary(user)
                     if has_perm(entity) else
                     _(u'Entity #%s (not viewable)') % e_id
            } for e_id, entity in ((e_id, entities.get(e_id)) for e_id in e_ids)
                if entity is not None
           ]


@login_required
def get_sanitized_html_field(request, entity_id, field_name):
    """Used to show an HTML document in an <iframe>."""
    entity = get_object_or_404(CremeEntity, pk=entity_id)
    request.user.has_perm_to_view_or_die(entity)

    entity = entity.get_real_entity()

    try:
        field = entity._meta.get_field(field_name)
    except FieldDoesNotExist:
        raise ConflictError('This field does not exist.')

    if not isinstance(field, UnsafeHTMLField):
        raise ConflictError('This field is not an HTMLField.')

    unsafe_value = getattr(entity, field_name)

    return HttpResponse('' if not unsafe_value else
                        sanitize_html(unsafe_value,
                                      allow_external_img=request.GET.get('external_img', False),
                                     )
                       )


# TODO: bake the result in HTML instead of ajax view ??
@jsonify
@login_required
def get_info_fields(request, ct_id):
    ct = get_ct_or_404(ct_id)
    model = ct.model_class()

    if not issubclass(model, CremeEntity):
        raise Http404('No a CremeEntity subclass: %s' % model)

    # TODO: use django.forms.models.fields_for_model ?
    form = modelform_factory(model, CremeEntityForm)(user=request.user)
    required_fields = [name for name, field in form.fields.iteritems()
                           if field.required and name != 'user'
                      ]

    kwargs = {}
    if len(required_fields) == 1:
        required_field = required_fields[0]
        kwargs['printer'] = lambda field: unicode(field.verbose_name) \
                                          if field.name != required_field else \
                                          _(u'%s [CREATION]') % field.verbose_name

    is_hidden = FieldsConfig.get_4_model(model).is_field_hidden

    return ModelFieldEnumerator(model).filter(viewable=True)\
                                      .exclude(lambda f, deep: is_hidden(f))\
                                      .choices(**kwargs)


@login_required
def clone(request):
    # TODO: Improve credentials ?
    entity_id = get_from_POST_or_404(request.POST, 'id')
    entity    = get_object_or_404(CremeEntity, pk=entity_id).get_real_entity()

    if entity.get_clone_absolute_url() != CremeEntity.get_clone_absolute_url():
        raise Http404(_(u'This model does not use the generic clone view.'))

    user = request.user
    user.has_perm_to_create_or_die(entity)
    user.has_perm_to_view_or_die(entity)

    new_entity = entity.clone()

    return redirect(new_entity)


@login_required
def search_and_view(request):
    GET = request.GET
    model_ids = get_from_GET_or_404(GET, 'models').split(',')
    fields    = get_from_GET_or_404(GET, 'fields').split(',')
    value     = get_from_GET_or_404(GET, 'value')

    if not value:  # Avoid useless queries
        raise Http404(u'Void "value" arg')

    user = request.user
    has_perm = user.has_perm
    models = []

    for model_id in model_ids:
        try:
            ct = ContentType.objects.get_by_natural_key(*model_id.split('-'))
        except (ContentType.DoesNotExist, TypeError):
            raise Http404(u'This model does not exist: %s' % model_id)

        if not has_perm(ct.app_label):
            raise PermissionDenied(_(u"You are not allowed to access to this app"))

        model = ct.model_class()

        if issubclass(model, CremeEntity):
            models.append(model)

    if not models:
        raise Http404(u'No valid model')

    fconfigs = FieldsConfig.get_4_models(models)

    for model in models:
        query = Q()

        for field_name in fields:
            try:
                field = model._meta.get_field(field_name)
            except FieldDoesNotExist:
                pass
            else:
                if fconfigs[model].is_field_hidden(field):
                    raise ConflictError(_('This field is hidden.'))

                query |= Q(**{field.name: value})

        if query:  # Avoid useless query
            found = EntityCredentials.filter(user, model.objects.filter(query)).first()

            if found:
                return redirect(found)

    raise Http404(_(u'No entity corresponding to your search was found.'))


def _bulk_has_perm(entity, user):
    owner = entity.get_related_entity() if hasattr(entity, 'get_related_entity') else entity
    return user.has_perm_to_change(owner)


@login_required
def inner_edit_field(request, ct_id, id, field_name):
    user   = request.user
    model  = get_ct_or_404(ct_id).model_class()
    entity = get_object_or_404(model, pk=id)  # TODO: rename (& 'entities' arg too ?) because not always an entity...

    if not _bulk_has_perm(entity, user):
        raise PermissionDenied(_(u'You are not allowed to edit this entity'))

    try:
        form_class = bulk_update_registry.get_form(model, field_name, BulkDefaultEditForm)

        if request.method == 'POST':
            form = form_class(entities=[entity], user=user, data=request.POST)

            if form.is_valid():
                form.save()
        else:
            form = form_class(entities=[entity], user=user)
    except (FieldDoesNotExist, FieldNotAllowed):
        return HttpResponseBadRequest(_(u'The field "%s" doesn\'t exist or cannot be edited' % field_name))

    return inner_popup(request, 'creme_core/generics/blockform/edit_popup.html',
                       {'form':  form,
                        'title': _(u'Edit «%s»') % unicode(entity),
                       },
                       is_valid=form.is_valid(),
                       reload=False, delegate_reload=True,
                      )


@login_required
def bulk_edit_field(request, ct_id, id, field_name):
    user   = request.user
    model  = get_ct_or_404(ct_id).model_class()
    entities = get_list_or_404(model, pk__in=id.split(','))

    filtered = [e for e in entities if _bulk_has_perm(e, user)]

    if not filtered:
        raise PermissionDenied(_(u'You are not allowed to edit these entities'))

    if field_name is None:
        field_name = bulk_update_registry.get_default_field(model).name

    try:
        form_class = bulk_update_registry.get_form(model, field_name, BulkDefaultEditForm)

        if request.method == 'POST':
            form = form_class(entities=filtered, user=user, data=request.POST, is_bulk=True)

            if form.is_valid():
                form.save()
                return render(request, 'creme_core/frags/bulk_process_report.html',
                              {'form':  form,
                               'title': _(u'Multiple update'),
                              },
                             )
        else:
            form = form_class(entities=filtered, user=user, is_bulk=True)
    except (FieldDoesNotExist, FieldNotAllowed):
        return HttpResponseBadRequest(_(u'The field "%s" doesn\'t exist or cannot be edited' % field_name))

    return inner_popup(request, 'creme_core/generics/blockform/edit_popup.html',
                       {'form':  form,
                        'title': _(u'Multiple update'),
                       },
                       is_valid=form.is_valid(),
                       reload=False, delegate_reload=True,
                      )


@login_required
def select_entity_for_merge(request, entity1_id):
    entity1 = get_object_or_404(CremeEntity, pk=entity1_id)

    if merge_form_factory(entity1.entity_type.model_class()) is None:
        raise ConflictError('This type of entity cannot be merged')

    user = request.user
    user.has_perm_to_view_or_die(entity1); user.has_perm_to_change_or_die(entity1)

    # TODO: filter viewable & deletable entities + (manage swapping ?)
    # TODO: change list_view_popup_from_widget code (o2m should be '1', but True works)
    return list_view_popup_from_widget(request, entity1.entity_type_id, o2m=True,
                                       extra_q=~Q(pk=entity1_id)
                                      )


@login_required
def merge(request, entity1_id, entity2_id):
    entity1 = get_object_or_404(CremeEntity, pk=entity1_id)
    entity2 = get_object_or_404(CremeEntity, pk=entity2_id)

    if entity1.id == entity2.id:
        raise ConflictError('You can not merge an entity with itself.')

    if entity1.entity_type_id != entity2.entity_type_id:
        raise ConflictError('You can not merge entities of different types.')

    user = request.user
    can_view = user.has_perm_to_view_or_die
    can_view(entity1); user.has_perm_to_change_or_die(entity1)
    can_view(entity2); user.has_perm_to_delete_or_die(entity2)

    # TODO: try to swap 1 & 2

    entity1 = entity1.get_real_entity()
    entity2 = entity2.get_real_entity()

    EntitiesMergeForm = merge_form_factory(entity1.__class__)

    if EntitiesMergeForm is None:
        raise ConflictError('This type of entity cannot be merged')

    if request.method == 'POST':
        POST = request.POST
        merge_form = EntitiesMergeForm(user=request.user, data=POST,
                                       entity1=entity1, entity2=entity2,
                                      )

        if merge_form.is_valid():
            merge_form.save()

            # NB: we get the entity1 attribute (ie: not the local variable),
            # because the entities can be swapped in the form (but form.entity1
            # is always kept & form.entity2 deleted).
            return redirect(merge_form.entity1)

        cancel_url = POST.get('cancel_url')
    else:
        try:
            merge_form = EntitiesMergeForm(user=request.user, entity1=entity1, entity2=entity2)
        except MergeEntitiesBaseForm.CanNotMergeError as e:
            raise ConflictError(e)

        cancel_url = request.META.get('HTTP_REFERER')

    return render(request, 'creme_core/merge.html',
                  {'form':   merge_form,
                   'title': _('Merge <%(entity1)s> with <%(entity2)s>') % {
                                   'entity1': entity1,
                                   'entity2': entity2,
                                },
                    'help_message': _(u'You are going to merge two entities into a new one.\n'
                                      'Choose which information you want the old entities '
                                      'give to the new entity.\n'
                                      'The relationships, the properties and the other links '
                                      'with any of old entities will be automatically '
                                      'available in the new merged entity.'
                                     ),
                    'submit_label': _('Merge'),
                    'cancel_url': cancel_url,
                  }
                 )


@login_required
def trash(request):
    return render(request, 'creme_core/trash.html')


@login_required
@POST_only
def empty_trash(request):
    user = request.user

    # We try to delete the remaining entities (which could not be deleted 
    # because of relationships) when there are errors, while the previous 
    # iteration managed to remove some entities.
    # It will not work with cyclic references (but it is certainly very unusual).
    while True:
        progress = False
        errors = []  # TODO: LimitedList
        # NB: we do not use delete() method of queryset in order to send signals
        entities = EntityCredentials.filter(user,
                                            CremeEntity.objects.filter(is_deleted=True),
                                            EntityCredentials.DELETE,
                                           )

        for entities_slice in iter_as_slices(entities, 1024):
            CremeEntity.populate_real_entities(entities_slice)

            for entity in entities_slice:
                entity = entity.get_real_entity()

                try:
                    entity.delete()
                except ProtectedError:
                    errors.append(_(u'"%s" can not be deleted because of its dependencies.') %
                                    entity.allowed_unicode(user)
                                 )
                except Exception as e:
                    logger.exception('Error when trying to empty the trash')
                    errors.append(_(u'"%(entity)s" deletion caused an unexpected error [%(error)s].') % {
                                        'entity': entity.allowed_unicode(user),
                                        'error':  e,
                                    }
                                 )
                else:
                    progress = True

        if not errors or not progress:
            break

    # TODO: factorise ??
    if not errors:
        status = 200
        message = _('Operation successfully completed')
    else:
        status = 409
        message = _('The following entities cannot be deleted') + \
                  u'<ul>%s</ul>' % u'\n'.join(u'<li>%s</li>' % msg for msg in errors)

    return HttpResponse(message, content_type='text/javascript', status=status)


@login_required
@POST_only
def restore_entity(request, entity_id):
    entity = get_object_or_404(CremeEntity.objects.filter(is_deleted=True), pk=entity_id) \
                                                  .get_real_entity()

    if entity.get_delete_absolute_url() != CremeEntity.get_delete_absolute_url(entity):
        raise Http404(_(u'This model does not use the generic deletion view.'))

    if hasattr(entity, 'get_related_entity'):
        raise Http404('Can not restore an auxiliary entity')  # See trash_entity()

    request.user.has_perm_to_delete_or_die(entity)
    entity.restore()

    if request.is_ajax():
        return HttpResponse(content_type='text/javascript')

    return redirect(entity)


def _delete_entity(user, entity):
    if entity.get_delete_absolute_url() != CremeEntity.get_delete_absolute_url(entity):
        return 404, _('%s does not use the generic deletion view.') % entity.allowed_unicode(user)

    if hasattr(entity, 'get_related_entity'):
        related = entity.get_related_entity()

        if related is None:
            logger.critical('delete_entity(): an auxiliary entity seems orphan (id=%s)', entity.id)
            return 403, _(u'You are not allowed to delete this entity: %s') % entity.allowed_unicode(user)

        if not user.has_perm_to_change(related):
            return 403, _(u'%s : <b>Permission denied</b>') % entity.allowed_unicode(user)

        trash = False
    else:
        if not user.has_perm_to_delete(entity):
            return 403, _(u'%s : <b>Permission denied</b>') % entity.allowed_unicode(user)

        trash = not entity.is_deleted

    try:
        if trash:
            entity.trash()
        else:
            entity.delete()
    except SpecificProtectedError as e:
        return (400,
                u'%s %s' % (
                    _(u'"%s" can not be deleted.') % entity.allowed_unicode(user),
                    e.args[0],
                  ),
               )
    except ProtectedError as e:
        return (400,
                _(u'"%s" can not be deleted because of its dependencies.') %
                    entity.allowed_unicode(user),
                {'protected_objects': e.args[1]},
               )
    except Exception as e:
        logger.exception('Error when trying to empty the trash')
        return (400,
                _(u'"%(entity)s" deletion caused an unexpected error [%(error)s].') % {
                        'entity': entity.allowed_unicode(user),
                        'error':  e,
                    }
               )


@login_required
def delete_entities(request):
    "Delete several CremeEntities, with a Ajax call (POST method)."
    try:
        entity_ids = [int(e_id) for e_id in get_from_POST_or_404(request.POST, 'ids').split(',') if e_id]
    except ValueError:
        return HttpResponse('Bad POST argument', content_type='text/javascript', status=400)

    if not entity_ids:
        return HttpResponse(_('No selected entities'), content_type='text/javascript', status=400)

    logger.debug('delete_entities() -> ids: %s ', entity_ids)

    user     = request.user
    entities = list(CremeEntity.objects.filter(pk__in=entity_ids))
    errors   = defaultdict(list)

    len_diff = len(entity_ids) - len(entities)
    if len_diff:
        errors[404].append(_(u"%s entities doesn't exist / doesn't exist any more") % len_diff)

    CremeEntity.populate_real_entities(entities)

    for entity in entities:
        error = _delete_entity(user, entity.get_real_entity())
        if error:
            errors[error[0]].append(error[1])  # TODO: use error[2] if exists ??

    if not errors:
        status = 200
        message = _('Operation successfully completed')
    else:
        status = min(errors.iterkeys())
        message = json_dumps({'count': len(entity_ids),
                              'errors': [msg for error_messages in errors.itervalues() for msg in error_messages],
                             }
                            )

    return HttpResponse(message, content_type='text/javascript', status=status)


@login_required
# TODO: @redirect_if_not_ajax
@POST_only
def delete_entity(request, entity_id):
    entity = get_object_or_404(CremeEntity, pk=entity_id).get_real_entity()
    error = _delete_entity(request.user, entity)

    if error:
        # code, msg = error #TODO: Python3 => code, msg, *args = error
        code, msg, args = error if len(error) == 3 else error + ({},)

        if code == 404: raise Http404(msg)
        # TODO: 400 => ConflictError ??

        raise PermissionDenied(msg, args)

    if request.is_ajax():
        return HttpResponse(content_type='text/javascript')

    if hasattr(entity, 'get_lv_absolute_url'):
        url = entity.get_lv_absolute_url()
    elif hasattr(entity, 'get_related_entity'):
        url = entity.get_related_entity().get_absolute_url()
    else:
        url = '/'

    return HttpResponseRedirect(url)


@login_required
def delete_related_to_entity(request, ct_id):
    """Delete a model related to a CremeEntity.
    @param request: Request with POST method ; POST data should contain an 'id'(=pk) value.
    @param model: A django model class that implements the method get_related_entity().
    """
    model = get_ct_or_404(ct_id).model_class()
    if issubclass(model, CremeEntity):
        raise Http404('This view can not delete CremeEntities.')

    auxiliary = get_object_or_404(model, pk=get_from_POST_or_404(request.POST, 'id'))
    entity = auxiliary.get_related_entity()

    request.user.has_perm_to_change_or_die(entity)

    try:
        auxiliary.delete()
    except ProtectedError as e:
        raise PermissionDenied(e.args[0])

    if request.is_ajax():
        return HttpResponse(content_type='text/javascript')

    return redirect(entity)
