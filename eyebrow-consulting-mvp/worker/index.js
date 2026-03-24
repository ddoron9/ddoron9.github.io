import { rankAds } from "../src/adEngine.js";
import { decideHqGeneration } from "../src/costGuard.js";
import { breakEvenPageRpmUsd, hqRequestCostUsd } from "../src/pricing.js";

export default {
  async fetch(request) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/api/health") {
      return json({
        ok: true,
        hqRequestCostUsd: hqRequestCostUsd(),
        breakEvenRpmPer1View: breakEvenPageRpmUsd(1)
      });
    }

    if (request.method === "POST" && url.pathname === "/api/hq-decision") {
      const body = await readJson(request);
      const result = decideHqGeneration({
        predictedPageRpmUsd: Number(body.predictedPageRpmUsd ?? 0),
        pageViewsPerRequest: Number(body.pageViewsPerRequest ?? 1),
        creditsBalance: Number(body.creditsBalance ?? 0)
      });
      return json(result);
    }

    if (request.method === "POST" && url.pathname === "/api/rank-ads") {
      const body = await readJson(request);
      const ranked = rankAds(
        Array.isArray(body.candidates) ? body.candidates : [],
        {
          pageType: body.pageType ?? "result",
          alreadyShownInSession: Number(body.alreadyShownInSession ?? 0),
          generationsSinceLastAd: Number(body.generationsSinceLastAd ?? 2),
          cwvPenalty: Number(body.cwvPenalty ?? 0)
        }
      );
      return json({ ranked });
    }

    return new Response("Not found", { status: 404 });
  }
};

async function readJson(request) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8"
    }
  });
}
