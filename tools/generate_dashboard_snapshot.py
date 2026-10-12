#!/usr/bin/env python3
import json

try:
    with open("metrics.json") as f:
        m = json.load(f)
except Exception:
    m = None

parts = []
parts.append('<?xml version="1.0" encoding="UTF-8"?>')
parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300">')
parts.append('<style>text{font-family:Arial,Helvetica,sans-serif; fill:#1a1a1a} .title{font-size:20px; font-weight:700}</style>')
parts.append('<rect width="100%" height="100%" fill="#f7f7f9"/>')
parts.append('<text x="20" y="35" class="title">DORA 4 Metrics</text>')

if m:
    parts.append(f'<text x="30" y="75">Window: {m.get("window_days")} days</text>')
    parts.append(f'<text x="30" y="105">As of: {m.get("as_of")}</text>')
    parts.append(f'<text x="30" y="135">Deployment Frequency: {m.get("deployment_frequency_count")}</text>')
    cfr = m.get("change_failure_rate")
    parts.append(f'<text x="330" y="135">Change Failure Rate: {round(cfr * 100, 1) if cfr is not None else "N/A"}%</text>')
    mttr = m.get("mttr_seconds")
    parts.append(f'<text x="30" y="165">MTTR: {round(mttr / 60, 1) if mttr is not None else "N/A"} min</text>')
    lt = m.get("lead_time_for_changes_seconds")
    parts.append(f'<text x="330" y="165">Lead Time: {round(lt / 60, 1) if lt is not None else "N/A"} min</text>')
else:
    parts.append('<text x="30" y="80">No metrics.json found. Run the workflow first.</text>')

parts.append('<rect x="20" y="190" width="180" height="70" fill="#ffffff" stroke="#dfe3f0"/>')
parts.append('<text x="35" y="220">Deployment</text>')
parts.append('<text x="35" y="245">Frequency</text>')

parts.append('<rect x="230" y="190" width="180" height="70" fill="#ffffff" stroke="#dfe3f0"/>')
parts.append('<text x="245" y="220">Change</text>')
parts.append('<text x="245" y="245">Failure Rate</text>')

parts.append('<rect x="440" y="190" width="180" height="70" fill="#ffffff" stroke="#dfe3f0"/>')
parts.append('<text x="455" y="220">MTTR</text>')

parts.append('<rect x="650" y="190" width="180" height="70" fill="#ffffff" stroke="#dfe3f0"/>')
parts.append('<text x="665" y="220">Lead Time</text>')

parts.append('</svg>')
with open("assets/dora_dashboard_sample.svg", "w") as f:
    f.write("\n".join(parts))

print("Wrote assets/dora_dashboard_sample.svg")
