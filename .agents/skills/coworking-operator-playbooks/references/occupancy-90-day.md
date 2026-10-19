# 90-day occupancy

Question: "What is going to be vacant, and what do we need to sell?"

## Order

1. `coworking-occupancy-revenue-dashboard` for today's three occupancy numbers.
2. `coworking-occupancy-forecast` for contracted occupancy at 30/60/90/180 days.
3. `coworking-renewal-expansion-risk` for agreements ending inside the window.
4. `coworking-cancellation-to-virtual-office` only for notices already given, as a save path, not as occupancy.
5. State the sales gap: vacant sellable offices and workstations at each horizon, from the forecast, not from a pipeline guess.

## Minimum files

Inventory and memberships, including end dates and notice dates. Signed future move-ins if the forecast skill has a field for them. Deals are a scenario layer and stay labeled scenario.

## Stop rules

Notice date is not end date. One office is not one workstation. Out-of-service units are not available to sell. Do not add unsigned pipeline into contracted occupancy.
