from typing import Dict, List
import math
import pandas as pd
import os

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

if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser(description="Shanghai Salary Tax Tool")
    sub = parser.add_subparsers(dest="mode", required=True)

    # ① monthly
    p_month = sub.add_parser("monthly")
    p_month.add_argument("amount", type=float)
    p_month.add_argument("--round-int", action="store_true")

    # ② annual
    p_annual = sub.add_parser("annual")
    p_annual.add_argument("amount", type=float)
    p_annual.add_argument("--round-int", action="store_true")

    # ③ yearly-details
    p_detail = sub.add_parser("details")
    p_detail.add_argument("amount", type=float,
                         help="Monthly gross salary (apply to all 12 months)")
    p_detail.add_argument("--csv", metavar="FILE",
                         help="Save result to CSV")
    p_detail.add_argument("--round-int", action="store_true")

    args = parser.parse_args()
    
    if args.mode == "monthly":
        result = monthly_net(args.amount, args.round_int)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.mode == "annual":
        result = annual_net(args.amount, args.round_int)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.mode == "details":
        # 创建一个12个月相同工资的列表
        monthly_list = [args.amount] * 12
        result = yearly_salary_details(monthly_list, args.round_int)
        
        if args.csv:
            # 确保 output_csv 目录存在
            os.makedirs("output_csv", exist_ok=True)
            
            # 构建输出文件路径
            monthly_file = os.path.join("output_csv", f"{args.csv}_monthly.csv")
            totals_file = os.path.join("output_csv", f"{args.csv}_totals.csv")
            
            # 保存月度明细
            monthly_df = pd.DataFrame(result["monthly"])
            monthly_df.to_csv(monthly_file, index=False)
            
            # 保存年度汇总
            totals_df = pd.DataFrame([result["totals"]])
            totals_df.to_csv(totals_file, index=False)
            
            print(f"Results saved to:\n- {monthly_file}\n- {totals_file}")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2)) 


# 使用实例
# # 计算月薪
# python tax_calculator.py monthly 40000

# # 计算年薪
# python tax_calculator.py annual 480000

# # 计算12个月详细信息并保存为CSV
# python tax_calculator.py details 40000 --csv salary_2024