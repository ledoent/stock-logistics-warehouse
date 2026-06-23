This module turns an external demand **forecast** into
`stock.demand.estimate` records.

It adds a source-agnostic staging model, `stock.demand.estimate.forecast`:
an external forecasting engine (statistical, machine-learning, frePPLe, ...)
pushes one record per product / location / period, and the module keeps the
matching demand estimate in sync. Generation is idempotent — re-pushing a
forecast for the same product, location and period updates the existing
estimate instead of creating duplicates.

Because the output is a standard `stock.demand.estimate`, it is consumed by any
module that reads demand estimates — in particular the OCA `ddmrp` module's
future-looking ADU calculation.

Keeping forecast-driven estimates behind their own records means they can be
regenerated or cleared without disturbing demand estimates entered by hand.
