import {
  CREDIT_PACKS,
  FREE_TIER,
  PRICING_DATE,
  breakEvenPageRpmUsd,
  grossMargin,
  hqRequestCostUsd,
  unitPriceUsd
} from "./pricing.js";
import { decideHqGeneration } from "./costGuard.js";
import { rankAds } from "./adEngine.js";

function run() {
  console.log(`Pricing date: ${PRICING_DATE}`);
  console.log(`HQ request COGS: $${hqRequestCostUsd()}`);
  console.log(`Break-even RPM (1 pageview/request): $${breakEvenPageRpmUsd(1)}`);
  console.log(`Break-even RPM (2 pageviews/request): $${breakEvenPageRpmUsd(2)}`);
  console.log(`Free tier HQ: ${FREE_TIER.hqCreditsPerDay} / day`);
  console.log(`Free tier preview: ${FREE_TIER.lowResPreviewPerDay} / day`);
  console.log("");
  console.log("Credit packs");
  for (const pack of CREDIT_PACKS) {
    console.log(
      `- ${pack.name}: $${pack.priceUsd} for ${pack.credits} credits (unit=$${unitPriceUsd(pack)}, margin=${grossMargin(pack)}%)`
    );
  }

  const decision = decideHqGeneration({
    predictedPageRpmUsd: 3.2,
    pageViewsPerRequest: 1.3,
    creditsBalance: 0
  });
  console.log("");
  console.log("HQ decision sample");
  console.log(decision);

  const ranked = rankAds(
    [
      { id: "adsense-a", pCtr: 0.023, eCpmUsd: 4.1, uxPenalty: 0.09, policySafe: true },
      { id: "affiliate-b", pCtr: 0.018, eCpmUsd: 6.2, uxPenalty: 0.16, policySafe: true },
      { id: "house-c", pCtr: 0.03, eCpmUsd: 1.2, uxPenalty: 0.02, policySafe: true }
    ],
    {
      pageType: "result",
      alreadyShownInSession: 3,
      generationsSinceLastAd: 2,
      cwvPenalty: 0.07
    }
  );
  console.log("");
  console.log("Ad ranking sample");
  console.log(ranked);
}

run();
