#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
WINDOW_DAYS = int(os.getenv("DORA_WINDOW_DAYS", "30"))
DEPLOY_ENV = os.getenv("DEPLOYMENT_ENVIRONMENT", "production")

if not GITHUB_TOKEN or not REPO:
    print("GITHUB_TOKEN and GITHUB_REPOSITORY must be set", file=sys.stderr)
    sys.exit(1)

OWNER, REPO_NAME = REPO.split("/", 1)
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "dora-metrics-action"
}
API_BASE = "https://api.github.com"


def paginate(url, params=None):
    results = []
    p = url
    params = params or {}
    while p:
        resp = requests.get(p, headers=HEADERS, params=params)
        if resp.status_code >= 400:
            print(f"HTTP {resp.status_code} when GET {p} -> {resp.text}", file=sys.stderr)
            break
        data = resp.json()
        if isinstance(data, list):
            results.extend(data)
        else:
            if 'items' in data:
                results.extend(data['items'])
            else:
                results.append(data)
        link = resp.headers.get("Link", "")
        next_url = None
        if link:
            parts = link.split(",")
            for part in parts:
                if 'rel="next"' in part:
                    next_url = part[part.find("<")+1:part.find(">")]
        p = next_url
        params = None
        time.sleep(0.1)
    return results


def parse_iso(s):
    if s is None:
        return None
    return dateparser.parse(s)


def iso_now_minus_days(days):
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.isoformat()


def get_deployments():
    url = f"{API_BASE}/repos/{OWNER}/{REPO_NAME}/deployments"
    return paginate(url, params={"per_page": 100})


def get_deployment_statuses(deployment_id):
    url = f"{API_BASE}/repos/{OWNER}/{REPO_NAME}/deployments/{deployment_id}/statuses"
    return paginate(url, params={"per_page": 100})


def list_merged_prs(since_iso):
    q = f"repo:{OWNER}/{REPO_NAME} is:pr is:merged merged:>={since_iso}"
    url = f"{API_BASE}/search/issues"
    items = paginate(url, params={"q": q, "per_page": 100})
    prs = []
    for it in items:
        number = it.get("number")
        pr_url = f"{API_BASE}/repos/{OWNER}/{REPO_NAME}/pulls/{number}"
        resp = requests.get(pr_url, headers=HEADERS)
        if resp.status_code == 200:
            pr = resp.json()
            if pr.get("merged_at"):
                prs.append(pr)
    return prs


def main():
    since_iso = iso_now_minus_days(WINDOW_DAYS)
    print(f"Collecting DORA metrics for repo {OWNER}/{REPO_NAME} since {since_iso} (last {WINDOW_DAYS} days)")

    deployments = get_deployments()
    filtered = []
    for d in deployments:
        env = (d.get("environment") or "").lower()
        created = parse_iso(d.get("created_at"))
        if env == DEPLOY_ENV.lower() and created and created >= parse_iso(since_iso):
            filtered.append(d)

    deployments_info = []
    for d in filtered:
        d_id = d.get("id")
        statuses = get_deployment_statuses(d_id)
        latest = None
        for s in statuses:
            if latest is None:
                latest = s
            else:
                if parse_iso(s.get("created_at")) and parse_iso(latest.get("created_at")):
                    if parse_iso(s.get("created_at")) > parse_iso(latest.get("created_at")):
                        latest = s
        deployments_info.append({
            "id": d_id,
            "sha": d.get("sha"),
            "ref": d.get("ref"),
            "creator": d.get("creator", {}).get("login"),
            "created_at": d.get("created_at"),
            "latest_status": latest
        })

    total_deploys = len(deployments_info)
    successful_deploys = [d for d in deployments_info if d.get("latest_status") and d["latest_status"].get("state") == "success"]
    failed_deploys = [d for d in deployments_info if d.get("latest_status") and d["latest_status"].get("state") in ("failure", "error")]
    deployment_frequency = len(successful_deploys)
    change_failure_rate = len(failed_deploys) / total_deploys if total_deploys > 0 else None

    mttr_list = []
    sorted_deps = sorted(deployments_info, key=lambda x: parse_iso(x.get("created_at") or "1970-01-01T00:00:00Z"))
    for i, d in enumerate(sorted_deps):
        state = (d.get("latest_status") or {}).get("state")
        if state in ("failure", "error"):
            this_time = parse_iso(d.get("created_at"))
            recovery = None
            for later in sorted_deps[i+1:]:
                if (later.get("latest_status") or {}).get("state") == "success":
                    recovery = parse_iso(later.get("created_at"))
                    break
            if recovery:
                delta = (recovery - this_time).total_seconds()
                if delta >= 0:
                    mttr_list.append(delta)
    mttr_seconds = sum(mttr_list) / len(mttr_list) if mttr_list else None

    merged_prs = list_merged_prs(since_iso)
    lead_list = []
    for pr in merged_prs:
        merged_at = parse_iso(pr.get("merged_at"))
        if not merged_at:
            continue
        candidate = None
        for d in sorted_deps:
            if (d.get("latest_status") or {}).get("state") == "success":
                dep_time = parse_iso(d.get("created_at"))
                if dep_time and dep_time >= merged_at:
                    candidate = dep_time
                    break
        if candidate:
            lead_list.append((candidate - merged_at).total_seconds())
    lead_time_seconds = sum(lead_list) / len(lead_list) if lead_list else None

    metrics = {
        "window_days": WINDOW_DAYS,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "deployment_count": total_deploys,
        "successful_deployments": len(successful_deploys),
        "failed_deployments": len(failed_deploys),
        "deployment_frequency_count": deployment_frequency,
        "change_failure_rate": change_failure_rate,
        "mttr_seconds": mttr_seconds,
        "lead_time_for_changes_seconds": lead_time_seconds
    }

    with open("metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    print("Wrote metrics.json")


if __name__ == "__main__":
    main()
