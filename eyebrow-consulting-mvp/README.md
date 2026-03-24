# Eyebrow Consulting MVP (Commercial + Ad Optimized)

This starter pack fixes numbers for a zero-loss MVP and includes:

- credit pricing table
- break-even RPM formulas
- cost guard logic for HQ generation
- high-density ad ranking logic with policy guardrails
- token/env template for Cloudflare, Hugging Face, and optional AWS

## 1) Confirmed Pricing (as of 2026-03-11)

Assumptions:

- HQ request outputs 3 variants at `1024x1024`
- Cloudflare Workers AI image cost: `$0.001384` per image
- Workers base fee: `$5/month`
- Monthly HQ requests: `10,000`
- R2 storage + operations per request: `$0.000011`

COGS per HQ request:

- Inference: `3 * 0.001384 = $0.004152`
- Fixed fee allocation: `$5 / 10000 = $0.000500`
- R2: `$0.000011`
- Total COGS: `$0.004663` (rounded `$0.00466`)

## 2) MVP Credit Prices (final)

- `100 credits = $2.99`  (`$0.0299/request`)
- `500 credits = $9.99`  (`$0.0200/request`)
- `2000 credits = $29.99` (`$0.0150/request`)

Each HQ generation consumes `1 credit`.

Free tier:

- HQ: `0/day` (for strict zero-loss protection)
- Low-res preview: `20/day` (client-side)

## 3) Break-even RPM

Formula:

`RPM_be = COGS * 1000 / pageviews_per_request`

With COGS = `$0.00466`:

- `1 pageview/request` => break-even RPM `~$4.66`
- `2 pageviews/request` => break-even RPM `~$2.33`

Operational safety rule:

- Require estimated ad revenue `>= COGS * 1.2` before unlocking ad-funded HQ.

## 4) Decision Rule (No-loss Guard)

For each HQ request:

1. estimate ad revenue from current RPM and expected page views
2. if ad revenue floor passes: allow HQ without credit
3. else if user has credit: allow HQ and deduct 1 credit
4. else block HQ and request top-up

Implementation: [`src/costGuard.js`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/src/costGuard.js)

## 5) Aggressive Ad Strategy (with guardrails)

Max slots by page:

- home: `3`
- result: `4`
- history: `4`

Guardrails:

- max impressions per session: `8`
- minimum gap: one ad exposure every `2` generations

Ranking score:

`score = (pCTR * eCPM * placementBoost) - uxPenalty - cwvPenalty`

Implementation: [`src/adEngine.js`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/src/adEngine.js)

## 6) Token Setup

Check `.env.example`:

- Cloudflare: account/token/model/R2 bucket
- Hugging Face fallback token
- optional AWS keys (if S3/CloudFront is later added)
- billing and ad identifiers

Token notes:

- You must create tokens in each vendor console manually.
- Do not commit real keys. Set as Cloudflare secrets and CI secrets only.

## 7) API + Web Entrypoints

- Web calculator: [`web/index.html`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/web/index.html)
- Worker API: [`worker/index.js`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/worker/index.js)
- Wrangler config: [`wrangler.toml`](/Users/gimdoi/workspace/eyebrow-consulting-mvp/wrangler.toml)

Worker endpoints:

- `GET /api/health`
- `POST /api/hq-decision`
- `POST /api/rank-ads`

## 8) Cloudflare Deploy (free tier start)

```bash
cd /Users/gimdoi/workspace/eyebrow-consulting-mvp
npm install -g wrangler
wrangler login
wrangler deploy
```

For web static hosting, deploy `web/` to Cloudflare Pages and connect it to the Worker routes.

## Eyebrow rendering note

The current preview path uses a **stroke renderer** for eyebrow synthesis.
It no longer depends on SVG eyebrow asset compositing for the final brow draw step.
MediaPipe landmarks are used to estimate brow geometry, then strands are rendered directly on canvas.

## 9) Run Demo

```bash
cd /Users/gimdoi/workspace/eyebrow-consulting-mvp
npm run demo
```

The output prints:

- COGS
- break-even RPM
- pack margins
- HQ allow/block decision example
- ranked ads example
