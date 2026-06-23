From an external forecasting engine, push forecast points and generate the
estimates in one idempotent call per product / location / period:

```python
env["stock.demand.estimate.forecast"].update_or_create_forecast({
    "product_id": product.id,
    "location_id": location.id,
    "date_from": "2026-01-01",
    "date_to": "2026-01-31",
    "product_uom_qty": 1200.0,
})
```

This creates (or refreshes) a forecast record and its linked
`stock.demand.estimate`.

Manually, go to *Inventory > Demand Planning > Demand Estimate Forecasts*,
create forecast lines, and use the **Generate Estimate(s)** button to
materialise the demand estimates.

The generated estimates are then picked up by any consumer of
`stock.demand.estimate`, such as the `ddmrp` future-looking ADU calculation
(set the buffer's ADU method to *future* / *blended* with source *estimates*).
