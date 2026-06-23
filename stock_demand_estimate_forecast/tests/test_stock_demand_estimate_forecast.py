# Copyright 2026 Ledo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestStockDemandEstimateForecast(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({"name": "Forecast Product"})
        cls.location = cls.env.ref("stock.stock_location_stock")
        cls.Forecast = cls.env["stock.demand.estimate.forecast"]

    def _make(self, qty=100.0, date_from="2026-01-01", date_to="2026-01-31"):
        return self.Forecast.create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "product_uom_qty": qty,
                "date_from": date_from,
                "date_to": date_to,
            }
        )

    def test_generate_creates_estimate(self):
        forecast = self._make()
        self.assertFalse(forecast.generated)

        forecast.action_generate_estimate()

        self.assertTrue(forecast.generated)
        estimate = forecast.estimate_id
        self.assertEqual(estimate.product_id, self.product)
        self.assertEqual(estimate.location_id, self.location)
        self.assertEqual(estimate.manual_date_from, date(2026, 1, 1))
        self.assertEqual(estimate.manual_date_to, date(2026, 1, 31))
        self.assertAlmostEqual(estimate.product_uom_qty, 100.0)
        # The contract ddmrp's future-ADU relies on: full-window overlap returns
        # the full quantity.
        self.assertAlmostEqual(
            estimate.get_quantity_by_date_range(date(2026, 1, 1), date(2026, 1, 31)),
            100.0,
            places=2,
        )

    def test_regenerate_updates_not_duplicates(self):
        forecast = self._make(qty=100.0)
        forecast.action_generate_estimate()
        estimate_id = forecast.estimate_id.id

        forecast.write({"product_uom_qty": 250.0})
        forecast.action_generate_estimate()

        self.assertEqual(forecast.estimate_id.id, estimate_id)
        self.assertAlmostEqual(forecast.estimate_id.product_uom_qty, 250.0)

    def test_update_or_create_is_idempotent(self):
        vals = {
            "product_id": self.product.id,
            "location_id": self.location.id,
            "product_uom_qty": 50.0,
            "date_from": "2026-02-01",
            "date_to": "2026-02-28",
        }
        first_id = self.Forecast.update_or_create_forecast(vals)
        self.assertTrue(self.Forecast.browse(first_id).estimate_id)

        second_id = self.Forecast.update_or_create_forecast(
            dict(vals, product_uom_qty=75.0)
        )

        self.assertEqual(first_id, second_id)
        self.assertEqual(
            self.Forecast.search_count([("product_id", "=", self.product.id)]), 1
        )
        self.assertAlmostEqual(
            self.Forecast.browse(second_id).estimate_id.product_uom_qty, 75.0
        )

    def test_unlink_removes_estimate(self):
        forecast = self._make()
        forecast.action_generate_estimate()
        estimate = forecast.estimate_id

        forecast.unlink()

        self.assertFalse(estimate.exists())

    def test_end_date_before_start_date_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._make(date_from="2026-03-31", date_to="2026-03-01")
