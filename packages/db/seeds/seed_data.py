"""
Seed data for MortgageAI.

Run with: cd packages/db && uv run python -m seeds.seed_data
"""

import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db.database import Base
from db.models import LLMConfig, LoanProduct

DATABASE_URL = "postgresql://user:password@localhost:5432/mortgage-ai"


LOAN_PRODUCTS = [
    {
        "name": "30-Year Fixed-Rate Conventional",
        "type": "conventional",
        "term_years": 30,
        "rate_type": "fixed",
        "min_down_payment_pct": Decimal("3.00"),
        "min_credit_score": 620,
        "max_dti_ratio": Decimal("43.00"),
        "max_loan_amount": Decimal("766550.00"),
        "description": (
            "The most popular mortgage option. Offers predictable monthly payments "
            "with a fixed interest rate for the entire 30-year term."
        ),
        "eligibility_requirements": [
            "Minimum credit score of 620",
            "Debt-to-income ratio below 43%",
            "Minimum 3% down payment",
            "Stable employment history (2+ years preferred)",
        ],
        "features": [
            "Fixed interest rate for the life of the loan",
            "PMI required if down payment is less than 20%",
            "No prepayment penalties",
            "Available for primary residences, second homes, and investment properties",
        ],
    },
    {
        "name": "15-Year Fixed-Rate Conventional",
        "type": "conventional",
        "term_years": 15,
        "rate_type": "fixed",
        "min_down_payment_pct": Decimal("3.00"),
        "min_credit_score": 620,
        "max_dti_ratio": Decimal("43.00"),
        "max_loan_amount": Decimal("766550.00"),
        "description": (
            "Build equity faster with lower interest rates. Higher monthly payments "
            "but significantly less total interest paid over the life of the loan."
        ),
        "eligibility_requirements": [
            "Minimum credit score of 620",
            "Debt-to-income ratio below 43%",
            "Minimum 3% down payment",
            "Higher income required due to larger monthly payments",
        ],
        "features": [
            "Lower interest rate than 30-year fixed",
            "Build equity faster",
            "Pay less total interest over the life of the loan",
            "No prepayment penalties",
        ],
    },
    {
        "name": "5/1 Adjustable-Rate Mortgage (ARM)",
        "type": "conventional",
        "term_years": 30,
        "rate_type": "adjustable",
        "min_down_payment_pct": Decimal("5.00"),
        "min_credit_score": 620,
        "max_dti_ratio": Decimal("43.00"),
        "max_loan_amount": Decimal("766550.00"),
        "description": (
            "Fixed rate for the first 5 years, then adjusts annually. "
            "Lower initial rate makes this ideal if you plan to sell or refinance within 5 years."
        ),
        "eligibility_requirements": [
            "Minimum credit score of 620",
            "Debt-to-income ratio below 43%",
            "Minimum 5% down payment",
        ],
        "features": [
            "Lower initial interest rate than fixed-rate mortgages",
            "Fixed rate for first 5 years",
            "Rate adjusts annually after initial period",
            "Rate caps limit how much the rate can increase",
        ],
    },
    {
        "name": "7/1 Adjustable-Rate Mortgage (ARM)",
        "type": "conventional",
        "term_years": 30,
        "rate_type": "adjustable",
        "min_down_payment_pct": Decimal("5.00"),
        "min_credit_score": 620,
        "max_dti_ratio": Decimal("43.00"),
        "max_loan_amount": Decimal("766550.00"),
        "description": (
            "Fixed rate for the first 7 years, then adjusts annually. "
            "Offers a longer fixed period than the 5/1 ARM."
        ),
        "eligibility_requirements": [
            "Minimum credit score of 620",
            "Debt-to-income ratio below 43%",
            "Minimum 5% down payment",
        ],
        "features": [
            "Lower initial rate than fixed-rate mortgages",
            "Fixed rate for first 7 years",
            "Rate adjusts annually after initial period",
            "Good balance of initial savings and rate stability",
        ],
    },
    {
        "name": "FHA 30-Year Fixed",
        "type": "fha",
        "term_years": 30,
        "rate_type": "fixed",
        "min_down_payment_pct": Decimal("3.50"),
        "min_credit_score": 500,
        "max_dti_ratio": Decimal("50.00"),
        "max_loan_amount": Decimal("498257.00"),
        "description": (
            "Government-backed loan ideal for first-time homebuyers. "
            "Lower credit score and down payment requirements make homeownership more accessible."
        ),
        "eligibility_requirements": [
            "Minimum credit score of 580 for 3.5% down payment",
            "Credit score 500-579 requires 10% down payment",
            "Debt-to-income ratio below 50%",
            "Property must be primary residence",
            "FHA mortgage insurance premium (MIP) required",
        ],
        "features": [
            "Lower credit score requirements",
            "Down payment as low as 3.5%",
            "More flexible debt-to-income ratios",
            "Mortgage insurance required for the life of the loan",
            "Gift funds allowed for down payment",
        ],
    },
    {
        "name": "VA 30-Year Fixed",
        "type": "va",
        "term_years": 30,
        "rate_type": "fixed",
        "min_down_payment_pct": Decimal("0.00"),
        "min_credit_score": None,
        "max_dti_ratio": Decimal("41.00"),
        "max_loan_amount": None,
        "description": (
            "Exclusive benefit for eligible veterans, active-duty service members, "
            "and surviving spouses. No down payment or private mortgage insurance required."
        ),
        "eligibility_requirements": [
            "Must be eligible veteran, active-duty, or surviving spouse",
            "Certificate of Eligibility (COE) required",
            "Property must be primary residence",
            "No minimum credit score (lenders may set their own)",
            "VA funding fee applies (unless exempt)",
        ],
        "features": [
            "No down payment required",
            "No private mortgage insurance (PMI)",
            "Competitive interest rates",
            "Limited closing costs",
            "No prepayment penalties",
        ],
    },
    {
        "name": "USDA 30-Year Fixed",
        "type": "usda",
        "term_years": 30,
        "rate_type": "fixed",
        "min_down_payment_pct": Decimal("0.00"),
        "min_credit_score": 640,
        "max_dti_ratio": Decimal("41.00"),
        "max_loan_amount": None,
        "description": (
            "Zero down payment loan for eligible rural and suburban homebuyers. "
            "Income limits apply based on area median income."
        ),
        "eligibility_requirements": [
            "Property must be in eligible rural/suburban area",
            "Household income below 115% of area median income",
            "Minimum credit score of 640",
            "Property must be primary residence",
            "US citizen, non-citizen national, or qualified alien",
        ],
        "features": [
            "No down payment required",
            "Lower mortgage insurance costs than FHA",
            "Below-market interest rates",
            "Closing costs can be financed",
            "Flexible credit guidelines",
        ],
    },
    {
        "name": "Jumbo 30-Year Fixed",
        "type": "jumbo",
        "term_years": 30,
        "rate_type": "fixed",
        "min_down_payment_pct": Decimal("10.00"),
        "min_credit_score": 700,
        "max_dti_ratio": Decimal("43.00"),
        "max_loan_amount": Decimal("3000000.00"),
        "description": (
            "For loan amounts exceeding conforming loan limits. "
            "Higher credit score and down payment required, but enables purchase of high-value properties."
        ),
        "eligibility_requirements": [
            "Minimum credit score of 700",
            "Minimum 10% down payment (20% preferred)",
            "Debt-to-income ratio below 43%",
            "Significant cash reserves (6-12 months of payments)",
            "Strong employment and income documentation",
        ],
        "features": [
            "Loan amounts above conforming limits",
            "Competitive rates for well-qualified borrowers",
            "Available for primary, secondary, and investment properties",
            "Multiple property types eligible",
        ],
    },
]


LLM_CONFIGS = [
    {
        "provider": "openai",
        "is_active": True,
        "is_default": True,
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "max_tokens": 4096,
        "temperature": Decimal("0.10"),
        "rate_limit_rpm": 60,
    },
    {
        "provider": "anthropic",
        "is_active": False,
        "is_default": False,
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "temperature": Decimal("0.10"),
        "rate_limit_rpm": 60,
    },
    {
        "provider": "local",
        "is_active": False,
        "is_default": False,
        "base_url": "http://localhost:8081/v1",
        "default_model": "default",
        "max_tokens": 4096,
        "temperature": Decimal("0.10"),
        "rate_limit_rpm": 0,
    },
]


def seed():
    """Insert seed data into the database."""
    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        # Seed loan products
        existing = session.execute(select(LoanProduct)).scalars().all()
        if not existing:
            print("Seeding loan products...")
            for product_data in LOAN_PRODUCTS:
                product = LoanProduct(**product_data)
                session.add(product)
            session.commit()
            print(f"  Created {len(LOAN_PRODUCTS)} loan products")
        else:
            print(f"  Loan products already exist ({len(existing)} found), skipping")

        # Seed LLM configs
        existing_configs = session.execute(select(LLMConfig)).scalars().all()
        if not existing_configs:
            print("Seeding LLM configurations...")
            for config_data in LLM_CONFIGS:
                config = LLMConfig(**config_data)
                session.add(config)
            session.commit()
            print(f"  Created {len(LLM_CONFIGS)} LLM configurations")
        else:
            print(f"  LLM configs already exist ({len(existing_configs)} found), skipping")

    print("Seed complete.")


if __name__ == "__main__":
    seed()
