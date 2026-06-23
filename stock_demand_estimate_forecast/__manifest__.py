# Copyright 2026 Ledo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Demand Estimate Forecast",
    "summary": "Generate demand estimates from an external demand forecast.",
    "version": "19.0.1.0.0",
    "author": "Ledo, Odoo Community Association (OCA)",
    "maintainers": ["dnplkndll"],
    "website": "https://github.com/OCA/stock-logistics-warehouse",
    "license": "AGPL-3",
    "category": "Warehouse",
    "development_status": "Beta",
    "depends": ["stock_demand_estimate"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_demand_estimate_forecast_views.xml",
    ],
    "installable": True,
}
