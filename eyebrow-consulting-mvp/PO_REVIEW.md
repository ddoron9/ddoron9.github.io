# PO Review

Date: `2026-03-16`

Review basis:

- Loaded `http://127.0.0.1:4173` in Playwright
- Verified desktop and mobile-width rendering
- Clicked `데모 얼굴로 실행`
- Re-ran with low RPM inputs to confirm `BLOCK_TOPUP_REQUIRED`

## QA coverage

- [x] Page loads without runtime crash
- [x] Demo flow renders original, cleaned, and 3 recommendation canvases
- [x] Monetization state flips to `BLOCK_TOPUP_REQUIRED` when RPM is too low
- [x] Ad slots render on initial load and after result generation
- [x] Mobile viewport remains readable
- [ ] Real uploaded photo quality verified
- [ ] Real eyebrow removal quality verified
- [ ] Real face-shape recommendation accuracy verified
- [ ] Production ad policy compliance verified

## PO verdict

This is a usable front-end prototype, not yet a product-ready eyebrow consulting experience.

What works:

- The page structure matches the intended funnel: upload area, original/cleaned comparison, 3 styled outputs, and monetization panels.
- The economic gate is understandable and visible.
- The page is visually coherent on mobile.

What does not yet clear MVP:

- The current pipeline is heuristic canvas drawing, not real eyebrow erase/generation for user photos.
- Recommendation quality is not grounded in actual face landmarks or model outputs.
- Ad behavior is wired too early in the funnel and conflicts with the result experience.

## Priority TODO

### P0

- [ ] Replace the heuristic erase/draw pipeline with a real image pipeline. Current logic is hard-coded region estimation and canvas repainting in [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):441, [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):623, [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):640, [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):673.
- [ ] Add a real upload result path backed by an inference API. Right now every result is generated entirely in-browser with no persistence or model boundary.
- [ ] Add privacy and retention messaging before upload. This app handles face images but currently has no consent copy, deletion copy, or retention statement.

### P1

- [ ] Fix the recommendation badge logic. `recommendStyle()` returns Korean display names while `bindStyleMeta()` compares against `style.id`, so no style can be selected as the true recommendation in code. See [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):459, [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):464, [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):721.
- [ ] Stop consuming ad session budget on boot. `createBootPreview()` calls `renderAds()` before the user has generated anything, which burns through the session inventory and causes fallback-only ads during the actual result flow. See [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):812, [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):818, [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):540.
- [ ] Rebalance result-page ad density. On mobile the result cards already carry inline ads, and stacking top + side + inline placements crowds the consult experience before trust is established.
- [ ] Add explicit upload validation and failure states for non-face images, oversized images, and unsupported formats.

### P2

- [ ] Use `willReadFrequently` or a dedicated readback canvas for repeated `getImageData()` calls to address the canvas performance warning. See [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):728, [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html):771.
- [ ] Add a clear before/after scrubber or swipe comparison. The current two-canvas layout proves processing happened, but it does not help users judge the improvement quickly.
- [ ] Separate “preview” and “HQ result” in the UI copy. The monetization logic exists, but the visual states do not yet teach users why they should pay.

## Feedback loop

### Loop 1: Product truth

- Build a backend route that accepts an uploaded face image and returns `cleaned`, `style_1`, `style_2`, `style_3`, and `recommended_style_id`.
- Test with 10 real face photos across lighting, skin tone, and brow thickness.
- Record failures in 4 buckets only: bad face crop, bad brow erase, bad brow color, bad recommendation.
- Do not tune ads during this loop.

### Loop 2: Conversion truth

- After real image quality is acceptable, move ads to the result page only after the first successful render.
- Log `upload_started`, `render_succeeded`, `style_selected`, `credit_prompt_seen`, `credit_purchase_clicked`.
- Compare `3-slot` vs `5-slot` layouts on the result page.
- Reject any ad layout that reduces `style_selected / render_succeeded` by more than 5%.

### Loop 3: Monetization truth

- Unlock ad-funded HQ only when estimated ad revenue clears the configured floor.
- Everything else should be preview-only or credit-gated.
- Review RPM, render cost, and purchase conversion together once per week, not per feature tweak.

## If I were the PO

I would say: stop calling this “AI eyebrow consulting” in product copy until a real inference path exists. Keep this build as a clickable monetization prototype, then spend the next sprint on actual photo quality and trust signals.
