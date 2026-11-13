# Tech resume rules

## ATS
> These are readiness heuristics. No ATS vendor publishes a scoring formula, and each one parses differently.

- Single column. No tables, text boxes, or graphics carrying content. Icons in place of words ("📞") parse as garbage.
- Standard section headings: Education, Experience, Projects, Skills, Achievements (or close variants).
- Contact details in the body, not the header or footer.
- Text-based PDF (not scanned); fonts that extract cleanly; no ligature tricks.
- Use exact keywords from the target job description where they're true ("REST APIs", "PostgreSQL", "React"), spelled the standard way.
- File name: `Firstname-Lastname-Resume.pdf`.

## Structure for students and freshers (1 page)
1. Header: name, phone, email, LinkedIn, GitHub, portfolio (all clickable).
2. Education: degree, college, year, CGPA (include if ≥ 7.5/10 or the company asks), relevant coursework only if space allows.
3. Experience / internships (if any), most recent first.
4. Projects: 2–3 strongest. Each needs a link, its stack, and 2–3 impact bullets.
5. Skills: grouped (Languages · Frameworks · Tools · Databases). No ratings, no bars, no "MS Office".
6. Achievements: contest ratings, hackathon wins, open-source merged PRs, scholarships. Use concrete numbers ("Codeforces Specialist, 1500+", "Top 2% of 30k in X").

Experienced (2+ years): experience before education, and one page per ~5 years at most.

## Bullets
Formula: **Action verb + what you built/did + how (tech) + measurable result**.

| Weak | Strong |
|---|---|
| Worked on backend of e-commerce app | Built order and payment APIs in Node.js + PostgreSQL handling [N] orders/day; cut checkout latency [X]% by adding Redis caching |
| Made a chat application | Built a real-time chat app (Socket.io, React) supporting [N] concurrent users; added message persistence and read receipts |
| Responsible for testing | Wrote [N] Jest integration tests raising coverage from [X]% to [Y]%, catching 3 regressions before release |

- Start with a strong past-tense verb: Built, Designed, Reduced, Automated, Shipped, Migrated, Optimized, Led.
- One line each where possible, two at most.
- Quantify: users, requests, latency, % improvement, time saved, dataset size, stars, downloads. Scale also counts ("10k-row dataset").
- Banned: "Responsible for", "Worked on", "Helped", "Various", "Etc.", "Hardworking", "Team player", "Passionate".
- No first-person pronouns.

## Projects that impress
Better than a clone: something with **real users**, **real data**, a **non-trivial technical problem** (concurrency, scale, performance, ML in production), or a **twist** on a common idea. Deployed and linked beats local-only.

## Instant red flags
Typos · inconsistent dates · photo (in most markets outside some regions) · an objective statement full of clichés · two pages for a fresher · skills listed that the candidate can't defend · broken links · a GitHub with no READMEs.
