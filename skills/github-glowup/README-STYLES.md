# Modern profile README styles

Pick **one** style (A–E) that fits the candidate's personality and target role, then fill it with **real** content only. All styles render on GitHub with no external services, except for optional, clearly marked widgets.

Before choosing, check the [`examples/`](examples/) folder next to this file: curated real-world READMEs live there as references. Match their quality bar. Never copy someone else's README wholesale; adapt the structure.

## Style A: ASCII terminal (developer-core)

Best for backend, systems and infra people. The ASCII banner is the hero.

Generate the banner; never hand-type block letters:
- `figlet -f "ANSI Shadow" "<name>"` if figlet is installed (also try the `slant`, `standard` and `small` fonts)
- otherwise `npx figlet -f "ANSI Shadow" "<name>"` (ask before running npx)
- otherwise `python3 -c "import pyfiglet; print(pyfiglet.figlet_format('<name>', font='ansi_shadow'))"` if pyfiglet is installed
- if none of these work, use Style C instead. Broken ASCII art is worse than none.

Keep the banner ≤ 80 columns wide (check the longest line) so it doesn't wrap on mobile. Use a short name or handle if needed.

````markdown
```
<figlet output here>
```

```yaml
whoami:   <Name> · <role> · <city/remote>
building: <current project, one line, link>
stack:    [<lang>, <lang>, <db>, <infra>]
learning: <one thing>
contact:  <email> · linkedin.com/in/<x>
```

### ~/projects
```
├── <project-1>   <one-line pitch>  · <stack>  · <metric or "live">
├── <project-2>   <one-line pitch>  · <stack>
└── <project-3>   <one-line pitch>  · <stack>
```
```bash
$ cat now.txt
<what you're working on or looking for: "Open to SDE-1 roles from <month year>">
```
````

## Style B: Clean recruiter-first

Best for most students and freshers. Scannable in 10 seconds.

```markdown
## Hi, I'm <Name> 👋
<Role> · <college / company> · <year>. I build <what you build> with <main stack>.

**Currently:** <building / interning at / looking for>

### Featured projects
| Project | What it does | Stack |
|---|---|---|
| [<name>](<link>) | <one line + one metric> | <stack> |
| [<name>](<link>) | … | … |

### Highlights
- <contest rating / hackathon win / merged OSS PR / internship>
- <…>

**Reach me:** <email> · [LinkedIn](<url>) · [Portfolio](<url>)
```

## Style C: Minimal one-liner + pinned work

Best when the pinned repos are strong. Let them speak.

```markdown
### <Name>: <role> who <one specific thing>.
<One sentence: what you're building now + link.> Reach me at <email>.
```

## Style D: Story-led (startups / product roles)

```markdown
## <Name>
I like shipping things people use. <Project> has <N real users>; <Project 2> <real outcome>.

**What I'm good at:** <3 concrete skills tied to projects>
**What I'm looking for:** <role, stack, remote/city>
**Recently:** <a learning or writing link>
```

## Style E: neofetch portrait (photo → ASCII)

The most memorable style: the candidate's photo rendered as braille ASCII on the left, `neofetch`-style facts on the right. See [examples/neofetch-dave1725.md](examples/neofetch-dave1725.md).

Make the portrait from their real photo (ask first, since it's their face on a public page):

1. Get the photo: their GitHub avatar (`curl -sL "https://avatars.githubusercontent.com/u/<id>?s=400" -o photo.jpg`) or a file they give you.
2. Cut out the background for a clean silhouette. On macOS, use the bundled `scripts/cutout.swift` (Apple Vision, on-device): `swift scripts/cutout.swift photo.jpg cut.png`. Elsewhere, skip this step; a plain background works best.
3. Convert: `python3 scripts/image-to-ascii.py cut.png --width 34` (braille, the default) or `--mode ascii`. Use `--invert` for light themes and `--contrast 1.4` if the face is flat. Look at the output; if it doesn't read as a face, adjust and rerun before showing it.

Layout: one ```` ```text ```` block (keeps alignment), portrait on the left, a `│` gutter, then facts:

````markdown
```text
<portrait line 1>  │ <handle>@github ─────────────────────────────
<portrait line 2>  │ . Host: ..................... <company or college>
<portrait line 3>  │ . Kernel: ..................... <role / year>
<portrait line 4>  │ . Location: ....................... <city>
<portrait line 5>  │ . Languages: ............. <top 3 from their repos>
<portrait line 6>  │ . Projects: ......... <2 real repos, one line each>
<portrait line 7>  │ - Contact ───────────────────────────────────
<portrait line 8>  │ . Website: ......................... <url>
```
````

Rules: every value is real (from their profile, repos, or what they tell you); dot leaders pad each line to the same width; at most ~90 columns total so it doesn't wrap; don't publish an email unless they ask.

## Widgets (optional, use sparingly)

Stat cards (`github-readme-stats`), streak counters, trophy grids and typing SVGs depend on third-party services that rate-limit and break. At most **one** widget. Never stack five stat cards. Recruiters read text, not graphs. Skip widgets entirely for Style A and C.

## Universal rules

- Under ~40 lines of rendered content. Above the fold: who, what, best work, contact.
- Every project mentioned must link to a real repo or live demo.
- No visitor counters, no "my skills" icon walls with 30 logos, no autoplay GIF banners heavier than 1 MB.
- Real facts only. A metric with no source becomes `[N]` and a question for the user.
