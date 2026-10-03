# RTT Tracking

Dash dashboard for tracking a return-to-throwing program from a throw-level CSV export.

Upload a CSV with `datetime`, `tag`, `ballWeight`, `ballVelocity`, `armSpeed`, `torque` columns to get:

- Metric-over-time chart (max/avg/peak velocity, arm speed, torque, velocity/torque)
- One Day Workload (ODW) with acute:chronic workload ratio
- Throw-by-throw velocity scatter, colored by ball weight
- Per-session summary table, filterable by date, drill, and ball

## Run

```
pip install -r requirements.txt
python RTTtracking.py
```

Open http://localhost:8051.
