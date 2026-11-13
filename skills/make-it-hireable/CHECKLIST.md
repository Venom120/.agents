# Hireable project checklist

| # | Item | What "done" looks like |
|---|---|---|
| 1 | **README** | One-line pitch, demo link/screenshot, features, stack, architecture note, run-locally steps that actually work, env vars table, "technical challenges" section |
| 2 | **Runs from a clean clone** | Documented setup works on a fresh machine; `.env.example` lists every variable; seed or sample data provided |
| 3 | **No secrets in repo** | No keys/passwords in code or history; `.env` in `.gitignore`; config read from env |
| 4 | **Tests** | Meaningful tests on core logic and at least one integration/API test; one command runs them |
| 5 | **CI** | GitHub Actions (or equivalent) running lint + tests on every push/PR; badge in README |
| 6 | **Lint and format** | Standard linter/formatter configured for the language (ESLint/Prettier, Ruff/Black, clang-format, gofmt) |
| 7 | **Error handling and validation** | Inputs validated at the boundary; errors return proper status codes and messages; no swallowed exceptions; no stack traces leaked to users |
| 8 | **Security basics** | Hashed passwords (bcrypt/argon2); parameterised queries; authz checks on protected routes; CORS not `*` with credentials; rate limiting on auth if it's a web API |
| 9 | **Structure** | Clear separation (routes/controllers/services/data, or the framework's idiom); no 1,000-line files; dead code removed |
| 10 | **Deployed** | Live URL on a free tier (Vercel, Netlify, Render, Fly, Railway, Cloudflare); linked in README and repo homepage |
| 11 | **Git hygiene** | Meaningful commit messages going forward; `.gitignore` correct; no committed build artifacts or `node_modules` |
| 12 | **Observability (bonus)** | Structured logging; a health endpoint |
| 13 | **Performance (bonus)** | Pagination on list endpoints; indexes for hot queries; no N+1 queries |
| 14 | **Docker (bonus)** | `Dockerfile` (+ `docker-compose.yml` if multiple services) that runs the app |

Priority for most student projects: 3 → 1 → 2 → 4 → 5 → 7 → 10 → 8 → 6, then bonuses.
