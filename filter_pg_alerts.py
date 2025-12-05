def filter_critical_or_error_alerts(data):
    filtered_rules = []

    for group in data.get("data", {}).get("groups", []):
        critical_rules = [
            rule
            for rule in group.get("rules", [])
            if rule.get("labels", {}).get("severity") in ("critical", "error")
        ]
        if critical_rules:
            filtered_rules.append({"name": group.get("name"), "rules": critical_rules})

    return filtered_rules


import json

# Assuming `alert_data` contains your JSON object
with open("alerts.json") as f:
    alert_data = json.load(f)

filtered = filter_critical_or_error_alerts(alert_data)
print(json.dumps(filtered, indent=2))
