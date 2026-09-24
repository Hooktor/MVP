# Design QA — Workflow « mission / évaluation » (archive)

## Comparison target

- Source visual truth: `C:\Users\hamza\.codex\generated_images\01a09d1a-b9cc-75f3-90ef-70978fd4bcc1\exec-b7f49c5b-e2cb-4655-be84-f996ef79f9a7.png`
- Implementation capture: `C:\Users\hamza\Desktop\mvp\docs\qa-workflow-evaluation-final.png`
- Combined comparison evidence: `C:\Users\hamza\Desktop\mvp\docs\qa-workflow-comparison-small.png`
- Viewport: 1440 × 1024 CSS px, device scale factor 1; source and implementation were normalized to a shared 720 × 512 comparison region.
- State: requester viewing a mission with a received PV and the evaluation action available.

## Comparison history

1. Initial build: the mission identity stacked vertically, pushing the primary action too far down the page (P1).
2. Fix: made the mission identity a compact horizontal summary with the expert on the right, reduced title spacing, and retained the full workflow ribbon above the action.
3. Post-fix evidence: `qa-workflow-evaluation-final.png` shows the closure banner, named responsible expert, eight-step progress ribbon, review context and start of the evaluation form in the first viewport.

## Required fidelity surfaces

- **Fonts and typography:** system sans font matches the project’s established rendering. Large mission title, orange eyebrow and action hierarchy follow the selected visual; compact labels remain readable.
- **Spacing and layout rhythm:** the selected wide Orange action band, horizontal progress ribbon, wide work column and narrow factual side column are represented. The actual form is intentionally retained instead of the mock’s illustrative checklist.
- **Colors and tokens:** Orange `#ff7900` is reserved for the active closure band and current stage; green marks completed stages; navy/charcoal navigation and warm neutral background remain aligned with ORBIT.
- **Image quality and asset fidelity:** the selected concept contained a generated portrait. The production app intentionally uses its existing initials avatar component because experts do not have profile photos; no placeholder image or custom graphic was substituted.
- **Copy and content:** all visible copy is tied to live mission, PV and evaluation data. The CTA retains the real action, “Évaluer la mission”.

## Findings

No actionable P0, P1 or P2 findings remained in that workflow review.

## Follow-up polish

- [P3] Add optional expert profile photos when the business provides approved media, then replace initials in the mission summary.
- [P3] Add a checklist model only if the evaluation process later requires separate scored criteria beyond the current rating and comment.

## Verification

- Django checks passed.
- 30 automated tests passed.
- Primary visible interaction verified: the top CTA anchors to the evaluation form; the existing evaluation form and submit action remain unchanged.

final result: passed
