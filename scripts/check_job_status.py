#!/usr/bin/env python3
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
JOBS_FILE = ROOT / "jobs.json"

CLOSED_PATTERNS = [
    r"job (?:is )?no longer available",
    r"position (?:has been )?filled",
    r"no longer accepting applications",
    r"job posting (?:has )?expired",
    r"requisition (?:is )?closed",
    r"this job has been closed",
    r"job not found",
    r"page you are looking for (?:does not|doesn't) exist",
]

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def append_history(job, status, source, note):
    hist = job.setdefault("posting_status_history", [])
    last = hist[-1]["status"] if hist else None
    if last != status:
        hist.append({"at": utcnow(), "status": status, "source": source, "note": note})
        return True
    return False

def main():
    payload = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    jobs = payload["jobs"]
    changed = False
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DerrickJobTracker/1.0; +https://github.com/)",
        "Accept": "text/html,application/xhtml+xml"
    }

    for job in jobs:
        url = job.get("url")
        if not url or job.get("verification_status") == "EU ONLY":
            continue

        check_at = utcnow()
        job["last_http_check_at"] = check_at
        try:
            r = requests.get(url, headers=headers, timeout=22, allow_redirects=True)
            job["last_http_status"] = r.status_code
            body = (r.text or "")[:600000].lower()
            closed_phrase = next((p for p in CLOSED_PATTERNS if re.search(p, body, flags=re.I)), None)

            if r.status_code in (404, 410) or closed_phrase:
                prev = job.get("posting_status")
                job["auto_check_state"] = "DEFINITIVE_CLOSED_SIGNAL"
                job["posting_status"] = "LIKELY_FILLED"
                job["verification_status"] = "LIKELY FILLED"
                job["verification_color"] = "red"
                job["status_checked_at"] = check_at
                job["last_checked_iso"] = check_at
                job["status_check_source"] = "GitHub Action HTTP/content check"
                job["verification_note"] = f"Automated check found {'HTTP '+str(r.status_code) if r.status_code in (404,410) else 'closure language'}."
                if prev != job["posting_status"]:
                    changed = True
                changed |= append_history(job, "LIKELY_FILLED", job["status_check_source"], job["verification_note"])

            elif r.status_code == 200:
                # Do not auto-reopen a previously closed posting because many job boards return generic shells.
                if job.get("verification_status") == "LIKELY FILLED":
                    job["auto_check_state"] = "REVIEW_REOPEN"
                    job["status_checked_at"] = check_at
                    job["status_check_source"] = "GitHub Action HTTP/content check"
                    job["verification_note"] = "HTTP 200 without closure language; manual verification required before reopening."
                else:
                    job["auto_check_state"] = "OPEN_HTTP_OK"
                    job["posting_status"] = "OPEN_VERIFIED"
                    job["verification_status"] = "LIVE"
                    job["verification_color"] = "green"
                    job["status_checked_at"] = check_at
                    job["last_checked_iso"] = check_at
                    job["status_check_source"] = "GitHub Action HTTP/content check"
                    job["verification_note"] = "Automated HTTP/content check passed; no definitive closure signal found."
                changed = True
            elif r.status_code in (401,403,429,503):
                job["auto_check_state"] = f"BLOCKED_{r.status_code}"
                # Preserve existing status; only record check metadata.
                changed = True
            else:
                job["auto_check_state"] = f"HTTP_{r.status_code}_REVIEW"
                changed = True

        except Exception as e:
            job["auto_check_state"] = "CHECK_ERROR"
            job["last_http_error"] = str(e)[:500]
            job["last_http_check_at"] = check_at
            changed = True

        job["scheduler_last_run_at"] = check_at

    payload["meta"]["scheduler_last_run_at"] = utcnow()
    payload["meta"]["open_actionable"] = sum(j.get("verification_status") == "LIVE" for j in jobs)
    payload["meta"]["likely_filled"] = sum(j.get("verification_status") == "LIKELY FILLED" for j in jobs)
    payload["meta"]["non_actionable"] = sum(j.get("verification_status") == "EU ONLY" for j in jobs)
    JOBS_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Checked {len(jobs)} jobs; open={payload['meta']['open_actionable']} filled={payload['meta']['likely_filled']} non_actionable={payload['meta']['non_actionable']}")

if __name__ == "__main__":
    main()
