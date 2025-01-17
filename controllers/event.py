# -*- coding: utf-8 -*-

"""
    Event Module - Controllers

    http://eden.sahanafoundation.org/wiki/BluePrintScenario
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(c, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Events
    s3_redirect_default(URL(f = "event"))

# -----------------------------------------------------------------------------
def create():
    """ Redirect to event/create """
    redirect(URL(f = "event",
                 args = "create",
                 ))

# -----------------------------------------------------------------------------
def event():
    """
        RESTful CRUD controller
    """

    # Pre-process
    def prep(r):
        if r.interactive:
            method = r.method
            if r.component:
                cname = r.component_name
                if cname == "req":
                    if method != "update" and method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        from s3db.inv import inv_req_create_form_mods
                        inv_req_create_form_mods(r)

                #elif cname == "document":
                #    # @ToDo: Filter Locations available based on Event Locations
                #    #s3db.doc_document.location_id.default = r.record.location_id

                #elif cname == "impact":
                #    # @ToDo: Filter Locations available based on Event Locations
                #    #s3db.stats_impact.location_id.default = r.record.location_id

                #elif cname == "image":
                #    # @ToDo: Filter Locations available based on Event Locations
                #    #s3db.doc_document.location_id.default = r.record.location_id

                elif cname == "response":
                    # @ToDo: Filter Locations available based on Event Locations
                    #s3db.dc_collection.location_id.default = r.record.location_id
                    s3.crud_strings["dc_response"].label_create = T("Add Assessment")

                elif cname == "target":
                    # Filter Locations available based on Event Locations
                    ltable = s3db.event_event_location
                    locations = db(ltable.event_id == r.id).select(ltable.location_id)
                    if len(locations) == 1:
                        s3db.dc_target.location_id.default = locations.first().location_id
                    #else:
                    #    # @ToDo: Filter to Event Locations
                    s3.crud_strings["dc_target"].label_create = T("Add Target")

            elif method in ("create", "list", "summary"):
                # Create or ListCreate: Simplify
                r.table.closed.writable = r.table.closed.readable = False

            #elif method == "update":
            #    # Can't change details after event activation
            #    table = r.table
            #    table.exercise.writable = False
            #    table.exercise.comment = None
            #    table.start_date.writable = False

        return True
    s3.prep = prep

    from s3db.event import event_rheader
    return s3_rest_controller(rheader = event_rheader)

# -----------------------------------------------------------------------------
def event_location():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def event_type():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def incident_type():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def incident():
    """
        RESTful CRUD controller
    """

    # Pre-process
    def prep(r):
        if r.interactive or r.representation == "aadata":
            if r.component:
                if r.component.alias == "assign":
                    if not r.method:
                        r.method = "assign"
                    if r.method == "assign":
                        r.custom_action = s3db.hrm_AssignMethod(component = "assign")

                cname = r.component_name
                if cname == "config":
                    s3db.configure("gis_config",
                                   deletable = False,
                                   )
                    s3.crud.submit_button = T("Update")

                elif cname == "sitrep":
                    stable = s3db.event_sitrep
                    stable.location_id.default = r.record.location_id
                    stable.event_id.readable = stable.event_id.writable = False
                    list_fields = s3db.get_config("event_sitrep", "list_fields")
                    try:
                        list_fields.remove("event_id")
                    except ValueError:
                        # Already removed
                        pass
                    # @ToDo: PDF export of Single SitReps
                    # - UI Button
                    # - Custom layout
                    # Remove PDF export of List of SitReps
                    # - currently crashing when there is significant richtext content & an unlikely usecase
                    export_formats = settings.ui.export_formats
                    if not export_formats:
                        export_formats = settings.get_ui_export_formats()
                    if "pdf" in export_formats:
                        export_formats = list(export_formats)
                        export_formats.remove("pdf")
                        settings.ui.export_formats = export_formats

                elif cname in ("asset", "human_resource", "event_organisation", "organisation", "site"):
                    atable = s3db.table("budget_allocation")
                    if atable:
                        atable.budget_entity_id.default = r.record.budget_entity_id

                    #s3.crud.submit_button = T("Assign")
                    #s3.crud.submit_button = T("Add")
                    s3.crud_labels["DELETE"] = T("Remove")

                    if cname == "asset":
                        # Filter Assets by Item Type
                        s3.scripts.append("/%s/static/scripts/S3/s3.event_asset.js" % r.application)
                        # Modify Popup URL
                        s3db.event_asset.asset_id.comment.vars = {"prefix": "event",
                                                                  "parent": "asset",
                                                                  }

                    # Default Event in the link to that of the Incident
                    if cname == "event_organisation":
                        ltable = s3db.table(cname)
                    else:
                        ltable = s3db.table("event_%s" % cname)
                    if ltable:
                        f = ltable.event_id
                        f.default = r.record.event_id
                        f.readable = f.writable = False

                elif cname == "incident_asset":
                    atable = s3db.table("budget_allocation")
                    if atable:
                        atable.budget_entity_id.default = r.record.budget_entity_id

                    #s3.crud.submit_button = T("Assign")
                    #s3.crud.submit_button = T("Add")
                    s3.crud_labels["DELETE"] = T("Remove")

                    # Default Event in the link to that of the Incident
                    ltable = s3db.table("event_asset")
                    f = ltable.event_id
                    f.default = r.record.event_id
                    f.readable = f.writable = False
                    # DateTime
                    datetime_represent = s3base.S3DateTime.datetime_represent
                    for f in (ltable.start_date, ltable.end_date):
                        f.requires = IS_EMPTY_OR(IS_UTC_DATETIME())
                        f.represent = lambda dt: datetime_represent(dt, utc=True)
                        f.widget = S3CalendarWidget(timepicker = True)

            elif r.method not in ("read", "update"):
                # Create or ListCreate
                table = r.table
                table.closed.writable = table.closed.readable = False
                table.end_date.writable = table.end_date.readable = False

            elif r.method == "update":
                # Can't change details after event activation
                table = r.table
                table.exercise.writable = False
                table.exercise.comment = None
                table.date.writable = False

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    #update_url = URL(c="hrm", f="human_resource",
                    #                 args = ["[id]"],
                    #                 )
                    #s3_action_buttons(r, update_url=update_url)
                    s3_action_buttons(r)
                    if "msg" in settings.modules:
                        s3base.S3CRUD.action_button(url = URL(f = "compose",
                                                              vars = {"hrm_id": "[id]"}
                                                              ),
                                                    _class = "action-btn send",
                                                    label = s3_str(T("Send Notification")),
                                                    )
        return output
    s3.postp = postp

    from s3db.event import event_rheader
    return s3_rest_controller(rheader = event_rheader)

# -----------------------------------------------------------------------------
def incident_report():
    """
        RESTful CRUD controller
    """

    def prep(r):
        if r.http == "GET":
            if r.method in ("create", "create.popup"):
                get_vars_get = get_vars.get
                # Lat/Lon from Feature?
                # @ToDo: S3PoIWidget() instead to pickup the passed Lat/Lon/WKT
                field = r.table.location_id
                lat = get_vars_get("lat", None)
                if lat is not None:
                    lon = get_vars.get("lon", None)
                    if lon is not None:
                        form_vars = Storage(lat = float(lat),
                                            lon = float(lon),
                                            )
                        form = Storage(vars = form_vars)
                        s3db.gis_location_onvalidation(form)
                        location_id = s3db.gis_location.insert(**form_vars)
                        field.default = location_id
                # WKT from Feature?
                wkt = get_vars_get("wkt", None)
                if wkt is not None:
                    form_vars = Storage(wkt = wkt,
                                        )
                    form = Storage(vars = form_vars)
                    s3db.gis_location_onvalidation(form)
                    location_id = s3db.gis_location.insert(**form_vars)
                    field.default = location_id
                # Incident Type from caller?
                incident_type = get_vars_get("incident_type", None)
                if incident_type is not None:
                    ttable = s3db.event_incident_type
                    incident_type = db(ttable.name == incident_type).select(ttable.id,
                                                                            limitby = (0, 1),
                                                                            ).first()
                    r.table.incident_type_id.default = incident_type.id

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def job_title():
    """ Job Titles Controller """

    table = s3db.hrm_job_title
    s3.crud_strings["hrm_job_title"] = Storage(
        label_create = T("Add Position"),
        title_display = T("Position Details"),
        title_list = T("Positions"),
        title_update = T("Edit Position"),
        label_list_button = T("List Positions"),
        label_delete_button = T("Remove Position"),
        msg_record_created = T("Position added"),
        msg_record_modified = T("Position updated"),
        msg_record_deleted = T("Position removed"),
        msg_list_empty = T("No Positions currently registered"),
        )

    def prep(r):
        # Default / Hide type
        f = table.type
        f.default = 4 # Deployment
        f.readable = f.writable = False

        # Positions are never org-specific
        f = table.organisation_id
        f.readable = f.writable = False

        if r.representation == "xls":
            # Export format should match Import format
            current.messages["NONE"] = ""
            #f.represent = \
            #    s3db.org_OrganisationRepresent(acronym = False,
            #                                   parent = False)
            #f.label = None
            table.comments.label = None
            table.comments.represent = lambda v: v or ""
        return True
    s3.prep = prep

    s3.filter = FS("type").belongs((4,))

    if not auth.s3_has_role("ADMIN"):
        s3.filter &= auth.filter_by_root_org(table)

    return s3_rest_controller("hrm")

# -----------------------------------------------------------------------------
def scenario():
    """
        RESTful CRUD controller
    """

    from s3db.event import event_rheader
    return s3_rest_controller(rheader = event_rheader)

# -----------------------------------------------------------------------------
def sitrep():
    """ RESTful CRUD controller """

    if settings.get_event_sitrep_dynamic():
        # All templates use the same component name for answers so need to add the right component manually
        try:
            sitrep_id = int(request.args(0))
        except:
            # Multiple record method
            pass
        else:
            dtable = s3db.s3_table
            stable = s3db.event_sitrep
            ttable = s3db.dc_template
            query = (stable.id == sitrep_id) & \
                    (stable.template_id == ttable.id) & \
                    (ttable.table_id == dtable.id)
            template = db(query).select(dtable.name,
                                        limitby = (0, 1),
                                        ).first()
            try:
                dtablename = template.name
            except:
                # Old URL?
                pass
            else:
                components = {dtablename: {"name": "answer",
                                           "joinby": "sitrep_id",
                                           "multiple": False,
                                           },
                              }
                s3db.add_components("event_sitrep", **components)

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component_name == "answer":
                # CRUD Strings
                tablename = r.component.tablename
                #s3.crud_strings[tablename] = Storage(
                #    label_create = T("Create Responses"),
                #    title_display = T("Response Details"),
                #    title_list = T("Responses"),
                #    title_update = T("Edit Response"),
                #    label_list_button = T("List Responses"),
                #    label_delete_button = T("Clear Response"),
                #    msg_record_created = T("Response created"),
                #    msg_record_modified = T("Response updated"),
                #    msg_record_deleted = T("Response deleted"),
                #    msg_list_empty = T("No Responses currently defined"),
                #)

                # Custom Form with Questions & Subheadings sorted correctly
                from s3db.dc import dc_answer_form
                dc_answer_form(r, tablename)

        return True
    s3.prep = prep

    from s3db.event import event_rheader
    return s3_rest_controller(rheader = event_rheader)

# -----------------------------------------------------------------------------
def template():
    """ RESTful CRUD controller """

    from s3 import FS
    s3.filter = FS("master") == "event_sitrep"

    s3db.dc_template.master.default = "event_sitrep"

    from s3db.dc import dc_rheader
    return s3_rest_controller("dc", "template",
                              rheader = dc_rheader,
                              )

# -----------------------------------------------------------------------------
def person():
    """ Person controller for AddPersonWidget """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            current.xml.show_ids = True
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person")

# -----------------------------------------------------------------------------
def group():
    """
        Module-specific controller for Teams

        @note: currently for development/testing/demo purposes only (WIP),
               may be replaced by hrm_group controller in future
    """

    def prep(r):
        # Make the team status visible in list/read views
        if r.interactive or r.representation == "aadata":
            resource = r.resource
            list_fields = ["name",
                           "description",
                           "team_status_team.status_id",
                           "comments",
                           ]
            resource.configure(list_fields = list_fields)
        if r.interactive:
            from s3 import S3SQLCustomForm, S3SQLInlineComponent
            crud_fields = ["name",
                           "description",
                           S3SQLInlineComponent("team_status_team",
                                                fields = [("", "status_id")],
                                                label = T("Status"),
                                                multiple = False,
                                                ),
                           "comments",
                           ]
            crud_form = S3SQLCustomForm(*crud_fields)
            r.resource.configure(crud_form = crud_form)
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "group")

# -----------------------------------------------------------------------------
def team():
    """ Events <> Teams """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def team_status():
    """ Team statuses """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def human_resource():
    """ Events <> Human Resources """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def organisation():
    """ Events <> Organisations """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def asset():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        item_id = r.get_vars.get("item_id")
        if item_id:
            # e.g. Coming from event_asset form in Incident Action Plan
            requires = r.table.asset_id.requires
            if hasattr(requires, 'other'):
                requires.other.set_filter(filterby = "item_id",
                                          filter_opts = [item_id],
                                          )
            else:
                requires.set_filter(filterby = "item_id",
                                    filter_opts = [item_id],
                                    )
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def compose():
    """ Send message to people/teams """

    req_vars = request.vars

    if "hrm_id" in req_vars:
        hrm_id = req_vars.hrm_id
        fieldname = "hrm_id"
        table = s3db.pr_person
        htable = s3db.hrm_human_resource
        pe_id_query = (htable.id == hrm_id) & \
                      (htable.person_id == table.id)
        title = T("Send a message to this person")
    else:
        session.error = T("Record not found")
        redirect(URL(f="index"))

    pe = db(pe_id_query).select(table.pe_id,
                                limitby = (0, 1),
                                ).first()
    if not pe:
        session.error = T("Record not found")
        redirect(URL(f="index"))

    pe_id = pe.pe_id

    # Get the individual's communications options & preference
    table = s3db.pr_contact
    contact = db(table.pe_id == pe_id).select(table.contact_method,
                                              orderby = "priority",
                                              limitby = (0, 1),
                                              ).first()
    if contact:
        s3db.msg_outbox.contact_method.default = contact.contact_method
    else:
        session.error = T("No contact method found")
        redirect(URL(f="index"))

    # URL to redirect to after message sent
    url = URL(c = "event",
              f = "compose",
              vars = {fieldname: hrm_id},
              )

    # Create the form
    output = msg.compose(recipient = pe_id,
                         url = url,
                         )

    output["title"] = title
    response.view = "msg/compose.html"
    return output

# END =========================================================================
