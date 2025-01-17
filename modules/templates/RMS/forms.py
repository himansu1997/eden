# -*- coding: utf-8 -*-

import os

from copy import deepcopy
from io import BytesIO

from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT#, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, \
                               Image, \
                               Paragraph, \
                               Table

from gluon import *
from gluon.contenttype import contenttype

from s3 import NONE, S3GroupedItems, S3GroupedItemsTable, s3_truncate
from s3.s3export import S3Exporter

from .layouts import OM

# Names of Orgs with specific settings
HNRC = "Honduran Red Cross"

# GRN Form
def inv_recv_form(r, **attr):
    if current.auth.root_org_name() == HNRC:
        return grn_hnrc(r, **attr)
    else:
        #return grn_S3html2pdf(r, **attr)
        return grn(r, **attr)

# Waybill Form
def inv_send_form(r, **attr):
    if current.auth.root_org_name() == HNRC:
        return waybill_hnrc(r, **attr)
    else:
        return waybill(r, **attr)

# Requests Form
def inv_req_form(r, **attr):

    T = current.T

    # Master record (=inv_req)
    resource = current.s3db.resource(r.tablename,
                                     id = r.id,
                                     components = ["req_item"],
                                     )

    # Columns and data for the form header
    header_fields = ["req_ref",
                     "date",
                     "date_required",
                     (T("Deliver to"), "site_id"),
                     (T("Reason for Request"), "purpose"),
                     "requester_id",
                     "site_id$site_id:inv_warehouse.contact",
                     "comments",
                     ]

    header_data = resource.select(header_fields,
                                  start = 0,
                                  limit = 1,
                                  represent = True,
                                  show_links = False,
                                  raw_data = True,
                                  )
    if not header_data:
        r.error(404, current.ERROR.BAD_RECORD)

    # Generate PDF header
    row = header_data.rows[0]
    labels = {rfield.colname: rfield.label for rfield in header_data.rfields}

    def row_(left, right):
        return header_row_(left, right, row=row, labels=labels)

    # Get organisation name and logo
    name, logo = OM().render()

    # The title
    title = H2(T("Logistics Requisition"))

    # Waybill details
    dtable = TABLE(TR(TD(DIV(logo,
                             H4(name),
                             ),
                         _colspan = 2,
                         ),
                      TD(DIV(title),
                         _colspan = 2,
                         ),
                      ),
                   row_("inv_req.req_ref", None),
                   row_("inv_req.date", "inv_req.date_required"),
                   row_("inv_req.site_id", "inv_req.purpose"),
                   row_("inv_req.requester_id", "inv_warehouse.contact"),
                   )

    # Waybill comments
    ctable = TABLE(TR(TH(T("Comments"))),
                   TR(TD(row["inv_req.comments"])),
                   )

    pdf_header = DIV(dtable,
                     P("&nbsp;"),
                     ctable,
                     )

    # Filename from send_ref
    header_row = header_data.rows[0]
    pdf_filename = header_row["_row"]["inv_req.req_ref"]

    # Component (=req_item)
    component = resource.components["req_item"]
    body_fields = ["item_id",
                   "item_pack_id",
                   "quantity",
                   "comments",
                   ]

    # Aggregate methods and column names
    aggregate = [("sum", "inv_req_item.quantity"),
                 ]

    # Generate the JSON data dict
    json_data = json_data_(component,
                           body_fields,
                           aggregate = aggregate,
                           )

    # Generate the grouped items table
    output = S3GroupedItemsTable(component,
                                 data = json_data,
                                 totals_label = T("Total"),
                                 title = T("Logistics Requisition"),
                                 pdf_header = pdf_header,
                                 pdf_footer = inv_req__footer,
                                 )

    # ...and export it as PDF
    return output.pdf(r, filename=pdf_filename)

# -----------------------------------------------------------------------------
def inv_req__footer(r):

    from s3db.pr import pr_PersonRepresent
    from s3db.inv import inv_req_approvers

    T = current.T

    header = TR(TH("&nbsp;"),
                TH(T("Name")),
                TH(T("Signature")),
                TH(T("Date")),
                )

    record = r.record
    requester = record.requester_id
    approvers = inv_req_approvers(record.site_id)
    person_ids = [requester] + list(approvers)

    names = pr_PersonRepresent().bulk(person_ids)

    signature_rows = [TR(TH(T("Requester")),
                         TD(names[requester]),
                         )]
    append = signature_rows.append

    for approver in approvers:
        append(TR(TH(approvers[approver]["title"]),
                  TD(names[approver]),
                  ))

    return TABLE(header,
                 *signature_rows
                 )

# =============================================================================
def header_row_(left, right, row=None, labels=None):
    """
        Helper function to generate a 2-column table row
        for the PDF header

        Used by inv_req_form, grn_hnrc and waybill_hnrc

        @param left: the column name for the left column
        @param right: the column name for the right column,
                      or None for an empty column
        @param row: the S3ResourceData row
        @param labels: dict of labels {colname: label}
    """

    if right:
        header_row = TR(TH(labels[left]),
                        TD(row[left]),
                        TH(labels[right]),
                        TD(row[right]),
                        )
    else:
        header_row = TR(TH(labels[left]),
                        TD(row[left],
                           _colspan = 3,
                           ),
                        )
    return header_row

# -----------------------------------------------------------------------------
def json_data_(component, list_fields, aggregate=None):
    """
        Extract, group and aggregate the data for the form body

        Used by inv_req_form, grn_hnrc and waybill_hnrc

        @param component: the component (S3Resource)
        @param list_fields: the columns for the form body
                            (list of field selectors)
        @param aggregate: aggregation methods and fields,
                          a list of tuples (method, column name)
    """

    # Extract the data
    data = component.select(list_fields,
                            limit = None,
                            raw_data = True,
                            represent = True,
                            show_links = False,
                            )

    # Get the column names and labels
    columns = []
    append_column = columns.append
    labels = {}
    for rfield in data.rfields:
        colname = rfield.colname
        append_column(colname)
        labels[colname] = rfield.label

    # Group and aggregate the items
    gi = S3GroupedItems(data.rows,
                        aggregate = aggregate,
                        )

    # Convert into JSON-serializable dict for S3GroupedItemsTable
    json_data = gi.json(fields = columns,
                        labels = labels,
                        as_dict = True,
                        )

    return json_data

# =============================================================================
def grn(r, **attr):
    """
        GRN (Goods Received Note) for French Red Cross (& current default)

        Using ReportLab's PLATYPUS direct

        @param r: the S3Request instance
        @param attr: controller attributes
    """

    # Styles
    styleSheet = getSampleStyleSheet()

    style = styleSheet["Normal"]
    style.fontName = "Helvetica"
    style.fontSize = 9

    style_center = deepcopy(style)
    style_center.alignment = TA_CENTER

    style_right = deepcopy(style)
    style_right.alignment = TA_RIGHT

    style_6_center = deepcopy(style_center)
    style_6_center.fontSize = 6

    style_7_center = deepcopy(style_center)
    style_7_center.fontSize = 7

    style_8_center = deepcopy(style_center)
    style_8_center.fontSize = 8

    style_8_right = deepcopy(style_8_center)
    style_8_right.alignment = TA_RIGHT

    style_12_center = deepcopy(style_center)
    style_12_center.fontSize = 12

    style_18_center = deepcopy(style_center)
    style_18_center.fontSize = 18

    Line = shapes.Line
    checkbox = shapes.Drawing(0.5 * cm, # width
                              0.5 * cm, # height
                              Line(0.1 * cm, # x1
                                   0.1 * cm, # y1
                                   0.4 * cm, # x2
                                   0.1 * cm, # y2
                                   strokeWidth = 2,
                                   ),
                              Line(0.4 * cm, # x1
                                   0.1 * cm, # y1
                                   0.4 * cm, # x2
                                   0.4 * cm, # y2
                                   strokeWidth = 2,
                                   ),
                              Line(0.4 * cm, # x1
                                   0.4 * cm, # y1
                                   0.1 * cm, # x2
                                   0.4 * cm, # y2
                                   ),
                              Line(0.1 * cm, # x1
                                   0.4 * cm, # y1
                                   0.1 * cm, # x2
                                   0.1 * cm, # y2
                                   ),
                              )
    checked = shapes.Drawing(0.5 * cm, # width
                             0.5 * cm, # height
                             Line(0.1 * cm, # x1
                                  0.1 * cm, # y1
                                  0.4 * cm, # x2
                                  0.1 * cm, # y2
                                  strokeWidth = 2,
                                  ),
                             Line(0.4 * cm, # x1
                                  0.1 * cm, # y1
                                  0.4 * cm, # x2
                                  0.4 * cm, # y2
                                  strokeWidth = 2,
                                  ),
                             Line(0.4 * cm, # x1
                                  0.4 * cm, # y1
                                  0.1 * cm, # x2
                                  0.4 * cm, # y2
                                  ),
                             Line(0.1 * cm, # x1
                                  0.4 * cm, # y1
                                  0.1 * cm, # x2
                                  0.1 * cm, # y2
                                  ),
                             Line(0.1 * cm, # x1
                                  0.1 * cm, # y1
                                  0.4 * cm, # x2
                                  0.4 * cm, # y2
                                  ),
                             Line(0.4 * cm, # x1
                                  0.1 * cm, # y1
                                  0.1 * cm, # x2
                                  0.4 * cm, # y2
                                  ),
                             )

    size = current.deployment_settings.get_pdf_size()
    if size == "Letter":
        pagesize = landscape(LETTER)
    elif size == "A4" or not isinstance(size, tuple):
        pagesize = landscape(A4)
    else:
        pagesize = landscape(size)

    db = current.db
    s3db = current.s3db

    # Master record
    recv_table = s3db.inv_recv
    record = r.record
    recv_ref = record.recv_ref
    date = recv_table.date.represent(record.date)
    wb = record.send_ref
    transport_type = record.transport_type
    if transport_type == "Air":
        awb = record.transport_ref or ""
        cmr = ""
        bl = ""
        flight = record.registration_no or ""
        reg = ""
        vessel = ""
    elif transport_type == "Sea":
        awb = ""
        cmr = ""
        bl = record.transport_ref or ""
        flight = ""
        reg = ""
        vessel = record.registration_no or ""
    elif transport_type == "Road":
        awb = ""
        cmr = record.transport_ref or ""
        bl = ""
        flight = ""
        reg = record.registration_no or ""
        vessel = ""
    #elif transport_type == "Hand":
    else:
        awb = ""
        cmr = ""
        bl = ""
        flight = ""
        reg = ""
        vessel = ""

    stable = s3db.org_site
    otable = s3db.org_organisation

    from_site_id = record.from_site_id
    if from_site_id:
        site = db(stable.site_id == from_site_id).select(stable.name,
                                                         limitby = (0, 1),
                                                         ).first()
        received_from = site.name
    else:
        org = db(otable.id == record.organisation_id).select(otable.name,
                                                             limitby = (0, 1),
                                                             ).first()
        received_from = org.name

    # Get organisation country & logo
    site = db(stable.site_id == record.site_id).select(stable.organisation_id,
                                                       limitby = (0, 1),
                                                       ).first()
    organisation_id = site.organisation_id

    from s3db.org import org_root_organisation_name
    recipient_ns = org_root_organisation_name(organisation_id)

    org = db(otable.id == organisation_id).select(otable.country,
                                                  otable.logo,
                                                  otable.root_organisation,
                                                  limitby = (0, 1),
                                                  ).first()
    logo = org.logo
    if not logo:
        root_organisation = org.root_organisation
        if organisation_id != root_organisation:
            org = db(otable.id == root_organisation).select(otable.country,
                                                            otable.logo,
                                                            limitby = (0, 1),
                                                            ).first()
            logo = org.logo

    if logo:
        src = os.path.join(r.folder,
                           "uploads",
                           logo,
                           )
    else:
        # Use default IFRC
        src = os.path.join(r.folder,
                           "static",
                           "themes",
                           "RMS",
                           "img",
                           "logo_small.png",
                           )

    logo = Image(src)

    # Assuming 96dpi original resolution
    resolution = 96
    iwidth = logo.drawWidth
    iheight = logo.drawHeight
    height = 50 * inch / resolution
    width = iwidth * (height / iheight)
    logo.drawHeight = height
    logo.drawWidth = width

    output = BytesIO()
    doc = SimpleDocTemplate(output,
                            title = recv_ref,
                            pagesize = pagesize,
                            leftMargin = 0.3 * inch,
                            rightMargin = 0.3 * inch,
                            topMargin = 0.5 * inch,
                            bottomMargin = 0.5 * inch,
                            )

    lightgrey = colors.lightgrey
    table_style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                   ("SPAN", (0, 0), (5, 0)),
                   ("SPAN", (7, 0), (8, 0)),
                   ("BACKGROUND", (6, 0), (8, 0), lightgrey),
                   ("SPAN", (0, 1), (5, 1)),
                   ("SPAN", (7, 1), (8, 1)),
                   ("SPAN", (0, 3), (1, 3)),
                   ("SPAN", (2, 3), (3, 3)),
                   ("SPAN", (4, 3), (6, 3)),
                   ("SPAN", (7, 3), (8, 3)),
                   ("BACKGROUND", (0, 3), (0, 3), lightgrey),
                   ("BACKGROUND", (4, 3), (4, 3), lightgrey),
                   ("SPAN", (2, 5), (3, 5)),
                   ("SPAN", (5, 5), (6, 5)),
                   ("SPAN", (7, 5), (8, 5)),
                   ("BACKGROUND", (0, 5), (0, 5), lightgrey),
                   ("BACKGROUND", (2, 5), (3, 5), lightgrey),
                   ("BACKGROUND", (5, 5), (6, 5), lightgrey),
                   ("SPAN", (0, 7), (0, 10)),
                   ("SPAN", (5, 7), (6, 7)),
                   ("SPAN", (5, 8), (6, 8)),
                   ("SPAN", (5, 9), (6, 9)),
                   ("SPAN", (3, 7), (4, 7)),
                   ("SPAN", (7, 7), (8, 7)),
                   ("SPAN", (3, 8), (4, 8)),
                   ("SPAN", (7, 8), (8, 8)),
                   ("SPAN", (3, 9), (4, 9)),
                   ("SPAN", (7, 9), (8, 9)),
                   ("BACKGROUND", (0, 7), (1, 10), lightgrey),
                   ("BACKGROUND", (5, 7), (6, 9), lightgrey),
                   ("SPAN", (3, 10), (4, 10)),
                   ("SPAN", (0, 12), (3, 12)),
                   ("SPAN", (4, 12), (6, 12)),
                   ("SPAN", (1, 13), (2, 13)),
                   ("SPAN", (7, 12), (7, 13)),
                   ("SPAN", (8, 12), (8, 13)),
                   ("BACKGROUND", (0, 12), (8, 13), lightgrey),
                   ]
    sappend = table_style.append

    spacer = ["",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              ]

    content = [
               # Row 0
               [logo,
                "",
                "",
                "",
                "",
                "",
                Paragraph(str(B("COUNTRY CODE")), style_center),
                Paragraph(str(B("GRN NUMBER")), style_center),
                "",
                ],
               # Row 1
               [Paragraph("%s / %s" % (B("GOODS RECEIVED NOTE"),
                                       I("Accusé de Réception"),
                                       ), style_18_center),
                "",
                "",
                "",
                "",
                "",
                Paragraph(str(B(org.country)), style_12_center),
                Paragraph(str(B(recv_ref)), style_12_center),
                "",
                ],
               # Row 2
               spacer,
               # Row 3
               [Paragraph("%s<br/>(%s)" % (B("DELEGATION/CONSIGNEE"),
                                           B("LOCATION"),
                                           ), style_right),
                "",
                Paragraph(recipient_ns, style_8_center),
                "",
                Paragraph("%s / %s" % (B("RECEIVED FROM"),
                                       I("reçu de"),
                                       ), style_center),
                "",
                "",
                Paragraph(received_from, style_center),
                "",
                ],
               # Row 4
               spacer,
               # Row 5
               [Paragraph("%s<br/>%s" % (B("DATE OF ARRIVAL"),
                                         I("Date de réception"),
                                         ), style_right),
                Paragraph(date, style_center),
                Paragraph(str(B("DOCUMENT WELL RECEIVED")), style_center),
                "",
                "",
                Paragraph(str(B("IF NO, PLEASE SPECIFY")), style_center),
                "",
                "",
                "",
                ],
               # Row 6
               spacer,
               # Row 7
               [Paragraph("%s<br/>%s" % (B("MEANS OF TRANSPORT"),
                                         I("Moyen de transport"),
                                         ), style_center),
                Paragraph(str(B("Air")), style_right),
                checked if transport_type == "Air" else checkbox,
                Paragraph("%s: %s" % (B("AWB n°"),
                                      awb,
                                      ), style),
                "",
                Paragraph(str(B("FLIGHT N°")), style_right),
                "",
                Paragraph(flight, style_center),
                "",
                ],
               # Row 8
               ["",
                Paragraph(str(B("Road")), style_right),
                checked if transport_type == "Road" else checkbox,
                Paragraph("%s: %s" % (B("Waybill n°/ CMR n°"),
                                      cmr,
                                      ), style),
                "",
                Paragraph(str(B("REGISTRATION N°")), style_right),
                "",
                Paragraph(reg, style_center),
                "",
                ],
               # Row 9
               ["",
                Paragraph(str(B("Sea")), style_right),
                checked if transport_type == "Sea" else checkbox,
                Paragraph("%s: %s" % (B("B/L n°"),
                                      bl,
                                      ), style),
                "",
                Paragraph(str(B("VESSEL")), style_right),
                "",
                Paragraph(vessel, style_center),
                "",
                ],
               # Row 10
               ["",
                Paragraph("Handcarried by", style_8_right),
                checked if transport_type == "Hand" else checkbox,
                Paragraph("%s: %s" % (B("Waybill n°"),
                                      wb,
                                      ), style),
                "",
                "",
                "",
                "",
                "",
                ],
               # Row 11
               spacer,
               # Row 12
               [Paragraph("%s / %s" % (B("GOODS RECEIVED"),
                                       I("Marchandises reçues"),
                                       ), style_7_center),
                "",
                "",
                "",
                Paragraph(str(I("FOR FOOD INDICATE NET WEIGHT")), style_7_center),
                "",
                "",
                Paragraph("%s<br/>%s" % (B("RECEIVED ACCORDING TO DOCUMENT AND RECEIVED IN GOOD CONDITIONS"),
                                         I("Reçu selon documents et en bonne condition"),
                                         ), style_7_center),

                Paragraph("%s<br/>%s" % (B("CLAIM"),
                                         I("Réclamation"),
                                         ), style_7_center),
                ],
               # Row 13
               [Paragraph("%s<br/>%s" % (B("ITEMS CODE"),
                                         I("Description générale et remarques"),
                                         ), style_6_center),
                Paragraph("%s<br/>%s" % (B("DESCRIPTION"),
                                         I("Code article"),
                                         ), style_6_center),
                "",
                Paragraph(str(B("COMMODITY TRACKING N° OR DONOR")), style_7_center),
                Paragraph("%s<br/>%s" % (B("NB. OF UNITS"),
                                         I("nb. colis"),
                                         ), style_6_center),
                Paragraph("%s<br/>%s" % (B("UNIT TYPE/WEIGHT"),
                                         I("type d'unité/poids"),
                                         ), style_6_center),
                Paragraph("%s<br/>%s" % (B("WEIGHT (kg)"),
                                         I("Total (kg)"),
                                         ), style_6_center),
                "",
                "",
                ],
               ]
    cappend = content.append

    rowHeights = [1.64 * cm,
                  1.16 * cm,
                  0.16 * cm,
                  0.82 * cm,
                  0.21 * cm,
                  1.06 * cm,
                  0.25 * cm,
                  0.56 * cm,
                  0.56 * cm,
                  0.56 * cm,
                  0.56 * cm,
                  0.24 * cm,
                  0.40 * cm,
                  0.85 * cm,
                  ]
    rappend = rowHeights.append

    # Received Items
    ttable = s3db.inv_track_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    query = (ttable.recv_id == record.id) & \
            (ttable.item_id == itable.id) & \
            (ttable.item_pack_id == ptable.id)
    items = db(query).select(itable.code,
                             itable.name,
                             ttable.item_source_no,
                             ttable.recv_quantity,
                             ptable.name,
                             ptable.quantity,
                             itable.weight,
                             )

    rowNo = 14
    for row in items:
        item = row["supply_item"]
        pack = row["supply_item_pack"]
        track_item = row["inv_track_item"]
        quantity = track_item.recv_quantity
        pack_details = pack.name
        weight = item.weight
        if weight:
            pack_weight = weight * pack.quantity
            pack_details = "%s / %s" % (pack_details,
                                        round(pack_weight, 2),
                                        )
            total_weight = round(pack_weight * quantity, 2)
        else:
            total_weight = NONE
        body_row = [Paragraph(item.code or NONE, style_7_center),
                    Paragraph(s3_truncate(item.name, 30), style_6_center),
                    "",
                    Paragraph(track_item.item_source_no or NONE, style_7_center),
                    Paragraph(str(quantity), style_7_center),
                    Paragraph(pack_details, style_7_center),
                    Paragraph(str(total_weight), style_7_center),
                    "",
                    checkbox,
                    ]
        rappend(0.67 * cm)
        sappend(("SPAN", (1, rowNo), (2, rowNo)))
        cappend(body_row)
        rowNo += 1

    rowHeights += [0.32 * cm,
                   0.45 * cm,
                   2.04 * cm,
                   0.32 * cm,
                   0.39 * cm,
                   0.81 * cm,
                   0.39 * cm,
                   0.81 * cm,
                   ]

    table_style += [("SPAN", (0, rowNo + 1), (8, rowNo + 1)),
                    ("SPAN", (0, rowNo + 2), (8, rowNo + 2)),
                    ("SPAN", (2, rowNo + 4), (3, rowNo + 4)),
                    ("SPAN", (4, rowNo + 4), (6, rowNo + 4)),
                    ("SPAN", (7, rowNo + 4), (8, rowNo + 4)),
                    ("SPAN", (2, rowNo + 5), (3, rowNo + 5)),
                    ("SPAN", (4, rowNo + 5), (6, rowNo + 5)),
                    ("SPAN", (7, rowNo + 5), (8, rowNo + 5)),
                    ("SPAN", (2, rowNo + 6), (3, rowNo + 6)),
                    ("SPAN", (4, rowNo + 6), (6, rowNo + 6)),
                    ("SPAN", (7, rowNo + 6), (8, rowNo + 6)),
                    ("SPAN", (2, rowNo + 7), (3, rowNo + 7)),
                    ("SPAN", (4, rowNo + 7), (6, rowNo + 7)),
                    ("SPAN", (7, rowNo + 7), (8, rowNo + 7)),
                    ("BACKGROUND", (0, rowNo + 4), (8, rowNo + 4), lightgrey),
                    ("BACKGROUND", (0, rowNo + 6), (8, rowNo + 6), lightgrey),
                    ]

    content += [spacer,
                [Paragraph("%s / %s" % (B("COMMENTS"),
                                        I("Observations"),
                                        ), style),
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 ],
                [Paragraph(record.comments or "", style_8_center),
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 ],
                spacer,
                [Paragraph(str(B("DELIVERED BY")), style_8_center),
                 Paragraph(str(B("DATE")), style_8_center),
                 Paragraph(str(B("FUNCTION")), style_8_center),
                 "",
                 Paragraph("%s (%s)" % (B("NAME"),
                                        "IN BLOCK LETTER",
                                        ), style_8_center),
                 "",
                 "",
                 Paragraph(str(B("SIGNATURE")), style_8_center),
                 "",
                 ],
                spacer,
                [Paragraph(str(B("RECEIVED BY")), style_8_center),
                 Paragraph(str(B("DATE")), style_8_center),
                 Paragraph(str(B("FUNCTION")), style_8_center),
                 "",
                 Paragraph("%s (%s)" % (B("NAME"),
                                        "IN BLOCK LETTER",
                                        ), style_8_center),
                 "",
                 "",
                 Paragraph(str(B("SIGNATURE / STAMP")), style_8_center),
                 "",
                 ],
                spacer,
                ]

    table = Table(content,
                  colWidths = (4.17 * cm, # A
                               2.73 * cm, # B
                               1.20 * cm, # C
                               4.06 * cm, # D
                               2.29 * cm, # E
                               3.13 * cm, # F
                               2.03 * cm, # G
                               6.25 * cm, # H
                               1.33 * cm, # I
                               ),
                  rowHeights = rowHeights,
                  style = table_style,
                  hAlign = "LEFT",   # defaults to "CENTER"
                  vAlign = "MIDDLE", # defaults to "MIDDLE", but better to specify
                  )

    doc.build([table],
              canvasmaker = canvas.Canvas, # S3NumberedCanvas
              )

    # Return the generated PDF
    response = current.response
    if response:
        filename = "%s.pdf" % recv_ref
        if "uwsgi_scheme" in current.request.env:
            # Running uwsgi then we can't have unicode filenames
            # Accent Folding
            def string_escape(s):
                import unicodedata
                return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("utf-8")
            filename = string_escape(filename)
        disposition = 'attachment; filename="%s"' % filename
        response.headers["Content-Type"] = contenttype(".pdf")
        response.headers["Content-disposition"] = disposition

    return output.getvalue()

# =============================================================================
def waybill(r, **attr):
    """
        Waybill for French Red Cross (& current default)

        Using ReportLab's PLATYPUS direct

        @param r: the S3Request instance
        @param attr: controller attributes
    """

    # Styles
    styleSheet = getSampleStyleSheet()

    style_center = styleSheet["Normal"]
    style_center.fontName = "Helvetica"
    style_center.fontSize = 9
    style_center.alignment = TA_CENTER

    style_6_center = deepcopy(style_center)
    style_6_center.fontSize = 6

    style_7_center = deepcopy(style_center)
    style_7_center.fontSize = 7

    style_8_center = deepcopy(style_center)
    style_8_center.fontSize = 8

    style_8 = deepcopy(style_8_center)
    style_8.alignment = TA_LEFT

    style_16_center = deepcopy(style_center)
    style_16_center.fontSize = 16

    style_22_center = deepcopy(style_center)
    style_22_center.fontSize = 22

    Line = shapes.Line
    checkbox = shapes.Drawing(0.5 * cm, # width
                              0.5 * cm, # height
                              Line(0.1 * cm, # x1
                                   0.1 * cm, # y1
                                   0.4 * cm, # x2
                                   0.1 * cm, # y2
                                   strokeWidth = 2,
                                   ),
                              Line(0.4 * cm, # x1
                                   0.1 * cm, # y1
                                   0.4 * cm, # x2
                                   0.4 * cm, # y2
                                   strokeWidth = 2,
                                   ),
                              Line(0.4 * cm, # x1
                                   0.4 * cm, # y1
                                   0.1 * cm, # x2
                                   0.4 * cm, # y2
                                   ),
                              Line(0.1 * cm, # x1
                                   0.4 * cm, # y1
                                   0.1 * cm, # x2
                                   0.1 * cm, # y2
                                   ),
                              )
    checked = shapes.Drawing(0.5 * cm, # width
                             0.5 * cm, # height
                             Line(0.1 * cm, # x1
                                  0.1 * cm, # y1
                                  0.4 * cm, # x2
                                  0.1 * cm, # y2
                                  strokeWidth = 2,
                                  ),
                             Line(0.4 * cm, # x1
                                  0.1 * cm, # y1
                                  0.4 * cm, # x2
                                  0.4 * cm, # y2
                                  strokeWidth = 2,
                                  ),
                             Line(0.4 * cm, # x1
                                  0.4 * cm, # y1
                                  0.1 * cm, # x2
                                  0.4 * cm, # y2
                                  ),
                             Line(0.1 * cm, # x1
                                  0.4 * cm, # y1
                                  0.1 * cm, # x2
                                  0.1 * cm, # y2
                                  ),
                             Line(0.1 * cm, # x1
                                  0.1 * cm, # y1
                                  0.4 * cm, # x2
                                  0.4 * cm, # y2
                                  ),
                             Line(0.4 * cm, # x1
                                  0.1 * cm, # y1
                                  0.1 * cm, # x2
                                  0.4 * cm, # y2
                                  ),
                             )

    size = current.deployment_settings.get_pdf_size()
    if size == "Letter":
        pagesize = landscape(LETTER)
    elif size == "A4" or not isinstance(size, tuple):
        pagesize = landscape(A4)
    else:
        pagesize = landscape(size)

    db = current.db
    s3db = current.s3db

    # Master record
    send_table = s3db.inv_send
    record = r.record
    send_ref = record.send_ref
    date = send_table.date.represent(record.date)
    transport_type = record.transport_type

    stable = s3db.org_site
    otable = s3db.org_organisation
    # Lookup recipient
    site = db(stable.site_id == record.to_site_id).select(stable.organisation_id,
                                                          limitby = (0, 1),
                                                          ).first()
    organisation_id = site.organisation_id
    org = db(otable.id == organisation_id).select(otable.name,
                                                  otable.root_organisation,
                                                  limitby = (0, 1),
                                                  ).first()
    root_organisation = org.root_organisation
    if organisation_id != root_organisation:
        org = db(otable.id == root_organisation).select(otable.name,
                                                        limitby = (0, 1),
                                                        ).first()
    recipient_ns = org.name
    # Get site name and organisation country/logo
    site = db(stable.site_id == record.site_id).select(stable.name,
                                                       stable.organisation_id,
                                                       limitby = (0, 1),
                                                       ).first()
    organisation_id = site.organisation_id
    org = db(otable.id == organisation_id).select(otable.country,
                                                  otable.logo,
                                                  otable.root_organisation,
                                                  limitby = (0, 1),
                                                  ).first()
    logo = org.logo
    if not logo:
        root_organisation = org.root_organisation
        if organisation_id != root_organisation:
            org = db(otable.id == root_organisation).select(otable.country,
                                                            otable.logo,
                                                            limitby = (0, 1),
                                                            ).first()
            logo = org.logo

    if logo:
        src = os.path.join(r.folder,
                           "uploads",
                           logo,
                           )
    else:
        # Use default IFRC
        src = os.path.join(r.folder,
                           "static",
                           "themes",
                           "RMS",
                           "img",
                           "logo_small.png",
                           )

    logo = Image(src)

    # Assuming 96dpi original resolution
    resolution = 96
    iwidth = logo.drawWidth
    iheight = logo.drawHeight
    height = 50 * inch / resolution
    width = iwidth * (height / iheight)
    logo.drawHeight = height
    logo.drawWidth = width

    output = BytesIO()
    doc = SimpleDocTemplate(output,
                            title = send_ref,
                            pagesize = pagesize,
                            leftMargin = 0.3 * inch,
                            rightMargin = 0.3 * inch,
                            topMargin = 0.5 * inch,
                            bottomMargin = 0.5 * inch,
                            )

    lightgrey = colors.lightgrey
    table_style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                   ("SPAN", (0, 0), (3, 0)),
                   ("SPAN", (5, 0), (7, 0)),
                   ("SPAN", (11, 0), (13, 0)),
                   ("BACKGROUND", (4, 0), (7, 0), lightgrey),
                   ("BACKGROUND", (9, 0), (13, 0), lightgrey),
                   ("SPAN", (0, 1), (3, 2)),
                   ("SPAN", (5, 1), (7, 1)),
                   ("SPAN", (11, 1), (13, 1)),
                   ("BACKGROUND", (9, 1), (9, 1), lightgrey),
                   ("SPAN", (9, 2), (10, 2)),
                   ("SPAN", (11, 2), (13, 2)),
                   ("BACKGROUND", (9, 2), (10, 2), lightgrey),
                   ("SPAN", (0, 3), (2, 3)),
                   ("SPAN", (3, 3), (11, 3)),
                   ("SPAN", (12, 3), (13, 3)),
                   ("BACKGROUND", (0, 3), (13, 3), lightgrey),
                   ("SPAN", (0, 4), (2, 7)),
                   ("SPAN", (3, 4), (11, 4)),
                   ("BACKGROUND", (3, 4), (12, 4), lightgrey),
                   ("SPAN", (3, 5), (11, 5)),
                   ("BACKGROUND", (12, 5), (12, 5), lightgrey),
                   ("SPAN", (3, 6), (5, 6)),
                   ("SPAN", (6, 6), (7, 6)),
                   ("SPAN", (9, 6), (10, 6)),
                   ("BACKGROUND", (3, 6), (5, 6), lightgrey),
                   ("BACKGROUND", (11, 6), (12, 6), lightgrey),
                   ("SPAN", (3, 7), (5, 7)),
                   ("SPAN", (6, 7), (7, 7)),
                   ("SPAN", (9, 7), (10, 7)),
                   ("BACKGROUND", (3, 7), (5, 7), lightgrey),
                   ("BACKGROUND", (12, 7), (12, 7), lightgrey),
                   ("SPAN", (1, 9), (2, 9)),
                   ("SPAN", (7, 9), (9, 9)),
                   ("SPAN", (10, 9), (13, 9)),
                   ("BACKGROUND", (0, 9), (13, 9), lightgrey),
                   ]
    #sappend = table_style.append

    spacer = ["",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              ]

    content = [# Row 0
               [logo,
                "",
                "",
                "",
                Paragraph(str(B("DATE")), style_8_center),
                Paragraph("%s / %s" % (B("WAREHOUSE"),
                                       I("Entrepôt"),
                                       ), style_8_center),
                "",
                "",
                "",
                Paragraph(str(B("TYPE")), style_7_center),
                Paragraph(str(B("COUNTRY")), style_8_center),
                Paragraph(str(B("NUMBER")), style_8_center),
                "",
                "",
                ],
               # Row 1
               [Paragraph("%s / %s" % (B("WAYBILL"),
                                       B("DELIVERY NOTE"),
                                       ), style_22_center),
                "",
                "",
                "",
                Paragraph(date, style_8_center),
                Paragraph(site.name, style_center),
                "",
                "",
                "",
                Paragraph(str(B("WB")), style_8_center),
                Paragraph(str(B(org.country)), style_center),
                Paragraph(str(B(send_ref)), style_center),
                "",
                "",
                ],
               # Row 2
               ["",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                Paragraph(str(B("PL REFERENCE")), style_8_center),
                "",
                Paragraph(send_ref, style_8_center),
                "",
                "",
                ],
               # Row 3
               [Paragraph("%s / %s" % (B("DESTINATION AND BENEFICIARY"),
                                       I("Destination et bénéficiaire"),
                                       ), style_center),
                "",
                "",
                Paragraph("%s / %s" % (B("TRANSPORT DATA"),
                                       I("Information transport"),
                                       ), style_center),
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                Paragraph(str(B("MEANS OF TRANSPORT")), style_center),
                "",
                ],
               # Row 4
               [Paragraph(str(B(recipient_ns)), style_16_center),
                "",
                "",
                Paragraph("%s / %s" % (B("COMMERCIAL OR FRC TRANSPORT CONTRACT"),
                                       I("No. Contrat commercial transporteur ou FRC"),
                                       ), style_center),
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                Paragraph(str(B("ROAD")), style_8_center),
                checked if transport_type == "Road" else checkbox,
                ],
               # Row 5
               ["",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                Paragraph(str(B("AIR")), style_8_center),
                checked if transport_type == "Air" else checkbox,
                ],
               # Row 6
               ["",
                "",
                "",
                Paragraph("%s / %s" % (B("VEHICLE"),
                                       I("Véhicule"),
                                       ), style_center),
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                Paragraph(str(B("ETD")), style_center),
                Paragraph(str(B("SEA")), style_8_center),
                checked if transport_type == "Sea" else checkbox,
                ],
               # Row 7
               ["",
                "",
                "",
                Paragraph("%s / %s" % (B("REGISTRATION No."),
                                       I("No. immatriculation"),
                                       ), style_center),
                "",
                "",
                Paragraph(record.registration_no or "", style_center),
                "",
                "",
                "",
                "",
                "",
                Paragraph(str(B("HAND")), style_8_center),
                checked if transport_type == "Hand" else checkbox,
                ],
               spacer,
               # Row 9
               [Paragraph("ITEM DESCRIPTION", style_7_center),
                Paragraph("DONOR", style_7_center),
                "",
                Paragraph("N° OF UNITS", style_7_center),
                Paragraph("%s/<br/>%s" % ("UNIT TYPE",
                                          "WEIGHT",
                                          ), style_7_center),
                Paragraph("%s<br/>%s" % ("WEIGHT",
                                         "(kg)",
                                         ), style_7_center),
                Paragraph("%s<br/>%s" % ("VOLUME",
                                         "(m3)",
                                         ), style_7_center),
                Paragraph("REQUISITION N°", style_7_center),
                "",
                "",
                Paragraph("REMARKS", style_7_center),
                "",
                "",
                "",
                ],
               ]
    cappend = content.append

    rowHeights = [1.30 * cm,
                  1.03 * cm,
                  0.87 * cm,
                  0.87 * cm,
                  0.64 * cm,
                  0.64 * cm,
                  0.64 * cm,
                  0.64 * cm,
                  0.21 * cm,
                  1.06 * cm,
                  ]
    rappend = rowHeights.append

    # Received Items
    ttable = s3db.inv_track_item
    rtable = s3db.inv_req
    ritable = s3db.inv_req_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    query = (ttable.send_id == record.id) & \
            (ttable.item_id == itable.id) & \
            (ttable.item_pack_id == ptable.id)
    left = rtable.on((rtable.id == ritable.req_id) & \
                     (ritable.id == ttable.req_item_id)
                     )
    items = db(query).select(itable.code,
                             itable.name,
                             ttable.item_source_no,
                             ttable.quantity,
                             ptable.name,
                             ptable.quantity,
                             itable.weight,
                             itable.volume,
                             rtable.req_ref,
                             ttable.comments,
                             left = left,
                             )

    all_quantity = 0
    all_weight = 0
    #all_volume = 0
    rowNo = 10
    for row in items:
        item = row["supply_item"]
        pack = row["supply_item_pack"]
        track_item = row["inv_track_item"]
        quantity = track_item.quantity
        all_quantity += quantity
        pack_details = pack.name
        weight = item.weight
        if weight:
            pack_weight = weight * pack.quantity
            pack_details = "%s / %s" % (pack_details,
                                        round(pack_weight, 2),
                                        )
            total_weight = pack_weight * quantity
            all_weight += total_weight
            total_weight = round(total_weight, 2)
        else:
            total_weight = NONE
        volume = item.volume
        if volume:
            pack_volume = volume * pack.quantity
            total_volume = pack_volume * quantity
            #all_volume += total_volume
            total_volume = round(total_volume, 2)
        else:
            total_volume = NONE
        body_row = [Paragraph(s3_truncate(item.name, 30), style_6_center),
                    Paragraph(track_item.item_source_no or NONE, style_7_center),
                    "",
                    Paragraph(str(quantity), style_7_center),
                    Paragraph(pack_details, style_7_center),
                    Paragraph(str(total_weight), style_7_center),
                    Paragraph(str(total_volume), style_7_center),
                    Paragraph(row["inv_req.req_ref"] or NONE, style_7_center),
                    "",
                    "",
                    Paragraph(track_item.comments or NONE, style_7_center),
                    "",
                    "",
                    "",
                    ]
        rappend(0.64 * cm)
        table_style += [("SPAN", (1, rowNo), (2, rowNo)),
                        ("SPAN", (7, rowNo), (9, rowNo)),
                        ("SPAN", (10, rowNo), (13, rowNo)),
                        ]
        cappend(body_row)
        rowNo += 1

    rowHeights += [0.60 * cm,
                   0.64 * cm,
                   0.77 * cm,
                   0.71 * cm,
                   0.21 * cm,
                   0.61 * cm,
                   0.64 * cm,
                   0.64 * cm,
                   0.58 * cm,
                   0.64 * cm,
                   0.42 * cm,
                   ]

    table_style += [("SPAN", (0, rowNo), (2, rowNo)),
                    ("SPAN", (3, rowNo), (5, rowNo)),
                    ("SPAN", (6, rowNo), (13, rowNo)),
                    ("BACKGROUND", (0, rowNo), (13, rowNo), lightgrey),
                    ("SPAN", (0, rowNo + 1), (2, rowNo + 3)),
                    ("SPAN", (6, rowNo + 1), (13, rowNo + 3)),
                    ("SPAN", (3, rowNo + 2), (5, rowNo + 3)),
                    ("SPAN", (0, rowNo + 5), (1, rowNo + 5)),
                    ("SPAN", (3, rowNo + 5), (4, rowNo + 5)),
                    ("SPAN", (5, rowNo + 5), (6, rowNo + 5)),
                    ("SPAN", (7, rowNo + 5), (9, rowNo + 5)),
                    ("SPAN", (10, rowNo + 5), (11, rowNo + 5)),
                    ("SPAN", (12, rowNo + 5), (13, rowNo + 5)),
                    ("BACKGROUND", (0, rowNo + 5), (13, rowNo + 5), lightgrey),
                    ("SPAN", (0, rowNo + 6), (1, rowNo + 6)),
                    ("SPAN", (3, rowNo + 6), (4, rowNo + 6)),
                    ("SPAN", (5, rowNo + 6), (6, rowNo + 6)),
                    ("SPAN", (7, rowNo + 6), (9, rowNo + 6)),
                    ("SPAN", (10, rowNo + 6), (11, rowNo + 6)),
                    ("SPAN", (12, rowNo + 6), (13, rowNo + 6)),
                    ("SPAN", (0, rowNo + 7), (1, rowNo + 7)),
                    ("SPAN", (3, rowNo + 7), (4, rowNo + 7)),
                    ("SPAN", (5, rowNo + 7), (6, rowNo + 7)),
                    ("SPAN", (7, rowNo + 7), (9, rowNo + 7)),
                    ("SPAN", (10, rowNo + 7), (11, rowNo + 7)),
                    ("SPAN", (12, rowNo + 7), (13, rowNo + 7)),
                    ("SPAN", (0, rowNo + 8), (1, rowNo + 8)),
                    ("SPAN", (3, rowNo + 8), (4, rowNo + 8)),
                    ("SPAN", (5, rowNo + 8), (6, rowNo + 8)),
                    ("SPAN", (7, rowNo + 8), (9, rowNo + 8)),
                    ("SPAN", (10, rowNo + 8), (11, rowNo + 8)),
                    ("SPAN", (12, rowNo + 8), (13, rowNo + 8)),
                    ("BACKGROUND", (0, rowNo + 8), (13, rowNo + 8), lightgrey),
                    ("SPAN", (0, rowNo + 9), (1, rowNo + 9)),
                    ("SPAN", (3, rowNo + 9), (4, rowNo + 9)),
                    ("SPAN", (5, rowNo + 9), (6, rowNo + 9)),
                    ("SPAN", (7, rowNo + 9), (9, rowNo + 9)),
                    ("SPAN", (10, rowNo + 9), (11, rowNo + 9)),
                    ("SPAN", (12, rowNo + 9), (13, rowNo + 9)),
                    ("SPAN", (0, rowNo + 10), (13, rowNo + 10)),
                    ]

    content += [[Paragraph("%s / %s" % (B("COMMENTS"),
                                        I("Commentaires"),
                                        ), style_8_center),
                 "",
                 "",
                 Paragraph(str(B("TOTAL")), style_8_center),
                 "",
                 "",
                 Paragraph("%s / %s" % (B("COMMENTS FROM RECEIVER"),
                                        I("Commentaires du réceptionniste"),
                                        ), style_8_center),
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 ],
                [Paragraph(record.comments or "", style_8_center),
                 "",
                 "",
                 Paragraph(str(B(round(all_quantity, 2))), style_8_center),
                 "",
                 Paragraph(str(B(round(all_weight, 2))), style_8_center),
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 ],
                spacer,
                spacer,
                spacer,
                [Paragraph(str(B("COMMODITIES LOADED")), style_8),
                 "",
                 Paragraph(str(B("DATE")), style_8_center),
                 Paragraph(str(B("FUNCTION")), style_8_center),
                 "",
                 Paragraph(str(B("NAME")), style_8_center),
                 "",
                 Paragraph(str(B("SIGNATURE")), style_8_center),
                 "",
                 "",
                 Paragraph(str(B("LOCATION (SITE)")), style_8_center),
                 "",
                 Paragraph(str(B("CONDITION")), style_8_center),
                 "",
                 ],
                [Paragraph("%s / %s" % (B("LOADED BY"),
                                        I("Chargé par"),
                                        ), style_8),
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 ],
                [Paragraph("%s / %s" % (B("TRANSPORTED BY"),
                                        I("transporté par (1)"),
                                        ), style_8),
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 ],
                [Paragraph(str(B("RECEPTION")), style_8),
                 "",
                 Paragraph(str(B("DATE")), style_8_center),
                 Paragraph(str(B("FUNCTION")), style_8_center),
                 "",
                 Paragraph(str(B("NAME")), style_8_center),
                 "",
                 Paragraph(str(B("SIGNATURE")), style_8_center),
                 "",
                 "",
                 Paragraph(str(B("LOCATION (SITE)")), style_8_center),
                 "",
                 Paragraph(str(B("CONDITION")), style_8_center),
                 "",
                 ],
                [Paragraph("%s / %s" % (B("RECEIVED BY"),
                                        I("Reçu par"),
                                        ), style_8),
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 ],
                [Paragraph(str(B("Please write in capital letters")), style_7_center),
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 ],
                ]

    table = Table(content,
                  colWidths = (4.04 * cm, # A
                               2.79 * cm, # B
                               2.16 * cm, # C
                               2.58 * cm, # D
                               2.14 * cm, # E
                               2.03 * cm, # F
                               2.03 * cm, # G
                               2.03 * cm, # H
                               0.39 * cm, # I
                               1.07 * cm, # J
                               1.88 * cm, # K
                               1.56 * cm, # L
                               1.33 * cm, # M
                               1.56 * cm, # N
                               ),
                  rowHeights = rowHeights,
                  style = table_style,
                  hAlign = "LEFT",   # defaults to "CENTER"
                  vAlign = "MIDDLE", # defaults to "MIDDLE", but better to specify
                  )

    doc.build([table],
              canvasmaker = canvas.Canvas, # S3NumberedCanvas
              )

    # Return the generated PDF
    response = current.response
    if response:
        filename = "%s.pdf" % send_ref
        if "uwsgi_scheme" in current.request.env:
            # Running uwsgi then we can't have unicode filenames
            # Accent Folding
            def string_escape(s):
                import unicodedata
                return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("utf-8")
            filename = string_escape(filename)
        disposition = 'attachment; filename="%s"' % filename
        response.headers["Content-Type"] = contenttype(".pdf")
        response.headers["Content-disposition"] = disposition

    return output.getvalue()

# =============================================================================
def grn_S3html2pdf(r, **attr):
    """
        GRN (Goods Received Note) for French Red Cross (& current default)

        Using S3html2pdf to convert gluon.html TABLE

        @param r: the S3Request instance
        @param attr: controller attributes
    """

    # Not translated (has both English & French elements within)
    #T = current.T
    db = current.db
    s3db = current.s3db

    # Master record
    table = s3db.inv_recv
    record = r.record
    recv_ref = record.recv_ref
    from_site_id = record.from_site_id
    if from_site_id:
        received_from = table.from_site_id.represent(from_site_id)
    else:
        received_from = table.organisation_id.represent(record.organisation_id)

    # Get organisation logo
    stable = s3db.org_site
    site = db(stable.site_id == record.site_id).select(stable.organisation_id,
                                                       limitby = (0, 1),
                                                       ).first()
    organisation_id = site.organisation_id

    otable = s3db.org_organisation
    org = db(otable.id == organisation_id).select(otable.logo,
                                                  otable.root_organisation,
                                                  limitby = (0, 1),
                                                  ).first()
    logo = org.logo
    if not logo:
        root_organisation = org.root_organisation
        if organisation_id != root_organisation:
            org = db(otable.id == root_organisation).select(otable.logo,
                                                            limitby = (0, 1),
                                                            ).first()
            logo = org.logo

    if logo:
        logo = URL(c="default", f="download",
                   args = logo,
                   )
    else:
        # Use default IFRC
        logo = "/%s/static/themes/RMS/img/logo_small.png" % r.application

    # Received Items
    ttable = s3db.inv_track_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    query = (ttable.recv_id == record.id) & \
            (ttable.item_id == itable.id) & \
            (ttable.item_pack_id == ptable.id)
    items = db(query).select(itable.code,
                             itable.name,
                             ttable.item_source_no,
                             ttable.recv_quantity,
                             ptable.name,
                             ptable.quantity,
                             itable.weight,
                             )

    body = TABLE()
    bappend = body.append

    for row in items:
        item = row["supply_item"]
        pack = row["supply_item_pack"]
        track_item = row["inv_track_item"]
        quantity = track_item.recv_quantity
        pack_details = pack.name
        weight = item.weight
        if weight:
            pack_weight = weight * pack.quantity
            pack_details = "%s / %s" % (pack_details,
                                        round(pack_weight, 2),
                                        )
            total_weight = round(pack_weight * quantity, 2)
        else:
            total_weight = NONE
        body_row = TR(TD(item.code or NONE),
                      TD(item.name),
                      TD(track_item.item_source_no or NONE),
                      TD(quantity),
                      TD(pack_details),
                      TD(total_weight),
                      )
        bappend(body_row)

    #styles = {}

    def pdf_header(r):
        return DIV(TABLE(TR(TD(IMG(_src = logo,
                                   _height = 50,
                                   ),
                               _colspan = 6,
                               ),
                            TH("COUNTRY CODE",
                               _align = "center",
                               _valign = "middle",
                               ),
                            TH("GRN NUMBER",
                               _align = "center",
                               _valign = "middle",
                               _colspan = 2,
                               ),
                            ),
                         TR(TD(B("GOODS RECEIVED NOTE"),
                               I(" / %s" % "Accusé de Réception"),
                               _align = "center",
                               _colspan = 6,
                               ),
                            TD(""), # @ToDo: Country Code?
                            TD(B(recv_ref),
                               _align = "center",
                               _colspan = 2,
                               ),
                            ),
                         TR(TH("%s\n(%s)" % ("DELEGATION/CONSIGNEE",
                                             "LOCATION",
                                             ),
                               _align = "right",
                               _colspan = 2,
                               ),
                            TD("", # @ToDo: Recipient NS
                               _align = "center",
                               _colspan = 2,
                               ),
                            TH("RECEIVED FROM",
                               I(" / %s" % "reçu de"),
                               _align = "center",
                               _colspan = 3,
                               ),
                            TD(received_from,
                               _align = "center",
                               _colspan = 2,
                               ),
                            ),
                         TR(TD("",
                               _colspan = 9,
                               ),
                            ),
                         TR(TH("DATE OF ARRIVAL",
                               I("\n%s" % "Date de réception"),
                               _align = "right",
                               ),
                            TD(table.date.represent(record.date),
                               _align = "center",
                               ),
                            TH("DOCUMENT WELL RECEIVED",
                               _align = "center",
                               _colspan = 2,
                               ),
                            TD("", # Leave Blank?
                               ),
                            TH("IF NO, PLEASE SPECIFY",
                               _align = "center",
                               _colspan = 2,
                               ),
                            TD("", # Leave Blank?
                               _colspan = 2,
                               ),
                            ),
                         TR(TD("",
                               _colspan = 9,
                               ),
                            ),
                         TR(TH("MEANS OF TRANSPORT",
                               I("\n%s" % "Moyen de transport"),
                               _align = "center",
                               ),
                            TH("ROAD",
                               "\n",
                               "AIR",
                               "\n",
                               "SEA",
                               "\n",
                               "Handcarried",
                               _align = "right",
                               ),
                            # @ToDo Checkboxes
                            TD(TABLE(TR(TD("")),
                                     TR(TD("")),
                                     TR(TD("")),
                                     TR(TD("")),
                                     ),
                               ),
                            TD(TABLE(TR(TD("AWB no:")),
                                     TR(TD("Waybill n°/ CMR n°:")),
                                     TR(TD("B/L n°:")),
                                     TR(TD("Waybill No.:")),
                                     ),
                               _colspan = 2,
                               ),
                            TD(TABLE(TR(TH("FLIGHT N°:"),
                                        TD(""),
                                        ),
                                     TR(TH("REGISTRATION N°:"),
                                        TD(""),
                                        ),
                                     TR(TH("VESSEL:"),
                                        TD(""),
                                        ),
                                     ),
                               _colspan = 4,
                               ),
                            ),
                         ))

    def pdf_body(r):
        #TABLE(TR(TH("GOODS RECEIVED",
                                   #      I("/ %s" % "Marchandises reçues"),
                                   #      _colpsan = 3,
                                   #      ),
                                   #   TH("FOR FOOD INDICATE NET WEIGHT",
                                   #      _colpsan = 3,
                                   #      ),
                                   #   ),
        body.insert(0, TR(TH("ITEMS CODE",
                             "\n",
                             I("Description générale et remarques"),
                             ),
                          TH("DESCRIPTION",
                             "\n",
                             I("Code article"),
                             ),
                          TH("COMMODITY TRACKING N° OR DONOR",
                             ),
                          TH("NB. OF UNITS",
                             "\n",
                             I("nb. colis"),
                             ),
                          TH("UNIT TYPE/WEIGHT",
                             "\n",
                             I("type d'unité/poids"),
                             ),
                          TH("WEIGHT (kg)",
                             "\n",
                             I("Total (kg)"),
                             ),
                          TH(B("RECEIVED ACCORDING TO DOCUMENT AND RECEIVED IN GOOD CONDITIONS"),
                             I("\n%s" % "Reçu selon documents et en bonne condition"),
                             ),
                          TH(B("CLAIM"),
                             I("\n%s" % "Réclamation"),
                             ),
                          ),
                    )

        bappend(TR(TD(B("COMMENTS"),
                      I(" / %s" % "Observations"),
                      _colspan = 8,
                      ),
                   ))
        bappend(TR(TD("\n\n\n\n",
                      _colspan = 8,
                      ),
                   ))
        bappend(TR(TD("",
                      _colspan = 8,
                      ),
                   ))

        return DIV(body)

    def pdf_footer(r):
        return DIV(TABLE(TR(TH("DELIVERED BY",
                               _align = "center",
                               ),
                            TH("DATE",
                               _align = "center",
                               ),
                            TH("FUNCTION",
                               _align = "center",
                               _colspan = 2,
                               ),
                            TH("%s (%s)" % ("NAME",
                                            "IN BLOCK LETTER",
                                            ),
                               _align = "center",
                               _colspan = 3,
                               ),
                            TH("SIGNATURE",
                               _align = "center",
                               _colspan = 2,
                               ),
                            ),
                         TR(TD(""),
                            TD(""),
                            TD("",
                               _colspan = 2,
                               ),
                            TD("",
                               _colspan = 3,
                               ),
                            TD("",
                               _colspan = 2,
                               ),
                            ),
                         TR(TH("RECEIVED BY",
                               _align = "center",
                               ),
                            TH("DATE",
                               _align = "center",
                               ),
                            TH("FUNCTION",
                               _align = "center",
                               _colspan = 2,
                               ),
                            TH("%s (%s)" % ("NAME",
                                            "IN BLOCK LETTER",
                                            ),
                               _align = "center",
                               _colspan = 3,
                               ),
                            TH("SIGNATURE / STAMP",
                               _align = "center",
                               _colspan = 2,
                               ),
                            ),
                         TR(TD(""),
                            TD(""),
                            TD("",
                               _colspan = 2,
                               ),
                            TD("",
                               _colspan = 3,
                               ),
                            TD("",
                               _colspan = 2,
                               ),
                            ),
                         ))

    exporter = S3Exporter().pdf
    return exporter(r.resource,
                    request = r,
                    pdf_title = current.deployment_settings.get_inv_recv_form_name(),
                    pdf_filename = recv_ref,
                    pdf_header = pdf_header,
                    pdf_header_padding = 12,
                    #method = "list",
                    #pdf_componentname = "track_item",
                    #list_fields = list_fields,
                    pdf_callback = pdf_body,
                    pdf_footer = pdf_footer,
                    pdf_hide_comments = True,
                    #pdf_html_styles = styles,
                    pdf_table_autogrow = "B",
                    pdf_orientation = "Landscape",
                    **attr
                    )

# =============================================================================
def grn_hnrc(r, **attr):
    """
        GRN (Goods Received Note) for HNRC: Honduran Red Cross

        @param r: the S3Request instance
        @param attr: controller attributes
    """

    T = current.T

    # Master record (=inv_recv)
    resource = current.s3db.resource(r.tablename,
                                     id = r.id,
                                     components = ["track_item"],
                                     )

    # Columns and data for the form header
    header_fields = ["eta",
                     "date",
                     (T("Origin"), "from_site_id"),
                     (T("Destination"), "site_id"),
                     "sender_id",
                     "recipient_id",
                     "send_ref",
                     "recv_ref",
                     "comments",
                     ]

    header_data = resource.select(header_fields,
                                  start = 0,
                                  limit = 1,
                                  represent = True,
                                  show_links = False,
                                  raw_data = True,
                                  )
    if not header_data:
        r.error(404, current.ERROR.BAD_RECORD)

    # Generate PDF header
    row = header_data.rows[0]
    labels = {rfield.colname: rfield.label for rfield in header_data.rfields}
    def row_(left, right):
        return header_row_(left, right, row=row, labels=labels)

    # Get organisation name and logo
    name, logo = OM().render()

    # The title
    title = H2(T("Goods Received Note"))

    # GRN details
    dtable = TABLE(TR(TD(DIV(logo,
                             H4(name),
                             ),
                         _colspan = 2,
                         ),
                      TD(DIV(title),
                         _colspan = 2,
                         ),
                      ),
                   row_("inv_recv.eta", "inv_recv.date"),
                   row_("inv_recv.from_site_id", "inv_recv.site_id"),
                   row_("inv_recv.sender_id", "inv_recv.recipient_id"),
                   row_("inv_recv.send_ref", "inv_recv.recv_ref"),
                   )

    # GRN comments
    ctable = TABLE(TR(TH(T("Comments"))),
                   TR(TD(row["inv_recv.comments"])),
                   )

    pdf_header = DIV(dtable,
                     P("&nbsp;"),
                     ctable,
                     )

    # Filename from send_ref
    header_row = header_data.rows[0]
    pdf_filename = header_row["_row"]["inv_recv.recv_ref"]

    # Component (=inv_track_item)
    component = resource.components["track_item"]
    body_fields = ["item_id",
                   "item_pack_id",
                   "recv_quantity",
                   (T("Total Volume (m3)"), "total_recv_volume"),
                   (T("Total Weight (kg)"), "total_recv_weight"),
                   "supply_org_id",
                   "inv_item_status",
                   ]
    # Any extra fields needed for virtual fields
    component.configure(extra_fields = ["item_id$weight",
                                        "item_id$volume",
                                        ],
                        )

    # Aggregate methods and column names
    aggregate = [("sum", "inv_track_item.recv_quantity"),
                 ("sum", "inv_track_item.total_recv_volume"),
                 ("sum", "inv_track_item.total_recv_weight"),
                 ]

    # Generate the JSON data dict
    json_data = json_data_(component,
                           body_fields,
                           aggregate = aggregate,
                           )

    # Generate the grouped items table
    from s3 import S3GroupedItemsTable
    output = S3GroupedItemsTable(component,
                                 data = json_data,
                                 totals_label = T("Total"),
                                 title = T("Goods Received Note"),
                                 pdf_header = pdf_header,
                                 pdf_footer = grn_hnrc_footer,
                                 )

    # ...and export it as PDF
    return output.pdf(r, filename=pdf_filename)

# -----------------------------------------------------------------------------
def grn_hnrc_footer(r):
    """
        Footer for Goods Received Notes for HNRC: Honduran Red Cross

        @param r: the S3Request
    """

    T = current.T

    return TABLE(TR(TH(T("Delivered by")),
                    TH(T("Date")),
                    TH(T("Function")),
                    TH(T("Name")),
                    TH(T("Signature")),
                    TH(T("Status")),
                    ),
                 TR(TD(T("&nbsp;"))),
                 TR(TH(T("Received by")),
                    TH(T("Date")),
                    TH(T("Function")),
                    TH(T("Name")),
                    TH(T("Signature")),
                    TH(T("Status")),
                    ),
                 TR(TD("&nbsp;")),
                 )

# =============================================================================
def waybill_hnrc(r, **attr):
    """
        Waybill for HNRC

        @param r: the S3Request instance
        @param attr: controller attributes
    """

    T = current.T
    s3db = current.s3db

    # Component declarations to distinguish between the
    # origin and destination warehouses
    s3db.add_components("inv_send",
                        inv_warehouse = ({"name": "origin",
                                          "joinby": "site_id",
                                          "pkey": "site_id",
                                          "filterby": False,
                                          "multiple": False,
                                          },
                                         {"name": "destination",
                                          "joinby": "site_id",
                                          "pkey": "to_site_id",
                                          "filterby": False,
                                          "multiple": False,
                                          },
                                         ),
                        )

    # Master record (=inv_send)
    resource = s3db.resource(r.tablename,
                             id = r.id,
                             components = ["origin",
                                           "destination",
                                           "track_item",
                                           ],
                             )

    # Columns and data for the form header
    header_fields = ["send_ref",
                     # @ToDo: Will ned updating to use inv_send_req
                     #"req_ref",
                     "date",
                     "delivery_date",
                     (T("Origin"), "site_id"),
                     (T("Destination"), "to_site_id"),
                     "sender_id",
                     "origin.contact",
                     "recipient_id",
                     "destination.contact",
                     "transported_by",
                     "transport_ref",
                     (T("Delivery Address"), "destination.location_id"),
                     "comments",
                     ]

    header_data = resource.select(header_fields,
                                  start = 0,
                                  limit = 1,
                                  represent = True,
                                  show_links = False,
                                  raw_data = True,
                                  )
    if not header_data:
        r.error(404, current.ERROR.BAD_RECORD)

    # Generate PDF header
    row = header_data.rows[0]
    labels = {rfield.colname: rfield.label for rfield in header_data.rfields}
    def row_(left, right):
        return header_row_(left, right, row=row, labels=labels)

    # Get organisation name and logo
    name, logo = OM().render()

    # The title
    title = H2(T("Waybill"))

    # Waybill details
    dtable = TABLE(TR(TD(DIV(logo,
                             H4(name),
                             ),
                         _colspan = 2,
                         ),
                      TD(DIV(title),
                         _colspan = 2,
                         ),
                      ),
                   # @ToDo: Will ned updating to use inv_send_req
                   row_("inv_send.send_ref", None
                        #"inv_send.req_ref",
                        ),
                   row_("inv_send.date", "inv_send.delivery_date"),
                   row_("inv_send.site_id", "inv_send.to_site_id"),
                   row_("inv_send.sender_id", "inv_send.recipient_id"),
                   row_("inv_origin_warehouse.contact",
                        "inv_destination_warehouse.contact",
                        ),
                   row_("inv_send.transported_by", "inv_send.transport_ref"),
                   row_("inv_destination_warehouse.location_id", None),
                   )

    # Waybill comments
    ctable = TABLE(TR(TH(T("Comments"))),
                   TR(TD(row["inv_send.comments"])),
                   )

    pdf_header = DIV(dtable,
                     P("&nbsp;"),
                     ctable,
                     )

    # Filename from send_ref
    header_row = header_data.rows[0]
    pdf_filename = header_row["_row"]["inv_send.send_ref"]

    # Component (=inv_track_item)
    component = resource.components["track_item"]
    body_fields = ["item_id",
                   "item_pack_id",
                   "quantity",
                   (T("Total Volume (m3)"), "total_volume"),
                   (T("Total Weight (kg)"), "total_weight"),
                   "supply_org_id",
                   "inv_item_status",
                   ]
    # Any extra fields needed for virtual fields
    component.configure(extra_fields = ["item_id$weight",
                                        "item_id$volume",
                                        ],
                        )

    # Aggregate methods and column names
    aggregate = [("sum", "inv_track_item.quantity"),
                 ("sum", "inv_track_item.total_volume"),
                 ("sum", "inv_track_item.total_weight"),
                 ]

    # Generate the JSON data dict
    json_data = json_data_(component,
                           body_fields,
                           aggregate = aggregate,
                           )

    # Generate the grouped items table
    output = S3GroupedItemsTable(component,
                                 data = json_data,
                                 totals_label = T("Total"),
                                 title = T("Waybill"),
                                 pdf_header = pdf_header,
                                 pdf_footer = waybill_hnrc_footer,
                                 )

    # ...and export it as PDF
    return output.pdf(r, filename=pdf_filename)

# -----------------------------------------------------------------------------
def waybill_hnrc_footer(r):
    """
        Footer for Waybills for HNRC

        @param r: the S3Request
    """

    T = current.T

    return TABLE(TR(TH(T("Shipment")),
                    TH(T("Date")),
                    TH(T("Function")),
                    TH(T("Name")),
                    TH(T("Signature")),
                    TH(T("Status")),
                    ),
                 TR(TD(T("Sent by"))),
                 TR(TD(T("Transported by"))),
                 TR(TH(T("Received by")),
                    TH(T("Date")),
                    TH(T("Function")),
                    TH(T("Name")),
                    TH(T("Signature")),
                    TH(T("Status")),
                    ),
                 TR(TD("&nbsp;")),
                 )

# END =========================================================================
