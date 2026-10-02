# CLAUDE.md

**Read [AGENTS.md](./AGENTS.md) first.** It is the single source of truth for this repository: architecture, modules, data structures, conventions, and contribution rules. Apply everything in AGENTS.md to your work.

This file only adds Claude-specific notes that do not belong in the generic agent reference.

## Claude-specific notes

- When asked to save analysis output, follow the `kb4itdoc_md` skill conventions and write to `responses/`.
- The user's auto-memory lives under `/home/t00m/.claude/projects/-home-t00m-Documents-devel-github-KB4IT/memory/`. Honor every entry in `MEMORY.md` and update it as feedback accumulates.
- Never use the em dash (`—`); use a comma, semicolon, colon, or rewrite the sentence.
- Do not commit unless explicitly asked; always suggest a commit message instead.
