"""
Simulated Credit Bureau Service.

Generates realistic credit bureau data derived from the borrower's
self-reported information. Uses deterministic seeding so repeated
calls for the same application produce identical reports.
"""

import hashlib
import logging
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Tradeline:
    """Individual credit account."""

    account_type: str  # revolving, installment, mortgage, student_loan
    creditor: str
    opened_date: str  # ISO date
    credit_limit: float | None = None
    current_balance: float = 0
    monthly_payment: float = 0
    status: str = "open"  # open, closed, collection
    payment_history_24m: list[str] = field(default_factory=list)  # OK, 30, 60, 90, CO


@dataclass
class PublicRecord:
    """Bankruptcy, foreclosure, or judgment."""

    record_type: str  # bankruptcy, foreclosure, judgment
    filed_date: str
    status: str = "discharged"  # discharged, dismissed, active
    amount: float | None = None


@dataclass
class Inquiry:
    """Hard credit inquiry."""

    date: str
    creditor: str
    inquiry_type: str  # mortgage, auto, credit_card, other


@dataclass
class FraudAlert:
    """Fraud or identity alert."""

    alert_type: str
    severity: str  # low, medium, high
    description: str


@dataclass
class CreditReportData:
    """Full credit bureau report."""

    credit_score: int
    score_model: str = "FICO 8"
    score_factors: list[str] = field(default_factory=list)
    tradelines: list[Tradeline] = field(default_factory=list)
    public_records: list[PublicRecord] = field(default_factory=list)
    inquiries: list[Inquiry] = field(default_factory=list)
    collections: list[dict[str, Any]] = field(default_factory=list)
    fraud_alerts: list[FraudAlert] = field(default_factory=list)
    fraud_score: int = 0

    # Summary metrics
    total_accounts: int = 0
    open_accounts: int = 0
    credit_utilization: float = 0.0
    oldest_account_months: int = 0
    avg_account_age_months: int = 0

    # Payment history
    on_time_payments_pct: float = 100.0
    late_payments_30d: int = 0
    late_payments_60d: int = 0
    late_payments_90d: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        data = asdict(self)
        return data


# ---------------------------------------------------------------------------
# Credit Bureau Service
# ---------------------------------------------------------------------------

class CreditBureauService:
    """Generates simulated credit bureau reports from application data."""

    CREDITOR_NAMES = {
        "revolving": ["Chase", "Capital One", "Discover", "Citi", "Amex"],
        "installment": ["Toyota Financial", "Ford Motor Credit", "Ally Financial"],
        "student_loan": ["Nelnet", "Great Lakes", "FedLoan"],
        "mortgage": ["Wells Fargo", "Quicken Loans", "US Bank"],
    }

    @classmethod
    def pull_credit_report(
        cls,
        application_id: str,
        financial_info: dict[str, Any],
        employment_info: dict[str, Any],
        declarations: dict[str, Any],
        property_info: dict[str, Any] | None = None,
    ) -> CreditReportData:
        """Generate a deterministic credit bureau report.

        Args:
            application_id: UUID string for deterministic seeding.
            financial_info: Applicant's self-reported financial data.
            employment_info: Employment details.
            declarations: Declarations (bankruptcy, foreclosure, etc.).
            property_info: Property details.

        Returns:
            CreditReportData with full simulated report.
        """
        rng = cls._seeded_rng(application_id)
        self_reported_score = financial_info.get(
            "credit_score_self_reported",
            financial_info.get("credit_score"),
        )

        # 1. Derive bureau credit score
        bureau_score = cls._derive_credit_score(self_reported_score, declarations, rng)

        # 2. Generate tradelines from monthly debts
        tradelines = cls._generate_tradelines(
            financial_info, bureau_score, rng
        )

        # 3. Generate public records
        public_records = cls._generate_public_records(declarations, rng)

        # 4. Generate inquiries
        inquiries = cls._generate_inquiries(rng)

        # 5. Generate collections
        collections = cls._generate_collections(declarations, bureau_score, rng)

        # 6. Compute summary metrics
        total_accounts = len(tradelines)
        open_accounts = sum(1 for t in tradelines if t.status == "open")

        total_limit = sum(t.credit_limit or 0 for t in tradelines if t.account_type == "revolving")
        total_balance = sum(
            t.current_balance for t in tradelines if t.account_type == "revolving"
        )
        credit_utilization = (
            round((total_balance / total_limit) * 100, 1) if total_limit > 0 else 0.0
        )

        today = datetime.now()
        account_ages = []
        for t in tradelines:
            try:
                opened = datetime.fromisoformat(t.opened_date)
                age_months = max(1, (today - opened).days // 30)
                account_ages.append(age_months)
            except (ValueError, TypeError):
                pass

        oldest_account_months = max(account_ages) if account_ages else 0
        avg_account_age_months = (
            round(sum(account_ages) / len(account_ages)) if account_ages else 0
        )

        # 7. Aggregate payment history
        total_payments = 0
        on_time = 0
        late_30 = late_60 = late_90 = 0
        for t in tradelines:
            for p in t.payment_history_24m:
                total_payments += 1
                if p == "OK":
                    on_time += 1
                elif p == "30":
                    late_30 += 1
                elif p == "60":
                    late_60 += 1
                elif p in ("90", "CO"):
                    late_90 += 1

        on_time_pct = round((on_time / total_payments) * 100, 1) if total_payments > 0 else 100.0

        # 8. Fraud assessment
        fraud_alerts, fraud_score = cls._assess_fraud(
            financial_info, employment_info, declarations, bureau_score, rng
        )

        # 9. Score factors
        score_factors = cls._generate_score_factors(
            bureau_score, credit_utilization, on_time_pct,
            oldest_account_months, public_records, late_30 + late_60 + late_90,
        )

        report = CreditReportData(
            credit_score=bureau_score,
            score_model="FICO 8",
            score_factors=score_factors,
            tradelines=tradelines,
            public_records=public_records,
            inquiries=inquiries,
            collections=collections,
            fraud_alerts=fraud_alerts,
            fraud_score=fraud_score,
            total_accounts=total_accounts,
            open_accounts=open_accounts,
            credit_utilization=credit_utilization,
            oldest_account_months=oldest_account_months,
            avg_account_age_months=avg_account_age_months,
            on_time_payments_pct=on_time_pct,
            late_payments_30d=late_30,
            late_payments_60d=late_60,
            late_payments_90d=late_90,
        )

        logger.info(
            f"Credit report pulled for application {application_id}: "
            f"score={bureau_score}, utilization={credit_utilization}%, "
            f"fraud_score={fraud_score}"
        )

        return report

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _seeded_rng(application_id: str) -> random.Random:
        """Create a deterministic RNG from the application ID."""
        seed = int(hashlib.sha256(application_id.encode()).hexdigest()[:16], 16)
        return random.Random(seed)

    @classmethod
    def _derive_credit_score(
        cls,
        self_reported: int | None,
        declarations: dict[str, Any],
        rng: random.Random,
    ) -> int:
        """Derive a bureau score from self-reported score with variance."""
        if self_reported and isinstance(self_reported, (int, float)) and self_reported > 0:
            variance = rng.randint(-30, 15)
            base_score = int(self_reported) + variance
        else:
            base_score = rng.randint(580, 720)

        # Penalize for derogatory marks
        if declarations.get("has_bankruptcy"):
            base_score -= rng.randint(40, 80)
        if declarations.get("has_foreclosure"):
            base_score -= rng.randint(50, 90)
        if declarations.get("has_judgments"):
            base_score -= rng.randint(20, 40)
        if declarations.get("has_delinquent_debt"):
            base_score -= rng.randint(15, 35)

        return max(300, min(850, base_score))

    @classmethod
    def _generate_tradelines(
        cls,
        financial_info: dict[str, Any],
        credit_score: int,
        rng: random.Random,
    ) -> list[Tradeline]:
        """Generate tradelines from monthly debt data."""
        tradelines: list[Tradeline] = []
        monthly_debts = financial_info.get("monthly_debts", {})
        today = datetime.now()

        # Map declared debts to tradeline types
        debt_mapping = {
            "car_loan": ("installment", "Auto Loan"),
            "auto_loan": ("installment", "Auto Loan"),
            "student_loans": ("student_loan", "Student Loan"),
            "student_loan": ("student_loan", "Student Loan"),
            "credit_cards": ("revolving", "Credit Card"),
            "credit_card": ("revolving", "Credit Card"),
            "personal_loan": ("installment", "Personal Loan"),
            "other": ("installment", "Other Installment"),
        }

        for debt_key, payment_amount in monthly_debts.items():
            if not isinstance(payment_amount, (int, float)) or payment_amount <= 0:
                continue

            acct_type, label = debt_mapping.get(
                debt_key, ("installment", debt_key.replace("_", " ").title())
            )

            if acct_type == "revolving":
                # Generate 1-3 credit card tradelines
                num_cards = rng.randint(1, 3)
                per_card_payment = payment_amount / num_cards
                for i in range(num_cards):
                    creditor = rng.choice(cls.CREDITOR_NAMES["revolving"])
                    months_old = rng.randint(12, 120)
                    opened = (today - timedelta(days=months_old * 30)).strftime("%Y-%m-%d")

                    # Utilization correlates inversely with score
                    if credit_score >= 740:
                        util_pct = rng.uniform(0.05, 0.25)
                    elif credit_score >= 670:
                        util_pct = rng.uniform(0.15, 0.45)
                    else:
                        util_pct = rng.uniform(0.40, 0.85)

                    balance = round(per_card_payment * rng.uniform(8, 20), 2)
                    limit = round(balance / util_pct, 2) if util_pct > 0 else balance * 4

                    tradelines.append(Tradeline(
                        account_type="revolving",
                        creditor=f"{creditor} {label} #{i + 1}",
                        opened_date=opened,
                        credit_limit=round(limit, 2),
                        current_balance=round(balance, 2),
                        monthly_payment=round(per_card_payment, 2),
                        status="open",
                        payment_history_24m=cls._generate_payment_history(
                            credit_score, rng, months=24
                        ),
                    ))
            else:
                creditors = cls.CREDITOR_NAMES.get(acct_type, ["Generic Lender"])
                creditor = rng.choice(creditors)
                months_old = rng.randint(6, 72)
                opened = (today - timedelta(days=months_old * 30)).strftime("%Y-%m-%d")

                # Estimate remaining balance
                original_term = rng.randint(36, 120)
                remaining_months = max(1, original_term - months_old)
                balance = round(payment_amount * remaining_months * 0.9, 2)

                tradelines.append(Tradeline(
                    account_type=acct_type,
                    creditor=f"{creditor} {label}",
                    opened_date=opened,
                    credit_limit=None,
                    current_balance=balance,
                    monthly_payment=round(payment_amount, 2),
                    status="open",
                    payment_history_24m=cls._generate_payment_history(
                        credit_score, rng, months=min(24, months_old)
                    ),
                ))

        # Ensure at least 3 tradelines
        while len(tradelines) < 3:
            acct_type = rng.choice(["revolving", "installment"])
            creditors = cls.CREDITOR_NAMES.get(acct_type, ["Generic Lender"])
            creditor = rng.choice(creditors)
            months_old = rng.randint(24, 96)
            opened = (today - timedelta(days=months_old * 30)).strftime("%Y-%m-%d")

            if acct_type == "revolving":
                limit = round(rng.uniform(1000, 15000), 2)
                balance = round(limit * rng.uniform(0.0, 0.3), 2)
                payment = round(balance * 0.03, 2)
            else:
                payment = round(rng.uniform(100, 500), 2)
                balance = round(payment * rng.randint(12, 48), 2)
                limit = None

            tradelines.append(Tradeline(
                account_type=acct_type,
                creditor=f"{creditor} (Closed)",
                opened_date=opened,
                credit_limit=limit,
                current_balance=balance,
                monthly_payment=payment,
                status="closed",
                payment_history_24m=cls._generate_payment_history(
                    credit_score, rng, months=24
                ),
            ))

        return tradelines

    @classmethod
    def _generate_payment_history(
        cls,
        credit_score: int,
        rng: random.Random,
        months: int = 24,
    ) -> list[str]:
        """Generate a 24-month payment history correlated with credit score."""
        history = []

        # Probability of late payment per month based on score
        if credit_score >= 760:
            late_prob = 0.005
        elif credit_score >= 700:
            late_prob = 0.02
        elif credit_score >= 660:
            late_prob = 0.06
        elif credit_score >= 620:
            late_prob = 0.12
        else:
            late_prob = 0.20

        for month_idx in range(months):
            if rng.random() < late_prob:
                # Recent months (lower index) are more recent
                severity_roll = rng.random()
                if severity_roll < 0.6:
                    history.append("30")
                elif severity_roll < 0.85:
                    history.append("60")
                else:
                    history.append("90")
            else:
                history.append("OK")

        return history

    @classmethod
    def _generate_public_records(
        cls,
        declarations: dict[str, Any],
        rng: random.Random,
    ) -> list[PublicRecord]:
        """Generate public records from declarations."""
        records: list[PublicRecord] = []
        today = datetime.now()

        if declarations.get("has_bankruptcy"):
            years_ago = rng.randint(2, 8)
            filed = (today - timedelta(days=years_ago * 365)).strftime("%Y-%m-%d")
            records.append(PublicRecord(
                record_type="bankruptcy",
                filed_date=filed,
                status="discharged" if years_ago >= 2 else "active",
                amount=rng.randint(20000, 150000),
            ))

        if declarations.get("has_foreclosure"):
            years_ago = rng.randint(3, 10)
            filed = (today - timedelta(days=years_ago * 365)).strftime("%Y-%m-%d")
            records.append(PublicRecord(
                record_type="foreclosure",
                filed_date=filed,
                status="completed",
                amount=rng.randint(100000, 400000),
            ))

        if declarations.get("has_judgments"):
            years_ago = rng.randint(1, 6)
            filed = (today - timedelta(days=years_ago * 365)).strftime("%Y-%m-%d")
            records.append(PublicRecord(
                record_type="judgment",
                filed_date=filed,
                status=rng.choice(["satisfied", "active"]),
                amount=rng.randint(2000, 50000),
            ))

        return records

    @classmethod
    def _generate_inquiries(cls, rng: random.Random) -> list[Inquiry]:
        """Generate recent credit inquiries."""
        inquiries: list[Inquiry] = []
        today = datetime.now()
        num = rng.randint(1, 4)

        # Always include a mortgage inquiry
        days_ago = rng.randint(1, 14)
        inquiries.append(Inquiry(
            date=(today - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            creditor="Mortgage Lender",
            inquiry_type="mortgage",
        ))

        inquiry_types = ["auto", "credit_card", "other"]
        creditor_names = ["Auto Dealer", "Bank of America", "Discover", "SoFi", "Marcus"]
        for _ in range(num - 1):
            days_ago = rng.randint(7, 180)
            inquiries.append(Inquiry(
                date=(today - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
                creditor=rng.choice(creditor_names),
                inquiry_type=rng.choice(inquiry_types),
            ))

        return inquiries

    @classmethod
    def _generate_collections(
        cls,
        declarations: dict[str, Any],
        credit_score: int,
        rng: random.Random,
    ) -> list[dict[str, Any]]:
        """Generate collections accounts based on delinquent debt declarations."""
        collections: list[dict[str, Any]] = []

        if declarations.get("has_delinquent_debt") or credit_score < 580:
            num = rng.randint(1, 3)
            agencies = ["IC System", "Midland Credit", "Portfolio Recovery", "LVNV Funding"]
            for _ in range(num):
                collections.append({
                    "agency": rng.choice(agencies),
                    "original_creditor": rng.choice(["Medical Center", "Utility Co", "Telecom"]),
                    "amount": rng.randint(200, 5000),
                    "status": rng.choice(["open", "paid", "settled"]),
                    "reported_date": (
                        datetime.now() - timedelta(days=rng.randint(90, 720))
                    ).strftime("%Y-%m-%d"),
                })

        return collections

    @classmethod
    def _assess_fraud(
        cls,
        financial_info: dict[str, Any],
        employment_info: dict[str, Any],
        declarations: dict[str, Any],
        credit_score: int,
        rng: random.Random,
    ) -> tuple[list[FraudAlert], int]:
        """Assess fraud risk and generate alerts."""
        alerts: list[FraudAlert] = []
        fraud_score = 0  # 0 = no risk, 100 = high risk

        # Income plausibility check
        annual_income = employment_info.get("annual_income", 0) or 0
        job_title = (employment_info.get("job_title") or "").lower()
        years_at_job = employment_info.get("years_at_job", 0) or 0

        # Flag implausibly high income for job tenure
        if annual_income > 200000 and years_at_job < 2:
            fraud_score += 15
            alerts.append(FraudAlert(
                alert_type="income_plausibility",
                severity="medium",
                description=(
                    f"High income (${annual_income:,}) with short tenure "
                    f"({years_at_job} years) warrants verification"
                ),
            ))

        # Data completeness check
        missing_fields = 0
        for fld in ["credit_score", "total_assets", "annual_income"]:
            val = financial_info.get(fld) or employment_info.get(fld)
            if not val:
                missing_fields += 1
        if missing_fields >= 2:
            fraud_score += 10
            alerts.append(FraudAlert(
                alert_type="data_completeness",
                severity="low",
                description=f"{missing_fields} key financial fields are missing or zero",
            ))

        # Velocity check (simulated — based on number of recent inquiries)
        # In real systems this would check actual credit pull history
        simulated_recent_pulls = rng.randint(0, 5)
        if simulated_recent_pulls > 3:
            fraud_score += 20
            alerts.append(FraudAlert(
                alert_type="velocity_check",
                severity="high",
                description=f"{simulated_recent_pulls} hard credit pulls in last 6 months",
            ))

        # SSN/identity mismatch simulation (very low probability)
        if rng.random() < 0.03:
            fraud_score += 30
            alerts.append(FraudAlert(
                alert_type="identity_flag",
                severity="high",
                description="SSN associated with multiple identities in bureau records",
            ))

        # Score inconsistency
        self_reported = financial_info.get(
            "credit_score_self_reported",
            financial_info.get("credit_score"),
        )
        if self_reported and isinstance(self_reported, (int, float)):
            diff = abs(int(self_reported) - credit_score)
            if diff > 50:
                fraud_score += 10
                alerts.append(FraudAlert(
                    alert_type="score_discrepancy",
                    severity="medium",
                    description=(
                        f"Self-reported score ({int(self_reported)}) differs from "
                        f"bureau score ({credit_score}) by {diff} points"
                    ),
                ))

        # Add random noise
        fraud_score += rng.randint(0, 8)
        fraud_score = max(0, min(100, fraud_score))

        return alerts, fraud_score

    @classmethod
    def _generate_score_factors(
        cls,
        credit_score: int,
        utilization: float,
        on_time_pct: float,
        oldest_months: int,
        public_records: list[PublicRecord],
        total_lates: int,
    ) -> list[str]:
        """Generate 4-5 human-readable score factor explanations."""
        factors: list[str] = []

        # Payment history factor
        if on_time_pct >= 99:
            factors.append("Excellent payment history with near-perfect on-time rate")
        elif on_time_pct >= 95:
            factors.append(f"Good payment history ({on_time_pct:.1f}% on-time)")
        else:
            factors.append(
                f"Payment history shows {total_lates} late payment(s) "
                f"({on_time_pct:.1f}% on-time)"
            )

        # Utilization factor
        if utilization <= 10:
            factors.append(f"Very low credit utilization ({utilization:.0f}%)")
        elif utilization <= 30:
            factors.append(f"Good credit utilization ({utilization:.0f}%)")
        elif utilization <= 50:
            factors.append(f"Moderate credit utilization ({utilization:.0f}%) — below 30% preferred")
        else:
            factors.append(f"High credit utilization ({utilization:.0f}%) — significant negative factor")

        # Account age factor
        years = oldest_months / 12
        if years >= 10:
            factors.append(f"Long credit history ({years:.0f} years oldest account)")
        elif years >= 5:
            factors.append(f"Moderate credit history length ({years:.1f} years)")
        else:
            factors.append(f"Short credit history ({years:.1f} years) — limited track record")

        # Public records factor
        if public_records:
            types = [r.record_type for r in public_records]
            factors.append(f"Public records present: {', '.join(types)}")
        else:
            factors.append("No derogatory public records found")

        # Score tier
        if credit_score >= 740:
            factors.append("Score in super-prime tier (740+)")
        elif credit_score >= 670:
            factors.append("Score in prime tier (670-739)")
        elif credit_score >= 580:
            factors.append("Score in near-prime tier (580-669)")
        else:
            factors.append("Score in sub-prime tier (below 580)")

        return factors
