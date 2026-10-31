# Handover

Report of the last work session. Read this after docs/WORK_PLAN.md at the start of every session.

## Session 30 to 31 October 2026: step 0.1

Step: 0.1 Project setup. Status: done except 1 check (see "Exact next step").
Sub-steps 0.1.1 and 0.1.2 written and tested by the coding assistant, then verified by the owner (output
and verification numbers matched). 0.1.3 organization and public repo created by the owner.
0.1.4 first commits pushed, then the repo was deleted and created again with one fresh commit
(decision D29). The earlier commits no longer exist on GitHub.
0.1.6 this update.

### Done-when test of step 0.1

| Check | Result |
|---|---|
| uv run python -m mrag.config prints the settings | Passed (owner) |
| Repo on GitHub with no data files | Passed. Checked by the coding assistant through the GitHub API after the repo was created again: 124 files, no .env, no database, nothing from data/private, data/public, scripts/ or .vscode/ |
| The coding assistant has loaded its local rules file | Open. The file was created during this session, so it can only be checked in a new session |
| Verification numbers match (rule C13) | Passed (owner) |

### Owner decisions in this session

| Item | Decision |
|---|---|
| Q1 licence | Apache-2.0 |
| Q8 "full access" | Admin role on the multiagent-ai-lab repo. The owner stays the only organization Owner |
| Migration tool | Alembic from the start |
| scripts/ (planning helper scripts) | Stay in the project folder, ignored by Git |

### Files created

pyproject.toml, uv.lock, .python-version, .gitignore, .env.example, LICENSE (official
Apache-2.0 text from apache.org), README.md, CHANGELOG.md, a local rules file for the coding assistant (not in Git), docs/HANDOVER.md,
src/mrag/__init__.py, src/mrag/config.py, src/mrag/db.py, migrations/env.py,
migrations/script.py.mako and the planned empty folders (configs, data/annotations, results,
tests/unit, tests/integration, tests/e2e, tests/fixtures, notebooks, demo, migrations/versions).
data/private and data/public exist only locally.

### Test results (run by the coding assistant on the Mac)

| Test | Result |
|---|---|
| uv sync | Python 3.12.14, 12 packages: alembic 1.20.1, pydantic-settings 2.16.2, sqlalchemy 2.1.6 and their dependencies |
| uv run python -m mrag.config (without and with .env) | Prints all 7 settings |
| Environment variable overrides .env | Works (MRAG_PROFILE=ci) |
| Wrong profile value | Clear error listing the allowed values |
| uv run alembic upgrade head, alembic current | Work. SQLite file created at data/app.db |
| SQLite settings | foreign_keys = 1, journal_mode = wal |
| Alembic revision template | A generated revision parses. Test revision deleted afterwards |

Verification numbers (rule C13): src/mrag/__init__.py 3543b4693a36, src/mrag/config.py
4239cc4118f7, src/mrag/db.py 511eeaebbdbd, migrations/env.py c95357b4cf62.

### Problems and fixes

- uv cache not on the SSD inside this project. Cause: uv stops looking for config files at the
  first pyproject.toml that has a [tool.uv...] section. Ours has [tool.uv.build-backend]
  (needed for the package name mrag), so /Volumes/MacbookAPFS/Project/uv.toml is ignored and
  uv uses ~/.cache/uv on the internal disk. Fix (owner approved): ~/.zshrc now sets
  UV_CACHE_DIR=/Volumes/MacbookAPFS/Project/.uv-cache when the SSD is connected. Checked in a
  new shell: uv cache dir prints the SSD path. Nothing machine-specific is in the repo.

### Deviations from the plan

- New folder migrations/ (Alembic). Not in WORK_PLAN.md section 8.2 yet.
- No alembic.ini: Alembic settings are in pyproject.toml under [tool.alembic].
- SQLite file at data/app.db. Its backup layer is not in section 6.3 or 6.4 yet. To decide in step 0.6.
- MLflow default port 5001 instead of 5000 (macOS AirPlay Receiver uses 5000).
- Model server port 8080 in .env.example is a placeholder until step 0.3.
- HF_HOME from .env is read by config.py but not exported to the environment. Step 0.3 must make
  sure the model download tools use /Volumes/MacbookAPFS/Project/.hf-cache.
- docs/07-security/secrets-management.md says .env.example lists names without values.
  WORK_PLAN.md step 0.1 asks for paths, ports and HF_HOME in it, so it has safe default values
  and no secrets.

### Docs updated (WORK_PLAN.md v1.8)

- WORK_PLAN.md: Current State, decisions D23 to D27, Q1 and Q8 answered,
  uv cache row in 6.3, migrations/ in 8.2, step 0.1 status.
- All 99 other docs: status banner, link to WORK_PLAN.md v1.8 and Last updated date. Rows copied
  word for word from WORK_PLAN.md (Q1, Q8, uv cache, 8.2) updated to match.
- README.md, database-design.md, environment-configuration.md, testing-status.md, roadmap.md,
  milestones.md: status and decided items. ADR-005 title fixed (it said Phase 1, the decision says Phase 15).
- .gitignore also ignores .vscode/ (personal editor settings).

### Repo created again: no assistant names

- Owner's decision D29 and new rule C15: the coding assistant's rules file and settings stay
  local (.git/info/exclude, never pushed). Repo files and commit messages name no assistant
  product. Every such mention in README.md, CHANGELOG.md and docs/ now says "the coding assistant".
- The GitHub repo was deleted and created again with one fresh commit, so the old
  history is gone. Checked: the GitHub API no longer finds the old commits.
- Owner's rule C16: no "step", "phase" or plan numbers in code comments, config comments or commit
  messages. Comments in db.py, config.py and .env.example reworded (verification numbers unchanged,
  only comments changed). The message of the first commit was corrected the same way.
- Owner's feedback: fix only exactly what needs fixing. Never delete and re-push everything when
  a targeted fix is possible.

### Earlier: vague wording removed (WORK_PLAN.md v1.9)

- First commit pushed to github.com/mdu-ai-lab/multiagent-ai-lab (organization and public repo
  created by the owner).
- Owner's decision D28 and new rule C14: no product comparisons ("ChatGPT-style", "ChatGPT-like",
  "NotebookLM-style") in the repo. All 31 places in README.md and docs/ (13 files) now describe the
  real feature instead. The words remain only inside rule C14 and decision D28, which name them
  in order to ban them.
- The local rules file has rule C14. docs/11-development-standards/coding-standards.md has the C14 row
  (word-for-word copy of section 5.2). All doc links point to WORK_PLAN.md v1.9.
- Owner's decision: the README description is only "Work in Progress" for now. A description
  is written later, when features exist.

### Exact next step

Next session (connect the SSD first):
1. Check that the coding assistant has loaded its local rules file.
2. Then step 0.2 (Qdrant in compose.yaml with a fixed version and its data folder on the SSD).
   Start Docker only after the SSD is connected. Ask the owner before writing any file (rule C3).

Not done yet by plan design (later steps): CI (1.4), make backup (0.6). The end-of-session
checklist items for CI and backup can't run until those steps exist.
