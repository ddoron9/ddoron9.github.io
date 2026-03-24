const MAX_SLOTS_BY_PAGE = {
  home: 3,
  result: 4,
  history: 4
};

const DEFAULT_GUARDRAILS = {
  maxImpressionsPerSession: 8,
  minGenerationGap: 2
};

export function rankAds(candidates, context) {
  const {
    pageType,
    alreadyShownInSession,
    generationsSinceLastAd,
    cwvPenalty = 0
  } = context;

  if (!MAX_SLOTS_BY_PAGE[pageType]) {
    throw new Error(`Unsupported pageType: ${pageType}`);
  }

  if (alreadyShownInSession >= DEFAULT_GUARDRAILS.maxImpressionsPerSession) {
    return [];
  }

  if (generationsSinceLastAd < DEFAULT_GUARDRAILS.minGenerationGap) {
    return [];
  }

  const slotCap = MAX_SLOTS_BY_PAGE[pageType];

  return candidates
    .filter((ad) => ad.policySafe === true)
    .map((ad) => ({
      ...ad,
      score: scoring(ad, pageType, cwvPenalty)
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, slotCap);
}

function scoring(ad, pageType, cwvPenalty) {
  const placementBoost = pageType === "result" ? 1.15 : 1.0;
  const ctrEarnings = ad.pCtr * ad.eCpmUsd * placementBoost;
  const uxCost = ad.uxPenalty * 0.4;
  const qualityCost = cwvPenalty * 0.2;
  return round(ctrEarnings - uxCost - qualityCost);
}

function round(value) {
  return Number(value.toFixed(6));
}
