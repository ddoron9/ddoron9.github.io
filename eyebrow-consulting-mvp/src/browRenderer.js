/**
 * Brow Renderer: integrates hair-stroke generation into the eyebrow studio
 */

import {
  createHairStrokes,
  renderHairStrokes,
  rasterizeStrokes
} from './hairStrokeGenerator.js';

/**
 * Draw eyebrow using hair-stroke procedural method
 */
export function drawEyebrowByHairStrokes(ctx, brow, style, color, side, faceBox, options = {}) {
  // Ensure we have a valid geometry
  const geometry = normalizeBrowGeometry(brow, side);

  // Generate strokes (with optional seed for consistency)
  const strokes = createHairStrokes(geometry, style, color, faceBox, {
    seed: options.seed
  });

  // Render directly or use rasterized layer
  if (options.useRasterization) {
    const raster = rasterizeStrokes(strokes, ctx.canvas.width, ctx.canvas.height);
    ctx.drawImage(raster, 0, 0);
  } else {
    // Save context state
    ctx.save();
    // Set global composite for natural blending
    ctx.globalCompositeOperation = 'multiply';
    // Optionally apply an overall opacity from style
    const alpha = 0.6 + (style.opacity || 0.8) * 0.35;
    ctx.globalAlpha = alpha;
    // Render
    renderHairStrokes(ctx, strokes);
    ctx.restore();
  }
}

/**
 * Fallback: emphasize existing drawEyebrow signature compatibility
 */
export function drawEyebrow(ctx, region, style, color, side, faceBox) {
  // Current implementation uses hair strokes; if needed, fallback to SVG method:
  if (window.__eyebrowStudioDebug && window.__eyebrowStudioDebug.drawEyebrowOriginal) {
    window.__eyebrowStudioDebug.drawEyebrowOriginal(ctx, region, style, color, side, faceBox);
  } else {
    // If hair strokes not ready, draw a simple placeholder
    ctx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, 0.3)`;
    ctx.fillRect(region.x, region.y, region.w, region.h);
  }
}

/**
 * Optional: attach debug overlay (landmarks, geometry, strokes)
 */
export function drawDebugOverlay(ctx, analysisData, options = {}) {
  if (!options.show) return;

  const { mode, faceBox, brows } = analysisData;

  // Draw face box
  ctx.strokeStyle = '#0f8b79';
  ctx.lineWidth = 2;
  ctx.strokeRect(faceBox.x, faceBox.y, faceBox.w, faceBox.h);

  // Draw brow geometry
  ['left', 'right'].forEach(side => {
    const brow = normalizeBrowGeometry(brows[side], side);
    ctx.strokeStyle = side === 'left' ? '#ba3b2f' : '#0b6659';
    ctx.lineWidth = 1;
    ctx.beginPath();
    brow.centerPoints.forEach((p, i) => {
      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();

    // Draw center points
    ctx.fillStyle = ctx.strokeStyle;
    brow.centerPoints.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  });
}
