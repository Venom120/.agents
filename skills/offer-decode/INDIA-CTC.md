# India CTC → in-hand reference

> **Current financial year: FY 2026-27 (April 2026 to March 2027, AY 2027-28).** Values checked on **2026-11-06**. Budget 2026 was reported (secondary sources) as leaving the new-regime slabs, the ₹12 lakh rebate limit and the ₹75,000 standard deduction unchanged from the Finance Act 2025. **Verify against the Finance Act 2026 or [incometax.gov.in](https://www.incometax.gov.in) before using these for a real decision**, and if the current date is past March 2027, look up the next year's rules first.

**Prefer the calculator over mental arithmetic:** `python3 scripts/ctc.py --fixed <annual fixed> [--variable <annual bonus>] [--regime both --rent <annual rent> --metro]`. It keeps the rules per financial year in one table, shows every assumption, and has a self-test (`--self-test`).

## Typical components
| Component | Typical value | In-hand? |
|---|---|---|
| Basic | 35–50% of fixed (see the labour-code note below) | Yes |
| HRA | 40–50% of basic | Yes (taxable in the new regime; partly exempt in the old one) |
| Special / flexi allowance | The balancing figure | Yes |
| Employer PF | 12% of PF wage, often capped at 12% of ₹15,000 = ₹1,800/month | No (goes to the PF account) |
| Employee PF | Same base, deducted from salary | Deducted |
| Gratuity | ≈ 4.81% of the gratuity wage | No (paid on leaving after the qualifying service) |
| Insurance premium | Varies | No |
| Variable / performance bonus | % of CTC | Only if earned. Ask for the company's historical payout. If it's unknown, show 0%, 70% and 100% side by side as an **assumption**. |
| Joining bonus | One-time | Yes, once (often with a clawback) |

## Labour codes (in force from 21 Nov 2025)

Under the labour codes, "wages" for PF and gratuity is generally the **higher of basic (+DA) or 50% of total remuneration**, so allowance-heavy structures get a larger PF and gratuity base and slightly lower take-home pay. Sources disagree on how far the central and state rules have been finalised, and employers are restructuring at different speeds. **Ask HR which wage base they use**, and run the calculator with `--wage-rule basic` and `--wage-rule labour-code` if it's unclear. Don't state the rule as settled for a specific employer.

## New regime (default), FY 2026-27
- Standard deduction (salaried): **₹75,000**
- Slabs on taxable income: 0–4 L **0%** · 4–8 L **5%** · 8–12 L **10%** · 12–16 L **15%** · 16–20 L **20%** · 20–24 L **25%** · above 24 L **30%**
- Section 87A rebate: tax is nil if taxable income ≤ **₹12,00,000** (gross salary up to about ₹12.75 L). **Marginal relief** just above it: the tax can't exceed the income above ₹12 L.
- Health and education cess: **4%** of the tax. Surcharge above ₹50 L taxable (10% / 15% / 25%; the new regime caps at 25%).

## Old regime (compute it as a second option)
- Standard deduction **₹50,000**. Slabs: 0–2.5 L 0% · 2.5–5 L 5% · 5–10 L 20% · above 10 L 30%. 87A rebate up to ₹12,500 if taxable ≤ ₹5 L. 4% cess.
- Deductions it allows: **80C** up to ₹1.5 L (employee PF counts), professional tax, and the **HRA exemption** = the least of (a) HRA received, (b) rent paid − 10% of basic, (c) 50% of basic in a metro (Delhi, Mumbai, Kolkata, Chennai) or 40% elsewhere.
- It usually wins only with high rent in a metro plus full 80C. Run `--regime both` and show both.

## Other deductions
- Professional tax: up to **₹2,500/year**, state-dependent (levied in e.g. Karnataka, Maharashtra, West Bengal, Telangana; not in Delhi). Use `--pt 0` where it doesn't apply.

## Method (what the script does)
1. Gross = fixed + variable at the stated payout (+ joining bonus in the year it's paid).
2. Taxable = gross − standard deduction (− HRA exemption, 80C and professional tax in the old regime).
3. Tax = slab tax → 87A rebate or marginal relief → surcharge if any → + 4% cess.
4. Annual in-hand = gross − tax − employee PF − professional tax.
5. Monthly in-hand on **fixed pay only**; variable is shown separately because it pays out later.
