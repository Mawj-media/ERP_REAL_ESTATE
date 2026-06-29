from __future__ import annotations

import json

import frappe

import uuid


def update_real_estate_workspace():
    workspace_name = "Real Estate"
    if not frappe.db.exists("Workspace", workspace_name):
        return

    workspace = frappe.get_doc("Workspace", workspace_name)

    _add_number_cards(workspace)
    _add_charts(workspace)
    _update_content(workspace)

    workspace.save(ignore_permissions=True)


def _add_number_cards(workspace):
    cards_config = [
        {"card_name": "Total Units", "label": "Total Units", "width": 3},
        {"card_name": "Available Units", "label": "Available Units", "width": 3},
        {"card_name": "Active Bookings", "label": "Active Bookings", "width": 3},
        {"card_name": "Total Booked Value", "label": "Total Booked Value", "width": 3},
    ]

    existing = {nc.card_name for nc in workspace.number_cards}
    for card in cards_config:
        if card["card_name"] not in existing:
            workspace.append("number_cards", {
                "card_name": card["card_name"],
                "label": card["label"],
                "width": card["width"],
            })


def _add_charts(workspace):
    charts_config = [
        {"chart_name": "Booking Trends", "label": "Booking Trends", "width": "Full"},
        {"chart_name": "Units by Status", "label": "Units by Status", "width": "Half"},
        {"chart_name": "Project Revenue", "label": "Project Revenue", "width": "Half"},
    ]

    existing = {c.chart_name for c in workspace.charts}
    for chart in charts_config:
        if chart["chart_name"] not in existing:
            workspace.append("charts", {
                "chart_name": chart["chart_name"],
                "label": chart["label"],
                "width": chart["width"],
            })


def _update_content(workspace):
    if not workspace.content:
        return

    content = json.loads(workspace.content)

    has_dashboard_blocks = any(
        block["type"] in ("number_card", "chart")
        for block in content
    )
    if has_dashboard_blocks:
        return

    number_card_blocks = [
        {
            "id": str(uuid.uuid4())[:11],
            "type": "number_card",
            "data": {"number_card_name": name, "col": 3},
        }
        for name in ["Total Units", "Available Units", "Active Bookings", "Total Booked Value"]
    ]
    chart_blocks = [
        {
            "id": str(uuid.uuid4())[:11],
            "type": "chart",
            "data": {"chart_name": "Booking Trends", "col": 12},
        },
        {
            "id": str(uuid.uuid4())[:11],
            "type": "chart",
            "data": {"chart_name": "Units by Status", "col": 6},
        },
        {
            "id": str(uuid.uuid4())[:11],
            "type": "chart",
            "data": {"chart_name": "Project Revenue", "col": 6},
        },
    ]

    spacer = {
        "id": str(uuid.uuid4())[:11],
        "type": "spacer",
        "data": {"col": 12},
    }

    insert_index = 0
    for i, block in enumerate(content):
        if block["type"] == "card":
            insert_index = i
            break

    dashboard_blocks = number_card_blocks + chart_blocks + [spacer]
    content[insert_index:insert_index] = dashboard_blocks

    workspace.content = json.dumps(content)
