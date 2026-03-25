/**
 * Hair-Stroke Eyebrow Renderer
 * Procedural generation of natural-looking eyebrow hair strands
 */

/**
 * Seeded random number generator for reproducible results
 */
class SeededRandom {
  constructor(seed = 0) {
    this.seed = seed;
  }
  next() {
    this.seed = (this.seed * 9301 + 49297) % 233280;
    return this.seed / 233280;
  }
  range(min, max) {
    return min + this.next() * (max - min);
  }
  normal(mean = 0, std = 1) {
    const u1 = this.next();
    const u2 = this.next();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return mean + z * std;
  }
}

/**
 * Sample a point along a polyline by parameter t [0,1]
 */
export function samplePolylinePoint(points, t) {
  if (points.length === 1) return { x: points[0].x, y: points[0].y };
  const scaled = Math.max(0, Math.min(1, t)) * (points.length - 1);
  const index = Math.min(points.length - 2, Math.floor(scaled));
  const local = scaled - index;
  const p0 = points[index];
  const p1 = points[index + 1];
  return {
    x: p0.x + (p1.x - p0.x) * local,
    y: p0.y + (p1.y - p0.y) * local
  };
}

/**
 * Compute unit tangent at a point on the polyline
 */
export function samplePolylineTangent(points, t) {
  const prev = samplePolylinePoint(points, Math.max(0, t - 0.02));
  const next = samplePolylinePoint(points, Math.min(1, t + 0.02));
  const dx = next.x - prev.x;
  const dy = next.y - prev.y;
  const len = Math.hypot(dx, dy) || 1;
  return { x: dx / len, y: dy / len };
}

/**
 * Adjust color based on simple lighting direction
 */
export function adjustColorForLighting(baseColor, faceBox, position, tangent, style) {
  // Simple top-down lighting model
  const lightDir = { x: 0, y: -1 };
  const normal = { x: tangent.y, y: -tangent.x };
  const NdotL = normal.x * lightDir.x + normal.y * lightDir.y;
  const diffuse = 0.7 + 0.3 * Math.max(0, NdotL);
  const specular = Math.pow(Math.max(0, NdotL), 16) * 0.3;

  // Variation from style and randomness
  const highlightRoll = Math.random();
  let r = baseColor.r * diffuse;
  let g = baseColor.g * diffuse;
  let b = baseColor.b * diffuse;

  if (highlightRoll < (style.highlightRatio || 0.18)) {
    r = Math.min(255, r * 1.25);
    g = Math.min(255, g * 1.22);
    b = Math.min(255, b * 1.18);
  } else if (highlightRoll > 1 - (style.shadowRatio || 0.22)) {
    r = r * 0.82;
    g = g * 0.85;
    b = b * 0.88;
  }

  // Apply color variation
  const variation = style.colorVariation || 0.12;
  r = Math.round(Math.max(0, Math.min(255, r + (Math.random() - 0.5) * 51 * variation)));
  g = Math.round(Math.max(0, Math.min(255, g + (Math.random() - 0.5) * 51 * variation)));
  b = Math.round(Math.max(0, Math.min(255, b + (Math.random() - 0.5) * 51 * variation)));

  return { r, g, b };
}

/**
 * Generate hair strokes for a single eyebrow
 */
export function createHairStrokes(brow, style, baseColor, faceBox, options = {}) {
  const rng = new SeededRandom(options.seed || Date.now());
  const strokes = [];
  const tangents = samplePolylineTangents(brow.centerPoints);
  const density = style.hairDensity || 1.0;
  const lengthBase = style.hairLengthBase || 1.0;
  const lengthVar = style.hairLengthVar || 0.25;
  const curlAmount = style.curlAmount || 0.07;
  const taperStrength = style.taperStrength || 0.45;

  // Determine number of strokes based on brow box width and density
  const baseStrandCount = Math.max(30, Math.floor(brow.box.w * density * 0.8));
  const strandsPerStep = Math.max(3, Math.floor(brow.box.h * 0.08));

  for (let i = 0; i < baseStrandCount; i++) {
    const t = i / (baseStrandCount - 1);
    const pt = samplePolylinePoint(brow.centerPoints, t);
    const tan = tangents[Math.min(tangents.length - 1, Math.floor(t * tangents.length))] || { x: 1, y: 0 };
    const normal = { x: tan.y, y: -tan.x };

    // Local thickness at this point
    const thicknessIdx = Math.floor(t * brow.thicknesses.length);
    const localThickness = brow.thicknesses[Math.min(thicknessIdx, brow.thicknesses.length - 1)] || brow.box.h * 0.2;

    // Distribute strands across the brow width at this cross-section
    const countAtT = Math.max(1, Math.floor(strandsPerT * (1 - Math.abs(t - 0.5) * 0.8)));
    for (let s = 0; s < countAtT; s++) {
      // Offset from center line (Gaussian-ish)
      const offsetParam = (s + 0.5) / countAtT; // 0..1 across width
      const offset = (offsetParam - 0.5) * localThickness * (0.9 + rng.normal(0, 0.15));

      // Starting point (slightly above skin to mimic hair root)
      const rootOffset = localThickness * 0.02;
      const start = {
        x: pt.x + normal.x * offset - tan.x * rootOffset,
        y: pt.y + normal.y * offset - tan.y * rootOffset
      };

      // Strand length with variation
      const length = localThickness * 0.6 * lengthBase * (1 + rng.normal(0, lengthVar));

      // End point
      const end = {
        x: pt.x + normal.x * offset + tan.x * length,
        y: pt.y + normal.y * offset + tan.y * length
      };

      // Control point for subtle curl
      const curl = curlAmount * localThickness * 0.5;
      const control = {
        x: (start.x + end.x) / 2 + (rng.next() - 0.5) * curl,
        y: (start.y + end.y) / 2 + (rng.next() - 0.5) * curl
      };

      // Thickness along strand (taper from root to tip)
      const thickness = localThickness * 0.05 * (1 - t * taperStrength) * (0.7 + rng.next() * 0.6);
      const alpha = 0.55 + rng.next() * 0.4;

      // Color lighting
      const color = adjustColorForLighting(baseColor, faceBox, start, tan, style);

      strokes.push({ start, control, end, thickness, alpha, color });
    }
  }

  return strokes;
}

/**
 * Sample tangent vectors for each center point
 */
function samplePolylineTangents(points) {
  const tangents = [];
  for (let i = 0; i < points.length; i++) {
    const prev = points[Math.max(0, i - 1)];
    const next = points[Math.min(points.length - 1, i + 1)];
    const dx = next.x - prev.x;
    const dy = next.y - prev.y;
    const len = Math.hypot(dx, dy) || 1;
    tangents.push({ x: dx / len, y: dy / len });
  }
  return tangents;
}

/**
 * Render generated strokes onto a canvas context
 */
export function renderHairStrokes(ctx, strokes) {
  // Group strokes by similar properties to reduce state changes? Simple version:
  strokes.forEach(s => {
    ctx.beginPath();
    ctx.moveTo(s.start.x, s.start.y);
    ctx.quadraticCurveTo(s.control.x, s.control.y, s.end.x, s.end.y);
    ctx.strokeStyle = `rgba(${s.color.r}, ${s.color.g}, ${s.color.b}, ${s.alpha})`;
    ctx.lineWidth = s.thickness;
    ctx.lineCap = 'round';
    ctx.stroke();
  });
}

/**
 * Create an offscreen canvas with strokes pre-rasterized (performance)
 */
export function rasterizeStrokes(strokes, width, height, options = {}) {
  const offscreen = new OffscreenCanvas(width, height);
  const ctx = offscreen.getContext('2d');
  renderHairStrokes(ctx, strokes);
  return offscreen;
}
