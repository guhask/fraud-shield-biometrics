# Behavioral Biometric Fraud Shield

**IDBI Innovate 2026 — Track 05: Wildcard Open Innovation**
**Team Pulse Capital Labs**

Authenticates banking sessions by *how* a customer types, not just what they type — catching account takeover before a fraudulent transaction is ever submitted.

🔗 **Live demo:** [fraudshieldbiometrics.netlify.app](https://fraudshieldbiometrics.netlify.app)

---

## The problem

Most bank fraud systems rely on transaction rules (amount/velocity thresholds) or device fingerprinting — both are reactive, and both add friction (OTPs, step-up checks) to *every* customer, not just risky ones.

## The idea

Every person has a subtly unique typing rhythm — how long they hold each key (**dwell time**) and the gaps between keystrokes (**flight time**). This project captures that rhythm passively during normal login/transaction entry, compares it against an enrolled baseline in real time, and produces an explainable **Trust Score (0–100)**:

- **75–100 → Authenticated**, zero added friction
- **45–74 → Step-up verification**, OTP triggered
- **0–44 → Blocked**, session flagged for fraud ops review

No new hardware, no separate biometric sensor, no customer-visible change unless risk is actually detected.

## What's in this repo

| File | Description |
|---|---|
| `fraud_shield_dashboard.html` | Self-contained interactive prototype — live keystroke capture, enrollment, verification, and session log. Open directly in any browser, no build step. |
| `fraud_shield_scoring_engine.py` | Standalone Python implementation of the same trust-scoring logic, framework-agnostic and ready to wrap as a FastAPI endpoint. |

## Try it yourself

1. Open the [live demo](https://fraudshieldbiometrics.netlify.app) (or `fraud_shield_dashboard.html` locally)
2. **Enroll:** type the passphrase `SecurePulse2026` three times to build your rhythm baseline
3. **Verify:** type it again naturally — watch your Trust Score
4. **Try it as an impostor:** type noticeably faster, slower, or hunt-and-peck, and watch the score and decision change in real time

## How the scoring works

1. Capture keydown/keyup timestamps for each character typed
2. Compute dwell time (hold duration) and flight time (inter-key gap) per keystroke
3. Build a baseline mean + standard deviation per keystroke position from 3 enrollment samples
4. On verification, compute a per-feature z-score deviation from baseline
5. Aggregate into a 0–100 Trust Score; route to Authenticate / Step-up / Block accordingly

See `fraud_shield_scoring_engine.py` for the full implementation, including a runnable example.

## Validation

Internal simulation across genuine and impostor typing patterns:

- Genuine sessions: consistently scored **88–98** (Authenticated)
- Natural session variance (tired/rushed typing): scored **65–75** (Step-up, not blocked)
- Impostor sessions (distinctly different rhythm): scored **0–28** (Blocked)

## Roadmap

- Integrate with a real core banking session/auth layer
- Calibrate thresholds against a real user population
- Extend behavioral signals to mobile touch/swipe and transaction-level step-up
- Pilot the session log with a fraud operations team

## Tech stack

JavaScript (browser-native keystroke capture) · Python (portable scoring engine) · statistical anomaly detection (z-score baseline comparison)

---

Built for IDBI Innovate 2026 by **Pulse Capital Labs**.
