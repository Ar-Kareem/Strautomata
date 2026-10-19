/**
 * Rating estimate for a user automaton against opponents with known (fixed) ratings.
 *
 * Model: Bradley-Terry / Elo logistic, P(user beats opp) = 1 / (1 + 10^((R_opp - R) / 400)).
 * The user's rating is the maximum-likelihood R given the observed scores, with one virtual
 * draw against the mean opponent rating as a weak prior so the estimate stays finite after
 * an all-win or all-loss streak. The 95% interval is a percentile bootstrap over the results.
 */

export interface RatedResult {
  opponentRating: number;
  /** 1 = win (incl. opponent faults), 0.5 = draw, 0 = loss (incl. own faults) */
  score: number;
}

export interface RatingEstimate {
  rating: number;
  low: number;
  high: number;
  n: number;
}

const LN10_400 = Math.log(10) / 400;

const expected = (r: number, opp: number): number => 1 / (1 + Math.pow(10, (opp - r) / 400));

const mle = (results: RatedResult[], priorRating: number, priorWeight: number): number => {
  let r = priorRating;
  for (let iter = 0; iter < 60; iter += 1) {
    let grad = priorWeight * (0.5 - expected(r, priorRating)) * LN10_400;
    let hess = -priorWeight * expected(r, priorRating) * (1 - expected(r, priorRating)) * LN10_400 * LN10_400;
    for (const res of results) {
      const p = expected(r, res.opponentRating);
      grad += (res.score - p) * LN10_400;
      hess -= p * (1 - p) * LN10_400 * LN10_400;
    }
    if (Math.abs(hess) < 1e-12) {
      break;
    }
    const step = Math.max(-200, Math.min(200, -grad / hess));
    r += step;
    if (Math.abs(step) < 0.01) {
      break;
    }
  }
  return r;
};

/** deterministic small PRNG so the interval does not jitter between renders */
const mulberry32 = (seed: number) => {
  let a = seed >>> 0;
  return (): number => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

export const estimateRating = (results: RatedResult[], bootstraps = 300): RatingEstimate | null => {
  if (results.length === 0) {
    return null;
  }
  const priorRating = results.reduce((sum, r) => sum + r.opponentRating, 0) / results.length;
  const rating = mle(results, priorRating, 1);
  const rand = mulberry32(42);
  const samples: number[] = [];
  for (let b = 0; b < bootstraps; b += 1) {
    const resampled: RatedResult[] = [];
    for (let i = 0; i < results.length; i += 1) {
      resampled.push(results[Math.floor(rand() * results.length)]);
    }
    samples.push(mle(resampled, priorRating, 1));
  }
  samples.sort((a, b) => a - b);
  const q = (p: number): number => samples[Math.min(samples.length - 1, Math.max(0, Math.floor(p * samples.length)))];
  return { rating, low: q(0.025), high: q(0.975), n: results.length };
};

/** Opponent order that spreads across the strength range (strongest, weakest, median, ...). */
export const spreadOrder = <T>(sortedByStrength: T[]): T[] => {
  const out: T[] = [];
  const queue: [number, number][] = [[0, sortedByStrength.length - 1]];
  const seen = new Set<number>();
  const push = (i: number) => {
    if (i >= 0 && i < sortedByStrength.length && !seen.has(i)) {
      seen.add(i);
      out.push(sortedByStrength[i]);
    }
  };
  while (queue.length) {
    const [lo, hi] = queue.shift()!;
    if (lo > hi) {
      continue;
    }
    push(lo);
    push(hi);
    const mid = Math.floor((lo + hi) / 2);
    push(mid);
    if (mid - 1 > lo) {
      queue.push([lo + 1, mid - 1]);
    }
    if (hi - 1 > mid) {
      queue.push([mid + 1, hi - 1]);
    }
  }
  return out;
};
