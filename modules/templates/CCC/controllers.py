# -*- coding: utf-8 -*-

import json
import uuid

from collections import OrderedDict

from gluon import *
from gluon.storage import Storage
from s3 import FS, ICON, IS_ONE_OF, IS_PHONE_NUMBER_MULTI, \
               S3AnonymizeWidget, S3CustomController, S3Method, \
               S3MultiSelectWidget, S3Profile, s3_request, S3SQLCustomForm, \
               s3_avatar_represent, s3_comments_widget, s3_fullname, \
               s3_mark_required, s3_str, s3_truncate

SEPARATORS = (",", ":")
THEME = "CCC"

ADMIN_CONSENT_OPTIONS = ("FOCV",
                         "STOREPID",
                         "EUA",
                         )
DONOR_CONSENT_OPTIONS = ("FOCD",
                         "STOREPID",
                         "EUA",
                         )
VOL_CONSENT_OPTIONS = ("18+",
                       "FOCV",
                       "STOREPID",
                       "EUA",
                       )

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        system_roles = current.auth.get_system_roles()
        ADMIN = system_roles.ADMIN in current.session.s3.roles
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"
        resource = "index"
        query = (ltable.module == module) & \
                ((ltable.resource == None) | \
                 (ltable.resource == resource)) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby = (0, 1)
                                        ).first()
        if item:
            if ADMIN:
                item = DIV(XML(item.body),
                           BR(),
                           A(current.T("Edit"),
                             _href = URL(c="cms", f="post",
                                         args = [item.id, "update"],
                                         vars = {"module": module,
                                                 "resource": resource,
                                                 },
                                         ),
                             _class = "action-btn",
                             ),
                           )
            else:
                item = DIV(XML(item.body))
        elif ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item = A(current.T("Edit"),
                     _href = URL(c="cms", f="post", args="create",
                                 vars = {"module": module,
                                         "resource": resource,
                                         },
                                 ),
                     _class = "%s cms-edit" % _class,
                     )
        else:
            item = ""
        output["item"] = item

        self._view(THEME, "index.html")
        return output

# =============================================================================
class donate(S3CustomController):
    """ Custom Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        system_roles = current.auth.get_system_roles()
        ADMIN = system_roles.ADMIN in current.session.s3.roles
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"

        resource = "Donate"
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby = (0, 1)
                                        ).first()
        if item:
            if ADMIN:
                item1 = DIV(XML(item.body),
                            BR(),
                            A(current.T("Edit"),
                              _href = URL(c="cms", f="post",
                                          args = [item.id, "update"],
                                          vars = {"module": module,
                                                  "resource": resource,
                                                  },
                                          ),
                              _class = "action-btn",
                              ),
                            )
            else:
                item1 = DIV(XML(item.body))
        elif ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item1 = A(current.T("Edit"),
                       _href = URL(c="cms", f="post", args="create",
                                  vars = {"module": module,
                                          "resource": resource,
                                          },
                                  ),
                      _class = "%s cms-edit" % _class,
                      )
        else:
            item1 = ""
        output["item"] = item1

        self._view(THEME, "donate.html")
        return output

# =============================================================================
class donate_redirect(S3CustomController):
    """ Custom Page """

    def __call__(self):
        if current.auth.s3_logged_in():
            url = URL(c="default", f="person")
        else:
            url = URL(c="default", f="index",
                      args = "register",
                      vars = {"donor": 1},
                      )
        redirect(url)

# =============================================================================
class donor(S3CustomController):
    """ Custom Page """

    def __call__(self):

        s3 = current.response.s3

        output = {}

        # Allow editing of page content from browser using CMS module
        system_roles = current.auth.get_system_roles()
        ADMIN = system_roles.ADMIN in current.session.s3.roles
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"

        resource = "Donor"
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby = (0, 1)
                                        ).first()
        if item:
            if ADMIN:
                item = DIV(XML(item.body),
                           BR(),
                           A(current.T("Edit"),
                             _href = URL(c="cms", f="post",
                                         args = [item.id, "update"],
                                         vars = {"module": module,
                                                 "resource": resource,
                                                 },
                                         ),
                             _class = "action-btn",
                             ),
                           )
            else:
                item = DIV(XML(item.body))
        elif ADMIN:
            if s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item = A(current.T("Edit"),
                     _href = URL(c="cms", f="post", args="create",
                                 vars = {"module": module,
                                         "resource": resource,
                                         },
                                 ),
                     _class = "%s cms-edit" % _class,
                     )
        else:
            item = ""
        output["item"] = item

        s3.scripts.append("https://platform.twitter.com/widgets.js")

        self._view(THEME, "donor.html")
        return output

# =============================================================================
class login_next(S3CustomController):
    """ Custom Page """

    def __call__(self):

        db = current.db
        auth = current.auth

        #user = auth.user
        #if user:
        #    utable = auth.settings.table_user
        #    account = db(utable.id == user.id).select(utable.deleted,
        #                                              limitby = (0, 1),
        #                                              ).first()
        #    if not account or account.deleted:
        #        # Logout after succesful Account Deletion
        #        redirect(URL(c="default", f="user", args=["logout"]))

        request = current.request
        settings = current.deployment_settings

        person_id = auth.s3_logged_in_person()

        # Check if there are new/modified/expired consent options
        if auth.s3_has_role("DONOR"):
            # Page to redirect to
            url = URL(c="default", f="index", args="donor")

            options = DONOR_CONSENT_OPTIONS
        else:
            # Page to redirect to
            url = URL(c="cms", f="post", args="datalist")

            if auth.s3_has_roles(("ORG_ADMIN",
                                  "GROUP_ADMIN",
                                  )):
                options = ADMIN_CONSENT_OPTIONS
            else:
                options = VOL_CONSENT_OPTIONS

        s3db = current.s3db
        ttable = s3db.auth_processing_type
        otable = s3db.auth_consent_option
        ctable = s3db.auth_consent
        query = (ttable.code.belongs(options)) & \
                (ttable.id == otable.type_id) & \
                (otable.obsolete == False) & \
                (otable.deleted == False)
        possible_options = db(query).select(otable.id,
                                            ttable.code,
                                            )
        options = {}
        for o in possible_options:
            options[o["auth_consent_option.id"]] = o["auth_processing_type.code"]
        query = (ctable.person_id == person_id) & \
                (ctable.option_id.belongs(options)) & \
                (ctable.consenting == True) & \
                ((ctable.expires_on == None) | \
                 (ctable.expires_on < request.utcnow))
        consented = db(query).select(ctable.option_id)

        if len(consented) == len(options):
            # All Consented already
            redirect(url)

        # Which are not consented?
        for c in consented:
            del options[c.option_id]

        # Show form
        T = current.T
        auth_Consent = s3db.auth_Consent
        consent = auth_Consent(processing_types = options.values())
        formfields = [Field("consent",
                            label = T("Consent"),
                            widget = consent.widget,
                            ),
                      ]
        # Generate labels (and mark required fields in the process)
        labels = s3_mark_required(formfields, mark_required=[])[0]
        form = SQLFORM.factory(#table_name = utable._tablename,
                               record = None,
                               #hidden = {"_next": request.vars._next},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = T("Accept"),
                               delete_label = auth.messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               #buttons = buttons,
                               *formfields
                               )

        if form.accepts(request.vars,
                        current.session,
                        formname = "consent",
                        ):
            auth_Consent.track(person_id, form.vars.consent)
            redirect(url)

        response = current.response
        response.view = "simple.html"
        # Anonymise button
        tablename = "pr_person"
        s3db.configure(tablename,
                       anonymize_next = URL(c = "default",
                                            f = "user",
                                            args = ["logout"],
                                            ),
                       )
        r = s3_request(prefix = "pr",
                      name = "person",
                      c = "default",
                      )
        r.id = person_id
        settings.customise_pr_person_resource(r, tablename)
        anonymise_btn = S3AnonymizeWidget.widget(r,
                                                 label = "Delete My Account",
                                                 ajaxURL = URL(c="pr", f="person",
                                                               args = [person_id, "anonymize.json"]
                                                               ),
                                                 _class = "action-btn anonymize-btn",
                                                 )
        response.s3.rfooter = DIV(P("If you do not accept the new terms, you should delete your account:"),
                                  anonymise_btn,
                                  _id = "login_next",
                                  )
        current.menu = Storage(about = current.menu.about)
        return {"item": form,
                "title": T("Consent Required"),
                }

# =============================================================================
class organisationApply(S3Method):
    """
        Apply to be affiliated with an Org
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "organisation" and \
           r.id and \
           not r.component and \
           r.representation in ("html", "aadata"):

            T = current.T
            db = current.db
            s3db = current.s3db
            auth = current.auth

            organisation_id = r.id

            # Check that this Org allows Applications
            ttable = s3db.org_organisation_tag
            query = (ttable.organisation_id == organisation_id) & \
                    (ttable.tag == "visible")
            #        (ttable.tag == "apply")
            apply = db(query).select(ttable.value,
                                     limitby = (0, 1)
                                     ).first()
            if not apply or apply.value != "1":
                current.session.error = T("Not permitted to Apply for this Organization")
                redirect(URL(args = [organisation_id]))

            requires = IS_IN_SET({"0": T("No"),
                                  "1": T("Yes"),
                                  })
            form = FORM(DIV(DIV(LABEL("Remain visible on the Reserves list as well?",
                                      SPAN(" *",
                                           _class = "req",
                                           ),
                                      _for = "org_organisation_sub_apply_value",
                                      ),
                                DIV(DIV(DIV(DIV(INPUT(requires = requires,
                                                      _type = "radio",
                                                      _name = "reserve",
                                                      _id = "reserve_0",
                                                      _value = "0",
                                                      #value = None,
                                                      ),
                                                LABEL(T("No"),
                                                      _for = "reserve_0",
                                                      ),
                                                ),
                                            ),
                                        DIV(DIV(INPUT(requires = requires,
                                                      _type = "radio",
                                                      _name = "reserve",
                                                      _id = "reserve_1",
                                                      _value = "1",
                                                      #value = None,
                                                      ),
                                                LABEL(T("Yes"),
                                                      _for = "reserve_1",
                                                      ),
                                                ),
                                            ),
                                        _class = "generic-widget web2py_radiowidget",
                                        _id = "org_organisation_sub_apply_value",
                                        ),
                                    _class = "controls",
                                    ),
                                _class = "small-12 columns",
                                ),
                            _class = "form-row row",
                            ),
                        DIV(DIV(DIV(INPUT(_class = "button primary small btn",
                                          _type = "submit",
                                          _value = "Apply",
                                          ),
                                    _class = "controls",
                                    ),
                                _class = "small-12 columns",
                                ),
                            _class = "form-row row",
                            ),
                        )

            if form.accepts(r.post_vars):
                # Lookup the Person
                ltable = s3db.pr_person_user
                ptable = s3db.pr_person
                query = (ltable.user_id == auth.user.id) & \
                        (ltable.pe_id == ptable.pe_id)
                person = db(query).select(ptable.id,
                                          ptable.first_name,
                                          ptable.middle_name,
                                          ptable.last_name,
                                          limitby = (0, 1)
                                          ).first()
                person_id = person.id

                # Store the Application
                delegation_id = s3db.hrm_delegation.insert(organisation_id = organisation_id,
                                                           person_id = person_id,
                                                           status = "APPL",
                                                           comments = form.vars.reserve,
                                                           )

                # Message OrgAdmins
                # Lookup Emails
                utable = db.auth_user
                mtable = db.auth_membership
                gtable = db.auth_group
                query = (utable.organisation_id == organisation_id) & \
                        (mtable.user_id == utable.id) & \
                        (mtable.group_id == gtable.id) & \
                        (gtable.uuid == "ORG_ADMIN")
                admins = db(query).select(utable.email,
                                          distinct = True)

                # Create Email
                settings = current.deployment_settings
                fullname = s3_fullname(person)
                system_name = settings.get_system_name_short()
                subject = "%s: New Application from %s" % \
                            (system_name,
                             fullname,
                             )
                url = "%s%s" % (settings.get_base_public_url(),
                                URL(c="org", f="organisation",
                                    args = [organisation_id, "application"],
                                    vars = {"delegation_id": delegation_id},
                                    ),
                                )
                message = "%s has applied to join your Organisation on %s. Please visit %s to respond." % \
                            (fullname,
                             system_name,
                             url,
                             )

                # Send Email to each Admin
                send_email = current.msg.send_email
                for admin in admins:
                    send_email(to = admin.email,
                               subject = subject,
                               message = message,
                               )
                # Redirect
                current.session.confirmation = T("Application has been submitted")
                redirect(URL(args = [organisation_id]))

            # Show Form
            header = DIV(P("By clicking 'yes' to 'remain visible on the reserve list' you will still be emailed opportunities to volunteer for other third party organisations, clicking 'no' disables you from this process and means, if your application is successful, you will only be affiliated to, and receive opportunities from, the organisation you apply to."),
                         P("If you have selected 'no' and later feel you would like to receive opportunities you may visit your profile and select the 'yes' on the affiliation tab at any time."),
                         P("Please note, if you have contacted the organisation (by email or phone) prior to the application process your application may be processed quicker.."),
                         )

            output = {"form": form,
                      "header": header,
                      "title": "Apply to join Organisation: %s" % r.record.name,
                      }
            current.response.title = T("Apply")
            S3CustomController._view(THEME, "apply.html")
            return output

        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class organisationApplication(S3Method):
    """
        Handle Application to be affiliated with an Org
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "organisation" and \
           r.id and \
           not r.component and \
           r.representation in ("html", "aadata"):

            organisation_id = r.id

            delegation_id = r.get_vars.get("delegation_id")
            if delegation_id is None:
                current.session.error = "Can't Approve Application if Delegation not supplied"
                redirect(URL(args = [organisation_id]))

            T = current.T
            db = current.db
            s3db = current.s3db
            auth = current.auth
            has_role = auth.s3_has_role

            # Check that this User is permitted to review Applications for this Org
            if has_role("ADMIN"):
                # OK
                pass
            elif has_role("ORG_ADMIN") and (auth.user.organisation_id == organisation_id): # @ToDo: Ideally (post-CCC) make this realm to allow OG_ADMIN role to be assigned to 1 User for multiple Orgs
                # OK
                pass
            else:
                current.session.error = "You are not permitted to Approve Applications for this Organisation"
                redirect(URL(args = [organisation_id]))

            # Read the delegation
            dtable = s3db.hrm_delegation
            delegation = db(dtable.id == delegation_id).select(dtable.id, # For update_record
                                                               dtable.organisation_id,
                                                               dtable.person_id,
                                                               dtable.status,
                                                               dtable.comments,
                                                               limitby = (0, 1)
                                                               ).first()
            if not delegation:
                current.session.error = "Application not found!"
                redirect(URL(args = [organisation_id]))

            if delegation.organisation_id != organisation_id:
                current.session.error = "Application not for this Organisation!"
                redirect(URL(args = [organisation_id]))

            if delegation.status != "APPL":
                current.session.error = "Application has incorrect status!"
                redirect(URL(args = [organisation_id]))

            # Lookup Person
            person_id = delegation.person_id
            ptable = s3db.pr_person
            person = db(ptable.id == person_id).select(ptable.first_name,
                                                       ptable.middle_name,
                                                       ptable.last_name,
                                                       ptable.pe_id,
                                                       limitby = (0, 1)
                                                       ).first()
            pe_id = person.pe_id

            # Lookup User Account
            ltable = s3db.pr_person_user
            utable = db.auth_user
            query = (ltable.pe_id == pe_id) & \
                    (ltable.user_id == utable.id)
            user = db(query).select(utable.id,
                                    utable.organisation_id,
                                    limitby = (0, 1),
                                    ).first()
            if user.organisation_id:
                current.session.error = "Volunteer has already been accepted to join an Organisation"
                redirect(URL(args = [organisation_id]))

            user_id = user.id

            record = r.record
            org_name = record.name
            realm_entity = record.pe_id

            requires = IS_IN_SET({"0": T("No"),
                                  "1": T("Yes"),
                                  })
            form = FORM(DIV(DIV(LABEL("Should this volunteer become affiliated to this Organisation?",
                                      SPAN(" *",
                                           _class = "req",
                                           ),
                                      _for = "pr_person_sub_apply_value",
                                      ),
                                DIV(DIV(DIV(DIV(INPUT(requires = requires,
                                                      _type = "radio",
                                                      _name = "approve",
                                                      _id = "approve_0",
                                                      _value = "0",
                                                      #value = None,
                                                      ),
                                                LABEL(T("No"),
                                                      _for = "approve_0",
                                                      ),
                                                ),
                                            ),
                                        DIV(DIV(INPUT(requires = requires,
                                                      _type = "radio",
                                                      _name = "approve",
                                                      _id = "approve_1",
                                                      _value = "1",
                                                      #value = None,
                                                      ),
                                                LABEL(T("Yes"),
                                                      _for = "approve_1",
                                                      ),
                                                ),
                                            ),
                                        _class = "generic-widget web2py_radiowidget",
                                        _id = "pr_person_sub_apply_value",
                                        ),
                                    _class = "controls",
                                    ),
                                _class = "small-12 columns",
                                ),
                            _class = "form-row row",
                            ),
                        DIV(DIV(DIV(INPUT(_class = "button primary small btn",
                                          _type = "submit",
                                          _value = "Save",
                                          ),
                                    _class = "controls",
                                    ),
                                _class = "small-12 columns",
                                ),
                            _class = "form-row row",
                            ),
                        )

            if form.accepts(r.post_vars):

                # Message Applicant

                # Lookup Email
                ctable = s3db.pr_contact
                query = (ctable.pe_id == pe_id) & \
                        (ctable.contact_method == "EMAIL") & \
                        (ctable.deleted == False)
                emails = db(query).select(ctable.value,
                                          distinct = True)

                # Create Email
                system_name = current.deployment_settings.get_system_name_short()
                if form.vars.approve == "0":
                    subject = "%s: Application to %s has been Rejected" % (system_name, org_name)

                    # Update Delegation
                    delegation.update_record(status = "RJCT")
                else:
                    subject = "%s: Application to %s has been Approved" % (system_name, org_name)

                    # Update Delegation
                    delegation.update_record(status = "ACPT")

                    # Update User Account
                    user.update_record(organisation_id = organisation_id)

                    # Add Human Resource Record
                    htable = s3db.hrm_human_resource
                    hr = {"organisation_id": organisation_id,
                          "person_id": person_id,
                          "realm_entity": realm_entity,
                          }
                    human_resource_id = htable.insert(**hr)
                    hr["id"] = human_resource_id
                    s3db.update_super(htable, hr)
                    onaccept = s3db.get_config("hrm_human_resource", "create_onaccept") or \
                               s3db.get_config("hrm_human_resource", "onaccept")
                    if callable(onaccept):
                        hform = Storage(vars = hr)
                        onaccept(hform)

                    # Add VOLUNTEER role
                    auth.s3_assign_role(user_id, "VOLUNTEER", for_pe=realm_entity)

                    # Remove RESERVE role
                    auth.s3_withdraw_role(user_id, "RESERVE", for_pe=[])

                    # Set Realm Entity
                    ttable = s3db.hrm_human_resource_tag
                    reserve = delegation.comments
                    if reserve == "1":
                        ftable = s3db.pr_forum
                        forum = db(ftable.organisation_id == organisation_id).select(ftable.pe_id,
                                                                                     limitby = (0, 1)
                                                                                     ).first()

                        auth.set_realm_entity("pr_person", person_id, entity=forum.pe_id, force_update=True)
                    else:
                        auth.set_realm_entity("pr_person", person_id, entity=realm_entity, force_update=True)

                    # Set Reserves Tag
                    ttable = s3db.hrm_human_resource_tag
                    ttable.insert(human_resource_id = human_resource_id,
                                  tag = "reserve",
                                  value = reserve,
                                  )

                message = subject

                # Send Email to each of the Person's emails
                send_email = current.msg.send_email
                for email in emails:
                    send_email(to = email.value,
                               subject = subject,
                               message = message,
                               )
                # Redirect
                current.session.confirmation = T("Application has been processed")
                redirect(URL(args = [organisation_id]))

            # Show Form
            ctable = s3db.hrm_competency
            stable = s3db.hrm_skill
            query = (ctable.person_id == person_id) & \
                    (ctable.deleted == False) & \
                    (ctable.skill_id == stable.id)
            offers = db(query).select(stable.name)
            offers = ", ".join([o.name for o in offers])

            ttable = s3db.pr_person_tag
            query = (ttable.person_id == person_id) & \
                    (ttable.tag == "skill_details")
            tag = db(query).select(ttable.id,
                                   ttable.value,
                                   limitby = (0, 1)
                                   ).first()
            if tag and tag.value is not None:
                offer_details = TR(TD("Offer Details:"),
                                   TD(tag.value),
                                   )
            else:
                offer_details = TR(TD(_colspan = 2))

            ctable = s3db.pr_contact
            query = (ctable.pe_id == pe_id) & \
                    (ctable.contact_method == "EMAIL") & \
                    (ctable.deleted == False)
            emails = db(query).select(ctable.value)
            email = ", ".join([e.value for e in emails])

            query = (ctable.pe_id == pe_id) & \
                    (ctable.contact_method.belongs(("SMS", "HOME_PHONE"))) & \
                    (ctable.deleted == False)
            phones = db(query).select(ctable.value)
            phone = ", ".join([p.value for p in phones])

            atable = s3db.pr_address
            gtable = s3db.gis_location
            query = (atable.pe_id == pe_id) & \
                    (atable.deleted == False) & \
                    (atable.location_id == gtable.id)
            location = db(query).select(gtable.L3,
                                        gtable.L4,
                                        gtable.addr_street,
                                        limitby = (0, 1)
                                        ).first()
            if location:
                address = location.addr_street or ""
                if location.L4:
                    if address:
                        address = "%s, %s" % (address, location.L4)
                    else:
                        address = location.L4
                if location.L3:
                    if address:
                        address = "%s, %s" % (address, location.L3)
                    else:
                        address = location.L3
                address = TR(TD("Address:"),
                             TD(address)
                             )
            else:
                address = TR(TD(_colspan = 2))

            header = DIV(P("This volunteer has applied to join this Organisation:"),
                         TABLE(TR(TD("Name:"),
                                  TD(s3_fullname(person))
                                  ),
                               TR(TD("Volunteer Offer:"),
                                  TD(offers),
                                  ),
                               offer_details,
                               TR(TD("Telephone:"),
                                  TD(phone),
                                  ),
                               TR(TD("Email:"),
                                  TD(email),
                                  ),
                               address,
                               ),
                         )

            output = {"form": form,
                      "header": header,
                      "title": "Application to join Organisation: %s" % org_name,
                      }
            current.response.title = T("Application")
            S3CustomController._view(THEME, "apply.html")
            return output

        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class personAdditional(S3Method):
    """
        Additional Information Tab
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "person" and \
           r.id and \
           not r.component and \
           r.representation in ("html", "aadata"):

            T = current.T
            auth = current.auth
            s3db = current.s3db

            # Check if this User is allowed access to this data for this Person
            if r.controller == "default":
                # Personal profile: OK
                pass
            elif auth.s3_has_role("RESERVE_ADMIN"):
                # OK
                pass
            else:
                htable = s3db.hrm_human_resource
                query = (htable.person_id == r.record.id) & \
                        (htable.deleted == False)
                hr = current.db(query).select(htable.organisation_id,
                                              limitby = (0, 1)
                                              ).first()
                if hr and hr.organisation_id == auth.user.organisation_id:
                    # OK
                    pass
                else:
                    # Not OK
                    current.session.error = T("Not permitted to access Additional Information for this Volunteer")
                    redirect(URL(c=r.controller, f="person", args=[r.id]))

            tablename = "pr_person"

            # Filtered components
            s3db.add_components(tablename,
                                pr_person_tag = (#{"name": "convictions",
                                                 # "joinby": "person_id",
                                                 # "filterby": {"tag": "convictions"},
                                                 # "multiple": False,
                                                 # },
                                                 {"name": "dbs",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "dbs"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "significant_physical",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "significant_physical"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "some_physical",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "some_physical"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "little_physical",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "little_physical"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "health_details",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "health_details"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "faith_support",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "faith_support"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "faith_support_other",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "faith_support_other"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "faith_requirements",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "faith_requirements"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "faith_requirements_details",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "faith_requirements_details"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "workplace",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "workplace"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "workplace_details",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "workplace_details"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "other_vol",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "other_vol"},
                                                  "multiple": False,
                                                  },
                                                 {"name": "other_vol_details",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "other_vol_details"},
                                                  "multiple": False,
                                                  },
                                                 ),
                                )

            # Individual settings for specific tag components
            components_get = s3db.resource(tablename).components.get

            #convictions = components_get("convictions")
            #f = convictions.table.value
            #f.requires = IS_IN_SET({"0": T("No"),
            #                        "1": T("Yes"),
            #                        })
            #f.widget = lambda f, v: \
            #                SQLFORM.widgets.radio.widget(f, v,
            #                                             style="divs")

            dbs = components_get("dbs")
            f = dbs.table.value
            f.requires = IS_IN_SET({"0": T("No"),
                                    "1": T("Yes"),
                                    })
            f.widget = lambda f, v: \
                            SQLFORM.widgets.radio.widget(f, v,
                                                         style="divs")

            significant_physical = components_get("significant_physical")
            f = significant_physical.table.value
            f.requires = IS_IN_SET({"0": T("No"),
                                    "1": T("Yes"),
                                    })
            f.widget = lambda f, v: \
                            SQLFORM.widgets.radio.widget(f, v,
                                                         style="divs")

            some_physical = components_get("some_physical")
            f = some_physical.table.value
            f.requires = IS_IN_SET({"0": T("No"),
                                    "1": T("Yes"),
                                    })
            f.widget = lambda f, v: \
                            SQLFORM.widgets.radio.widget(f, v,
                                                         style="divs")

            little_physical = components_get("little_physical")
            f = little_physical.table.value
            f.requires = IS_IN_SET({"0": T("No"),
                                    "1": T("Yes"),
                                    })
            f.widget = lambda f, v: \
                            SQLFORM.widgets.radio.widget(f, v,
                                                         style="divs")

            faith_requirements = components_get("faith_requirements")
            f = faith_requirements.table.value
            f.requires = IS_IN_SET({"0": T("No"),
                                    "1": T("Yes"),
                                    })
            f.widget = lambda f, v: \
                            SQLFORM.widgets.radio.widget(f, v,
                                                         style="divs")

            workplace = components_get("workplace")
            f = workplace.table.value
            f.requires = IS_IN_SET({"0": T("No"),
                                    "1": T("Yes"),
                                    })
            f.widget = lambda f, v: \
                            SQLFORM.widgets.radio.widget(f, v,
                                                         style="divs")

            other_vol = components_get("other_vol")
            f = other_vol.table.value
            f.requires = IS_IN_SET({"0": T("No"),
                                    "1": T("Yes"),
                                    })
            f.widget = lambda f, v: \
                            SQLFORM.widgets.radio.widget(f, v,
                                                         style="divs")

            form = S3SQLCustomForm((T("That require significant physical activity (including lifting and carrying) and may involve being outdoors (e.g. clean up of affected properties)"), "significant_physical.value"),
                                   (T("That require some physical activity and may involve being outdoors (e.g. door knocking)"), "some_physical.value"),
                                   (T("That require little physical activity and are based indoors (e.g. preparing refreshments)"), "little_physical.value"),
                                   (T("If you wish, you can give us some further information on any fitness, medical or mobility issues that might limit the kind of activities you are able to volunteer for; this will help us to suggest suitable opportunities for you"), "health_details.value"),
                                   (T("Are you volunteering under your workplace volunteering scheme?"), "workplace.value"),
                                   (T("If yes please name your employer"), "workplace_details.value"),
                                   (T("Are you volunteering for any organisation not registered with Support Cumbria?"), "other_vol.value"),
                                   (T("If Yes please name organisation and outline details"), "other_vol_details.value"),
                                   (T("Are you DBS checked?"), "dbs.value"),
                                   #(T("Do you have any unspent convictions?"), "convictions.value"),
                                   (T("Please indicate Faith support you can offer"), "faith_support.value"),
                                   (T("What help and support can you give those from other Faiths?"), "faith_support_other.value"),
                                   (T("Do you have any faith requirements that you would like help with if you are coming to Support Cumbria?"), "faith_requirements.value"),
                                   (T("If Yes please outline"), "faith_requirements_details.value"),
                                   )

            form = {"type": "form",
                    #"label": ,
                    #"icon": ,
                    "tablename": tablename,
                    "sqlform": form,
                    "filter": FS("id") == r.id,
                    }

            profile_widgets= [form,
                              ]

            if r.representation == "html":
                response = current.response
                # Maintain normal rheader for consistency
                rheader = attr["rheader"]
                profile_header = TAG[""](H2(response.s3.crud_strings["pr_person"].title_display),
                                         DIV(rheader(r),
                                             _id = "rheader",
                                             ),
                                         )
            else:
                profile_header = None

            s3db.configure(tablename,
                           profile_cols = 1,
                           profile_header = profile_header,
                           profile_widgets = profile_widgets,
                           )

            profile = S3Profile()
            profile.tablename = tablename
            profile.request = r
            output = profile.profile(r, **attr)
            if r.representation == "html":
                output["title"] = response.title = T("Additional Information")
            return output

        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class personAffiliation(S3Method):
    """
        Affiliation Tab for unaffiliated Volunteers
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "person" and \
           r.id and \
           not r.component and \
           r.representation in ("html", "aadata"):

            T = current.T
            auth = current.auth
            s3db = current.s3db

            # Check if this User is allowed access to this data for this Person
            if r.controller == "default":
                # Personal profile: OK
                pass
            elif auth.s3_has_role("RESERVE_ADMIN"):
                # OK
                pass
            else:
                htable = s3db.hrm_human_resource
                query = (htable.person_id == r.record.id) & \
                        (htable.deleted == False)
                hr = current.db(query).select(htable.organisation_id,
                                              limitby = (0, 1)
                                              ).first()
                if hr and hr.organisation_id == auth.user.organisation_id:
                    # OK
                    pass
                else:
                    # Not OK
                    current.session.error = T("Not permitted to access Additional Information for this Volunteer")
                    redirect(URL(c=r.controller, f="person", args=[r.id]))

            tablename = "pr_person"

            # Filtered components
            s3db.add_components(tablename,
                                pr_person_tag = ({"name": "reserve",
                                                  "joinby": "person_id",
                                                  "filterby": {"tag": "reserve"},
                                                  "multiple": False,
                                                  },
                                                 ),
                                )

            # Individual settings for specific tag components
            components_get = s3db.resource(tablename).components.get

            reserve = components_get("reserve")
            f = reserve.table.value
            # Has no effect:
            #f.default = "1"
            f.requires = IS_IN_SET({"0": T("No"),
                                    "1": T("Yes"),
                                    })
            f.widget = lambda f, v: \
                            SQLFORM.widgets.radio.widget(f, v,
                                                         style="divs")

            form = S3SQLCustomForm((T("Visible on the Reserves list?"), "reserve.value"),
                                   postprocess = self.affiliation_postprocess,
                                   )

            form = {"type": "form",
                    #"label": ,
                    #"icon": ,
                    "tablename": tablename,
                    "sqlform": form,
                    "filter": FS("id") == r.id,
                    }

            profile_widgets= [form,
                              ]

            if r.representation == "html":
                response = current.response
                # Maintain normal rheader for consistency
                rheader = attr["rheader"]
                profile_header = TAG[""](H2(response.s3.crud_strings["pr_person"].title_display),
                                         DIV(rheader(r), _id="rheader"),
                                         )
            else:
                profile_header = None

            s3db.configure(tablename,
                           profile_cols = 1,
                           profile_header = profile_header,
                           profile_widgets = profile_widgets,
                           )

            profile = S3Profile()
            profile.tablename = tablename
            profile.request = r
            output = profile.profile(r, **attr)
            if r.representation == "html":
                output["title"] = response.title = T("Affiliation")
            return output

        else:
            r.error(405, current.ERROR.BAD_METHOD)

    # -----------------------------------------------------------------------------
    @staticmethod
    def affiliation_postprocess(form):
        """
            Set Realm to either Reserves Forum or Inactives Forum
        """

        db = current.db
        s3db = current.s3db
        auth = current.auth
        record = form.record
        person_id = form.vars.get("id")

        # Find Tag
        ttable = s3db.pr_person_tag
        query = (ttable.person_id == person_id) & \
                (ttable.tag == "reserve")
        reserve = db(query).select(ttable.value,
                                   limitby = (0, 1)
                                   ).first()
        reserve = reserve.value

        if record is None or \
           reserve != record.sub_reserve_value:

            # Find User Account
            #ptable = s3db.pr_person
            #putable = s3db.pr_person_user
            #query = (ptable.id == person_id) & \
            #        (ptable.pe_id == putable.pe_id)
            #link = db(query).select(putable.user_id,
            #                        limitby = (0, 1)
            #                        ).first()
            #user_id = link.user_id

            # Update Realm Entity
            ftable = s3db.pr_forum
            if reserve == "0":
                FORUM = "Inactives"
                # Withdraw Old Role
                #auth.s3_withdraw_role(user_id, "RESERVE", for_pe=[])
            elif reserve == "1":
                FORUM = "Reserves"
            forum = db(ftable.name == FORUM).select(ftable.pe_id,
                                                    limitby = (0, 1)
                                                    ).first()
            realm_entity = forum.pe_id
            auth.set_realm_entity("pr_person", person_id, entity=realm_entity, force_update=True)

            #if reserve == "1":
            #    # Add New Role
            #    auth.s3_assign_role(user_id, "RESERVE", for_pe=realm_entity)

# =============================================================================
class register(S3CustomController):
    """ Custom Registration Page """

    def __call__(self):

        auth = current.auth
        auth_settings = auth.settings

        # Redirect if already logged-in
        if auth.is_logged_in():
            redirect(auth_settings.logged_url)

        T = current.T
        db = current.db
        s3db = current.s3db

        request = current.request
        response = current.response
        session = current.session
        settings = current.deployment_settings

        auth_messages = auth.messages

        utable = auth_settings.table_user
        passfield = auth_settings.password_field

        # Lookup Districts + UK
        gtable = s3db.gis_location
        districts = db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                 gtable.name)
        districts = {d.id:d.name for d in districts}
        districts = OrderedDict(sorted(districts.items(), key=lambda t: t[1]))

        uk = db((gtable.level == "L0") & (gtable.name == "United Kingdom")).select(gtable.id,
                                                                                   limitby = (0, 1)
                                                                                   ).first()

        districts_and_uk = OrderedDict([(uk.id, "Outside Cumbria")])
        for key in districts:
            districts_and_uk[key] = districts[key]

        # Lookup Slots
        stable = s3db.pr_slot
        slots = db(stable.deleted == False).select(stable.id,
                                                   stable.name)
        slots = {s.id:s.name for s in slots}

        # Lookup Certificates
        ctable = s3db.hrm_certificate
        certificates = db(ctable.deleted == False).select(ctable.id,
                                                          ctable.name,
                                                          )
        certificates = {c.id:c.name for c in certificates}

        # Check Type of Registration
        agency = donor = existing = group = False

        def individual_formfields():
            """
                DRY Helper for individuals (whether with existing agency or not)
            """
            # Instantiate Consent Tracker
            consent = s3db.auth_Consent(processing_types = VOL_CONSENT_OPTIONS)

            formfields = [utable.first_name,
                          utable.last_name,
                          Field("addr_L3",
                                label = T("Location"),
                                requires = IS_IN_SET(districts_and_uk),
                                ),
                          Field("addr_street",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode",
                                label = T("Postcode"),
                                ),
                          Field("mobile",
                                label = T("Contact Number (Preferred)"),
                                requires = IS_PHONE_NUMBER_MULTI(),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                                  T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                              ),
                                ),
                          Field("home",
                                label = T("Contact Number (Secondary)"),
                                requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                                ),
                          utable.email,
                          utable[passfield],
                          # Password Verification Field
                          Field("password_two", "password",
                                label = auth_messages.verify_password,
                                requires = IS_EXPR("value==%s" % \
                                                   repr(request.vars.get(passfield)),
                                                   error_message = auth_messages.mismatched_password,
                                                   ),
                                ),

                          # Skills
                          s3db.hrm_multi_skill_id(empty = False,
                                                  label = T("Volunteer Offer"),
                                                  ),
                          Field("skills_details",
                                label = T("Please specify details"),
                                ),
                          Field("certificates", "list:string",
                                label = T("Qualifications"),
                                requires = IS_IN_SET(certificates, multiple=True),
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("experience",
                                label = T("Skills and Experience"),
                                widget = lambda f, v: \
                                    s3_comments_widget(f, v, _placeholder = "e.g. Co-ordination, Event Management, PCV qualified.")
                                ),
                          Field("resources",
                                label = T("Offers of Resources"),
                                widget = lambda f, v: \
                                    s3_comments_widget(f, v, _placeholder = "e.g. Minibus.")
                                ),
                          Field("where_operate", "list:string",
                                label = T("Where would you be willing to volunteer?"),
                                requires = IS_IN_SET(districts, multiple=True),
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("travel", "integer",
                                label = T("Willing to Travel?"),
                                requires = IS_IN_SET({0: T("No"),
                                                      1: T("Yes"),
                                                      }),
                                widget = lambda f, v: \
                                    SQLFORM.widgets.radio.widget(f, v,
                                                                 style="divs"),
                                ),
                          Field("slots", "list:string",
                                label = T("Times"),
                                requires = IS_IN_SET(slots, multiple=True),
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("significant_physical", "integer",
                                label = T("That require significant physical activity (including lifting and carrying) and may involve being outdoors (e.g. clean up of affected properties)"),
                                requires = IS_IN_SET({0: T("No"),
                                                      1: T("Yes"),
                                                      }),
                                widget = lambda f, v: \
                                    SQLFORM.widgets.radio.widget(f, v,
                                                                 style="divs"),
                                ),
                          Field("some_physical", "integer",
                                label = T("That require some physical activity and may involve being outdoors (e.g. door knocking)"),
                                requires = IS_IN_SET({0: T("No"),
                                                      1: T("Yes"),
                                                      }),
                                widget = lambda f, v: \
                                    SQLFORM.widgets.radio.widget(f, v,
                                                                 style="divs"),
                                ),
                          Field("little_physical", "integer",
                                label = T("That require little physical activity and are based indoors (e.g. preparing refreshments)"),
                                requires = IS_IN_SET({0: T("No"),
                                                      1: T("Yes"),
                                                      }),
                                widget = lambda f, v: \
                                    SQLFORM.widgets.radio.widget(f, v,
                                                                 style="divs"),
                                ),
                          Field("health_details",
                                label = T("If you wish, you can give us some further information on any fitness, medical or mobility issues that might limit the kind of activities you are able to volunteer for; this will help us to suggest suitable opportunities for you"),
                                ),
                          Field("faith_requirements", "integer",
                                label = T("Do you have any faith requirements that you would like help with if you are coming to Support Cumbria?"),
                                requires = IS_IN_SET({0: T("No"),
                                                      1: T("Yes"),
                                                      }),
                                widget = lambda f, v: \
                                    SQLFORM.widgets.radio.widget(f, v,
                                                                 style="divs"),
                                ),
                          Field("faith_requirements_details",
                                label = T("If Yes please outline"),
                                ),
                          Field("emergency_contact_name",
                                label = T("Contact Name"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("emergency_contact_number",
                                label = T("Contact Number"),
                                requires = IS_PHONE_NUMBER_MULTI(),
                                ),
                          Field("emergency_contact_relationship",
                                label = T("Relationship"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("workplace", "integer",
                                label = T("Are you volunteering under your workplace volunteering scheme?"),
                                requires = IS_IN_SET({0: T("No"),
                                                      1: T("Yes"),
                                                      }),
                                widget = lambda f, v: \
                                    SQLFORM.widgets.radio.widget(f, v,
                                                                 style="divs"),
                                ),
                          Field("workplace_details",
                                label = T("If yes please name your employer"),
                                ),
                          Field("dbs", "integer",
                                label = T("Are you DBS checked?"),
                                requires = IS_IN_SET({0: T("No"),
                                                      1: T("Yes"),
                                                      }),
                                widget = lambda f, v: \
                                    SQLFORM.widgets.radio.widget(f, v,
                                                                 style="divs"),
                                ),
                          #Field("convictions", "integer",
                          #      label = T("Do you have any unspent convictions?"),
                          #      comment = T("Please tick 'Yes' if you have any convictions that are not yet spent under the Rehabilitation of Offenders Act 1974. The term 'convictions' is used to refer to any sentence or disposal issued by a court. If all your convictions are spent, you can tick 'No'. If you're not sure if your convictions are unspent or spent, you can use a tool available at www.disclosurecalculator.org.uk and read guidance at hub.unlock.org.uk/roa"),
                          #      requires = IS_IN_SET({0: T("No"),
                          #                            1: T("Yes"),
                          #                            }),
                          #      widget = lambda f, v: \
                          #          SQLFORM.widgets.radio.widget(f, v,
                          #                                       style="divs"),
                          #      ),
                          # Consent (GDPR + FOC)
                          Field("consent",
                                label = T("Consent"),
                                widget = consent.widget,
                                ),
                          ]

            required_fields = ["first_name",
                               "last_name",
                               "addr_L3",
                               "addr_street",
                               "addr_postcode",
                               "mobile",
                               "emergency_contact",
                               "where_operate",
                               ]

            return formfields, required_fields

        get_vars_get = request.get_vars.get
        org = get_vars_get("org")
        if org:
            # Volunteer for Existing Organisation
            existing = True
            otable = s3db.org_organisation
            row = db(otable.id == org).select(otable.name,
                                              limitby = (0, 1)
                                              ).first()
            if not row:
                session.error = T("Organization not found")
                redirect(URL(vars={}))
            title = T("Register as a Volunteer for %(org)s") % {"org": row.name}
            header = ""
            utable.organisation_id.default = org

            # Form Fields
            formfields, required_fields = individual_formfields()

        elif get_vars_get("agency"):
            # Organisation
            agency = True
            title = T("Register as an Organization or Agency")
            header = P()
            #header = P("This is for known CEP/Flood Action Group etc based within Cumbria. Please use ",
            #           A("Volunteer Group", _href=URL(args="register", vars={"vol_group": 1})),
            #           " if you do not fall into these",
            #           )

            # Instantiate Consent Tracker
            consent = s3db.auth_Consent(processing_types = ADMIN_CONSENT_OPTIONS)

            # Form Fields
            formfields = [Field("organisation",
                                label = T("Organization Name"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          s3db.org_organisation_type_id(),
                          #Field("addr_L3", "reference gis_location",
                          #      label = T("Where Based"),
                          #      requires = IS_IN_SET(districts_and_uk),
                          #      ),
                          #Field("addr_street",
                          #      label = T("Street Address"),
                          #      ),
                          #Field("addr_postcode",
                          #      label = T("Postcode"),
                          #      ),
                          #Field("where_operate", "list:reference gis_location",
                          #      label = T("Where would you be willing to operate?"),
                          #      requires = IS_IN_SET(districts, multiple=True),
                          #      widget = S3MultiSelectWidget(header="",
                          #                                   selectedList=3),
                          #      ),
                          # Group Leader 1
                          utable.first_name,
                          utable.last_name,
                          Field("addr_street1",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode1",
                                label = T("Postcode"),
                                ),
                          Field("mobile",
                                label = T("Contact Number (Preferred)"),
                                requires = IS_PHONE_NUMBER_MULTI(),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                                  T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                              ),
                                ),
                          Field("home",
                                label = T("Contact Number (Secondary)"),
                                requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                                ),
                          utable.email,
                          utable[passfield],
                          # Password Verification Field
                          Field("password_two", "password",
                                label = auth_messages.verify_password,
                                requires = IS_EXPR("value==%s" % \
                                                   repr(request.vars.get(passfield)),
                                                   error_message = auth_messages.mismatched_password,
                                                   ),
                                ),
                          # Org Admin 2
                          #Field("first_name2",
                          #      label = T("First Name"),
                          #      ),
                          #Field("last_name2",
                          #      label = T("Last Name"),
                          #      ),
                          #Field("addr_street2",
                          #      label = T("Street Address"),
                          #      ),
                          #Field("addr_postcode2",
                          #      label = T("Postcode"),
                          #      ),
                          #Field("email2",
                          #      label = T("Email"),
                          #      requires = IS_EMPTY_OR(IS_EMAIL()),
                          #      ),
                          #Field("mobile2",
                          #      label = T("Contact Number (Preferred)"),
                          #      requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                          #      comment = DIV(_class = "tooltip",
                          #                    _title = "%s|%s" % (T("Contact Number (Preferred)"),
                          #                                        T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                          #                    ),
                          #      ),
                          #Field("home2",
                          #      label = T("Contact Number (Secondary)"),
                          #      requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                          #      ),
                          # Consent (GDPR + FOC)
                          Field("consent",
                                label = T("Consent"),
                                widget = consent.widget,
                                ),
                          ]

            # Generate labels (and mark required fields in the process)
            required_fields = ["first_name",
                               "last_name",
                               #"addr_L3",
                               #"addr_street",
                               #"addr_postcode",
                               "mobile",
                               #"first_name2",
                               #"last_name2",
                               ]

        elif get_vars_get("donor"):
            # Donor
            donor = True
            title = T("Register as a Donor")
            header = DIV(P("Please use this page to register your offer to Donate Goods or Professional Services."),
                         P("If instead you wish to Volunteer your time, please ",
                           A("Register as a Volunteer", _href=URL(args="register", vars={})),
                           #" or ",
                           #A("Volunteer Group", _href=URL(args="register", vars={"vol_group": 1})),
                           ),
                         )

            # Instantiate Consent Tracker
            consent = s3db.auth_Consent(processing_types = DONOR_CONSENT_OPTIONS)

            # Form Fields
            formfields = [utable.first_name,
                          utable.last_name,
                          Field("organisation",
                                label = T("Name of Organization"),
                                ),
                          #Field("organisation_type",
                          #      label = T("Type of Organization"),
                          #      requires = IS_EMPTY_OR(
                          #                  IS_IN_SET([T("Business Donor"),
                          #                             T("Individual Donor"),
                          #                             T("Public Sector Organization"),
                          #                             T("Voluntary Sector Organization"),
                          #                             ])),
                          #      ),
                          Field("addr_L3", "reference gis_location",
                                label = T("Location"),
                                requires = IS_IN_SET(districts_and_uk),
                                ),
                          Field("addr_street",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode",
                                label = T("Postcode"),
                                ),
                          Field("mobile",
                                label = T("Contact Number (Preferred)"),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                                  T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                              ),
                                ),
                          Field("home",
                                label = T("Contact Number (Secondary)"),
                                ),
                          utable.email,
                          utable[passfield],
                          # Password Verification Field
                          Field("password_two", "password",
                                label = auth_messages.verify_password,
                                requires = IS_EXPR("value==%s" % \
                                                   repr(request.vars.get(passfield)),
                                                   error_message = auth_messages.mismatched_password,
                                                   ),
                                ),

                          # Goods / Services
                          Field("item_id", "list:reference supply_item",
                                label = T("Goods / Services"),
                                ondelete = "SET NULL",
                                represent = s3db.supply_ItemRepresent(multiple=True),
                                requires = IS_ONE_OF(db, "supply_item.id",
                                                     s3db.supply_item_represent,
                                                     sort=True,
                                                     multiple=True
                                                     ),
                                sortby = "name",
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("items_details",
                                label = T("Please specify details"),
                                ),
                          Field("delivery", "integer",
                                comment = T("Please indicate if you can deliver the item/s at no cost?"),
                                label = T("Are you able to Deliver?"),
                                requires = IS_IN_SET({0: T("No"),
                                                      1: T("Yes"),
                                                      }),
                                widget = lambda f, v: \
                                    SQLFORM.widgets.radio.widget(f, v,
                                                                 style="divs"),
                                ),
                          Field("where_deliver", "list:reference gis_location",
                                label = T("Where would you be willing to deliver?"),
                                requires = IS_IN_SET(districts, multiple=True),
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("availability",
                                label = T("Please indicate if the offer is only available for a period of time (please state) or it is an open ended offer. Household items, such as furniture, are normally not required for some months but very gratefully received at the right time"),
                                ),
                          # Consent (GDPR + FOC)
                          Field("consent",
                                label = T("Consent"),
                                widget = consent.widget,
                                ),
                          ]

            # Generate labels (and mark required fields in the process)
            required_fields = ["first_name",
                               "last_name",
                               "addr_L3",
                               "addr_street",
                               "addr_postcode",
                               "mobile",
                               "delivery",
                               "availability",
                               ]

        elif get_vars_get("vol_group"): # Can't be just 'group' without causing issues in HRM
            # Volunteer Group
            group = True
            title = T("Register as a Volunteer Group")
            header = DIV(P("Please use this page if you wish to register a group of volunteers."),
                         P("If you are registering as an individual volunteer please use ",
                           A("Register as a Volunteer", _href=URL(args="register", vars={})),
                           ),
                         #P("Families with children under 18 should register here to ensure you are tasked together."),
                         )

            # Instantiate Consent Tracker
            consent = s3db.auth_Consent(processing_types = ADMIN_CONSENT_OPTIONS)

            # Form Fields
            formfields = [Field("group",
                                label = T("Group Name"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          # Group Leader 1
                          utable.first_name,
                          utable.last_name,
                          Field("addr_street",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode",
                                label = T("Postcode"),
                                ),
                          Field("mobile",
                                label = T("Contact Number (Preferred)"),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                                  T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                              ),
                                ),
                          Field("home",
                                label = T("Contact Number (Secondary)"),
                                ),
                          utable.email,
                          utable[passfield],
                          # Password Verification Field
                          Field("password_two", "password",
                                label = auth_messages.verify_password,
                                requires = IS_EXPR("value==%s" % \
                                                   repr(request.vars.get(passfield)),
                                                   error_message = auth_messages.mismatched_password,
                                                   ),
                                ),
                          # Group Leader 2
                          Field("first_name2",
                                label = T("First Name"),
                                comment = T("Having two different contacts helps us make contact more easily, however if you only have one group leader please re-enter the details of Group Leader 1 again."),
                                ),
                          Field("last_name2",
                                label = T("Last Name"),
                                ),
                          Field("addr_street2",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode2",
                                label = T("Postcode"),
                                ),
                          Field("email2",
                                label = T("Email"),
                                requires = IS_EMAIL(),
                                ),
                          Field("mobile2",
                                label = T("Contact Number (Preferred)"),
                                requires = IS_PHONE_NUMBER_MULTI(),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                                  T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                              ),
                                ),
                          Field("home2",
                                label = T("Contact Number (Secondary)"),
                                requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                                ),
                          Field("password2", "password", length=512,
                                label = T("Password"),
                                requires = CRYPT(key=auth.settings.hmac_key,
                                                 min_length=settings.get_auth_password_min_length(),
                                                 digest_alg="sha512"),
                                ),
                          Field("password2_two", "password",
                                label = auth_messages.verify_password,
                                requires = IS_EXPR("value==%s" % \
                                                   repr(request.vars.get("password2")),
                                                   error_message = auth_messages.mismatched_password,
                                                   ),
                                ),
                          Field("vols", "integer",
                                label = T("Approximate Number of Volunteers"),
                                requires = IS_INT_IN_RANGE(1, 999),
                                ),
                          Field("transport",
                                label = T("Mode of Transport"),
                                comment = T("This will help organisations find your group appropriate volunteering opportunities. Cumbria is a rural county with many hard to access communities where a coach would be unable to access. Please be aware public transport is limited and can be impacted by incidents."),
                                requires = IS_NOT_EMPTY(),
                                ),
                          # Skills
                          s3db.hrm_multi_skill_id(empty = False,
                                                  label = T("Volunteer Offer"),
                                                  ),
                          Field("skills_details",
                                label = T("Please specify details"),
                                ),
                          Field("where_operate", "list:reference gis_location",
                                label = T("Where would you be willing to volunteer?"),
                                requires = IS_IN_SET(districts, multiple=True),
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("parish",
                                label = T("Parish(es)"),
                                comment = T("Put specific parish)es) here if you want to limit your availability."),
                                ),
                          Field("faith_requirements", "integer",
                                label = T("Do you have any faith requirements that you would like help with if you are coming to Support Cumbria?"),
                                requires = IS_IN_SET({0: T("No"),
                                                      1: T("Yes"),
                                                      }),
                                widget = lambda f, v: \
                                    SQLFORM.widgets.radio.widget(f, v,
                                                                 style="divs"),
                                ),
                          Field("faith_requirements_details",
                                label = T("If Yes please outline"),
                                ),
                          Field("emergency_contact_name",
                                label = T("Contact Name"),
                                comment = T("Contact must not be listed as a leader above"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("emergency_contact_number",
                                label = T("Contact Number"),
                                requires = IS_PHONE_NUMBER_MULTI(),
                                ),
                          # Consent (GDPR + FOC)
                          Field("consent",
                                label = T("Consent"),
                                widget = consent.widget,
                                ),
                          ]

            # Generate labels (and mark required fields in the process)
            required_fields = ["first_name",
                               "last_name",
                               "addr_street",
                               "addr_postcode",
                               "mobile",
                               "first_name2",
                               "last_name2",
                               "skill_id",
                               "where_operate",
                               ]

        else:
            # Individual Volunteer
            title = T("Register as a Volunteer")
            header = DIV(P("Please use this page if you wish to volunteer as an individual."),
                         P(#"If you are registering on behalf of a group please use ",
                           #A("Volunteer Group", _href=URL(args="register", vars={"vol_group": 1})),
                           "If you are registering on behalf of a group please ",
                           A("Register as Organisation", _href=URL(args="register", vars={"agency": 1})),
                           ".",
                           ),
                         #P("Families with children under 18 should register as a ",
                         #  A("Volunteer Group", _href=URL(args="register", vars={"vol_group": 1})),
                         #  " to ensure you are tasked together.",
                         #  ),
                         )

            # Form Fields
            formfields, required_fields = individual_formfields()

        # Generate labels (and mark required fields in the process)
        labels = s3_mark_required(formfields, mark_required=required_fields)[0]

        # Form buttons
        REGISTER = T("Register")
        buttons = [INPUT(_type = "submit",
                         _value = REGISTER,
                         ),
                   A(T("Login"),
                     _href = URL(f="user",
                                 args = "login"),
                     _id = "login-btn",
                     _class = "action-lnk",
                     ),
                   ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = utable._tablename,
                               record = None,
                               hidden = {"_next": request.vars._next},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = REGISTER,
                               delete_label = auth_messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Captcha, if configured
        #if auth_settings.captcha != None:
        #    form[0].insert(-1, DIV("", auth_settings.captcha, ""))

        # Identify form for CSS & JS Validation
        form.add_class("auth_register")

        # Add Subheadings
        if agency:
            form[0].insert(2, DIV(_class = "subheading",
                                  ))
            #form[0].insert(6, DIV("Group Leader 1",
            #                     _class = "subheading",
            #                      ))
            #form[0].insert(16, DIV("Group Leader 2",
            #                       _class = "subheading",
            #                       ))
            form[0].insert(12, DIV(_class = "subheading",
                                   ))

        elif donor:
            pass
        elif group:
            form[0].insert(1, DIV("Group Leader 1",
                                  _class = "subheading",
                                  ))
            form[0].insert(11, DIV("Group Leader 2",
                                   _class = "subheading",
                                   ))
            form[0].insert(21, DIV(_class = "subheading",
                                   ))
            form[0].insert(-4, DIV("Person to be contacted in case of an emergency",
                                   _class = "subheading",
                                   ))
            form[0].insert(-2, DIV(_class = "subheading",
                                   ))
        else:
            # Individual / Existing
            form[0].insert(2, DIV("Home Address",
                                  _class = "subheading",
                                  ))
            form[0].insert(6, DIV(_class = "subheading",
                                  ))
            # Volunteer Offer
            form[0].insert(12, DIV(_class = "subheading",
                                   ))
            # Availability
            form[0].insert(18, DIV("Availability",
                                   _class = "subheading",
                                   ))
            # Health
            form[0].insert(22, DIV("Many of the opportunities available following an incident require volunteers to be fit and active, may involve working in dirty or dusty environments, and could involve being outdoors - for example, removing damaged furniture and cleaning affected buildings, or lifting, packaging and distributing donated items. Some volunteer roles will be less physically demanding - for example, knocking on doors to check people are OK and gather information, making refreshments and helping with administration. Are you interested in opportunities:",
                                   _class = "subheading",
                                   ))
            form[0].insert(-8, DIV("Person to be contacted in case of an emergency",
                                   _class = "subheading",
                                   ))
            form[0].insert(-5, DIV(_class = "subheading",
                                   ))
            form[0].insert(-3, DIV(_class = "subheading",
                                   ))
            form[0].insert(-1, DIV(_class = "subheading",
                                   ))

        # Inject client-side Validation
        auth.s3_register_validation()

        # Set default registration key, so new users are prevented
        # from logging in until approved
        utable.registration_key.default = key = str(uuid.uuid4())

        if form.accepts(request.vars,
                        session,
                        formname = "register",
                        onvalidation = auth_settings.register_onvalidation,
                        ):

            form_vars = form.vars

            # Create the user record
            user_id = utable.insert(**utable._filter_fields(form_vars, id=False))
            form_vars.id = user_id

            # Save temporary user fields in s3db.auth_user_temp
            # Default just handles mobile, home, consent
            #auth.s3_user_register_onaccept(form)

            temptable = s3db.auth_user_temp
            record  = {"user_id": user_id}

            # Store the mobile_phone ready to go to pr_contact
            mobile = form_vars.mobile
            record["mobile"] = mobile

            # Store Consent Question Response
            consent = form_vars.consent
            record["consent"] = consent

            # Store the home_phone ready to go to pr_contact
            home = form_vars.home
            if home:
                record["home"] = home

            # Store Custom fields
            if agency:
                custom = {"registration_type": "agency",
                          "organisation": form_vars.organisation,
                          "organisation_type_id": form_vars.organisation_type_id,
                          #"addr_L3": form_vars.addr_L3,
                          #"addr_street": form_vars.addr_street,
                          #"addr_postcode": form_vars.addr_postcode,
                          #"where_operate": form_vars.where_operate or [],
                          "addr_street1": form_vars.addr_street1,
                          "addr_postcode1": form_vars.addr_postcode1,
                          #"first_name2": form_vars.first_name2,
                          #"last_name2": form_vars.last_name2,
                          #"addr_street2": form_vars.addr_street2,
                          #"addr_postcode2": form_vars.addr_postcode2,
                          #"email2": form_vars.email2,
                          #"mobile2": form_vars.mobile2,
                          #"home2": form_vars.home2,
                          }
            elif donor:
                custom = {"registration_type": "donor",
                          "organisation": form_vars.organisation,
                          "organisation_type": form_vars.organisation_type,
                          "addr_L3": form_vars.addr_L3,
                          "addr_street": form_vars.addr_street,
                          "addr_postcode": form_vars.addr_postcode,
                          "item_id": form_vars.item_id or [],
                          "items_details": form_vars.items_details,
                          "delivery": form_vars.delivery,
                          "where_deliver": form_vars.where_deliver or [],
                          "availability": form_vars.availability,
                          }
            elif group:
                custom = {"registration_type": "group",
                          "group": form_vars.group,
                          # Assume outside Cumbria
                          #"addr_L3": form_vars.addr_L3,
                          "addr_street": form_vars.addr_street,
                          "addr_postcode": form_vars.addr_postcode,
                          "first_name2": form_vars.first_name2,
                          "last_name2": form_vars.last_name2,
                          "addr_street2": form_vars.addr_street2,
                          "addr_postcode2": form_vars.addr_postcode2,
                          "email2": form_vars.email2,
                          "password2": str(form_vars.password2),
                          "mobile2": form_vars.mobile2,
                          "home2": form_vars.home2,
                          "where_operate": form_vars.where_operate or [],
                          "vols": form_vars.vols,
                          "transport": form_vars.transport,
                          "parish": form_vars.parish,
                          "skill_id": form_vars.skill_id or [],
                          "skills_details": form_vars.skills_details,
                          "faith_requirements": form_vars.faith_requirements,
                          "faith_requirements_details": form_vars.faith_requirements_details,
                          "emergency_contact_name": form_vars.emergency_contact_name,
                          "emergency_contact_number": form_vars.emergency_contact_number,
                          }
            else:
                # Individual or Existing
                custom = {"addr_L3": form_vars.addr_L3,
                          "addr_street": form_vars.addr_street,
                          "addr_postcode": form_vars.addr_postcode,
                          "skill_id": form_vars.skill_id or [],
                          "skills_details": form_vars.skills_details,
                          "certificates": form_vars.certificates or [],
                          "experience": form_vars.experience,
                          "resources": form_vars.resources,
                          "where_operate": form_vars.where_operate or [],
                          "travel": form_vars.travel,
                          "slots": form_vars.slots or [],
                          "convictions": form_vars.convictions,
                          "dbs": form_vars.dbs,
                          "significant_physical": form_vars.significant_physical,
                          "some_physical": form_vars.some_physical,
                          "little_physical": form_vars.little_physical,
                          "health_details": form_vars.health_details,
                          "faith_requirements": form_vars.faith_requirements,
                          "faith_requirements_details": form_vars.faith_requirements_details,
                          "emergency_contact_name": form_vars.emergency_contact_name,
                          "emergency_contact_number": form_vars.emergency_contact_number,
                          "emergency_contact_relationship": form_vars.emergency_contact_relationship,
                          "workplace": form_vars.workplace,
                          "workplace_details": form_vars.workplace_details,
                          }
                if existing:
                    custom["registration_type"] = "existing"
                else:
                    custom["registration_type"] = "individual"

            record["custom"] = json.dumps(custom)

            temptable.insert(**record)

            # Post-process the new user record
            users = db(utable.id > 0).select(utable.id, limitby=(0, 2))
            if len(users) == 1:
                # 1st user to register doesn't need verification/approval
                auth.s3_approve_user(form.vars)
                session.confirmation = auth_messages.registration_successful

                # 1st user gets Admin rights
                admin_group_id = 1
                auth.add_membership(admin_group_id, users.first().id)

                # Log them in
                if "language" not in form.vars:
                    # Was missing from login form
                    form.vars.language = T.accepted_language
                user = Storage(utable._filter_fields(form.vars, id=True))
                auth.login_user(user)

                # Send welcome email
                auth.s3_send_welcome_email(form.vars)

                # Where to go next?
                register_next = request.vars._next or auth_settings.register_next

            else:
                # Request User Verify their Email
                # System Details for Verification Email
                system = {"system_name": settings.get_system_name(),
                          "url": "%s/default/index/verify_email/%s" % (response.s3.base_url, key),
                          }

                # Try to send the Verification Email
                if not auth_settings.mailer or \
                   not auth_settings.mailer.settings.server or \
                   not auth_settings.mailer.send(to = form.vars.email,
                                                 subject = auth_messages.verify_email_subject % system,
                                                 message = auth_messages.verify_email % system,
                                                 ):
                    response.error = auth_messages.email_verification_failed

                    # Custom View
                    self._view(THEME, "register.html")

                    return {"title": title,
                            "header": header,
                            "form": form,
                            }

                # Redirect to Verification Info page
                register_next = URL(c = "default",
                                    f = "message",
                                    args = ["verify_email_sent"],
                                    vars = {"email": form.vars.email},
                                    )

            # Log action
            #if log:
            auth.log_event(auth_messages.register_log, form.vars)

            # Run custom onaccept for registration form
            #onaccept = auth_settings.register_onaccept
            #if onaccept:
            #    onaccept(form)

            # Redirect
            redirect(register_next)

        # Custom View
        self._view(THEME, "register.html")

        return {"title": title,
                "header": header,
                "form": form,
                }

# =============================================================================
class verify_email(S3CustomController):
    """ Custom verify_email Page """

    def __call__(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        auth_settings = auth.settings
        s3 = current.response.s3

        key = current.request.args[-1]
        utable = auth_settings.table_user
        query = (utable.registration_key == key)
        user = db(query).select(limitby = (0, 1)
                                ).first()
        if not user:
            redirect(auth_settings.verify_email_next)

        auth_messages = auth.messages

        session = current.session
        settings = current.deployment_settings

        user_id = user.id

        # Read custom fields to determine registration type
        temptable = s3db.auth_user_temp
        record = db(temptable.user_id == user_id).select(temptable.custom,
                                                         limitby = (0, 1),
                                                         ).first()
        custom = json.loads(record.custom)
        registration_type = custom["registration_type"]

        if registration_type == "agency":
            agency = True
        else:
            agency = False
            organisation_id = user.organisation_id

        if not agency and not organisation_id:
            # Donor/Individual/Group, so doesn't need approval
            # Add hook to process custom fields
            s3db.configure("auth_user",
                           register_onaccept = auth_user_register_onaccept,
                           )
            # Calls s3_link_user() which calls s3_link_to_person() which applies 'normal' data from s3db.auth_user_temp (home_phone, mobile_phone, consent)
            # Calls s3_auth_user_register_onaccept() which calls our custom auth_user_register_onaccept
            auth.s3_approve_user(user)

            # Log them in
            user = Storage(utable._filter_fields(user, id=True))
            auth.login_user(user)

            #if log:
            auth.log_event(auth_messages.verify_email_log, user)

            session.confirmation = auth_messages.email_verified
            session.flash = auth_messages.registration_successful

            if registration_type == "donor":
                # Show General Information for Donors
                _next = URL(c="default", f="index", args="donor")
            else:
                # Individual / Group
                # Show General Information & Advice
                _next = URL(c="cms", f="post", args="datalist")
            redirect(_next)

        db(utable.id == user_id).update(registration_key = "pending")
        session.information = "Thank you for validating your email. Your user account is still pending for approval by the administrator. You will get a notification by email when your account is activated."

        # Lookup the Approvers
        gtable = db.auth_group
        mtable = db.auth_membership
        approvers = None
        if not agency:
            # Existing, so normally approved by ORG_ADMIN(s)
            query = (gtable.uuid == "ORG_ADMIN") & \
                    (gtable.id == mtable.group_id) & \
                    (mtable.user_id == utable.id) & \
                    (utable.organisation_id == organisation_id)
            approvers = db(query).select(utable.email)

        if not approvers:
            # Agencies are approved by ADMIN(s) with a CVS email
            # Others approved by these same ADMINs if no ORG_ADMIN(s) exist
            query = (gtable.uuid == "ADMIN") & \
                    (gtable.id == mtable.group_id) & \
                    (mtable.user_id == utable.id)
            if not s3.debug:
                query &= (utable.email.like("%@cumbriacvs.org.uk"))
            approvers = db(query).select(utable.email)

        # Mail the Approver(s)
        # NB This is not multi-lingual
        # For a multi-lingual process, see auth.s3_approve_user_message()
        first_name = user.first_name
        last_name = user.last_name
        email = user.email
        system_name = settings.get_system_name()

        if agency:
            subject = "%(system_name)s: New Organisation Registration Approval Pending" % \
                        {"system_name": system_name}
            message = """Your action is required to approve a New Organisation for %(system_name)s:
%(organisation)s
%(first_name)s %(last_name)s
%(email)s
Please go to %(url)s to approve this user.""" % \
                        {"organisation": custom["organisation"],
                         "system_name": system_name,
                         "first_name": first_name,
                         "last_name": last_name,
                         "email": email,
                         "url": "%(base_url)s/admin/user/%(id)s" % \
                                {"base_url": s3.base_url,
                                 "id": user_id,
                                 },
                         }
        else:
            otable = s3db.org_organisation
            org = db(otable.id == organisation_id).select(otable.name,
                                                          limitby = (0, 1)
                                                          ).first()
            subject = "%(system_name)s: New Volunteer Registration Approval Pending" % \
                        {"system_name": system_name}
            message = """Your action is required to approve a New Volunteer for %(organisation)s:
%(first_name)s %(last_name)s
%(email)s
Please go to %(url)s to approve this user.""" % \
                        {"organisation": org.name,
                         "first_name": first_name,
                         "last_name": last_name,
                         "email": email,
                         "url": "%(base_url)s/admin/user/%(id)s" % \
                                {"base_url": s3.base_url,
                                 "id": user_id,
                                 },
                         }

        mailer = auth_settings.mailer
        result = None
        if mailer.settings.server:
            for approver in approvers:
                result = mailer.send(to = approver.email,
                                     subject = subject,
                                     message = message,
                                     )
        if not result:
            # Don't prevent registration just because email not configured
            #db.rollback()
            session.error = auth_messages.email_send_failed

        redirect(auth_settings.verify_email_next)

# =============================================================================
class volunteer(S3CustomController):
    """ Custom Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        system_roles = current.auth.get_system_roles()
        ADMIN = system_roles.ADMIN in current.session.s3.roles
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"

        resource = "Volunteer"
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby=(0, 1)).first()
        if item:
            if ADMIN:
                item1 = DIV(XML(item.body),
                            BR(),
                            A(current.T("Edit"),
                              _href = URL(c="cms", f="post",
                                          args = [item.id, "update"],
                                          vars = {"module": module,
                                                  "resource": resource,
                                                  },
                                          ),
                              _class="action-btn",
                              ),
                            )
            else:
                item1 = DIV(XML(item.body))
        elif ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item1 = A(current.T("Edit"),
                      _href = URL(c="cms", f="post", args="create",
                                  vars = {"module": module,
                                          "resource": resource,
                                          },
                                  ),
                      _class="%s cms-edit" % _class,
                      )
        else:
            item1 = ""
        output["item"] = item1

        self._view(THEME, "volunteer.html")
        return output

# =============================================================================
def org_organisation_create_onaccept(form):
    """
        Create a Reserves Forum for this Organisation with dual hierarchy to main Reserves Forum & this Organisation
    """

    db = current.db
    s3db = current.s3db
    ftable = s3db.pr_forum

    # Lookup the Reserves Forum
    forum = db(ftable.name == "Reserves").select(ftable.pe_id,
                                                 limitby = (0, 1)
                                                 ).first()
    try:
        reserves_pe_id = forum.pe_id
    except AttributeError:
        current.log.error("Unable to link Org Forum to Reserves Forum: Forum not Found")
        return

    form_vars_get = form.vars.get
    organisation_id = form_vars_get("id")

    # Lookup the Organisation
    otable = s3db.org_organisation
    org = db(otable.id == organisation_id).select(otable.pe_id,
                                                  limitby = (0, 1)
                                                  ).first()
    org_pe_id = org.pe_id

    # Create Forum
    record = {"organisation_id": organisation_id,
              "name": "%s Reserves" % form_vars_get("name"),
              }
    forum_id = ftable.insert(**record)
    record["id"] = forum_id
    s3db.update_super(ftable, record)
    forum_pe_id = record["pe_id"]

    # Add the Hierarchy links
    s3db.pr_add_affiliation(org_pe_id, forum_pe_id, role="Realm Hierarchy")
    s3db.pr_add_affiliation(reserves_pe_id, forum_pe_id, role="Realm Hierarchy")

# =============================================================================
def auth_user_register_onaccept(user_id):
    """
        Process Custom Fields
    """

    db = current.db
    s3db = current.s3db

    # Read custom fields & determine registration type
    temptable = s3db.auth_user_temp
    record = db(temptable.user_id == user_id).select(temptable.custom,
                                                     limitby = (0, 1),
                                                     ).first()
    if not record:
        # Prepop or Group Leader 2
        return

    auth = current.auth
    get_config = s3db.get_config

    custom = json.loads(record.custom)
    registration_type = custom["registration_type"]

    # Apply custom fields & Assign correct Roles
    if registration_type == "agency":
        # New Organisation (& Org Admin)

        pe_id = auth.s3_user_pe_id(user_id)

        # Create Home Address
        addr_street = custom.get("addr_street1")
        if addr_street:
            gtable = s3db.gis_location
            record = {"addr_street": addr_street,
                      "addr_postcode": custom["addr_postcode1"],
                      }
            location_id = gtable.insert(**record)
            record["id"] = location_id
            location_onaccept = get_config("gis_location", "create_onaccept") or \
                                get_config("gis_location", "onaccept")
            if callable(location_onaccept):
                gform = Storage(vars = record)
                location_onaccept(gform)

            atable = s3db.pr_address
            record = {"pe_id": pe_id,
                      "location_id": location_id,
                      }
            address_id = atable.insert(**record)
            record["id"] = address_id
            address_onaccept = get_config("pr_address", "create_onaccept") or \
                               get_config("pr_address", "onaccept")
            if callable(address_onaccept):
                aform = Storage(vars = record)
                address_onaccept(aform)

        # Create Organisation
        otable = s3db.org_organisation
        organisation = {"name": custom["organisation"],
                        }
        organisation_id = otable.insert(**organisation)
        organisation["id"] = organisation_id
        s3db.update_super(otable, organisation)
        db(otable.id == organisation_id).update(realm_entity = organisation["pe_id"])
        onaccept = get_config("org_organisation", "create_onaccept") or \
                   get_config("org_organisation", "onaccept")
        oform = Storage(vars = organisation)
        if callable(onaccept):
            onaccept(oform)
        org_organisation_create_onaccept(oform)

        ltable = s3db.org_organisation_organisation_type
        ltable.insert(organisation_id = organisation_id,
                      organisation_type_id = custom["organisation_type_id"],
                      )
        # Currently no need to onaccept since we don't have type-dependent realm entities

        ttable = s3db.org_organisation_tag
        ttable.insert(organisation_id = organisation_id,
                      tag = "visible",
                      value = "1",
                      )
        ttable.insert(organisation_id = organisation_id,
                      tag = "apply",
                      value = "0",
                      )

        #ltable = s3db.org_organisation_location
        #for location_id in custom["where_operate"]:
        #    ltable.insert(organisation_id = organisation_id,
        #                  location_id = location_id,
        #                  )
        #    # Currently no need to onaccept as none defined

        # Update User Record with organisation_id
        db(db.auth_user.id == user_id).update(organisation_id = organisation_id)

        # Lookup Person
        ptable = s3db.pr_person
        person = db(ptable.pe_id == pe_id).select(ptable.id,
                                                  limitby = (0, 1),
                                                  ).first()
        person_id = person.id

        # Create HR record to allow default realm to operate
        auth.s3_link_to_human_resource(Storage(id = user_id,
                                               organisation_id = organisation_id,
                                               ),
                                       person_id, hr_type=1)

        # Assign correct Roles
        add_membership = auth.add_membership
        realm_entity = organisation["pe_id"]
        add_membership(user_id = user_id,
                       role = "Organisation Administrator",
                       # Leave to Default Realm to make easier to switch affiliations
                       #entity = realm_entity,
                       )
        # (DRY with auth_add_role in config.py)
        ftable = s3db.pr_forum
        forums = db(ftable.name.belongs(("Donors",
                                         "Groups",
                                         "Reserves"))).select(ftable.pe_id,
                                                              ftable.name,
                                                              limitby = (0, 3)
                                                              )
        for forum in forums:
            if forum.name == "Donors":
                add_membership(user_id = user_id,
                               role = "Donors Admin",
                               entity = forum.pe_id,
                               )
            elif forum.name == "Groups":
                add_membership(user_id = user_id,
                               role = "Groups Admin",
                               entity = forum.pe_id,
                               )
            elif forum.name == "Reserves":
                add_membership(user_id = user_id,
                               role = "Reserves Reader",
                               entity = forum.pe_id,
                               )
        person.update_record(realm_entity = realm_entity)

        # Create Office
        #record = {"parent": custom["addr_L3"],
        #          "addr_street": custom["addr_street"],
        #          "addr_postcode": custom["addr_postcode"],
        #          }
        #location_id = gtable.insert(**record)
        #record["id"] = location_id
        #if callable(location_onaccept):
        #    gform = Storage(vars = record)
        #    location_onaccept(gform)

        #otable = s3db.org_office
        #record = {"name": custom["organisation"],
        #          "organisation_id": organisation_id,
        #          "realm_entity": realm_entity,
        #          }
        #office_id = otable.insert(**record)
        #record["id"] = office_id
        #s3db.update_super(otable, record)
        #onaccept = get_config("org_office", "create_onaccept") or \
        #           get_config("org_office", "onaccept")
        #if callable(onaccept):
        #    oform = Storage(vars = record)
        #    onaccept(oform)

        # 2nd OrgAdmin
        # Create Person
        #record = {"first_name": custom["first_name2"],
        #          "last_name": custom["last_name2"],
        #          "realm_entity": realm_entity,
        #          }
        #person_id = ptable.insert(**record)
        #record["id"] = person_id
        #s3db.update_super(ptable, record)
        #onaccept = get_config("pr_person", "create_onaccept") or \
        #           get_config("pr_person", "onaccept")
        #if callable(onaccept):
        #    pform = Storage(vars = record)
        #    onaccept(pform)

        # Add Address
        #pe_id = record.get("pe_id")
        #record = {"addr_street": custom["addr_street2"],
        #          "addr_postcode": custom["addr_postcode2"],
        #          }
        #location_id = gtable.insert(**record)
        #record["id"] = location_id
        #if callable(location_onaccept):
        #    gform = Storage(vars = record)
        #    location_onaccept(gform)

        #record = {"pe_id": pe_id,
        #          "location_id": location_id,
        #          "realm_entity": realm_entity,
        #          }
        #address_id = atable.insert(**record)
        #record["id"] = address_id
        #if callable(address_onaccept):
        #    aform = Storage(vars = record)
        #    address_onaccept(aform)

        # Add Contacts
        #ctable = s3db.pr_contact
        #email2 = custom["email2"]
        #if email2:
        #    record = {"pe_id": pe_id,
        #              "contact_method": "EMAIL",
        #              "value": email2,
        #              "realm_entity": realm_entity,
        #              }
        #    ctable.insert(**record)
        #    # Currently no need to onaccept as none defined
        #mobile2 = custom["mobile2"]
        #if mobile2:
        #    record = {"pe_id": pe_id,
        #              "contact_method": "SMS",
        #              "value": mobile2,
        #              "realm_entity": realm_entity,
        #              }
        #home2 = custom["home2"]
        #if home2:
        #    ctable.insert(**record)
        #    record = {"pe_id": pe_id,
        #              "contact_method": "HOME_PHONE",
        #              "value": home2,
        #              "realm_entity": realm_entity,
        #              }
        #    ctable.insert(**record)

        # Add Human Resource
        #hrtable = s3db.hrm_human_resource
        #record = {"organisation_id": organisation_id,
        #          "person_id": person_id,
        #          "realm_entity": realm_entity,
        #          }
        #human_resource_id = hrtable.insert(**record)
        #record["id"] = human_resource_id
        #onaccept = get_config("hrm_human_resource", "create_onaccept") or \
        #           get_config("hrm_human_resource", "onaccept")
        #if callable(onaccept):
        #    hrform = Storage(vars = record)
        #    onaccept(hrform)

    elif registration_type == "donor":
        # Donor

        # Lookup Realm Entity
        ftable = s3db.pr_forum
        forum = db(ftable.name == "Donors").select(ftable.pe_id,
                                                   limitby = (0, 1)
                                                   ).first()
        try:
            realm_entity = forum.pe_id
        except AttributeError:
            current.log.error("Cannot set Realm Entity for Donor: Forum not found")
            realm_entity = None

        # Create Home Address
        gtable = s3db.gis_location
        record = {"parent": custom["addr_L3"],
                  "addr_street": custom["addr_street"],
                  "addr_postcode": custom["addr_postcode"],
                  }
        location_id = gtable.insert(**record)
        record["id"] = location_id
        onaccept = get_config("gis_location", "create_onaccept") or \
                   get_config("gis_location", "onaccept")
        if callable(onaccept):
            gform = Storage(vars = record)
            onaccept(gform)

        pe_id = auth.s3_user_pe_id(user_id)
        atable = s3db.pr_address
        record = {"pe_id": pe_id,
                  "location_id": location_id,
                  "owned_by_user": user_id,
                  "realm_entity": realm_entity,
                  }
        address_id = atable.insert(**record)
        record["id"] = address_id
        onaccept = get_config("pr_address", "create_onaccept") or \
                   get_config("pr_address", "onaccept")
        if callable(onaccept):
            aform = Storage(vars = record)
            onaccept(aform)

        # Lookup Person
        ptable = s3db.pr_person
        person = db(ptable.pe_id == pe_id).select(ptable.id,
                                                  limitby = (0, 1),
                                                  ).first()
        person_id = person.id

        # Set Realm Entity
        person.update_record(realm_entity = realm_entity)

        # Create Items
        items_details = custom["items_details"]
        stable = s3db.supply_person_item_status
        status = db(stable.name == "Available").select(stable.id,
                                                       limitby = (0, 1)
                                                       ).first()
        if status:
            status_id = status.id
        else:
            raise HTTP(500, "'Available' Status for Donations not found")
        itable = s3db.supply_person_item
        for item_id in custom["item_id"]:
            record = {"person_id": person_id,
                      "item_id": item_id,
                      "comments": items_details,
                      "status_id": status_id,
                      }
            itable.insert(**record)

        ttable = s3db.pr_person_tag
        #record = {"person_id": person_id,
        #          "tag": "items_details",
        #          "value": custom["items_details"],
        #          }
        #ttable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "organisation",
                  "value": custom["organisation"],
                  }
        ttable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "organisation_type",
                  "value": custom["organisation_type"],
                  }
        ttable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "delivery",
                  "value": "Y" if custom["delivery"] else "N",
                  }
        ttable.insert(**record)

        # Where Deliver
        ltable = s3db.pr_person_location
        for location_id in custom["where_deliver"]:
            record = {"person_id": person_id,
                      "location_id": location_id,
                      }
            ltable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "availability",
                  "value": custom["availability"],
                  }
        ttable.insert(**record)

        # Assign correct Role
        auth.add_membership(user_id = user_id,
                            role = "Donor",
                            entity = pe_id,
                            )

    elif registration_type == "group":
        # Group

        # Create Group
        gtable = s3db.pr_group
        group = {"name": custom["group"]}
        group_id = gtable.insert(**group)
        group["id"] = group_id
        s3db.update_super(gtable, group)
        realm_entity = group["pe_id"]
        db(gtable.id == group_id).update(realm_entity = realm_entity)

        # Affiliate with Groups Forum to allow management by AGENCY & ORG_ADMINs
        ftable = s3db.pr_forum
        forum = db(ftable.name == "Groups").select(ftable.pe_id,
                                                   limitby = (0, 1)
                                                   ).first()
        try:
            master = forum.pe_id
        except AttributeError:
            current.log.error("Unable to link Group to Groups Forum: Forum not Found")
            return
        s3db.pr_add_affiliation(master, realm_entity, role="Realm Hierarchy")

        # Lookup Person
        pe_id = auth.s3_user_pe_id(user_id)

        # Set Realm Entity
        ptable = s3db.pr_person
        db(ptable.pe_id == pe_id).update(realm_entity = realm_entity)

        # Create Home Address
        gtable = s3db.gis_location
        record = {# Assume outside Cumbria
                  #"parent": custom["addr_L3"],
                  "addr_street": custom["addr_street"],
                  "addr_postcode": custom["addr_postcode"],
                  }
        location_id = gtable.insert(**record)
        record["id"] = location_id
        location_onaccept = get_config("gis_location", "create_onaccept") or \
                            get_config("gis_location", "onaccept")
        if callable(location_onaccept):
            gform = Storage(vars = record)
            location_onaccept(gform)

        atable = s3db.pr_address
        record = {"pe_id": pe_id,
                  "location_id": location_id,
                  "owned_by_user": user_id,
                  "realm_entity": realm_entity,
                  }
        address_id = atable.insert(**record)
        record["id"] = address_id
        address_onaccept = get_config("pr_address", "create_onaccept") or \
                           get_config("pr_address", "onaccept")
        if callable(address_onaccept):
            aform = Storage(vars = record)
            address_onaccept(aform)

        # Add Leader to Group
        ptable = s3db.pr_person
        person = db(ptable.pe_id == pe_id).select(ptable.id,
                                                  limitby = (0, 1),
                                                  ).first()
        mtable = s3db.pr_group_membership
        record = {"group_id": group_id,
                  "person_id": person.id,
                  "group_head": True,
                  "realm_entity": realm_entity,
                  }
        membership_id = mtable.insert(**record)
        record["id"] = membership_id
        membership_onaccept = get_config("pr_group_membership", "create_onaccept") or \
                              get_config("pr_group_membership", "onaccept")
        if callable(membership_onaccept):
            mform = Storage(vars = record)
            membership_onaccept(mform)

        # Assign correct Role
        auth.add_membership(user_id = user_id,
                            role = "Volunteer Group Leader",
                            entity = realm_entity,
                            )

        # 2nd Leader
        email = custom["email2"]
        utable = db.auth_user
        exists = db(utable.email == email).select(utable.id,
                                                  limitby = (0, 1)
                                                  )
        if exists:
            current.log.error = "Unable to add 2nd Leader to database: Email already exists"
        else:
            # Create User
            user2 = Storage(first_name = custom["first_name2"],
                            last_name = custom["last_name2"],
                            email = email,
                            password = custom["password2"],
                            )
            user_id = utable.insert(**user2)
            user2.id = user_id
            # Approve User (Creates Person & Email)
            auth.s3_approve_user(user2)

            # Lookup Person
            pe_id = auth.s3_user_pe_id(user_id)

            # Set Realm Entity
            ptable = s3db.pr_person
            db(ptable.pe_id == pe_id).update(realm_entity = realm_entity)

            # Add Address
            record = {"addr_street": custom["addr_street2"],
                      "addr_postcode": custom["addr_postcode2"],
                      }
            location_id = gtable.insert(**record)
            record["id"] = location_id
            if callable(location_onaccept):
                gform = Storage(vars = record)
                location_onaccept(gform)

            record = {"pe_id": pe_id,
                      "location_id": location_id,
                      "realm_entity": realm_entity,
                      }
            address_id = atable.insert(**record)
            record["id"] = address_id
            if callable(address_onaccept):
                aform = Storage(vars = record)
                address_onaccept(aform)

            # Add Contacts
            ctable = s3db.pr_contact
            # Currently no need to onaccept as none defined
            record = {"pe_id": pe_id,
                      "contact_method": "SMS",
                      "value": custom["mobile2"],
                      "realm_entity": realm_entity,
                      }
            ctable.insert(**record)
            home_phone = custom["home2"]
            if home_phone:
                record = {"pe_id": pe_id,
                          "contact_method": "HOME_PHONE",
                          "value": home_phone,
                          "realm_entity": realm_entity,
                          }
                ctable.insert(**record)

            # Add Leader to Group
            person = db(ptable.pe_id == pe_id).select(ptable.id,
                                                      limitby = (0, 1),
                                                      ).first()
            record = {"group_id": group_id,
                      "person_id": person.id,
                      "group_head": True,
                      "realm_entity": realm_entity,
                      }
            membership_id = mtable.insert(**record)
            record["id"] = membership_id
            if callable(membership_onaccept):
                mform = Storage(vars = record)
                membership_onaccept(mform)

            # Assign correct Role
            auth.add_membership(user_id = user_id,
                                role = "Volunteer Group Leader",
                                entity = realm_entity,
                                )

        # Locations
        ltable = s3db.pr_group_location
        for location_id in custom["where_operate"]:
            ltable.insert(group_id = group_id,
                          location_id = location_id,
                          realm_entity = realm_entity,
                          )
            # Currently no need to onaccept as none defined

        # Create Group Skills
        ctable = s3db.pr_group_competency
        for skill_id in custom["skill_id"]:
            record = {"group_id": group_id,
                      "skill_id": skill_id,
                      "realm_entity": realm_entity,
                      }
            ctable.insert(**record)

        ttable = s3db.pr_group_tag
        record = {"group_id": group_id,
                  "tag": "skills_details",
                  "value": custom["skills_details"],
                  }
        ttable.insert(**record)

        # Parish(es)
        record = {"group_id": group_id,
                  "tag": "parish",
                  "value": custom["parish"],
                  }
        ttable.insert(**record)

        # Volunteers
        record = {"group_id": group_id,
                  "tag": "volunteers",
                  "value": custom["vols"],
                  }
        ttable.insert(**record)

        # Transport
        record = {"group_id": group_id,
                  "tag": "transport",
                  "value": custom["transport"],
                  }
        ttable.insert(**record)

        # Faith Requirements
        record = {"group_id": group_id,
                  "tag": "faith_requirements",
                  "value": custom["faith_requirements"],
                  }
        ttable.insert(**record)
        record = {"group_id": group_id,
                  "tag": "faith_requirements_details",
                  "value": custom["faith_requirements_details"],
                  }
        ttable.insert(**record)

        # Emergency Contact
        record = {"group_id": group_id,
                  "tag": "contact_name",
                  "value": custom["emergency_contact_name"],
                  }
        ttable.insert(**record)
        record = {"group_id": group_id,
                  "tag": "contact_number",
                  "value": custom["emergency_contact_number"],
                  }
        ttable.insert(**record)

    else:
        # Individual / Existing

        ttable = s3db.pr_person_tag

        pe_id = auth.s3_user_pe_id(user_id)

        # Lookup Person
        ptable = s3db.pr_person
        person = db(ptable.pe_id == pe_id).select(ptable.id,
                                                  limitby = (0, 1),
                                                  ).first()
        person_id = person.id

        # Assign correct Role
        utable = db.auth_user
        user = db(utable.id == user_id).select(utable.organisation_id,
                                               limitby = (0, 1)
                                               ).first()
        organisation_id = user.organisation_id
        if organisation_id:
            # Existing
            otable = s3db.org_organisation
            org = db(otable.id == organisation_id).select(otable.name,
                                                          otable.pe_id,
                                                          limitby = (0, 1)
                                                          ).first()
            realm_entity = org.pe_id
            if org.name == "Agency Group":
                add_membership = auth.add_membership
                add_membership(user_id = user_id,
                               role = "Agency Staff",
                               )
                ftable = s3db.pr_forum
                forums = db(ftable.name.belongs(("Cases",
                                                 "Donors",
                                                 "Groups",
                                                 "Reserves"))).select(ftable.pe_id,
                                                                      ftable.name,
                                                                      )
                for forum in forums:
                    if forum.name == "Cases":
                        add_membership(user_id = user_id,
                                       role = "Cases Admin",
                                       entity = forum.pe_id,
                                       )
                    elif forum.name == "Donors":
                        add_membership(user_id = user_id,
                                       role = "Donors Admin",
                                       entity = forum.pe_id,
                                       )
                    elif forum.name == "Groups":
                        add_membership(user_id = user_id,
                                       role = "Groups Admin",
                                       entity = forum.pe_id,
                                       )
                    elif forum.name == "Reserves":
                        add_membership(user_id = user_id,
                                       role = "Reserves Reader",
                                       entity = forum.pe_id,
                                       )
            else:
                auth.add_membership(user_id = user_id,
                                    role = "Community Volunteer",
                                    # Leave to Default Realm to make easier to switch affiliations
                                    #entity = realm_entity,
                                    )

            # Not on Reserves by Default
            htable = s3db.hrm_human_resource
            hr = db(htable.person_id == person_id).select(htable.id,
                                                          limitby = (0, 1),
                                                          ).first()
            human_resource_id = hr.id
            httable = s3db.hrm_human_resource_tag
            record = {"human_resource_id": human_resource_id,
                      "tag": "reserve",
                      "value": "0",
                      }
            httable.insert(**record)
        else:
            # Reserve
            ftable = s3db.pr_forum
            forum = db(ftable.name == "Reserves").select(ftable.pe_id,
                                                         limitby = (0, 1)
                                                         ).first()
            realm_entity = forum.pe_id
            auth.add_membership(user_id = user_id,
                                role = "Reserve Volunteer",
                                entity = realm_entity,
                                )

            # Visible by Default
            record = {"person_id": person_id,
                      "tag": "reserve",
                      "value": "1",
                      }
            ttable.insert(**record)

        # Set Realm Entity
        person.update_record(realm_entity = realm_entity)

        # Create Home Address
        gtable = s3db.gis_location
        record = {"parent": custom["addr_L3"],
                  "addr_street": custom["addr_street"],
                  "addr_postcode": custom["addr_postcode"],
                  }
        location_id = gtable.insert(**record)
        record["id"] = location_id
        onaccept = get_config("gis_location", "create_onaccept") or \
                   get_config("gis_location", "onaccept")
        if callable(onaccept):
            gform = Storage(vars = record)
            onaccept(gform)

        atable = s3db.pr_address
        record = {"pe_id": pe_id,
                  "location_id": location_id,
                  "owned_by_user": user_id,
                  "realm_entity": realm_entity,
                  }
        address_id = atable.insert(**record)
        record["id"] = address_id
        onaccept = get_config("pr_address", "create_onaccept") or \
                   get_config("pr_address", "onaccept")
        if callable(onaccept):
            aform = Storage(vars = record)
            onaccept(aform)

        # Create Skills
        ctable = s3db.hrm_competency
        for skill_id in custom["skill_id"]:
            record = {"person_id": person_id,
                      "skill_id": skill_id,
                      "owned_by_user": user_id,
                      "realm_entity": realm_entity,
                      }
            ctable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "skills_details",
                  "value": custom["skills_details"],
                  }
        ttable.insert(**record)

        # Qualifications
        ltable = s3db.hrm_certification
        certificates = custom.get("certificates", [])
        for certificate_id in certificates:
            record = {"person_id": person_id,
                      "certificate_id": certificate_id,
                      "owned_by_user": user_id,
                      "realm_entity": realm_entity,
                      }
            ltable.insert(**record)

        experience = custom.get("experience")
        if experience is not None:
            record = {"person_id": person_id,
                      "tag": "experience",
                      "value": experience,
                      }
            ttable.insert(**record)

        resources = custom.get("resources")
        if resources is not None:
            record = {"person_id": person_id,
                      "tag": "resources",
                      "value": resources,
                      }
            ttable.insert(**record)

        # Where Operate
        ltable = s3db.pr_person_location
        for location_id in custom["where_operate"]:
            record = {"person_id": person_id,
                      "location_id": location_id,
                      "owned_by_user": user_id,
                      }
            ltable.insert(**record)

        # Slots
        ltable = s3db.pr_person_slot
        slots = custom.get("slots", [])
        for slot_id in slots:
            record = {"person_id": person_id,
                      "slot_id": slot_id,
                      "owned_by_user": user_id,
                      }
            ltable.insert(**record)

        # Additional Information
        #convictions = custom.get("convictions")
        #if convictions is not None:
        #    record = {"person_id": person_id,
        #              "tag": "convictions",
        #              "value": convictions,
        #              }
        #    ttable.insert(**record)

        dbs = custom.get("dbs")
        if dbs is not None:
            record = {"person_id": person_id,
                      "tag": "dbs",
                      "value": dbs,
                      }
            ttable.insert(**record)

        travel = custom.get("travel")
        if travel is not None:
            record = {"person_id": person_id,
                      "tag": "travel",
                      "value": travel,
                      }
            ttable.insert(**record)

        workplace = custom.get("workplace")
        if workplace is not None:
            record = {"person_id": person_id,
                      "tag": "workplace",
                      "value": workplace,
                      }
            ttable.insert(**record)

        workplace_details = custom.get("workplace_details")
        if workplace_details is not None:
            record = {"person_id": person_id,
                      "tag": "workplace_details",
                      "value": workplace_details,
                      }
            ttable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "significant_physical",
                  "value": custom["significant_physical"],
                  }
        ttable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "some_physical",
                  "value": custom["some_physical"],
                  }
        ttable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "little_physical",
                  "value": custom["little_physical"],
                  }
        ttable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "health_details",
                  "value": custom["health_details"],
                  }
        ttable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "faith_requirements",
                  "value": custom["faith_requirements"],
                  }
        ttable.insert(**record)

        record = {"person_id": person_id,
                  "tag": "faith_requirements_details",
                  "value": custom["faith_requirements_details"],
                  }
        ttable.insert(**record)

        # Emergency Contact
        etable = s3db.pr_contact_emergency
        record = {"pe_id": pe_id,
                  "name": custom["emergency_contact_name"],
                  "phone": custom["emergency_contact_number"],
                  "relationship": custom["emergency_contact_relationship"],
                  "owned_by_user": user_id,
                  "realm_entity": realm_entity,
                  }
        etable.insert(**record)

    return

# =============================================================================
def cms_post_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for CMS Posts on the
        Home & News Feed pages.

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["cms_post.id"]
    item_class = "thumbnail"

    db = current.db
    s3db = current.s3db
    settings = current.deployment_settings
    NONE = current.messages["NONE"]

    org_field = settings.get_cms_organisation()
    # Convert to the right format for this context
    if org_field == "created_by$organisation_id":
        org_field = "auth_user.organisation_id"
    elif org_field == "post_organisation.organisation_id":
        org_field = "cms_post_organisation.organisation_id"

    org_group_field = settings.get_cms_organisation_group()
    # Convert to the right format for this context
    if org_group_field == "created_by$org_group_id":
        org_group_field = "auth_user.org_group_id"
    elif org_group_field == "post_organisation_group.group_id":
        org_group_field = "cms_post_organisation_group.group_id"

    raw = record._row
    body = record["cms_post.body"]
    series_id = raw["cms_post.series_id"]

    title  = record["cms_post.title"]
    if title and title != NONE:
        subtitle = [DIV(title,
                        _class="card-subtitle"
                        )
                    ]
    else:
        subtitle = []

    #for event_resource in ["event", "incident"]:
    #    label = record["event_post.%s_id" % event_resource]
    #    if label and label != NONE:
    #        link=URL(c="event", f=event_resource,
    #                 args=[raw["event_post.%s_id" % event_resource],
    #                      "profile"]
    #                 )
    #        subtitle.append(DIV(A(ICON(event_resource),
    #                              label,
    #                              _href=link,
    #                              _target="_blank",
    #                              ),
    #                            _class="card-subtitle"
    #                            ))
    if subtitle:
        subtitle.append(body)
        body = TAG[""](*subtitle)

    # Allow records to be truncated
    # (not yet working for HTML)
    body = DIV(body,
               _class="s3-truncate",
               )

    date = record["cms_post.date"] or ""
    date = SPAN(date,
                _class="date-title",
                )

    location_id = raw["cms_post.location_id"]
    if location_id:
        location = record["cms_post.location_id"]
        if settings.get_cms_location_click_filters():
            # Which levels of Hierarchy are we using?
            levels = current.gis.get_relevant_hierarchy_levels()

            data = {}
            for level in levels:
                data[level[1:]] = raw["gis_location.%s" % level]
            onclick = '''S3.filter_location(%s)''' % json.dumps(data, separators=SEPARATORS)
            location = SPAN(A(location,
                              _href="#",
                              _onclick=onclick,
                              ),
                            _class="location-title",
                            )
        else:
            location_url = URL(c="gis", f="location", args=[location_id, "profile"])
            location = SPAN(A(location,
                              _href=location_url,
                              ),
                            _class="location-title",
                            )
    else:
        location = ""

    person = ""
    contact_field = settings.get_cms_person()
    if contact_field == "created_by":
        author_id = raw["cms_post.created_by"]
        person = record["cms_post.created_by"]

        # @ToDo: Bulk lookup
        ltable = s3db.pr_person_user
        ptable = db.pr_person
        query = (ltable.user_id == author_id) & \
                (ltable.pe_id == ptable.pe_id)
        row = db(query).select(ptable.id,
                               limitby=(0, 1)
                               ).first()
        if row:
            person_id = row.id
        else:
            person_id = None
    elif contact_field == "person_id":
        person_id = raw["cms_post.person_id"]
        if person_id:
            person = record["cms_post.person_id"]
    else:
        person_id = None

    if person:
        if person_id:
            # @ToDo: deployment_setting for controller to use?
            person_url = URL(c="pr", f="person", args=[person_id])
        else:
            person_url = "#"
        person = A(person,
                   _href=person_url,
                   )

    avatar = ""

    organisation = ""
    if org_field:
        organisation_id = raw[org_field]
        if organisation_id:
            organisation = record[org_field]
            org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
            organisation = A(organisation,
                             _href=org_url,
                             _class="card-organisation",
                             )

            # Avatar
            # Try Organisation Logo
            otable = db.org_organisation
            row = db(otable.id == organisation_id).select(otable.logo,
                                                          limitby=(0, 1)
                                                          ).first()
            if row and row.logo:
                logo = URL(c="default", f="download", args=[row.logo])
                avatar = IMG(_src=logo,
                             _height=50,
                             _width=50,
                             _style="padding-right:5px",
                             _class="media-object")
            else:
                avatar = organisation
            avatar = A(avatar,
                       _href=org_url,
                       _class="pull-left",
                       )

    org_group = ""
    if org_group_field:
        org_group_id = raw[org_group_field]
        if org_group_id:
            org_group = record[org_group_field]
            org_group_url = URL(c="org", f="group", args=[org_group_id, "profile"])
            org_group = A(org_group,
                          _href=org_group_url,
                          _class="card-org-group",
                          )

    if not avatar and person_id:
        # Personal Avatar
        avatar = s3_avatar_represent(person_id,
                                     tablename="pr_person",
                                     _class="media-object")

        avatar = A(avatar,
                   _href=person_url,
                   _class="pull-left",
                   )

    if person and organisation:
        card_person = DIV(person,
                          " - ",
                          organisation,
                          _class="card-person",
                          )
    elif person and org_group:
        card_person = DIV(person,
                          " - ",
                          org_group,
                          _class="card-person",
                          )
    elif person:
        card_person = DIV(person,
                          _class="card-person",
                          )
    #elif organisation:
    #    card_person = DIV(organisation,
    #                      _class="card-person",
    #                      )
    elif org_group:
        card_person = DIV(org_group,
                          _class="card-person",
                          )
    else:
        card_person = DIV(_class="card-person",
                          )

    permit = current.auth.s3_has_permission
    table = db.cms_post
    updateable = permit("update", table, record_id=record_id)

    if settings.get_cms_show_tags():
        tags = raw["cms_tag.name"]
        if tags or updateable:
            tag_list = UL(_class="s3-tags",
                          )
            tag_list["_data-post_id"] = record_id
        else:
            tag_list = ""
        if tags:
            if not isinstance(tags, list):
                tags = [tags]#.split(", ")
            for tag in tags:
                tag_item = LI(tag)
                tag_list.append(tag_item)
        tags = tag_list
    else:
        tags = ""

    T = current.T
    if series_id:
        series = record["cms_post.series_id"]
        translate = settings.get_L10n_translate_cms_series()
        if translate:
            series_title = T(series)
        else:
            series_title = series
    else:
        series_title = series = ""

    request = current.request

    # Tool box
    if updateable:
        if request.function == "newsfeed":
            fn = "newsfeed"
        else:
            fn = "post"
        edit_btn = A(ICON("edit"),
                     _href=URL(c="cms", f=fn,
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}
                               ),
                     _class="s3_modal",
                     _title=T("Edit %(type)s") % dict(type=series_title),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    user = current.auth.user
    if user and settings.get_cms_bookmarks():
        ltable = s3db.cms_post_user
        query = (ltable.post_id == record_id) & \
                (ltable.user_id == user.id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            bookmark_btn = A(ICON("bookmark"),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "remove_bookmark"]),
                                 list_id,
                                 record_id),
                             _title=T("Remove Bookmark"),
                             )
        else:
            bookmark_btn = A(ICON("bookmark-empty"),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "add_bookmark"]),
                                 list_id,
                                 record_id),
                             _title=T("Add Bookmark"),
                             )
    else:
        bookmark_btn = ""
    toolbox = DIV(bookmark_btn,
                  edit_btn,
                  delete_btn,
                  _class="edit-bar fright",
                  )

    # Dropdown of available documents
    documents = raw["doc_document.file"]
    if documents:
        if not isinstance(documents, list):
            documents = [documents]
        doc_list_id = "attachments-%s" % item_id
        doc_list = UL(_class="f-dropdown dropdown-menu",
                      _role="menu",
                      _id=doc_list_id,
                      # Foundation:
                      data={"dropdown-content": ""},
                      )
        retrieve = db.doc_document.file.retrieve
        for doc in documents:
            try:
                doc_name = retrieve(doc)[0]
            except (IOError, TypeError):
                doc_name = NONE
            doc_url = URL(c="default", f="download",
                          args=[doc])
            doc_item = LI(A(ICON("file"),
                            " ",
                            doc_name,
                            _href=doc_url,
                            ),
                          _role="menuitem",
                          )
            doc_list.append(doc_item)
        docs = DIV(A(ICON("attachment"),
                     SPAN(_class="caret"),
                     _class="btn dropdown-toggle dropdown",
                     _href="#",
                     data={# Both Bootstrap & Foundation:
                           "dropdown": doc_list_id,
                           # Foundation:
                           "options": "is_hover:true; hover_timeout:5000",
                           # Bootstrap:
                           "toggle": "dropdown",
                           },
                     ),
                   doc_list,
                   _class="btn-group attachments dropdown pull-right",
                   )
    else:
        docs = ""

    links = raw["doc_document.url"]
    if links:
        if not isinstance(links, list):
            links = [links]
        link_list = DIV(_class="media card-links")
        for link in links:
            link_item = A(ICON("link"),
                          " ",
                          link,
                          _href=link,
                          _target="_blank",
                          _class="card-link",
                          )
            link_list.append(link_item)
    else:
        link_list = ""

    if "profile" in request.args:
        # Single resource list
        # - don't show series_title
        if settings.get_cms_show_titles():
            title = raw["cms_post.title"] or ""
        else:
            title = ""
        card_label = SPAN(" %s" % title,
                          _class="card-title")
    else:
        # Mixed resource lists (Home, News Feed)
        icon = series.lower().replace(" ", "_")
        series_title = SPAN(" %s" % series_title,
                            _class="card-title")
        raw_title = raw["cms_post.title"]
        if settings.get_cms_show_titles() and raw_title:
            title = SPAN(s3_truncate(raw_title), _class="card-title2")
            card_label = TAG[""](ICON(icon),
                                 series_title,
                                 title,
                                 )
        else:
            card_label = TAG[""](ICON(icon),
                                 series_title,
                                 )
        # Type cards
        #if series == "Alert":
        #    # Apply additional highlighting for Alerts
        #    item_class = "%s disaster" % item_class

    # Render the item
    if series == "Event" and "newsfeed" not in request.args: # and request.function != "newsfeed"
        # Events on Homepage have a different header
        date.add_class("event")
        header = DIV(date,
                     location,
                     toolbox,
                     _class="card-header",
                     )
    else:
        header = DIV(card_label,
                     location,
                     date,
                     toolbox,
                     _class="card-header",
                     )

    item = DIV(header,
               DIV(avatar,
                   DIV(DIV(body,
                           card_person,
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               tags,
               docs,
               link_list,
               _class=item_class,
               _id=item_id,
               )

    return item

# END =========================================================================
