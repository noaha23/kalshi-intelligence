# Legal, Compliance, and Tax Considerations

> **IMPORTANT DISCLAIMER:** This document is for educational and research purposes only. **Nothing in this document constitutes legal, tax, or financial advice.** Tax treatment of event contracts is genuinely unsettled territory. Consult a qualified tax professional and/or attorney before making any trading or tax decisions. Laws and regulations change; this document reflects understanding as of early 2026 and may be outdated.

---

## 1. CFTC Regulation

Kalshi is a CFTC-regulated Designated Contract Market (DCM), placing it under the same federal regulatory framework as major exchanges like CME Group, CBOE, and ICE.

### Regulatory Status

| Attribute | Detail |
|---|---|
| Regulator | Commodity Futures Trading Commission (CFTC) |
| Designation | Designated Contract Market (DCM) |
| Comparable exchanges | CME Group, CBOE, ICE (same DCM framework) |
| Event contracts ruling | CFTC dropped appeal May 2025; event contracts including political markets are legal |
| Contract type | Binary event contracts ($0 or $1 payout) |
| Customer fund protection | Segregated accounts required under CFTC Core Principles |

### What DCM Status Means in Practice

- Kalshi must comply with all CFTC Core Principles: financial integrity, market surveillance, customer protection, system safeguards, and emergency authority.
- Customer funds are held in segregated accounts, separate from Kalshi's operating capital.
- The exchange is subject to CFTC audits, examinations, and enforcement actions.
- Market manipulation and fraud are federal offenses under the Commodity Exchange Act (CEA).
- All contract listings must be approved through the CFTC self-certification or approval process.

---

## 2. Eligible Contract Participants

### Who Can Trade on Kalshi

| Requirement | Detail |
|---|---|
| Minimum age | 18 years old |
| Citizenship/residency | US persons (citizens, permanent residents, or those with qualifying US presence) |
| Identity verification | Government-issued ID, Social Security Number, date of birth |
| Address | US residential address required |
| Funding | US bank account (ACH) or debit card |
| International access | Not available -- Kalshi serves US persons only |

### State Restrictions

| Status | Detail |
|---|---|
| Fully available | Most US states |
| Restricted/limited | Some states have specific restrictions on certain contract types |
| Active litigation | Connecticut (state-level challenge to event contracts) |

State-level restrictions can change independently of federal regulation. Verify your state's current status on Kalshi's website before opening an account.

### Corporate and Institutional Accounts

Corporate accounts are available with additional documentation requirements. High-volume traders and market makers may qualify for maker rebates and FIX protocol access.

---

## 3. Tax Treatment

> **This section describes the current landscape of uncertainty. It is NOT tax advice. Consult a CPA or tax attorney.**

### What Kalshi Reports

| Tax Document | Threshold | Content |
|---|---|---|
| **1099-MISC** | Net winnings > $600 in a calendar year | Reported in Box 3 ("Other Income") |
| **No 1099-B** | N/A | Kalshi does not issue 1099-B (brokerage) forms |

Kalshi reports winnings as "Other Income" on Form 1099-MISC, not as brokerage proceeds on Form 1099-B. This reporting treatment has implications for how traders should file.

### Default Reporting: Ordinary Income

| Line Item | Form | Description |
|---|---|---|
| Schedule 1, Line 8z | Form 1040 | "Other Income" -- where 1099-MISC amounts are reported |
| Tax rate | Ordinary income rates | Taxed at your marginal income tax rate |

Under the default treatment consistent with Kalshi's 1099-MISC reporting, winnings are taxed as ordinary income at your marginal tax rate.

### Section 1256 Contracts: The 60/40 Question

Section 1256 of the Internal Revenue Code provides favorable tax treatment for "regulated futures contracts" traded on CFTC-designated exchanges:

| Treatment | Rate |
|---|---|
| 60% of gains | Long-term capital gains rate (max 20%) |
| 40% of gains | Short-term capital gains rate (ordinary income) |

**The argument for Section 1256 treatment:**
- Kalshi is a CFTC-regulated DCM.
- Contracts traded on CFTC-regulated exchanges are generally Section 1256 contracts.
- Binary event contracts are listed and traded on a DCM.
- If event contracts qualify, traders benefit from the blended 60/40 rate regardless of holding period.

**The argument against Section 1256 treatment:**
- The IRS has not issued specific guidance confirming event contracts qualify.
- Event contracts may not meet the statutory definition of "regulated futures contract."
- No court case, private letter ruling, or IRS notice addresses this question directly.
- Claiming Section 1256 treatment without IRS confirmation carries audit risk.

**Current consensus:** Most tax professionals advise reporting as ordinary income (Schedule 1, Line 8z) until the IRS provides clarity. Some aggressive tax positions exist, but they are untested. The safest approach is to report as ordinary income and retain documentation to amend if guidance changes.

### Form 1099-B Reporting

Kalshi does **not** issue Form 1099-B. This means:
- Kalshi does not report cost basis to the IRS.
- Traders are responsible for tracking their own cost basis for all positions.
- If you choose to report on Schedule D (capital gains), you must maintain your own records of purchase price, sale price, and fees for every transaction.

### Wash Sale Rules

| Question | Status |
|---|---|
| Do wash sale rules apply to event contracts? | Unknown -- no IRS guidance |
| Practical concern | If you sell a YES contract at a loss and repurchase the same YES contract within 30 days, wash sale rules might disallow the loss deduction |
| Conservative approach | Track potential wash sale triggers; do not rely on loss harvesting strategies until rules are clarified |

Wash sale rules under IRC Section 1091 apply to "stock or securities." Whether event contracts constitute "securities" for wash sale purposes is an open question. If Section 1256 treatment applies, wash sale rules do not apply (Section 1256 contracts are marked to market annually).

### Loss Deduction Rules

| Question | Status |
|---|---|
| Can losses offset winnings? | Likely yes (net against other Kalshi gains within the same tax year) |
| Can losses offset other income? | Unclear -- depends on classification as ordinary loss, capital loss, or gambling loss |
| Gambling loss limitation | If treated as gambling: losses deductible only to the extent of gambling winnings, must itemize |
| Capital loss limitation | If treated as capital losses: $3,000 annual deduction limit against ordinary income, unlimited carryforward |

---

## 4. CFTC Position Limits

| Attribute | Detail |
|---|---|
| Explicit position limits | Kalshi does not publish explicit per-contract position limits for most markets |
| Exchange-level limits | Kalshi may impose limits as part of its DCM self-regulatory obligations |
| CFTC large trader reporting | Standard CFTC large trader reporting thresholds apply |
| Practical limit | Extremely large positions relative to market open interest may trigger compliance review |

Position limits vary by contract type and may be adjusted by Kalshi or the CFTC at any time. The CFTC's general position limit framework (Part 150 of CFTC regulations) applies to certain referenced contracts, though event contracts may not fall under the same specific thresholds as traditional commodity futures.

---

## 5. No Leverage or Margin

| Attribute | Detail |
|---|---|
| Margin trading | Not available on Kalshi |
| Leverage | None -- all positions are fully collateralized |
| Maximum loss per YES contract | Purchase price (e.g., buy at $0.65, max loss is $0.65) |
| Maximum loss per NO contract | Purchase price (e.g., buy NO at $0.35, max loss is $0.35) |
| Collateral requirement | Full contract value paid at time of purchase |

Because YES + NO = $1.00, buying a YES contract at $0.65 is economically equivalent to selling a NO contract at $0.35. In both cases, the maximum loss is the premium paid. There is no scenario where a trader owes more than their initial investment on any single contract.

---

## 6. Anti-Manipulation Rules

The Commodity Exchange Act and CFTC regulations prohibit market manipulation on all DCMs, including Kalshi.

### CFTC Regulation 180.1

Regulation 180.1 is the CFTC's broad anti-manipulation and anti-fraud rule, modeled after SEC Rule 10b-5. It prohibits:

| Prohibited Activity | Description |
|---|---|
| **Price manipulation** | Trading with the intent to artificially influence prices |
| **Spoofing** | Placing orders with the intent to cancel before execution (CEA Section 4c(a)(5)) |
| **Wash trading** | Trading with yourself to create artificial volume or misleading activity |
| **Front-running** | Trading ahead of known incoming customer orders |
| **Material misrepresentation** | Spreading false information to influence market prices |
| **Fraud** | Any scheme to defraud in connection with a swap, contract of sale, or commodity |

### Penalties

| Violation | Potential Penalty |
|---|---|
| Civil enforcement (CFTC) | Disgorgement of profits, civil monetary penalties (up to $1M+ per violation), trading bans |
| Criminal prosecution (DOJ) | Up to 25 years imprisonment for manipulation, up to 10 years for spoofing |

### For Systematic Traders

Automated trading systems must be designed to avoid inadvertent violations:

- **Spoofing risk:** Rapid order placement and cancellation patterns can resemble spoofing even if unintentional. Implement safeguards to ensure order-to-fill ratios remain reasonable.
- **Wash trading risk:** If running multiple strategies, ensure they cannot trade against each other.
- **Multiple accounts:** Prohibited. One account per person. Do not create separate accounts for different strategies.

---

## 7. Record-Keeping Requirements

### What to Track

Regardless of how you ultimately report for tax purposes, maintain comprehensive records:

| Record | Detail |
|---|---|
| Complete transaction history | Every buy, sell, and settlement with timestamps |
| Contract descriptions | Market name, ticker, outcome description |
| Prices | Entry price, exit price (or settlement value of $0 / $1) |
| Quantities | Number of contracts per transaction |
| Fees | Per-transaction fees and cumulative fees |
| Cost basis | Purchase price + fees for each position |
| Net P&L | Per-contract and cumulative profit/loss |
| Account statements | Monthly/annual statements from Kalshi |
| Tax documents | 1099-MISC received from Kalshi |
| Deposits and withdrawals | All funding and withdrawal transactions |

### Retention Period

The IRS generally requires records be retained for 3 years from the date of filing, or 6 years if income is underreported by more than 25%. For safety, retain all trading records for at least 7 years.

### Trade Log Implementation

Build or use a system that captures:

```
Date/Time | Market | Direction | Quantity | Entry Price | Exit/Settlement | Fees | Net P&L | Cost Basis
```

The `kalshi-intelligence` system should log all trades automatically if executing via API. For manual trades, maintain a parallel spreadsheet or database.

---

## 8. Disclaimer Requirements

### For This Project

This project and all associated documentation, code, and outputs:

- **Are not financial advice.** Nothing produced by this system constitutes a recommendation to buy, sell, or hold any contract.
- **Are for educational and research use only.** The system is a tool for analysis, not a trading signal service.
- **Do not guarantee any outcome.** Historical performance, backtests, and model outputs do not predict future results.
- **Are not a substitute for professional advice.** Consult a licensed financial advisor, CPA, or attorney for decisions about trading, taxes, or compliance.

### For Any Outputs or Reports

If sharing analysis, reports, or model outputs with others, include at minimum:

> This analysis is for educational and research purposes only. It does not constitute financial, investment, or trading advice. Event contract trading involves risk of total loss of premium on every contract. Consult a qualified professional before making trading decisions.

---

## 9. Risk Disclosure

### Total Loss of Premium

On every binary contract traded on Kalshi, the buyer can lose 100% of their premium:

| Scenario | Outcome |
|---|---|
| Buy YES at $0.65 -- event occurs | Receive $1.00 (profit: $0.35 minus fees) |
| Buy YES at $0.65 -- event does not occur | Receive $0.00 (loss: $0.65 plus fees) |
| Buy NO at $0.35 -- event does not occur | Receive $1.00 (profit: $0.65 minus fees) |
| Buy NO at $0.35 -- event occurs | Receive $0.00 (loss: $0.35 plus fees) |

There is no partial settlement. Every contract pays $1.00 or $0.00. Fees are incurred regardless of outcome.

### Additional Risk Factors

| Risk | Detail |
|---|---|
| **Estimation error** | Your probability estimates may be wrong; the market may be more efficient than you think |
| **Fee drag** | Fees reduce expected value on every trade; thin edges can become negative after fees |
| **Liquidity risk** | You may not be able to exit a position at a fair price before settlement |
| **Concentration risk** | Correlated positions can all lose simultaneously |
| **Platform risk** | Exchange downtime, API outages, or settlement disputes |
| **Regulatory risk** | CFTC rule changes, state restrictions, or tax law changes |
| **Behavioral risk** | Overconfidence, overtrading, revenge trading, and other behavioral biases |

---

## 10. Summary of Key Compliance Points

| Area | Key Point |
|---|---|
| Regulation | CFTC-regulated DCM; same framework as CME/CBOE |
| Eligibility | US persons 18+; some state restrictions |
| Tax reporting | Kalshi issues 1099-MISC for winnings > $600; reported as Other Income |
| Section 1256 | Potentially applicable (60/40 capital gains split) but IRS has not confirmed; report conservatively |
| Wash sales | Applicability unknown; track potential triggers |
| Position limits | Not explicitly published; CFTC rules apply |
| Leverage | None; all positions fully collateralized |
| Anti-manipulation | CFTC Regulation 180.1; spoofing, wash trading, and manipulation are federal offenses |
| Records | Keep complete transaction logs for 7+ years |
| Risk | Total loss of premium is possible on every contract |

---

## 11. Actionable Next Steps

### Before Trading

- [ ] Verify your state allows Kalshi trading.
- [ ] Complete KYC verification (government ID, SSN, proof of address).
- [ ] Consult a tax professional about your specific situation.
- [ ] Ask your CPA specifically about Section 1256 treatment for Kalshi event contracts.
- [ ] Set up a record-keeping system for all transactions.

### Compliance Checklist for Systematic Trading

| Item | Status |
|---|---|
| Single account verified (no duplicate accounts) | [ ] |
| API rate limits understood and implemented | [ ] |
| No spoofing patterns in order logic | [ ] |
| No wash trading possible in algorithm | [ ] |
| Transaction logging operational | [ ] |
| Fee tracking integrated | [ ] |
| Tax record export capability built | [ ] |
| Quarterly tax estimate process established | [ ] |
| CPA/tax professional identified and consulted | [ ] |

### Tax Calendar

| Date | Action |
|---|---|
| **January** | Receive 1099-MISC from Kalshi (if applicable) |
| **April 15** | Federal tax filing deadline (or extension) |
| **Quarterly** | Estimated tax payments if withholding is insufficient (April 15, June 15, Sept 15, Jan 15) |
| **Year-round** | Maintain transaction records contemporaneously |

**Bottom line:** The regulatory foundation is solid -- CFTC DCM status is as legitimate as it gets for an event contract exchange. Tax treatment remains a genuine gray area. Report conservatively, keep meticulous records, and get professional tax advice before making assumptions about how your trading income will be taxed.
