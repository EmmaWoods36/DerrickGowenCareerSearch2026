# Derrick Gowen Executive Opportunity Tracker

GitHub Pages-ready live tracker.

## Files
- `index.html` — executive dashboard and editable application/interview tracker.
- `jobs.json` — source-of-truth job records, scores, live-status audit fields, history, queue fields, and pipeline defaults.
- `updates.json` — optional source-controlled event log / update handoff.
- `scripts/check_job_status.py` — conservative automated posting checker.
- `.github/workflows/refresh-job-status.yml` — runs every 12 hours and commits updated job-status metadata.

## GitHub Pages
Publish the repository from the `main` branch / root. `index.html` polls `jobs.json` every 60 seconds with cache-busting, so committed status changes appear without rebuilding the page.

## Tracking mirrored from Amber's system
The page includes Application Status, Next Action, Open Verification fields, Deadline, Date Added, Date Applied, Urgency, Queue Rank, notes, interview request/completed-interview counts, conversion metrics, audit timestamps/cadence, posting-status history, Recent Moves, Interview Pipeline, zombie-pending detection, browser-local persistence, custom jobs, JSON import/export, and CSV export.

## Important status behavior
The GitHub checker is intentionally conservative. HTTP 404/410 or explicit closure language can close a job automatically. A previously closed job that returns HTTP 200 is flagged for reopen review rather than auto-reopened, because many career platforms serve generic shell pages.

Current snapshot: 60 tracked; 59 actionable live; 1 non-actionable; 0 likely filled.


## Derrick self-service mode

Derrick does not need to edit HTML or JSON.

### Application tracking
Use the Pipeline dropdown or `DETAILS / COMP / INTERVIEWS` on any job. The browser stores:
- applied/not applied and stage;
- recruiter / hiring manager;
- interview invitation and completed-interview counts;
- salary base asked and total compensation asked;
- offer base, bonus, equity/LTI, and total compensation;
- last-contact and follow-up dates;
- interview-stage notes, next action, and general notes.

These fields stay in browser `localStorage` by default. That is intentional: if this Pages repo is public, salary asks, offer details, contacts, and interview notes should **not** be committed to the public repository.

Use Export JSON / CSV for backup or migration between devices.

### Add a job + AI fit assessment
Paste the posting URL into **Derrick Self-Service Job Console** and click **AI ASSESS + ADD**.

On GitHub Pages this opens a pre-filled GitHub issue. After Derrick clicks **Submit new issue**:
1. `.github/workflows/ai-assess-job.yml` runs.
2. The workflow fetches the posting.
3. GitHub Models compares the posting to `profile.json`.
4. The workflow scores resume screening, capability, culture/work-style, technical fit, level, overall fit, priority, money signal, strengths and gaps.
5. It commits the new role into `jobs.json`.
6. The issue is commented with the assessment and closed.
7. The website polls `jobs.json` and receives the new role automatically.

### Required GitHub repository settings
- Issues: enabled.
- Actions: enabled.
- Settings → Actions → General → Workflow permissions → **Read and write permissions**.
- GitHub Models access must be available for the repository/account because the AI workflow uses the `models: read` permission.


## Fix: no tracker-config.js required

The dashboard no longer depends on a separate `tracker-config.js` file.

On normal GitHub Pages URLs such as:

`https://USERNAME.github.io/REPOSITORY/`

the page automatically detects the GitHub username and repository name.

If a custom domain is ever used, the AI button can still be given the repo explicitly with:

`?githubOwner=USERNAME&githubRepo=REPOSITORY`

You can delete any old `tracker-config.js` file from the repository after uploading the corrected `index.html`.
