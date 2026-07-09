"""
Behavioral Biometric Fraud Shield — Scoring Engine
IDBI Innovate 2026 — Track 05: Wildcard Open Innovation

Authenticates a session by comparing live keystroke dynamics (dwell time and
flight time) against an enrolled baseline, producing a 0-100 Trust Score and
a decision (Authenticate / Step-up verification / Block).

In production, the frontend captures raw keydown/keyup timestamps during
passphrase entry and forwards them here; this module contains no browser
dependencies so it can run as a FastAPI endpoint or batch job.
"""

from dataclasses import dataclass
from typing import List
import statistics


@dataclass
class KeystrokeSample:
    dwell: List[float]   # ms each key was held, one per character
    flight: List[float]  # ms between key-up and next key-down
    total_ms: float


@dataclass
class Baseline:
    dwell_mean: List[float]
    dwell_std: List[float]
    flight_mean: List[float]
    flight_std: List[float]
    total_mean: float


@dataclass
class VerificationResult:
    trust_score: float
    decision: str
    mean_abs_z: float
    dwell_deviation_pct: float
    total_deviation_pct: float
    explanation: List[str]


MIN_STD_MS = 6.0          # floor to avoid divide-by-near-zero on very consistent enrollment
Z_CLIP = 6.0               # cap per-feature z-score influence from extreme outliers
PENALTY_MULTIPLIER = 12    # tuned so natural session variance lands in step-up, not block
AUTH_THRESHOLD = 75
STEPUP_THRESHOLD = 45


def build_baseline(samples: List[KeystrokeSample]) -> Baseline:
    n_dwell = len(samples[0].dwell)
    n_flight = len(samples[0].flight)

    dwell_mean, dwell_std = [], []
    for i in range(n_dwell):
        vals = [s.dwell[i] for s in samples]
        dwell_mean.append(statistics.mean(vals))
        dwell_std.append(max(statistics.pstdev(vals), MIN_STD_MS))

    flight_mean, flight_std = [], []
    for i in range(n_flight):
        vals = [s.flight[i] for s in samples]
        flight_mean.append(statistics.mean(vals))
        flight_std.append(max(statistics.pstdev(vals), MIN_STD_MS))

    total_mean = statistics.mean(s.total_ms for s in samples)

    return Baseline(dwell_mean, dwell_std, flight_mean, flight_std, total_mean)


def verify_session(sample: KeystrokeSample, baseline: Baseline) -> VerificationResult:
    dwell_z = [
        (v - baseline.dwell_mean[i]) / baseline.dwell_std[i]
        for i, v in enumerate(sample.dwell)
    ]
    flight_z = [
        (v - baseline.flight_mean[i]) / baseline.flight_std[i]
        for i, v in enumerate(sample.flight)
    ]
    all_z = [min(abs(z), Z_CLIP) for z in dwell_z + flight_z]
    mean_abs_z = statistics.mean(all_z)

    trust_score = max(0.0, min(100.0, 100 - mean_abs_z * PENALTY_MULTIPLIER))

    mean_dwell_sample = statistics.mean(sample.dwell)
    mean_dwell_baseline = statistics.mean(baseline.dwell_mean)
    dwell_deviation_pct = (mean_dwell_sample - mean_dwell_baseline) / mean_dwell_baseline * 100

    total_deviation_pct = (sample.total_ms - baseline.total_mean) / baseline.total_mean * 100

    if trust_score >= AUTH_THRESHOLD:
        decision = "Authenticated"
    elif trust_score >= STEPUP_THRESHOLD:
        decision = "Step-up verification"
    else:
        decision = "Blocked — flagged for review"

    explanation = [
        f"Dwell time {dwell_deviation_pct:+.0f}% vs baseline",
        f"Typing duration {total_deviation_pct:+.0f}% vs baseline",
        f"Overall rhythm deviation: {mean_abs_z:.2f}\u03c3 from baseline",
    ]

    return VerificationResult(
        trust_score=round(trust_score, 1),
        decision=decision,
        mean_abs_z=round(mean_abs_z, 2),
        dwell_deviation_pct=round(dwell_deviation_pct, 1),
        total_deviation_pct=round(total_deviation_pct, 1),
        explanation=explanation,
    )


if __name__ == "__main__":
    # Illustrative example — in production these come from real captured keystroke events
    enroll = [
        KeystrokeSample(dwell=[92, 88, 95, 90, 87, 93, 91, 89, 94, 90, 88, 92, 96, 89, 91],
                         flight=[118, 122, 115, 120, 119, 116, 121, 117, 120, 118, 115, 119, 122, 117],
                         total_ms=2950),
        KeystrokeSample(dwell=[90, 91, 93, 88, 89, 92, 90, 91, 93, 89, 90, 91, 94, 88, 92],
                         flight=[120, 119, 117, 121, 118, 117, 119, 120, 118, 119, 117, 120, 121, 118],
                         total_ms=2940),
        KeystrokeSample(dwell=[93, 89, 91, 92, 88, 90, 92, 90, 91, 91, 89, 93, 92, 90, 89],
                         flight=[117, 121, 119, 118, 120, 119, 118, 119, 121, 117, 118, 120, 119, 119],
                         total_ms=2960),
    ]
    baseline = build_baseline(enroll)

    genuine_attempt = KeystrokeSample(
        dwell=[91, 90, 92, 91, 88, 91, 90, 90, 92, 90, 89, 92, 93, 90, 90],
        flight=[119, 120, 118, 119, 119, 118, 119, 118, 119, 118, 117, 119, 120, 118],
        total_ms=2955,
    )
    result = verify_session(genuine_attempt, baseline)
    print("Genuine attempt:", result)

    impostor_attempt = KeystrokeSample(
        dwell=[35, 38, 33, 40, 36, 34, 37, 39, 35, 36, 38, 34, 37, 36, 35],
        flight=[42, 45, 40, 44, 41, 43, 42, 44, 41, 43, 40, 42, 44, 41],
        total_ms=1120,
    )
    result2 = verify_session(impostor_attempt, baseline)
    print("Impostor attempt:", result2)
