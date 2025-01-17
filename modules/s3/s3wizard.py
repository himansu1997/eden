# -*- coding: utf-8 -*-

""" Resource Wizard Pages

    @copyright: 2013-2021 (c) Sahana Software Foundation
    @license: MIT

    @requires: U{B{I{gluon}} <http://web2py.com>}

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

from gluon import current
from gluon.html import *
from gluon.storage import Storage
from gluon.tools import redirect

from .s3crud import crud_button, embed_component
from .s3forms import S3SQLDefaultForm
from .s3rest import S3Method
from .s3utils import s3_redirect_default

__all__ = ("S3Wizard",
           "S3CrudWizard",
           )

# =============================================================================
class S3Wizard(S3Method):
    """ Resource Wizard Pages """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST interface

            @param r: the S3Request
            @param attr: controller attributes
        """

        wizard = r.resource.get_config("wizard") # Should be a sub-class of S3CrudWizard
        if not wizard:
            s3_redirect_default(r.url(method = ""))

        page = r.get_vars.get("page")
        if not page:
            # Use the 1st page
            r.get_vars["page"] = wizard.pages[0]["page"]

        # Allow the Wizard class access to the Method methods
        wizard.method = self

        # Hide other navigation to keep focus on the workflow
        current.menu.main = ""
        current.menu.options = None

        # Select the View template
        current.response.view = self._view(r, "wizard.html")

        return wizard(r, **attr)

# =============================================================================
class S3CrudWizard:
    """
        Base Class

        Each Wizard should inherit from this & configure it's pages & form method
    """

    # -------------------------------------------------------------------------
    def __init__(self):

        self.cancel = None # Page to go to upon 'Cancel'...defaults to List View for Resource
        self.new_id = None
        self.method = None
        self.pages = [{"page": "basic", # visible to developers via r.get_vars, can be used by prep/customise
                       "label": current.T("Basic info"), # visible to users via header
                       },
                      ]

    # -------------------------------------------------------------------------
    def __call__(self, r, **attr):

        if r.representation == "aadata":
            # dataTable paging
            return self._select(r, **attr)
        else:
            # Assume HTML
            output = self._select(r, **attr)
            output["form"] = self._form(r)
            output["header"] = self._header(r)

        return output

    # -------------------------------------------------------------------------
    def _form(self, r):
        """
            Produce the correct form for the current page
            - includes a simplified/merged version of S3CRUD.create / S3CRUD.update
        """

        pages = self.pages
        current_page = r.get_vars.get("page")

        method = self.method
        _config = method._config
        resource = method.resource
        component = r.component
        s3 = current.response.s3

        sqlform = _config("crud_form", S3SQLDefaultForm())

        if component:
            update = r.component_id
        else:
            update = r.id

        # Component join
        link = None
        if component:
            # JS Cancel (no redirect with embedded form)
            s3.cancel = {"hide": "list-add",
                         "show": "show-add-btn",
                         }

            record = r.record
            if not update:
                defaults = component.get_defaults(record)
                table = resource.table

            if resource.link is None:
                if not update:
                    # Apply component defaults
                    linked = resource.linked
                    ctable = linked.table if linked else table
                    for (k, v) in defaults.items():
                        ctable[k].default = v

                # Configure post-process for S3EmbeddedComponentWidget
                link = embed_component(resource, record=r.id)

                # Set default value for parent key (fkey)
                pkey = resource.pkey
                fkey = resource.fkey
                field = table[fkey]
                value = r.record[pkey]
                field.default = field.update = value

                # Add parent key to POST vars so that callbacks can see it
                if r.http == "POST":
                    r.post_vars.update({fkey: value})

                # Hide the parent link in component forms
                field.comment = None
                field.readable = False
                field.writable = False

            else:
                if not update:
                    # Apply component defaults
                    for (k, v) in defaults.items():
                        table[k].default = v

                # Configure post-process to add a link table entry
                link = Storage(resource = resource.link,
                               master = record,
                               )
        else:
            # Back / Next [or Finish] / Cancel buttons for Wizard
            # @ToDo: Also add these to the Component View (underneath Table)
            s3.cancel = self.cancel or r.url(method = "")          
            settings = s3.crud
            settings.submit_button = "Back"
            if current_page == pages[-1]["page"]:
                label = "Finish"
            else:
                label = "Next"
            settings.custom_submit = [("next",
                                       label,
                                       "small button next",
                                       ),
                                      ]

        if update:
            # Update form
            if not _config("editable", True) or \
               not method._permitted("update"):
                r.unauthorised()
            record_id = method.record_id
            message = method.crud_string(method.tablename, "msg_record_modified")
            onvalidation = _config("update_onvalidation") or \
                           _config("onvalidation")
            onaccept = _config("update_onaccept") or \
                       _config("onaccept")
        else:
            # Create form
            if not _config("insertable", True) or \
               not method._permitted("create"):
                r.unauthorised()
            record_id = None
            message = method.crud_string(method.tablename, "msg_record_created")
            onvalidation = _config("create_onvalidation") or \
                           _config("onvalidation")
            onaccept = _config("create_onaccept") or \
                       _config("onaccept")  

        form = sqlform(request = r,
                       resource = resource,
                       record_id = record_id,
                       onvalidation = onvalidation,
                       onaccept = onaccept,
                       link = link,
                       message = message,
                       subheadings = _config("subheadings"),
                       format = r.representation,
                       )

        if not component:
            if current_page == pages[0]["page"]:
                # Disable the Back button
                try:
                    form[0][-1][0][1][0][0]["_disabled"] = True
                except (KeyError, IndexError, TypeError):
                    # Submit button has been removed or a different formstyle,
                    # such as Bootstrap
                    pass

            if not update and \
               form.accepted:
                # If a master record create has been accepted then the next step of the wizard should use the new record
                self.new_id = form.session.rcvars[r.tablename]

        return form

    # -------------------------------------------------------------------------
    def _header(self, r):
        """
            Provide a visual of how many steps there are & which step we are on

            CSS in static/themes/default/scss/theme/_wizard.scss
        """

        T = current.T

        current_page = r.get_vars.get("page")
        pages = self.pages

        steps = []
        sappend = steps.append
        step = 1
        _back = None
        _next = None
        past = True
        for page in pages:
            _page = page["page"]
            if _page == current_page:
                _class = "current"
                past = False
                this = step - 1
            elif past:
                _class = "past"
                _back = _page # Last past
            else:
                _class = "future"
                if not _next:
                    _next = _page # 1st future
            sappend(LI(SPAN(STRONG(T("Step %d") % step)),
                       page["label"],
                       I(),
                       _class = _class,
                       ))
            step += 1

        # Configure Next
        if r.http == "POST":
            next_vars = dict(r.get_vars)
            if "next" in r.post_vars:
                next_vars.update(page = _next)
                component = pages[this + 1].get("component")
            else:
                next_vars.update(page = _back)
                component = pages[this - 1].get("component")
            record_id = r.id or self.new_id
            self.method.next = r.url(id = record_id,
                                     component = component,
                                     vars = next_vars,
                                     )

        ul = UL(*steps,
                _class = "steps",
                )
        # Include the number of steps to have each step use the available width
        ul["_data-steps"] = len(steps)
        return ul

    # -------------------------------------------------------------------------
    def _select(self, r, **attr):
        """
            Provide a list of Component Items
        """

        if not r.component:
            # No List View
            return {}

        output = self._datatable(r, **attr)

        if r.representation == "aadata":
            return output

        method = self.method
        resource = method.resource
        if resource.get_config("insertable", True):
            # Add a hidden add-form and a button to activate it
            tablename = resource.tablename
            output["addtitle"] = method.crud_string(tablename, "label_create")
            output["showadd_btn"] = crud_button(None,
                                                tablename = tablename,
                                                name = "label_create",
                                                icon = "add",
                                                _id = "show-add-btn",
                                                )

        return output

    # -------------------------------------------------------------------------
    def _datatable(self, r, **attr):
        """
            Get a data table
            - comes from S3CRUD._datatable

            @param r: the S3Request
            @param attr: parameters for the method handler
        """

        method = self.method

        # Check permission to read in this table
        if not self.method._permitted():
            r.unauthorised()

        resource = self.method.resource
        get_config = resource.get_config

        # Get table-specific parameters

        # List ID
        list_id = attr.get("list_id", "datatable")

        # List fields
        list_fields = resource.list_fields()

        # Default orderby
        orderby = get_config("orderby", None)

        response = current.response
        s3 = response.s3
        representation = r.representation

        # Pagination
        get_vars = r.get_vars
        if representation == "aadata":
            start, limit = self.method._limits(get_vars)
        else:
            # Initial page request always uses defaults (otherwise
            # filtering and pagination would have to be relative to
            # the initial limits, but there is no use-case for that)
            start = None
            limit = None if s3.no_sspag else 0

        # Initialize output
        output = {}

        # Linkto
        #linkto = get_config("linkto", None)
        #if not linkto:
        #    linkto = self._linkto(r)

        left = []
        distinct = False
        dtargs = attr.get("dtargs", {})

        if r.interactive:

            # How many records per page?
            if s3.dataTable_pageLength:
                display_length = s3.dataTable_pageLength
            else:
                display_length = 25

            # Server-side pagination?
            if not s3.no_sspag:
                dt_pagination = "true"
                if not limit:
                    limit = 2 * display_length
                current.session.s3.filter = get_vars
                if orderby is None:
                    dt_sorting = {"iSortingCols": "1",
                                  "sSortDir_0": "asc"
                                  }

                    if len(list_fields) > 1:
                        dt_sorting["bSortable_0"] = "false"
                        dt_sorting["iSortCol_0"] = "1"
                    else:
                        dt_sorting["bSortable_0"] = "true"
                        dt_sorting["iSortCol_0"] = "0"

                    orderby, left = resource.datatable_filter(list_fields,
                                                              dt_sorting,
                                                              )[1:3]
            else:
                dt_pagination = "false"

            # Get the data table
            dt, totalrows = resource.datatable(fields = list_fields,
                                               start = start,
                                               limit = limit,
                                               left = left,
                                               orderby = orderby,
                                               distinct = distinct,
                                               )
            displayrows = totalrows

            if not dt.data:
                # Empty table - or just no match?
                #if dt.empty:
                #    datatable = DIV(self.method.crud_string(resource.tablename,
                #                                            "msg_list_empty"),
                #                    _class = "empty")
                #else:
                #    #datatable = DIV(self.method.crud_string(resource.tablename,
                #                                             "msg_no_match"),
                #                     _class = "empty")

                # Must include export formats to allow subsequent unhiding
                # when Ajax (un-)filtering produces exportable table contents:
                #s3.no_formats = True

                if r.component and "showadd_btn" in output:
                    # Hide the list and show the form by default
                    del output["showadd_btn"]
                    datatable = ""

            # Always show table, otherwise it can't be Ajax-filtered
            # @todo: need a better algorithm to determine total_rows
            #        (which excludes URL filters), so that datatables
            #        shows the right empty-message (ZeroRecords instead
            #        of EmptyTable)
            dtargs["dt_pagination"] = dt_pagination
            dtargs["dt_pageLength"] = display_length
            dtargs["dt_base_url"] = r.url(method="", vars={})
            dtargs["dt_permalink"] = r.url()
            datatable = dt.html(totalrows,
                                displayrows,
                                id = list_id,
                                **dtargs)

            # View + data
            output["items"] = datatable

        elif representation == "aadata":

            # Apply datatable filters
            searchq, orderby, left = resource.datatable_filter(list_fields,
                                                               get_vars)
            if searchq is not None:
                totalrows = resource.count()
                resource.add_filter(searchq)
            else:
                totalrows = None

            # Orderby fallbacks
            if orderby is None:
                orderby = get_config("orderby", None)

            # Get a data table
            if totalrows != 0:
                dt, displayrows = resource.datatable(fields = list_fields,
                                                     start = start,
                                                     limit = limit,
                                                     left = left,
                                                     orderby = orderby,
                                                     distinct = distinct,
                                                     )
            else:
                dt, displayrows = None, 0
            if totalrows is None:
                totalrows = displayrows

            # Echo
            draw = int(get_vars.get("draw", 0))

            # Representation
            if dt is not None:
                output = dt.json(totalrows,
                                 displayrows,
                                 list_id,
                                 draw,
                                 **dtargs)
            else:
                output = '{"recordsTotal":%s,' \
                         '"recordsFiltered":0,' \
                         '"dataTable_id":"%s",' \
                         '"draw":%s,' \
                         '"data":[]}' % (totalrows, list_id, draw)

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

# END =========================================================================
