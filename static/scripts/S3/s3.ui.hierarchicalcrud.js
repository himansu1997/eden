/**
 * jQuery UI HierarchicalCRUD Widget for S3HierarchyCRUD
 *
 * @copyright 2015-2021 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 * requires jQuery jstree 3.0.3
 */
(function($, undefined) {

    "use strict";
    var hierarchicalcrudID = 0;

    /**
     * HierarchicalCRUD widget
     */
    $.widget('s3.hierarchicalcrud', {

        /**
         * Default options
         *
         * @todo document options
         * @todo simplify CRUD URL handling
         */
        options: {
            widgetID: null,
            ajaxURL: null,

            openLabel: 'Open',
            openURL: null,

            editTitle: 'Edit Record',
            editLabel: 'Edit',
            editURL: null,

            deleteLabel: 'Delete',
            deleteURL: null,
            deleteRoot: true,

            addTitle: 'Add Record',
            addLabel: 'Add',
            addURL: null,

            icons: false,
            stripes: true,
            htmlTitles: true
        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element);

            this.treeID = el.attr('id') + '-tree';

            this.id = hierarchicalcrudID;
            hierarchicalcrudID += 1;

        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            // The tree
            this.tree = el.find('.s3-hierarchy-tree');

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            var tree = this.tree,
                opts = this.options;

            this._unbindEvents();

            var roots = tree.find('> ul > li');
            if (roots.length == 1) {
                var root = roots.first();
                var node_data = root.data('jstree');
                root.data('jstree', $.extend({}, node_data, {'opened': true}));
            }

            var self = this;

            // Render tree
            tree.jstree({
                'core': {
                    'themes': {
                        //name: 'default', // 'default-dark' available, although not in our sources
                        icons: opts.icons,
                        stripes: opts.stripes
                    },
                    animation: 100,
                    multiple: false,
                    check_callback: true
                },
                'contextmenu': {
                    items: function($node) {

                        var deletable = true;
                        if (tree.jstree(true).get_parent($node) == '#') {
                           deletable = opts.deleteRoot;
                        }

                        var items = {};
                        if (opts.openURL) {
                            items.open = {
                                label: opts.openLabel,
                                action: function(obj) {
                                    self._openNode($node);
                                },
                                separator_after: true
                            }
                        }

                        // @todo: check permission for node and disable if forbidden
                        if (opts.editURL) {
                            items.edit = {
                                label: opts.editLabel,
                                action: function(obj) {
                                    self._editNode($node);
                                }
                            }
                        }

                        // @todo: check permission for node and disable if forbidden
                        if (deletable && opts.deleteURL) {
                            items.delete = {
                                label: opts.deleteLabel,
                                separator_after: true,
                                action: function(obj) {
                                    self._deleteNode($node);
                                }
                            }
                        }

                        if (opts.addURL) {
                            items.add = {
                                label: opts.addLabel,
                                action: function(obj) {
                                    self._addNode($node);
                                }
                            }
                        }

                        return items;
                    },
                    select_node: true
                },
                'plugins': ['sort', 'contextmenu']
            });

            this._bindEvents();
        },

        /**
         * Reload Tree
         * - called from s3.popup.js after a new top-level node created
         */
        reload: function() {
            // Load the data
            var ajaxURL = this.options.ajaxURL.replace('json', 'tree'),
                self = this;
            $.getS3(ajaxURL, function (data) {

                // Replace in the DOM
                self.tree.html(data);

                // Redraw the Tree
                self.refresh();
            }, 'html');
        },

        /**
         * Open a node
         *
         * @param {jQuery} node - the node object (li element)
         */
        _openNode: function(node) {

            var openURL = this.options.openURL,
                id = node.id;
            if (!openURL || !id) {
                return;
            }
            var record_id = parseInt(id.split('-').pop());
            if (record_id) {
                openURL = openURL.replace('[id]', record_id)
                                 .replace('%5Bid%5D', record_id);
                window.location.href = openURL;
            }
        },

        /**
         * Refresh a node
         *
         * @param {jQuery} node - the node object (li element)
         */
        refreshNode: function(node) {

            var ajaxURL = this.options.ajaxURL,
                id = node.attr('id');
            if (!ajaxURL || !id) {
                return;
            }
            var record_id = parseInt(id.split('-').pop());
            if (record_id) {
                ajaxURL = ajaxURL + '?node=' + record_id;
                var tree = this.tree,
                    treeID = this.treeID;
                $.getJSONS3(ajaxURL, function(data) {
                    if (data.label) {
                        tree.jstree('rename_node', node, data.label);
                    }
                    var children = data.children;
                    if (children) {
                        // Must render existing children so they can be updated,
                        // otherwise would add duplicates
                        tree.jstree('open_node', node, false, false);
                        var child, childID, childNode, added = 0;
                        for (var i=0, len=children.length; i<len; i++) {
                            child = children[i];
                            childID = treeID + '-' + child.node;
                            childNode = tree.jstree('get_node', '#' + childID, true);
                            if (childNode) {
                                tree.jstree('rename_node', childNode, child.label);
                            } else {
                                tree.jstree('create_node', node, {
                                    id: childID,
                                    text: child.label,
                                    li_attr: {
                                        // HTML attributes of the new node
                                        // @todo: CRUD permissions
                                        rel: 'leaf'
                                    }
                                });
                                added++;
                            }
                        }
                        if (added) {
                            tree.jstree('open_node', node);
                            node.attr({rel: 'parent'});
                        }
                    }
                });
            }
        },

        /**
         * Edit a node in a popup and refresh the node
         *
         * @param {jQuery} node - the node object (li element)
         */
        _editNode: function(node) {

            var editURL = this.options.editURL,
                id = node.id;
            if (!editURL || !id) {
                return;
            }
            var record_id = parseInt(id.split('-').pop());
            if (record_id) {

                var url = editURL.replace('[id]', record_id)
                                 .replace('%5Bid%5D', record_id)
                                 .split('?')[0];

                url += '?node=' + id + '&hierarchy=' + this.options.widgetID;

                // Open a jQueryUI Dialog showing a spinner until iframe is loaded
                var uid = S3.uid();
                var dialog = $('<iframe id="' + uid + '" src=' + url + ' onload="S3.popup_loaded(\'' + uid + '\')" class="loading" marginWidth="0" marginHeight="0" frameBorder="0"></iframe>')
                            .appendTo('body');
                this._openPopup(dialog, this.options.editTitle);
            }
        },

        /**
         * Add a node in a popup and refresh the parent node
         *
         * @param {jQuery} node - the parent node object (li element)
         */
        _addNode: function(parent) {

            var addURL = this.options.addURL,
                parent_id = parent.id;
            if (!addURL || !parent_id) {
                return;
            }
            var record_id = parseInt(parent_id.split('-').pop());
            if (record_id) {
                var url = addURL.split('?')[0];
                url += '?node=' + parent_id + '&link_to_parent=' + record_id + '&hierarchy=' + this.options.widgetID;

                // Open a jQueryUI Dialog showing a spinner until iframe is loaded
                var uid = S3.uid();
                var dialog = $('<iframe id="' + uid + '" src=' + url + ' onload="S3.popup_loaded(\'' + uid + '\')" class="loading" marginWidth="0" marginHeight="0" frameBorder="0"></iframe>')
                            .appendTo('body');
                this._openPopup(dialog, this.options.addTitle);
            }
        },

        /**
         * Ajax-delete a node (recursively, including all child nodes)
         *
         * @todo: option to disallow deletion of root node
         *
         * @param {jQuery} node - the node to delete
         */
        _deleteNode: function(node) {

            // Confirmation dialog
            if (!confirm(i18n.delete_confirmation)) {
                return false;
            }

            var deleteURL = this.options.deleteURL,
                id = node.id,
                tree = this.tree,
                self = this;
            if (!deleteURL || !id) {
                return;
            }
            var record_id = parseInt(id.split('-').pop());
            if (record_id) {
                var url = deleteURL.replace('[id]', record_id)
                                   .replace('%5Bid%5D', record_id)
                                   .split('?')[0];
                url += '?recursive=1';
                $.ajaxS3({
                    type: 'POST',
                    url: url,
                    data: {},
                    dataType: 'JSON',
                    // gets moved to .done() inside .ajaxS3
                    success: function(data) {
                        tree.jstree('delete_node', node);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        var msg = jqXHR.responseText;
                        if (msg[0] == "{") {
                            try {
                                msg = JSON.parse(jqXHR.responseText)
                                S3.showAlert(msg.message, 'error');
                            } catch(e) {}
                        }
                    }
                });
            }
        },

        /**
         * Open an iframe overlay as jQuery dialog, used by _addNode and _editNode
         *
         * @param {jQuery} dialog - the dialog
         * @param {string} title - the dialog title
         */
        _openPopup: function(dialog, title) {

            dialog.dialog({
                // add a close listener to prevent adding multiple divs to the document
                close: function(event, ui) {
                    if (self.parent) {
                        // There is a parent modal: refresh it to fix layout
                        var iframe = self.parent.$('iframe.ui-dialog-content');
                        var width = iframe.width();
                        iframe.width(0);
                        window.setTimeout(function() {
                            iframe.width(width);
                        }, 300);
                    }
                    // Remove div with all data and events
                    dialog.remove();
                },
                minHeight: 480,
                modal: true,
                open: function(event, ui) {
                    $('.ui-widget-overlay').bind('click', function() {
                        dialog.dialog('close');
                    });
                },
                title: title,
                minWidth: 320,
                closeText: ''
            });
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {
            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {
            this.tree.jstree('destroy', 'true'); // true = keep_html
            return true;
        }
    });
})(jQuery);
