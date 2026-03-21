# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MAS (Multi-Agent System) for automated grading of student projects submitted as PRs in GitHub Classroom. The system processes PRs, evaluates artifacts against lab specifications, runs code in sandboxes, calculates deadline penalties, and posts detailed grading comments back to the PR.

Built for the "Системы ИИ" course (VolGTU) and also serves as a case study for the Software Design AI Production Systems course (ITMO).

## Tech Stack

- **Language:** Python 3.13
- **Agent orchestration:** LangGraph
- **LLM:** GLM-4.7 via Z.AI API (OpenAI-compatible, `https://api.z.ai/api/paas/v4`)
- **LLM observability:** Langfuse
- **Sandbox:** E2B (Firecracker microVM)
- **GitHub App:** gidgethub[httpx]
- **Google Sheets:** aiogoogle
- **Task queue:** Taskiq + Redis
- **ASGI server:** Granian
- **HTTP client:** httpx
- **Config:** python-dotenv
- **Deploy:** VPS + Docker

## Architecture

GitHub App receives PR webhook via Granian ASGI server, dispatches to Taskiq worker. Worker runs a **tool use loop agent** (Claude Code pattern) built on low-level LangGraph (`StateGraph` + `ToolNode` + `tools_condition`).

The agent decides which tools to call, in what order, how many times — adapts to different labs and projects without hardcoded control flow.

**Tools available to the agent:**
- `read_roster`, `fetch_spec`, `check_artifacts`, `parse_dod`, `check_deadline` — deterministic
- `evaluate_content` — sub-agent (separate LLM call for content evaluation)
- `run_sandbox` — sub-agent (E2B sandbox execution)
- `post_comment`, `write_results` — write actions

## Key Design Decisions

- **Deterministic where possible:** File checks, DoD parsing, branch name parsing, deadline penalties — all use regex/formulas, not LLM
- **LLM only for content quality:** Document evaluation against rubrics and PR comment generation
- **Prompt injection defense:** Input sanitization before LLM, structural isolation of user content, JSON schema output validation
- **Penalty based on `pr.created_at`** (immutable via GitHub API), not commit dates
- **Escalation to instructor:** Auto-labels PR `needs-review` when score is 40-60%, injection detected, sandbox errors, or agent disagreement >30%
- **No irreversible actions:** Agent never merges PRs or modifies student repos; only posts comments and writes to Sheets

## Branch/PR Conventions

- Lab 1: one PR per team, arbitrary branch name
- Lab 2+: one PR per student, branch format `lab{N}-{role}-deliverables`

## Documentation

- `docs/architecture.md` — system architecture diagram and agent specs
- `docs/data-sources.md` — sources of truth, Google Sheets schema
- `docs/grading-rules.md` — PR/branch conventions, penalty logic, PR comment format, escalation rules
- `docs/tech-stack.md` — technologies, caching strategy, PoC scope
- `docs/product-proposal.md` — product goals, metrics, use cases, edge cases
- `docs/governance.md` — risk register, logging policy, PD handling, injection defense
