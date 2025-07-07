from typing import Dict, List
import math
import pandas as pd

MIN_BASE = 2690
MAX_BASE = 36921
SOCIAL_RATES = {"pension": 0.08, "medical": 0.02, "unemployment": 0.005}
HOUSING_FUND_RATE = 0.07
HOUSING_FUND_RATE_EMPLOYER = 0.07
STANDARD_DEDUCTION_MONTHLY = 5000
STANDARD_DEDUCTION_ANNUAL = STANDARD_DEDUCTION_MONTHLY * 12
MONTHLY_TAX_BRACKETS = [
    (3000, 0.03, 0),
    (12000, 0.10, 210),
    (25000, 0.20, 1410),
    (35000, 0.25, 2660),
    (55000, 0.30, 4410),
    (80000, 0.35, 7160),
    (float('inf'), 0.45, 15160),
]
ANNUAL_TAX_BRACKETS = [
    (36000, 0.03, 0),
    (144000, 0.10, 2520),
    (300000, 0.20, 16920),
    (420000, 0.25, 31920),
    (660000, 0.30, 52920),
    (960000, 0.35, 85920),
    (float('inf'), 0.45, 181920),
]

def _cap_base(salary: float) -> float:
    """Clamp contribution base to the legal range [MIN_BASE, MAX_BASE] as required by Shanghai social insurance rules."""
    return max(MIN_BASE, min(salary, MAX_BASE))

def _r(value: float, to_int: bool) -> float:
    """Round value to 2 decimals or nearest integer (0.5 up) depending on *to_int*."""
    if to_int:
        return int(math.floor(value + 0.5))
    return round(value, 2)

def _social(base: float, round_int: bool) -> Dict[str, float]:
    """Calculate employee-side contributions for pension, medical, unemployment insurance and housing fund."""
    pension = base * SOCIAL_RATES['pension']
    medical = base * SOCIAL_RATES['medical'] + 3
    unemployment = base * SOCIAL_RATES['unemployment']
    housing = base * HOUSING_FUND_RATE
    return {
        'pension': _r(pension, round_int),
        'medical': _r(medical, round_int),
        'unemployment': _r(unemployment, round_int),
        'housing_fund': _r(housing, round_int),
    }

def _tax(taxable: float, brackets):
    """Compute personal income tax for the given taxable income using a bracket table.

    Parameters
    ----------
    taxable : float
        Taxable income after social security, housing fund and standard deduction.
    brackets : list[tuple]
        Tax brackets defined as (upper_limit, rate, quick_deduction).
    """
    for limit, rate, quick in brackets:
        if taxable <= limit:
            return round(taxable * rate - quick, 2)
    return 0.0

def monthly_net(gross: float, round_int: bool = False):
    """Return social contributions, personal income tax and net salary for a given gross monthly wage."""
    base = _cap_base(gross)
    social = _social(base, round_int)
    social_total_val = sum(social.values())
    social_total = _r(social_total_val, round_int)
    taxable = max(0, gross - social_total_val - STANDARD_DEDUCTION_MONTHLY)
    tax = _r(_tax(taxable, MONTHLY_TAX_BRACKETS), round_int)
    net = _r(gross - social_total_val - tax, round_int)
    return {**social, 'social_total': social_total, 'taxable': _r(taxable, round_int), 'tax': tax, 'net': net}

def annual_net(gross_annual: float, round_int: bool = False):
    """Return yearly social contributions, annual income tax and net income for a given gross annual salary."""
    avg = gross_annual / 12
    base = _cap_base(avg)
    social_m = _social(base, round_int)
    social_total_year_val = sum(social_m.values()) * 12
    social_total_year = _r(social_total_year_val, round_int)
    taxable = max(0, gross_annual - social_total_year_val - STANDARD_DEDUCTION_ANNUAL)
    tax = _r(_tax(taxable, ANNUAL_TAX_BRACKETS), round_int)
    net = _r(gross_annual - social_total_year_val - tax, round_int)
    return {k+'_year': (_r(v*12, round_int)) for k,v in social_m.items() } | {
        'social_total_annual': social_total_year,
        'taxable_annual': _r(taxable, round_int),
        'tax_annual': tax,
        'net_annual': net,
        'net_monthly_equivalent': _r(net/12, round_int)
    }

def yearly_salary_details(gross_monthly: List[float], round_int: bool = False):
    """Return detailed monthly and yearly salary breakdown using cumulative withholding method.

    Parameters
    ----------
    gross_monthly : list[float]
        List of gross salary for each month (length ≤ 12). If shorter than 12, remaining months
        are assumed to have 0 income.
    round_int : bool, optional
        If True, round all numeric outputs to nearest integer; otherwise keep two decimals.

    Returns
    -------
    dict
        {
          "monthly": [ {...}, ... ],
          "totals": {...}
        }
    """

    # ensure length 12
    gross_list = (gross_monthly + [0.0] * 12)[:12]

    monthly_details = []
    cumulative_taxable = 0.0
    cumulative_tax_paid = 0.0

    totals = {
        "gross_annual": 0.0,
        "social_personal_annual": 0.0,
        "housing_personal_annual": 0.0,
        "housing_company_annual": 0.0,
        "tax_annual": 0.0,
        "net_annual": 0.0,
    }

    for idx, gross in enumerate(gross_list, start=1):
        base = _cap_base(gross)
        social = _social(base, round_int)
        personal_social_total = sum(social.values())

        # housing fund parts
        personal_housing = social["housing_fund"]
        company_housing = _r(base * HOUSING_FUND_RATE_EMPLOYER, round_int)

        # cumulative taxable income up to this month
        cumulative_taxable += gross - personal_social_total - STANDARD_DEDUCTION_MONTHLY

        taxable_for_bracket = max(0.0, cumulative_taxable)
        cumulative_tax = _tax(taxable_for_bracket, ANNUAL_TAX_BRACKETS)
        month_tax_raw = cumulative_tax - cumulative_tax_paid
        month_tax = _r(max(0.0, month_tax_raw), round_int)
        cumulative_tax_paid += month_tax

        net = _r(gross - personal_social_total - month_tax, round_int)

        details = {
            "month": idx,
            "gross": _r(gross, round_int),
            **social,
            "social_total": _r(personal_social_total, round_int),
            "personal_housing": personal_housing,
            "company_housing": company_housing,
            "housing_total": _r(personal_housing + company_housing, round_int),
            "tax": month_tax,
            "net": net,
        }
        monthly_details.append(details)

        # accumulate totals
        totals["gross_annual"] += gross
        totals["social_personal_annual"] += personal_social_total
        totals["housing_personal_annual"] += personal_housing
        totals["housing_company_annual"] += company_housing
        totals["tax_annual"] += month_tax
        totals["net_annual"] += net

    # apply rounding to totals
    for k, v in totals.items():
        totals[k] = _r(v, round_int)

    return {"monthly": monthly_details, "totals": totals}

def _print_or_save_details(res: dict, csv_path=None):
    df = pd.DataFrame(res["monthly"])
    if csv_path:
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"CSV saved → {csv_path}")
    else:
        # 在终端打印紧凑表；在 Jupyter 会自动渲染为表格
        print(df.to_string(index=False))
    print("\nAnnual Totals:")
    print(pd.Series(res["totals"]))

if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument('--monthly', type=float)
    g.add_argument('--annual', type=float)
    p.add_argument('--round-int', action='store_true', help='Round all numeric outputs to nearest integer')
    args = p.parse_args()
    use_int = args.round_int
    if args.monthly is not None:
        print(json.dumps(monthly_net(args.monthly, use_int), ensure_ascii=False, indent=2))
    elif args.annual is not None:
        print(json.dumps(annual_net(args.annual, use_int), ensure_ascii=False, indent=2))
    else:
        # interactive fallback
        mode = input("Select mode ('monthly' or 'annual'): ").strip().lower()
        while mode not in {"monthly", "annual"}:
            mode = input("Please type 'monthly' or 'annual': ").strip().lower()
        amount_str = input(f"Enter gross {mode} salary (RMB): ")
        try:
            amount = float(amount_str)
        except ValueError:
            raise SystemExit("Invalid number provided.")
        round_choice = input("Round results to whole numbers? (y/n): ").strip().lower()
        use_int = round_choice in {"y", "yes"}
        if mode == "monthly":
            res = monthly_net(amount, use_int)
        else:
            res = annual_net(amount, use_int)
        print(json.dumps(res, ensure_ascii=False, indent=2)) 