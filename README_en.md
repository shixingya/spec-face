<p align="center">
  <a href="README.md">中文</a> | <strong>English</strong>
</p>

# spec-face · A numbered library for badge-ready professional headshots

> **Can't describe professional presence? Unsure about ID photo specs? Pick a number and get a headshot you can actually print on a badge.**

20 **persona styles** (P) · 12 **wardrobe codes** (W) · 8 **backdrop & lighting setups** (B) · 8 **expression codes** (E) — and, most importantly, 12 **compliance specs** (S): 1-inch/2-inch, CR80 badge portrait area, Schengen and US visa formats, circular-cropped enterprise IM avatars, access-control face enrollment. Every spec carries exact dimensions, DPI, head-height ratio, eye-line position, background RGB and file-size ceiling.

You don't need to memorize "Rembrandt lighting" or "head height must be 70% of frame". Pick a spec and a persona, describe the person, and you get a structured bilingual prompt — then run a local check to see whether the result actually passes.

---

## Why this exists

AI headshot tools are everywhere, and nearly all of them solve the same problem: **making people look better**.

A badge photo is not that. A badge photo has to clear three other bars, in this order:

1. **Does it pass the spec** — head ratio off by 5% and the visa is rejected; background drifts and you reshoot; forget CMYK conversion and the print comes back the wrong color
2. **Does it still look like the person** — after skin smoothing, face slimming and eye enlargement, coworkers don't recognize them, and neither does the turnstile
3. **Is a batch consistent** — 500 store staff, each lit differently, reads as a pile of scraps

None of these are fixed by a prettier prompt. They are fixed by **specs, constraints and verification**. That is the entire difference between `spec-face` and a generic portrait prompt library — and the reason `spec` comes first in the name.

## What it solves

| Your problem | How spec-face handles it |
| :-- | :-- |
| No idea what a role should look like | **20 persona codes**, gaze and posture included |
| Generated face doesn't resemble the person | Identity fidelity is hard-wired into the prompt: no smoothing, no slimming, no proportion edits |
| Constant rework on size and background | **12 specs** with measurable targets plus a pre-delivery checklist |
| Don't know which model to trust | `identity_matrix.json` records measured identity fidelity per model |
| Batch output is inconsistent | `--locked` mode pins all five codes and refuses silent defaults |
| Rewriting prompts per model | Bilingual, segmented, every layer reusable |

## Quick start

```bash
pip install pillow                # required for spec checking
pip install opencv-python         # optional, estimates head ratio automatically

python scripts/prompt_spec.py --spec S-09 --persona P-001 \
  --subject "30-year-old man, square face, buzz cut, natural skin tone"
```

`--wear / --backdrop / --mood` are optional; the script fills them from the persona's recommended set and tells you why.

Then check the output image — **locally, nothing is uploaded**:

```bash
python scripts/check_spec.py headshot.jpg --spec S-09
python scripts/check_spec.py batch/*.jpg --spec S-11 --json
```

Anything the checker cannot measure is reported as `SKIP`, never as a pass. It will not lie to you.

## The five layers

| Prefix | Layer | Count | Decides |
| :-- | :-- | :-- | :-- |
| `S` | Compliance spec | 12 | Dimensions, DPI, head ratio, eye line, background, file size — **pick this first** |
| `P` | Persona | 20 | Looks like someone who does this job: gaze, posture, pitfalls |
| `W` | Wardrobe | 12 | White coat, brand uniform, crisp shirt, dark suit |
| `B` | Backdrop & light | 8 | Environment and lighting, with verifiable target color |
| `E` | Expression | 8 | Facial state, with a numeric smile intensity for batch consistency |

Browse them in [PERSONAS.md](PERSONAS.md) and [SPECS.md](SPECS.md), or open `skills/portrait-prompter/gallery/index.html` — a single offline page with full-text search and one-click copy.

<div align="center">

![Spec tab](images/specs-preview.png)

*The spec tab: background target color, head ratio, eye line, file ceiling — measurable numbers, not adjectives.*

</div>

## Three ways to use it

**Zero-threshold** — just say what you need: *"make badge photos for our new store staff, friendly-looking."* The skill picks `P-018` + `S-09` and explains why.

**Exact** — you already know: *"S-07, P-005, E-01, subject: 28-year-old woman, shoulder-length hair."*

**Batch locked** — for teams:

```bash
python scripts/prompt_spec.py --locked \
  --spec S-09 --persona P-018 --wear W-09 --backdrop B-01 --mood E-02 \
  --subject "employee ID 0341 + objective appearance description"
```

`--locked` rejects every silent default so all five codes are explicit and the whole batch shares identical wording. Avoid `B-07` for batches (ambient light can't be unified); for brand backgrounds use `B-08` and get the client's VI RGB first.

## Install as an agent skill

Send the repo URL to Codex or Claude Code:

> Install this skill: https://github.com/shixingya/spec-face — definition at `skills/portrait-prompter/SKILL.md`

Then say "I need door-access photos for 40 employees" and the agent walks the whole chain: spec → persona → assemble → batch lock → local verification. It will also refuse if you ask it to process someone else's face, or to use an AI photo to get past a turnstile.

## About identity_matrix: the most valuable file, and the emptiest

`references/identity_matrix.json` defines six evaluation dimensions — identity fidelity, spec attainability, beauty drift, batch consistency, failure modes — plus a reproducible blind-test protocol (8 consenting volunteers, 3 source photos each, 5 runs per model, three-judge identity test, face-embedding cosine similarity reported as mean and P10).

**Every score in v1 is `null`,** because I have not run the human trial yet.

I could have filled in plausible-looking numbers. The file would have read as more mature — and it would have misled everyone who used it to choose a model, which is precisely the thing that makes this project worth maintaining. So what ships now is the scaffold, the methodology, and an honest empty table.

This is the project's only real moat and the reason it's worth maintaining: models change monthly, and somebody has to re-measure the true fidelity ranking every month. Do that and you hold data nobody can copy.

## Contributing

Edit `references/*.json`, then:

```bash
python scripts/validate_library.py
python scripts/build_gallery.py
python scripts/build_docs.py
```

The validator blocks duplicate IDs, `aspect` that disagrees with `px`, a `bg_rgb` with no tolerance, and `tested: true` with empty scores — i.e. fabricated claims.

## Open source vs commercial

This project intends to make money, so let's be upfront:

- **Free forever (MIT)**: all libraries, bilingual prompts, spec knowledge, local verification, offline gallery, agent skill. Enough to run badge production for a company yourself.
- **Paid**: cloud rendering quota, monthly spec-update subscription, HR roster batch production dashboard, access-control/IM integration, private deployment, print-ready CMYK + bleed export.
- One line: **knowledge free, repetitive labor paid.**

## Compliance notice

- Faces are sensitive personal data. Everything runs locally by default; nothing is collected, uploaded or stored.
- **Process only your own image or one you have written authorization to use.** Unauthorized face swapping may constitute infringement; using it for identity verification may be unlawful.
- **Not for bypassing face recognition, liveness detection or real-name verification.** Both the docs and the skill refuse such requests.
- For passports, visas and driving licenses this project offers **spec references only** and promises nothing. Most countries do not accept AI-generated ID photos — confirm with the issuing authority first.
- Consider embedding AI-generation provenance (C2PA, or visible/invisible watermarks) in deliverables.

## Roadmap

- [ ] First human trial for `identity_matrix.json` (3 models × 8 volunteers)
- [ ] Expand personas to 40; add healthcare, manufacturing, public-service counters
- [ ] Add face landmarks to `check_spec.py` so head ratio and eye line move from `SKIP` to measured
- [ ] Print-ready export: CMYK conversion, 3mm bleed, batch packaging
- [ ] Circular safe-area preview for IM avatar cropping
- [ ] Verify each spec against official sources and retire the `needs_verification` flag

## Author

**卜天 (Bǔ Tiān)** — ten years writing code, and years listening to what people actually mean. This project joins both halves: engineering specs, and how a person wants to be seen at work.

Same handle on Zhihu and CSDN. For batch production or enterprise training, search the WeChat public account and reply **咨询**.

## License

[MIT](LICENSE)
