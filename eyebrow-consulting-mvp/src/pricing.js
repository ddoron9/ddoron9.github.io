export const PRICING_DATE = "2026-03-11";

export const COST_MODEL = {
  imageSize: "1024x1024",
  hqVariantsPerRequest: 3,
  workersAiCostPerImageUsd: 0.001384,
  workersBaseFeeUsdPerMonth: 5,
  monthlyHqRequestsAssumption: 10000,
  r2StorageAndOpsUsdPerRequest: 0.000011
};

export const CREDIT_PACKS = [
  { name: "Starter", credits: 100, priceUsd: 2.99 },
  { name: "Growth", credits: 500, priceUsd: 9.99 },
  { name: "Scale", credits: 2000, priceUsd: 29.99 }
];

export const FREE_TIER = {
  hqCreditsPerDay: 0,
  lowResPreviewPerDay: 20
};

export function hqRequestCostUsd() {
  const inference = COST_MODEL.hqVariantsPerRequest * COST_MODEL.workersAiCostPerImageUsd;
  const fixedFee = COST_MODEL.workersBaseFeeUsdPerMonth / COST_MODEL.monthlyHqRequestsAssumption;
  const total = inference + fixedFee + COST_MODEL.r2StorageAndOpsUsdPerRequest;
  return roundUsd(total);
}

export function breakEvenPageRpmUsd(pageViewsPerRequest = 1) {
  if (pageViewsPerRequest <= 0) {
    throw new Error("pageViewsPerRequest must be > 0");
  }
  return roundUsd((hqRequestCostUsd() * 1000) / pageViewsPerRequest);
}

export function unitPriceUsd(pack) {
  return roundUsd(pack.priceUsd / pack.credits);
}

export function grossMargin(pack) {
  const unit = unitPriceUsd(pack);
  const cost = hqRequestCostUsd();
  return Number((((unit - cost) / unit) * 100).toFixed(1));
}

function roundUsd(value) {
  return Number(value.toFixed(6));
}
