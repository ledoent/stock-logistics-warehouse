# Copyright 2026 Ledo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockDemandEstimateForecast(models.Model):
    """A forecast data point that materialises a stock.demand.estimate.

    This model is the source-agnostic feed: an external forecasting engine
    (statistical, ML, frePPLe, ...) creates one record per product / location /
    period through ``update_or_create_forecast`` and the module keeps the
    matching ``stock.demand.estimate`` in sync. Keeping forecast-driven
    estimates behind their own records means they can be regenerated or cleared
    without disturbing demand estimates entered by hand.
    """

    _name = "stock.demand.estimate.forecast"
    _description = "Forecast-driven Demand Estimate"
    _order = "date_from desc, product_id"

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
        ondelete="cascade",
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Location",
        required=True,
        ondelete="cascade",
    )
    product_uom = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure")
    product_uom_qty = fields.Float(
        string="Forecast Quantity", digits="Product Unit of Measure"
    )
    date_from = fields.Date(string="From", required=True)
    date_to = fields.Date(string="To", required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    estimate_id = fields.Many2one(
        comodel_name="stock.demand.estimate",
        string="Demand Estimate",
        readonly=True,
        ondelete="set null",
        help="Demand estimate generated from this forecast.",
    )
    generated = fields.Boolean(
        compute="_compute_generated",
        store=True,
        help="Whether the demand estimate has been generated.",
    )

    _unique_forecast = models.Constraint(
        "unique(product_id, location_id, date_from, date_to, company_id)",
        "A forecast already exists for this product, location and period.",
    )

    @api.depends("estimate_id")
    def _compute_generated(self):
        for rec in self:
            rec.generated = bool(rec.estimate_id)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(
                    self.env._("The end date must not be before the start date.")
                )

    def _prepare_demand_estimate_vals(self):
        self.ensure_one()
        return {
            "product_id": self.product_id.id,
            "location_id": self.location_id.id,
            "product_uom": (self.product_uom or self.product_id.uom_id).id,
            "product_uom_qty": self.product_uom_qty,
            "manual_date_from": self.date_from,
            "manual_date_to": self.date_to,
            "company_id": self.company_id.id,
        }

    def action_generate_estimate(self):
        """Create or refresh the linked demand estimate for each forecast."""
        Estimate = self.env["stock.demand.estimate"]
        for rec in self:
            vals = rec._prepare_demand_estimate_vals()
            if rec.estimate_id:
                rec.estimate_id.write(vals)
            else:
                rec.estimate_id = Estimate.create(vals)
        return True

    @api.model
    def update_or_create_forecast(self, vals):
        """Idempotent entry point for an external forecast engine.

        This is public on purpose: an external engine calls it over RPC (Odoo
        forbids remote calls to private ``_``-prefixed methods).

        ``vals`` must hold ``product_id``, ``location_id``, ``date_from``,
        ``date_to`` and ``product_uom_qty`` (``product_uom``/``company_id`` are
        optional). Re-pushing the same product/location/period updates the
        existing forecast and its estimate instead of creating duplicates.

        Returns the forecast record id (an int, so the result marshals over RPC).
        """
        company_id = vals.get("company_id") or self.env.company.id
        existing = self.search(
            [
                ("product_id", "=", vals["product_id"]),
                ("location_id", "=", vals["location_id"]),
                ("date_from", "=", vals["date_from"]),
                ("date_to", "=", vals["date_to"]),
                ("company_id", "=", company_id),
            ],
            limit=1,
        )
        if existing:
            existing.write(vals)
            forecast = existing
        else:
            forecast = self.create(vals)
        forecast.action_generate_estimate()
        return forecast.id

    def unlink(self):
        # The forecast owns its estimate — drop it alongside the forecast.
        estimates = self.estimate_id
        res = super().unlink()
        estimates.unlink()
        return res
