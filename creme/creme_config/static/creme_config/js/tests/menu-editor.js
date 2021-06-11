(function($) {
"use strict";

QUnit.module("creme.MenuEditor", new QUnitMixin(QUnitEventMixin,
                                                QUnitAjaxMixin,
                                                QUnitDialogMixin,
                                                QUnitMouseMixin, {
    beforeEach: function() {
        var backend = this.backend;

        this.setMockBackendPOST({
            'mock/group/reorder/0': backend.response(200, ''),
            'mock/group/reorder/0/fail': backend.response(400, 'Invalid request'),
            'mock/group/reorder/1': backend.response(200, ''),
            'mock/group/reorder/2': backend.response(200, ''),
            'mock/group/expand': backend.response(200, '')
        });
    },

    createJSONDataHtml: function(id, data) {
        var html = '<script type="application/json" class="${id}"><!-- ${data} --></script>'.template({
            id: id,
            data: Object.isString(data) ? data : JSON.stringify(data)
        });

        return html;
    },

    createMenuEditorWidgetHtml: function(options) {
        options = $.extend({
            id: 'test-menu-id'
        }, options || {});

        return (
            '<div class="menu-edit-widget" id="${id}">' +
                '${initialData}' +
                '${regularChoices}' +
                '<div class="menu-edit-entries-container">' +
                    '<div class="menu-edit-entries"></div>' +
                '</div>' +
                '<div class="menu-edit-widget-creations">' +
                    '<button class="ui-creme-actionbutton new-entries new-regular-entries" type="button">Add regular entries</button>' +
                    '${customButtons}' +
                '</div>' +
            '</div>'
        ).template({
            initialData: this.createJSONDataHtml('menu-edit-initial-data', options.initial || []),
            regularChoices: this.createJSONDataHtml('menu-edit-regular-choices', options.regularChoices || []),
            id: options.id,
            customButtons: (options.customButtons || []).map(function(button) {
                return (
                    '<button class="ui-creme-actionbutton new-entries new-extra-entry" type="button" data-url="${url}">${label}</button>'
                ).template(button);
            }).join('')
        });
    },

    createMenuItemHtml: function(options) {
        options = options || {};

        return (
            '<div class="menu-config-entry0" data-reorderable-menu-container-url="${url}">' +
                '<div class="menu-config-entry0-header">' +
                    '<span class="menu-config-entry0-header-title">${title}</span>' +
                '</div>' +
                '<div class="menu-config-entry0-content"><ul>' +
                    '${items}' +
                '</ul></div>' +
            '</div>'
        ).template({
            url: options.url,
            items: (options.items || []).map(function(item) {
                return '<li class="menu-config-entry0-${id}>${label}</li>'.template(item);
            }).join('')
        });
    },

    createMenuHtml: function(options) {
        options = options || {};

        return (
            '<div class="menu-config-container">${menus}</div>' +
            '<div class="menu-config-actions">${addRoot}${addSpecialRoot}</div>'
        ).template({
            items: (options.menus || []).map(this.createMenuEditorItemHtml.bind(this)).join(''),
            addRoot: this.createBrickActionHtml({
                url: '/mock/menu/add',
                action: 'add'
            }),
            addSpecialRoot: this.createBrickActionHtml({
                url: '/mock/menu/add/special',
                action: 'add'
            })
        });
    },

    createMenuBrickHtml: function(options) {
        options = $.extend({
            menu: {}
        }, options || {});

        var content = options.models.map(this.createMenuHtml.bind(this)).join('');

        return this.createBrickHtml($.extend({
            content: content
        }, options));
    },

    createMenuBrick: function(options) {
        var html = this.createMenuEditorBrickHtml(options);

        var element = $(html).appendTo(this.qunitFixture());
        var widget = creme.widget.create(element);
        var brick = widget.brick();

        equal(true, brick.isBound());
        equal(false, brick.isLoading());

        return widget;
    }
}));

QUnit.test('creme.MenuEditor (missing initial data)', function(assert) {
    var element = $(this.createMenuEditorWidgetHtml({}));

    this.assertRaises(function() {
        return new creme.MenuEditor(element, {});
    }, Error, 'Error: MenuEditor missing options.initialSelector');

    this.assertRaises(function() {
        return new creme.MenuEditor(element, {initialSelector: 'nowhere'});
    }, Error);
});

QUnit.test('creme.MenuEditor (invalid initial data)', function(assert) {
    var element = $(this.createMenuEditorWidgetHtml({
        initial: 'invalid{"json"'
    }));

    this.assertRaises(function() {
        return new creme.MenuEditor(element, {
            initialSelector: '.menu-edit-initial-data',
            regularChoicesSelector: '.menu-edit-regular-choices'
        });
    });
});

QUnit.test('creme.MenuEditor (invalid regular entries)', function(assert) {
    var element = $(this.createMenuEditorWidgetHtml({
        regularChoices: 'invalid{"json"'
    }));

    this.assertRaises(function() {
        return new creme.MenuEditor(element, {
            initialSelector: '.menu-edit-initial-data',
            regularChoicesSelector: '.menu-edit-regular-choices'
        });
    });
});


QUnit.test('creme.MenuEditor (empty initial, empty regular entries)', function(assert) {
    var element = $(this.createMenuEditorWidgetHtml({
        initial: [],
        regularChoices: []
    }));

    var editor = new creme.MenuEditor(element, {
        initialSelector: '.menu-edit-initial-data',
        regularChoicesSelector: '.menu-edit-regular-choices'
    });

    deepEqual(editor.value(), []);
    equal(element.find('.new-regular-entries').length, 0);
});


QUnit.test('creme.MenuEditor (empty initial, regular entries)', function(assert) {
    var element = $(this.createMenuEditorWidgetHtml({
        initial: [],
        regularChoices: [
            ['Item A', 'item-a'],
            ['Item B', 'item-b']
        ]
    }));

    var editor = new creme.MenuEditor(element, {
        initialSelector: '.menu-edit-initial-data',
        regularChoicesSelector: '.menu-edit-regular-choices'
    });

    deepEqual(editor.value(), []);
    equal(element.find('.menu-edit-entry').length, 0);
    equal(element.find('.new-regular-entries').length, 1);
});

QUnit.test('creme.MenuEditor (initial)', function(assert) {
    var element = $(this.createMenuEditorWidgetHtml({
        initial: [
            {label: "Item A", value: {id: "item-a"}},
            {label: "Item B", value: {id: "item-b"}}
        ]
    }));

    var editor = new creme.MenuEditor(element, {
        initialSelector: '.menu-edit-initial-data',
        regularChoicesSelector: '.menu-edit-regular-choices'
    });

    deepEqual(editor.value(), [
        {id: "item-a"},
        {id: "item-b"}
    ]);

    equal(element.find('.menu-edit-entry').length, 2);
    deepEqual(element.find('.menu-edit-entry-item-a').data('value'), {id: "item-a"});
    deepEqual(element.find('.menu-edit-entry-item-b').data('value'), {id: "item-b"});
});

QUnit.test('creme.MenuEditor (regular entry)', function(assert) {
    var element = $(this.createMenuEditorWidgetHtml({
        regularChoices: [
            ['Item A', 'item-a'],
            ['Item B', 'item-b'],
            ['Item C', 'item-c']
        ]
    }));

    var editor = new creme.MenuEditor(element, {
        initialSelector: '.menu-edit-initial-data',
        regularChoicesSelector: '.menu-edit-regular-choices'
    });

    deepEqual(editor.value(), []);

    element.find('new-regular-entries').trigger('click');
});

}(jQuery));
