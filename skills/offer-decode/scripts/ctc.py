#!/usr/bin/env python3
"""India CTC -> in-hand calculator for /offer-decode. Standard library only.

    ctc.py --fixed 1200000                                   # new regime, PF capped, PT 2,500
    ctc.py --fixed 1800000 --variable 150000 --regime both --rent 300000 --metro
    ctc.py --fixed 1500000 --pf full --wage-rule labour-code
    ctc.py --self-test

All amounts are annual rupees. "fixed" = basic + HRA + allowances paid in cash (not employer
PF, gratuity, insurance or one-time bonuses).

Rules are kept per financial year in RULES, so a new budget is a one-entry change. Every
entry names its source; VERIFY the current year's entry before relying on it. Surcharge
(income above Rs 50 lakh) is applied without surcharge marginal relief and is flagged.
Estimates for planning only, not tax advice.
"""
import argparse
import sys

RULES = {
    # Source: Finance Act 2025 (Union Budget 2025-26). Budget 2026 reported as leaving the new
    # regime unchanged for FY 2026-27 (secondary sources, checked 2026-11-06). Confirm against
    # the Finance Act 2026 / incometax.gov.in before use.
    "2026-27": {
        "checked": "2026-11-06",
        "source": "Finance Act 2025; Budget 2026 reported no change (verify on incometax.gov.in)",
        "new": {
            "std_deduction": 75_000,
            "slabs": [(400_000, 0.0), (800_000, 0.05), (1_200_000, 0.10), (1_600_000, 0.15),
                      (2_000_000, 0.20), (2_400_000, 0.25), (None, 0.30)],
            "rebate_limit": 1_200_000, "rebate_max": 60_000,
        },
        "old": {
            "std_deduction": 50_000,
            "slabs": [(250_000, 0.0), (500_000, 0.05), (1_000_000, 0.20), (None, 0.30)],
            "rebate_limit": 500_000, "rebate_max": 12_500,
            "limit_80c": 150_000,
        },
        "cess": 0.04,
        "surcharge": [(5_000_000, 0.10), (10_000_000, 0.15), (20_000_000, 0.25)],  # new regime caps at 25%
        "pf_wage_cap_monthly": 15_000,
    },
}
RULES["2025-26"] = RULES["2026-27"]  # same rules (Finance Act 2025)
DEFAULT_FY = "2026-27"


def slab_tax(income, slabs):
    tax, lower = 0.0, 0
    for upper, rate in slabs:
        top = income if upper is None else min(income, upper)
        if top > lower:
            tax += (top - lower) * rate
        if upper is None or income <= upper:
            break
        lower = upper
    return tax


def income_tax(taxable, regime_rules, rules):
    """Return (tax incl. cess, notes)."""
    notes = []
    tax = slab_tax(taxable, regime_rules["slabs"])
    if taxable <= regime_rules["rebate_limit"]:
        tax = max(0.0, tax - regime_rules["rebate_max"])
    elif regime_rules is rules["new"]:
        # 87A marginal relief: tax can't exceed the income above the rebate limit.
        excess = taxable - regime_rules["rebate_limit"]
        if tax > excess:
            tax = excess
            notes.append("87A marginal relief applied")
    sur = 0.0
    for threshold, rate in rules["surcharge"]:
        if taxable > threshold:
            sur = rate
    if sur:
        tax *= 1 + sur
        notes.append(f"surcharge {int(sur * 100)}% applied without surcharge marginal relief; verify")
    return round(tax * (1 + rules["cess"])), notes


def pf_employee(fixed, basic, rule, mode, rules):
    if mode == "none":
        return 0
    wage = basic if rule == "basic" else max(basic, 0.5 * fixed)  # labour codes: higher of basic or 50%
    if mode == "capped":
        wage = min(wage, rules["pf_wage_cap_monthly"] * 12)
    return round(0.12 * wage)


def compute(a, regime, payout):
    rules = RULES[a.fy]
    r = rules[regime]
    basic = a.fixed * a.basic_pct / 100
    hra = basic * a.hra_pct / 100
    variable = a.variable * payout
    gross = a.fixed + variable
    pf = pf_employee(a.fixed, basic, a.wage_rule, a.pf, rules)
    deductions = r["std_deduction"]
    detail = {}
    if regime == "old":
        if a.rent:
            exempt = max(0.0, min(hra, a.rent - 0.10 * basic, (0.50 if a.metro else 0.40) * basic))
            deductions += exempt
            detail["hra_exempt"] = round(exempt)
        sec80c = min(pf + a.extra_80c, r["limit_80c"])
        deductions += sec80c + a.pt
        detail["80c"] = round(sec80c)
    taxable = max(0.0, gross - deductions)
    tax, notes = income_tax(taxable, r, rules)
    annual_in_hand = gross - tax - pf - a.pt
    # Monthly in-hand on fixed pay only (variable usually pays out later).
    tax_fixed, _ = compute_fixed_tax(a, regime, rules, basic, hra, pf)
    monthly_fixed = (a.fixed - tax_fixed - pf - a.pt) / 12
    return {
        "regime": regime, "payout": payout, "gross": round(gross), "taxable": round(taxable),
        "tax": tax, "pf": pf, "pt": a.pt, "annual_in_hand": round(annual_in_hand),
        "monthly_in_hand_fixed": round(monthly_fixed), "notes": notes, **detail,
    }


def compute_fixed_tax(a, regime, rules, basic, hra, pf):
    r = rules[regime]
    deductions = r["std_deduction"]
    if regime == "old":
        if a.rent:
            deductions += max(0.0, min(hra, a.rent - 0.10 * basic, (0.50 if a.metro else 0.40) * basic))
        deductions += min(pf + a.extra_80c, r["limit_80c"]) + a.pt
    return income_tax(max(0.0, a.fixed - deductions), r, rules)


def inr(n):
    s = str(int(round(n)))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


def report(a):
    rules = RULES[a.fy]
    regimes = ["new", "old"] if a.regime == "both" else [a.regime]
    payouts = [0.0, 0.7, 1.0] if a.variable else [0.0]
    print(f"FY {a.fy} · rules checked {rules['checked']} · {rules['source']}")
    print(f"Assumptions: basic {a.basic_pct}% of fixed · HRA {a.hra_pct}% of basic · PF {a.pf} "
          f"({a.wage_rule} wage) · professional tax {inr(a.pt)}"
          + (f" · rent {inr(a.rent)} ({'metro' if a.metro else 'non-metro'})" if a.rent else ""))
    if a.variable:
        print("Variable pay shown at 0%, 70% and 100% payout: an assumption unless the company shares its history.")
    print()
    hdr = f"{'regime':<7}{'variable':>9}{'gross':>13}{'taxable':>13}{'tax':>11}{'emp. PF':>10}{'annual in-hand':>16}{'monthly (fixed)':>17}"
    print(hdr)
    print("-" * len(hdr))
    for reg in regimes:
        for p in payouts:
            r = compute(a, reg, p)
            print(f"{reg:<7}{str(int(p * 100)) + '%':>9}{inr(r['gross']):>13}{inr(r['taxable']):>13}{inr(r['tax']):>11}"
                  f"{inr(r['pf']):>10}{inr(r['annual_in_hand']):>16}{inr(r['monthly_in_hand_fixed']):>17}")
            for n in r["notes"]:
                print(f"{'':>7}  note: {n}")
    print("\nMonthly in-hand is on fixed pay only; variable pays out when earned. Estimates only, not tax advice.")


def self_test():
    """Hand-checked cases (FY 2026-27 rules, PF capped at 21,600, PT 2,500)."""
    class A:  # minimal args
        def __init__(self, **k):
            self.__dict__.update(dict(fy="2026-27", basic_pct=40, hra_pct=50, variable=0, pf="capped",
                                      wage_rule="basic", pt=2_500, rent=0, metro=False, extra_80c=0), **k)
    cases = [
        # fixed 12L: taxable 11.25L <= 12L -> rebate -> tax 0; in-hand 12,00,000 - 21,600 - 2,500
        (A(fixed=1_200_000), "new", "tax", 0),
        (A(fixed=1_200_000), "new", "annual_in_hand", 1_175_900),
        # fixed 18L: taxable 17.25L -> 20,000+40,000+60,000+25,000 = 1,45,000 -> +4% = 1,50,800
        (A(fixed=1_800_000), "new", "tax", 150_800),
        # fixed 25L: taxable 24.25L -> 20k+40k+60k+80k+1,00,000+7,500 = 3,07,500 -> +4% = 3,19,800
        (A(fixed=2_500_000), "new", "tax", 319_800),
        # marginal relief: fixed 12.85L -> taxable 12.10L; slab tax 61,500 > 10,000 excess -> 10,000 -> +4% = 10,400
        (A(fixed=1_285_000), "new", "tax", 10_400),
        # old regime: fixed 12L, basic 4.8L, HRA 2.4L, rent 3L metro -> HRA exempt 2.4L;
        # taxable = 12L - 50k - 2.4L - 21,600 (80C via PF) - 2,500 PT = 8,85,900
        # tax = 12,500 + 20% * 3,85,900 = 89,680 -> +4% = 93,267
        (A(fixed=1_200_000, rent=300_000, metro=True), "old", "tax", 93_267),
        # labour-code wage: fixed 15L, basic 30% (4.5L) -> PF wage = max(4.5L, 7.5L) = 7.5L, full PF = 90,000
        (A(fixed=1_500_000, basic_pct=30, pf="full", wage_rule="labour-code"), "new", "pf", 90_000),
    ]
    ok = True
    for args, regime, key, want in cases:
        got = compute(args, regime, 0.0)[key]
        status = "ok " if got == want else "FAIL"
        ok &= got == want
        print(f"{status} fixed={inr(args.fixed):>10} {regime:<3} {key:<15} want {inr(want):>10} got {inr(got):>10}")
    print("all passed" if ok else "FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixed", type=float, help="annual fixed cash pay (basic + HRA + allowances)")
    ap.add_argument("--variable", type=float, default=0, help="annual variable/performance bonus at 100%% payout")
    ap.add_argument("--basic-pct", type=float, default=40, help="basic as %% of fixed (default 40)")
    ap.add_argument("--hra-pct", type=float, default=50, help="HRA as %% of basic (default 50)")
    ap.add_argument("--pf", choices=["capped", "full", "none"], default="capped",
                    help="employee PF: 12%% of wage capped at Rs 15,000/month, 12%% of full wage, or none")
    ap.add_argument("--wage-rule", choices=["basic", "labour-code"], default="basic",
                    help="PF wage base: basic, or labour-code (higher of basic or 50%% of pay; codes in force from 21 Nov 2025, verify the employer's policy)")
    ap.add_argument("--pt", type=float, default=2_500, help="annual professional tax (state-dependent; 0 in e.g. Delhi)")
    ap.add_argument("--regime", choices=["new", "old", "both"], default="new")
    ap.add_argument("--rent", type=float, default=0, help="annual rent paid (old regime HRA exemption)")
    ap.add_argument("--metro", action="store_true", help="metro city for HRA (50%% of basic instead of 40%%)")
    ap.add_argument("--extra-80c", type=float, default=0, help="other 80C investments beyond employee PF (old regime)")
    ap.add_argument("--fy", default=DEFAULT_FY, choices=sorted(RULES))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if a.fixed is None:
        ap.error("--fixed is required (annual fixed cash pay)")
    report(a)


if __name__ == "__main__":
    main()
