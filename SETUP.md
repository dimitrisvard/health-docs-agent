# SETUP.md — Manual setup checklist

Things **you** do by hand (accounts, keys, installs). Everything else, Claude Code builds from `PLAN.md` + `CLAUDE.md`. Items tagged **[now]** are needed to start; **[later]** are for the optional production phase (Phase 8).

## Order of operations
1. Install local prerequisites → 2. Create the GitHub repo → 3. Confirm the Anthropic key → 4. Create a Cloudflare AI Gateway → 5. Fill `.env` → 6. Gather the seed corpus → then point Claude Code at the repo and start Phase 0. Cloudflare production resources come later.

---

## 1. Local prerequisites [now]
- [ ] **Docker Desktop** installed and **running** (`docker info` succeeds). This is what runs Postgres + pgvector — no manual DB setup needed.
- [ ] **Node.js 20+** (`node -v`).
- [ ] **Python 3.12** (`python3 --version`).
- [ ] **Claude Code** installed and logged in.
- [ ] *(optional, for Phase 8)* **GitHub CLI** (`gh`) and **wrangler** (`npm i -g wrangler`).

## 2. GitHub [now]
- [ ] Create a **new repo**. Start **private**; flip to **public** at submission — the JD explicitly values a visible "trail of built things".
- [ ] Add an **MIT license**.
- [ ] Authenticate locally (`gh auth login`, or add an SSH key).
- [ ] *(Phase 6+/CI)* Add a repo secret `ANTHROPIC_API_KEY` under **Settings → Secrets and variables → Actions**. Used only by the judged-eval CI job; unit/integration tests mock the LLM, so they need no key.

## 3. Anthropic API [now]
- [ ] Confirm your **API key** at console.anthropic.com → **API Keys** (you said you already have this).
- [ ] Confirm **billing/credit** is active and note your **rate limits**.
- [ ] Confirm the **model id** you'll use (latest Claude Sonnet, e.g. `claude-sonnet-4-5`).
- [ ] You'll paste the key into `.env` in step 5 — **never commit it**.

## 4. Cloudflare AI Gateway [now]
- [ ] Create / sign in to a Cloudflare account at dash.cloudflare.com (free tier is fine for the gateway).
- [ ] **AI → AI Gateway → Create Gateway**; give it a name — that name is your **Gateway ID**.
- [ ] Note your **Account ID** (right sidebar / in the dashboard URL).
- [ ] Your base URL is: `https://gateway.ai.cloudflare.com/v1/<ACCOUNT_ID>/<GATEWAY_ID>/anthropic`
- [ ] *(recommended before any public deploy)* Enable **Authenticated Gateway**, create a gateway token, set it as `CF_AIG_TOKEN`. For local dev you can skip this.
- [ ] *(once it's live)* In the gateway settings, turn on **caching** and set a **spend limit** — these make great README screenshots and a real cost-control story.

## 5. Environment variables [now]
- [ ] `cp .env.example .env`, then fill:
  - `ANTHROPIC_API_KEY` — from step 3
  - `ANTHROPIC_BASE_URL` — the gateway URL from step 4
  - `ANTHROPIC_MODEL` — your Sonnet id
  - `CF_AIG_TOKEN` — only if you enabled gateway auth
- [ ] Leave `DATABASE_URL`, `MCP_URL`, `EMBED_MODEL` at their defaults — docker-compose provides them.
- [ ] Confirm `.env` is gitignored (it is in the template).

## 6. Seed corpus [now]
- [ ] Gather **~10–20 public, non-PII** digital-health documents into `data/`. Safe sources:
  - **ClinicalTrials.gov** — a few trial records/protocols (PDF or text).
  - **EMA medicines** (ema.europa.eu) — a couple of **SmPC** PDFs.
  - **DailyMed / FDA labels** — one or two drug labels.
  - **NICE** or **WHO** — a public clinical guideline.
- [ ] Add a short `data/README.md` listing each file's **source URL** (provenance is a nice README detail).
- [ ] Do **not** add anything with patient PII (these public docs don't contain any).
- [ ] `make seed` (once Claude Code builds it) ingests this folder.

---

## 7. Cloudflare production resources [later — Phase 8, optional]
- [ ] Create a **Cloudflare API token** (Account-scoped: Workers, Vectorize, D1, R2, Pages) → `CLOUDFLARE_API_TOKEN`.
- [ ] `wrangler vectorize create health-docs --dimensions=768 --metric=cosine`
- [ ] `wrangler d1 create health-docs`
- [ ] `wrangler r2 bucket create health-docs`
- [ ] Create a **Pages** project for `apps/web`.
- [ ] Note: **Containers require the Workers Paid plan.**

---

## You're ready when…
`.env` is filled, Docker is running, `data/` has your corpus, and the GitHub repo exists. Then open Claude Code in the repo, point it at `PLAN.md` + `CLAUDE.md`, and start **Phase 0**.
