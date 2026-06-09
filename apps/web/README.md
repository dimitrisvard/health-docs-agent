# web

Next.js 15 (App Router) frontend. Claude Code scaffolds this in Phase 3.

Build the two-pane workspace from PLAN.md section 11:
- left: corpus / source cards
- right: chat thread; each answer has an expandable retrieval-inspector drawer
  (which tools fired, retrieved chunks, fusion scores)
- /evals page: render the latest eval run from the DB
- persistent, tasteful "not medical advice" note

Routes: `/`, `/chat`, `/sources`, `/evals`. Talk to the agent at NEXT_PUBLIC_AGENT_URL (SSE).
