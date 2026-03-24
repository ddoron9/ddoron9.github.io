import { hqRequestCostUsd } from "./pricing.js";

const DEFAULT_SAFETY_MULTIPLIER = 1.2;

export function decideHqGeneration(input) {
  const {
    predictedPageRpmUsd,
    pageViewsPerRequest = 1,
    creditsBalance = 0,
    safetyMultiplier = DEFAULT_SAFETY_MULTIPLIER
  } = input;

  const cost = hqRequestCostUsd();
  const estimatedAdRevenue = (Math.max(predictedPageRpmUsd, 0) / 1000) * pageViewsPerRequest;
  const adRevenueFloor = cost * safetyMultiplier;

  if (estimatedAdRevenue >= adRevenueFloor) {
    return {
      decision: "ALLOW_AD_FUNDED",
      hqCostUsd: cost,
      estimatedAdRevenueUsd: round(estimatedAdRevenue),
      reason: "Ad revenue floor passed"
    };
  }

  if (creditsBalance >= 1) {
    return {
      decision: "ALLOW_CREDIT",
      hqCostUsd: cost,
      estimatedAdRevenueUsd: round(estimatedAdRevenue),
      reason: "Ad revenue floor failed, using 1 credit"
    };
  }

  return {
    decision: "BLOCK_TOPUP_REQUIRED",
    hqCostUsd: cost,
    estimatedAdRevenueUsd: round(estimatedAdRevenue),
    reason: "No credit and ad floor failed"
  };
}

function round(value) {
  return Number(value.toFixed(6));
}
