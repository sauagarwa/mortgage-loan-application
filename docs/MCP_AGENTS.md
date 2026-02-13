# MortgageAI: MCP Agents Design

**Version:** 1.0
**Date:** 2026-02-13

---

## 1. Overview

MortgageAI uses the **Model Context Protocol (MCP)** to define specialized AI agents that analyze mortgage applications. Each agent is an MCP Server exposing **Tools**, **Resources**, and **Prompts** that the orchestration layer (MCP Host) invokes via the standard MCP protocol.

### Agent Orchestration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Host (Orchestrator)                   │
│              risk_assessment_service.py                      │
│                                                             │
│   1. Receive application_id                                 │
│   2. Load application data from DB                          │
│   3. Run Document Processing Agent (sequential)             │
│   4. Fan-out: Run analysis agents in parallel               │
│   5. Run Regulatory Compliance Agent                        │
│   6. Run Risk Aggregation Agent                             │
│   7. Store results, update application status               │
└────────┬──────────────┬──────────────┬──────────────────────┘
         │              │              │
    ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
    │MCP Server│  │MCP Server │  │MCP Server│   ... (8 agents)
    │(Agent 1) │  │(Agent 2)  │  │(Agent N) │
    └─────────┘  └───────────┘  └──────────┘
```

### LLM Integration

Every agent uses the **LLM Gateway** to call the configured LLM provider. The gateway provides a unified interface regardless of whether the backend is OpenAI, Anthropic, or a local model.

```python
class LLMGateway:
    """Unified LLM interface supporting multiple providers."""

    async def chat(self, messages, tools=None, model=None) -> LLMResponse:
        """Send chat completion request to configured provider."""

    async def chat_with_tools(self, messages, tools, model=None) -> LLMResponse:
        """Chat completion with tool/function calling support."""

    # Provider-specific adapters handle:
    # - OpenAI: standard openai SDK
    # - Anthropic: anthropic SDK with tool_use blocks
    # - Local: OpenAI-compatible API with custom base_url
```

---

## 2. Agent Definitions

### 2.1 Document Processing Agent

**Purpose:** Extract structured data from uploaded documents using OCR and LLM analysis.

**When Called:** First in the pipeline, before other agents. Runs once per document upload and again during risk assessment to consolidate all extracted data.

**MCP Server Definition:**

```python
# agents/document_processing.py

AGENT_NAME = "document_processing"
AGENT_DESCRIPTION = "Extracts and validates data from uploaded mortgage documents"

# --- TOOLS ---

@tool
async def extract_text_from_document(document_id: str) -> dict:
    """Run OCR on a document and return raw extracted text.

    Args:
        document_id: UUID of the document in the database

    Returns:
        {"text": "...", "confidence": 0.95, "pages": 3}
    """

@tool
async def extract_structured_data(document_id: str, document_type: str) -> dict:
    """Extract structured fields from a document based on its type.

    For a pay_stub, extracts: employer, pay_period, gross_pay, net_pay, deductions.
    For a bank_statement, extracts: account_holder, bank_name, period, ending_balance,
        deposits, withdrawals, average_balance.
    For a tax_return, extracts: filing_status, agi, taxable_income, total_tax, refund.
    For a w2, extracts: employer, ein, wages, federal_tax_withheld, state, state_wages.

    Args:
        document_id: UUID of the document
        document_type: Type classification of the document

    Returns:
        Structured data dict specific to document type
    """

@tool
async def validate_document_consistency(
    application_id: str,
    field_name: str
) -> dict:
    """Cross-validate a field across multiple documents.

    Example: Check that employer name on pay stub matches W-2 matches
    employment verification letter.

    Args:
        application_id: UUID of the application
        field_name: The field to cross-validate (e.g., "employer_name", "income")

    Returns:
        {
            "field": "employer_name",
            "consistent": true,
            "values_found": [
                {"source": "pay_stub", "value": "Acme Corp"},
                {"source": "w2", "value": "Acme Corporation"}
            ],
            "confidence": 0.92,
            "notes": "Minor name variation, likely same entity"
        }
    """

@tool
async def detect_document_anomalies(document_id: str) -> dict:
    """Check document for potential issues: low resolution, tampering indicators,
    expired documents, or missing required fields.

    Args:
        document_id: UUID of the document

    Returns:
        {
            "anomalies": [
                {"type": "low_resolution", "severity": "warning", "details": "..."},
            ],
            "is_valid": true
        }
    """

# --- RESOURCES ---

@resource("document://{document_id}/text")
async def get_document_text(document_id: str) -> str:
    """Get the raw OCR text of a document."""

@resource("document://{document_id}/metadata")
async def get_document_metadata(document_id: str) -> dict:
    """Get document metadata (type, size, upload date, status)."""

@resource("application://{application_id}/documents")
async def get_application_documents(application_id: str) -> list:
    """List all documents for an application with their processing status."""

# --- PROMPTS ---

SYSTEM_PROMPT = """You are a document processing specialist for mortgage applications.
Your job is to:
1. Extract accurate structured data from documents
2. Cross-validate information across multiple documents
3. Flag any inconsistencies or anomalies
4. Rate your confidence in each extraction

Be precise with numbers (income, account balances). When uncertain, provide a
confidence score and explain what's unclear. Never fabricate data - if a field
cannot be reliably extracted, mark it as "unreadable" with a reason."""
```

---

### 2.2 Credit Analysis Agent

**Purpose:** Analyze credit history beyond the raw score, identifying trajectory, patterns, and context.

**MCP Server Definition:**

```python
# agents/credit_analysis.py

AGENT_NAME = "credit_analysis"
AGENT_DESCRIPTION = "Analyzes credit history, trajectory, and behavioral patterns"

# --- TOOLS ---

@tool
async def analyze_credit_trajectory(
    credit_score: int,
    credit_history_months: int,
    recent_inquiries: int,
    payment_history: dict
) -> dict:
    """Analyze credit score trajectory and direction.

    Args:
        credit_score: Current credit score
        credit_history_months: Length of credit history in months
        recent_inquiries: Number of hard inquiries in last 12 months
        payment_history: {
            "on_time_pct": 0.95,
            "late_30_count": 1,
            "late_60_count": 0,
            "late_90_count": 0,
            "collections": 0,
            "months_since_last_late": 14
        }

    Returns:
        {
            "trajectory": "improving|stable|declining",
            "trajectory_score": 85,
            "analysis": "Credit trajectory is strongly positive..."
        }
    """

@tool
async def assess_credit_utilization(
    total_credit_limit: float,
    total_credit_used: float,
    individual_accounts: list
) -> dict:
    """Assess credit utilization ratio and patterns.

    Args:
        total_credit_limit: Combined credit limits
        total_credit_used: Current total balances
        individual_accounts: List of {name, limit, balance, type}

    Returns:
        {
            "overall_utilization": 0.22,
            "assessment": "healthy",
            "score": 78,
            "details": "..."
        }
    """

@tool
async def evaluate_credit_mix(accounts: list) -> dict:
    """Evaluate the diversity of credit types.

    Args:
        accounts: List of {type: "revolving|installment|mortgage|other", ...}

    Returns:
        {
            "mix_score": 70,
            "types_present": ["revolving", "installment"],
            "recommendation": "Limited credit mix. Adding an installment loan would improve diversity."
        }
    """

@tool
async def analyze_derogatory_marks(
    bankruptcies: list,
    collections: list,
    judgments: list,
    foreclosures: list
) -> dict:
    """Analyze severity and recency of derogatory marks with context.

    Returns:
        {
            "severity_score": 60,
            "context_analysis": "Single medical collection from 3 years ago...",
            "recovery_indicators": ["18 months clean", "active credit building"],
            "impact_assessment": "moderate_but_recovering"
        }
    """

# --- RESOURCES ---

@resource("application://{application_id}/credit_data")
async def get_credit_data(application_id: str) -> dict:
    """Get all credit-related data from application and extracted documents."""

# --- PROMPTS ---

SYSTEM_PROMPT = """You are a credit analysis specialist for mortgage underwriting.
Your role is to analyze credit history HOLISTICALLY, not just the credit score number.

Key principles:
1. TRAJECTORY matters more than current position. Someone improving from 580 to 680
   is often a better risk than someone stable at 700 with recent negative trends.
2. CONTEXT matters. Medical collections, pandemic-era hardships, and job transitions
   are different from reckless spending.
3. THIN FILES are not the same as bad credit. New immigrants, young adults, and people
   who paid cash for everything may have short histories but strong financial discipline.
4. RECOVERY PATTERNS indicate character. Look for evidence of financial responsibility
   after setbacks.

Provide specific scores (0-100) for each sub-dimension and explain your reasoning."""
```

---

### 2.3 Employment Verification Agent

**Purpose:** Assess employment stability, income reliability, and career trajectory.

```python
# agents/employment_verification.py

AGENT_NAME = "employment_verification"
AGENT_DESCRIPTION = "Verifies employment and assesses income stability and career trajectory"

# --- TOOLS ---

@tool
async def assess_employment_stability(
    employment_status: str,
    employer_name: str,
    years_at_current_job: float,
    years_in_field: float,
    is_self_employed: bool,
    industry: str
) -> dict:
    """Assess the stability of the applicant's employment situation.

    Returns:
        {
            "stability_score": 82,
            "risk_level": "low",
            "factors": {
                "tenure": {"score": 75, "note": "3 years - moderate tenure"},
                "industry": {"score": 90, "note": "Technology sector - high demand"},
                "employer": {"score": 85, "note": "Large established company"}
            }
        }
    """

@tool
async def verify_income_consistency(
    stated_annual_income: float,
    pay_stubs: list,
    w2s: list,
    tax_returns: list
) -> dict:
    """Cross-verify stated income against documentary evidence.

    Args:
        stated_annual_income: What applicant reported
        pay_stubs: Extracted pay stub data
        w2s: Extracted W-2 data
        tax_returns: Extracted tax return data

    Returns:
        {
            "verified": true,
            "stated_income": 95000,
            "documented_income": 94500,
            "variance_pct": 0.5,
            "income_trend": "increasing",
            "confidence": 0.95
        }
    """

@tool
async def assess_career_trajectory(
    job_title: str,
    years_in_field: float,
    industry: str,
    education_level: str,
    field_of_study: str
) -> dict:
    """Assess the applicant's career growth potential and income trajectory.

    Returns:
        {
            "trajectory_score": 80,
            "growth_potential": "high",
            "industry_outlook": "strong",
            "income_growth_projection": "above_average",
            "analysis": "Software engineering in technology sector..."
        }
    """

@tool
async def evaluate_self_employment_risk(
    business_type: str,
    years_in_business: float,
    revenue_history: list,
    client_concentration: float,
    industry: str
) -> dict:
    """Special evaluation for self-employed applicants.

    Returns:
        {
            "risk_score": 65,
            "revenue_stability": "moderate",
            "client_diversification": "good",
            "business_viability": "strong",
            "concerns": ["Revenue fluctuation of 15% year-over-year"],
            "strengths": ["5+ years in business", "Multiple revenue streams"]
        }
    """

# --- PROMPTS ---

SYSTEM_PROMPT = """You are an employment verification and income analysis specialist.
Your role is to assess:
1. Is the applicant's employment stable enough to maintain mortgage payments?
2. Is the stated income consistent with documentary evidence?
3. What is the applicant's career trajectory - will income grow, remain stable, or decline?
4. For self-employed applicants, is the business viable and income predictable?

Consider industry trends, employer stability, and career stage. A junior engineer at
a well-funded tech company may have more income growth potential than a senior manager
at a declining industry, even if current income is lower."""
```

---

### 2.4 Financial Health Agent

**Purpose:** Analyze overall financial health including savings, assets, debt management, and behavioral patterns.

```python
# agents/financial_health.py

AGENT_NAME = "financial_health"
AGENT_DESCRIPTION = "Analyzes financial health, savings patterns, DTI, and behavioral indicators"

# --- TOOLS ---

@tool
async def calculate_dti_ratio(
    gross_monthly_income: float,
    monthly_debts: dict,
    proposed_mortgage_payment: float
) -> dict:
    """Calculate front-end and back-end DTI ratios.

    Returns:
        {
            "front_end_dti": 28.5,
            "back_end_dti": 36.2,
            "assessment": "within_limits",
            "max_allowed_back_end": 43.0,
            "headroom_pct": 6.8,
            "monthly_breakdown": {
                "gross_income": 7916.67,
                "proposed_mortgage": 2256.00,
                "car_loan": 350.00,
                "student_loans": 400.00,
                "credit_cards": 150.00,
                "total_obligations": 3156.00
            }
        }
    """

@tool
async def assess_reserves_and_assets(
    liquid_assets: float,
    retirement_accounts: float,
    investment_accounts: float,
    proposed_monthly_payment: float
) -> dict:
    """Assess adequacy of financial reserves.

    Returns:
        {
            "months_of_reserves": 6.2,
            "assessment": "adequate",
            "score": 75,
            "breakdown": {
                "liquid_reserves_months": 3.1,
                "total_net_worth": 120000,
                "emergency_fund_adequate": true
            }
        }
    """

@tool
async def analyze_savings_pattern(bank_statements: list) -> dict:
    """Analyze savings behavior from bank statement data.

    Args:
        bank_statements: Extracted bank statement data (2-3 months)

    Returns:
        {
            "pattern": "consistent_saver",
            "score": 80,
            "average_monthly_savings": 1200,
            "savings_trend": "increasing",
            "irregular_deposits": [
                {"date": "2026-01-15", "amount": 5000, "flag": "needs_explanation"}
            ],
            "overdraft_count": 0
        }
    """

@tool
async def analyze_alternative_credit_data(
    rent_payments: list,
    utility_payments: list,
    insurance_payments: list,
    phone_payments: list
) -> dict:
    """Analyze non-traditional credit indicators for thin-file applicants.

    Returns:
        {
            "alternative_credit_score": 72,
            "data_points_available": 4,
            "rent_payment_history": {
                "months_analyzed": 24,
                "on_time_pct": 100,
                "score": 95
            },
            "utility_payment_history": {
                "months_analyzed": 18,
                "on_time_pct": 97,
                "score": 85
            },
            "overall_assessment": "Strong alternative credit profile..."
        }
    """

# --- PROMPTS ---

SYSTEM_PROMPT = """You are a financial health analyst for mortgage underwriting.
Evaluate the applicant's complete financial picture:

1. DTI RATIO: Calculate both front-end (housing only) and back-end (all debts).
   Consider future changes (loans ending soon, expected income increases).

2. RESERVES: Assess whether the applicant has enough savings to weather financial
   disruptions. 3-6 months of reserves is standard; more is better.

3. SAVINGS BEHAVIOR: Regular saving indicates financial discipline even when
   absolute amounts are modest. Pattern matters more than total.

4. ALTERNATIVE CREDIT: For applicants without traditional credit history, rent
   payments, utility bills, and phone payments can demonstrate responsibility.

5. BEHAVIORAL FLAGS: Look for overdrafts, bounced checks, irregular large deposits
   (potential undisclosed debt or gift funds), and spending patterns."""
```

---

### 2.5 Property Valuation Agent

**Purpose:** Assess property value, market conditions, and collateral adequacy.

```python
# agents/property_valuation.py

AGENT_NAME = "property_valuation"
AGENT_DESCRIPTION = "Assesses property value, market conditions, and LTV ratio"

# --- TOOLS ---

@tool
async def calculate_ltv_ratio(
    purchase_price: float,
    down_payment: float,
    appraised_value: float = None
) -> dict:
    """Calculate Loan-to-Value ratio.

    Returns:
        {
            "ltv_ratio": 80.0,
            "loan_amount": 280000,
            "assessment": "standard",
            "pmi_required": false,
            "pmi_threshold": 80.0
        }
    """

@tool
async def assess_property_type_risk(
    property_type: str,
    property_use: str,
    location: dict
) -> dict:
    """Assess risk based on property type and intended use.

    Returns:
        {
            "risk_score": 82,
            "property_type_risk": "low",
            "usage_risk": "low",
            "location_risk": "low",
            "factors": [
                "Single-family primary residence - lowest risk category",
                "Located in stable suburban market"
            ]
        }
    """

@tool
async def analyze_market_conditions(
    state: str,
    city: str,
    zip_code: str,
    property_type: str
) -> dict:
    """Analyze local real estate market conditions.

    Note: In v1, this uses general market knowledge from the LLM.
    In v2, this will integrate with real estate data APIs.

    Returns:
        {
            "market_trend": "appreciating",
            "appreciation_rate_annual": 3.5,
            "market_temperature": "warm",
            "days_on_market_avg": 45,
            "inventory_level": "moderate",
            "forecast": "stable_growth",
            "risk_factors": [],
            "score": 78
        }
    """

# --- PROMPTS ---

SYSTEM_PROMPT = """You are a property valuation and real estate market analyst.
Assess the property as collateral for a mortgage loan:

1. LTV RATIO: Lower LTV = lower risk. Above 80% requires PMI. Above 95% is high risk.
2. PROPERTY TYPE: Single-family < Condo < Multi-family < Manufactured (risk order).
3. PROPERTY USE: Primary residence < Second home < Investment (risk order).
4. MARKET CONDITIONS: Consider local trends, but avoid speculation.
5. COLLATERAL ADEQUACY: Would the lender be able to recover the loan balance if needed?

Be conservative in valuation estimates. It's better to be slightly under than over."""
```

---

### 2.6 Applicant Profile Agent

**Purpose:** Analyze residency status, education, career potential, and contextual factors that may affect loan risk.

```python
# agents/applicant_profile.py

AGENT_NAME = "applicant_profile"
AGENT_DESCRIPTION = "Analyzes applicant's residency, education, career potential, and contextual factors"

# --- TOOLS ---

@tool
async def assess_residency_status(
    citizenship_status: str,
    visa_type: str = None,
    years_in_country: int = None,
    has_itin: bool = False,
    tax_filing_years: int = 0
) -> dict:
    """Assess the impact of residency/citizenship status on loan risk.

    This is NOT used to discriminate but to understand:
    - Legal eligibility for certain loan programs
    - Stability of residency (visa duration)
    - Flight risk assessment

    Returns:
        {
            "eligibility": {
                "conventional": true,
                "fha": true,
                "va": false,
                "usda": true
            },
            "stability_score": 75,
            "factors": [
                "H-1B visa with 4 years remaining",
                "Employer-sponsored - indicates valued employee",
                "3 years of US tax filing history"
            ],
            "risk_assessment": "Moderate stability. Visa renewal is typical for this role.",
            "score": 72
        }
    """

@tool
async def assess_education_and_career_potential(
    education_level: str,
    field_of_study: str,
    current_role: str,
    industry: str,
    years_of_experience: int
) -> dict:
    """Assess future earning potential based on education and career stage.

    Returns:
        {
            "career_potential_score": 85,
            "education_relevance": "high",
            "industry_growth_outlook": "strong",
            "income_growth_projection": "above_average",
            "analysis": "Bachelor's in CS with 8 years in software engineering..."
        }
    """

@tool
async def identify_compensating_factors(
    application_data: dict,
    risk_factors: list
) -> dict:
    """For each identified risk factor, find compensating strengths.

    This is critical for applicants with non-traditional profiles who may
    have risk factors in one area but strengths in others.

    Args:
        application_data: Full application data
        risk_factors: List of identified concerns from other agents

    Returns:
        {
            "compensating_factors": [
                {
                    "risk": "Limited credit history (2 years)",
                    "compensation": "24 months of verified on-time rent payments ($1,800/month)",
                    "strength": "strong"
                },
                {
                    "risk": "Non-citizen (H-1B visa)",
                    "compensation": "Employer is Fortune 500, role in high demand, 4 years on visa",
                    "strength": "moderate"
                }
            ],
            "net_assessment": "Risk factors are well-compensated by alternative indicators"
        }
    """

# --- PROMPTS ---

SYSTEM_PROMPT = """You are an applicant profile analyst specializing in holistic assessment.
Your role is crucial for FAIR and INCLUSIVE lending:

1. RESIDENCY: Assess stability and eligibility without discriminating. Non-citizens
   with stable visas and employment are often excellent borrowers.

2. EDUCATION & CAREER: Consider future earning trajectory, not just current income.
   A medical resident earning $60K will earn $200K+ within years.

3. COMPENSATING FACTORS: This is your most important function. When other agents
   identify risk factors, find legitimate compensating strengths. Examples:
   - No credit score → strong rent payment history
   - Short employment → strong industry demand and credentials
   - Lower income → low DTI and strong savings

4. FAIR LENDING: NEVER use race, ethnicity, religion, gender, or marital status
   in your analysis. These are prohibited factors under ECOA and Fair Housing Act.

You are an advocate for creditworthy borrowers who might be overlooked by
traditional scoring systems."""
```

---

### 2.7 Regulatory Compliance Agent

**Purpose:** Ensure every assessment complies with fair lending laws and regulatory requirements.

```python
# agents/regulatory_compliance.py

AGENT_NAME = "regulatory_compliance"
AGENT_DESCRIPTION = "Ensures fair lending compliance and regulatory adherence"

# --- TOOLS ---

@tool
async def check_fair_lending_compliance(
    risk_dimensions: list,
    recommendation: str,
    adverse_factors: list
) -> dict:
    """Review the risk assessment for potential fair lending violations.

    Checks:
    - No prohibited factors (race, religion, sex, marital status, national origin)
      used in the analysis
    - Adverse action reasons are specific and actionable
    - Assessment is consistent with similar profiles
    - No disparate impact indicators

    Returns:
        {
            "compliant": true,
            "issues": [],
            "warnings": [],
            "prohibited_factors_detected": false,
            "adverse_action_valid": true,
            "score": 100
        }
    """

@tool
async def generate_adverse_action_notice(
    application_data: dict,
    risk_assessment: dict,
    decision: str
) -> dict:
    """Generate legally compliant adverse action notice if application is denied.

    Must comply with ECOA Regulation B requirements:
    - Specific reasons for denial (up to 4)
    - Name and address of credit bureau used (if applicable)
    - Applicant's right to request specific reasons
    - Equal credit opportunity notice

    Returns:
        {
            "notice_required": true,
            "reasons": [
                "Debt-to-income ratio exceeds program guidelines",
                "Insufficient length of credit history",
                "Insufficient cash reserves after closing"
            ],
            "disclosure_text": "...",
            "compliant": true
        }
    """

@tool
async def validate_loan_eligibility(
    applicant_data: dict,
    loan_product: dict
) -> dict:
    """Verify the applicant meets all regulatory eligibility requirements
    for the selected loan product.

    Returns:
        {
            "eligible": true,
            "requirements_met": [...],
            "requirements_not_met": [],
            "alternative_programs": []
        }
    """

# --- PROMPTS ---

SYSTEM_PROMPT = """You are a mortgage regulatory compliance specialist.
Your role is to ensure every lending decision complies with federal law:

1. ECOA (Equal Credit Opportunity Act): Prohibits discrimination based on
   race, color, religion, national origin, sex, marital status, age,
   receipt of public assistance, or exercise of rights under consumer credit laws.

2. FAIR HOUSING ACT: Prohibits discrimination in housing-related transactions.

3. HMDA: Ensure data collection requirements are met.

4. TILA: Ensure required disclosures are accurate and timely.

5. ADVERSE ACTION NOTICES: If recommending denial, provide specific, actionable
   reasons that do not reference prohibited factors.

YOU ARE THE LAST CHECKPOINT before a decision is presented. If you detect any
compliance issue, flag it immediately. A false negative here has legal consequences."""
```

---

### 2.8 Risk Aggregation Agent

**Purpose:** Synthesize all agent outputs into a final composite risk score with natural-language explanation.

```python
# agents/risk_aggregation.py

AGENT_NAME = "risk_aggregation"
AGENT_DESCRIPTION = "Synthesizes all agent analyses into a composite risk score and recommendation"

# --- TOOLS ---

@tool
async def calculate_composite_score(dimension_scores: list) -> dict:
    """Calculate the weighted composite risk score.

    Args:
        dimension_scores: List of {
            "dimension": "credit_history",
            "score": 58,
            "weight": 0.20,
            "agent": "credit_analysis"
        }

    Returns:
        {
            "composite_score": 72.5,
            "risk_band": "medium",
            "confidence": 0.85,
            "weighted_breakdown": [...]
        }
    """

@tool
async def generate_recommendation(
    composite_score: float,
    risk_band: str,
    dimension_scores: list,
    compliance_result: dict,
    loan_product: dict
) -> dict:
    """Generate final recommendation with explanation.

    Returns:
        {
            "recommendation": "approve_with_conditions",
            "conditions": [
                "Verify employment with current employer within 10 business days",
                "Provide most recent bank statement (within 30 days)"
            ],
            "confidence": 0.85,
            "summary_for_applicant": "Your application shows strong fundamentals...",
            "summary_for_servicer": "Moderate risk profile with positive trajectory..."
        }
    """

@tool
async def generate_detailed_explanation(
    dimension_scores: list,
    recommendation: str,
    compensating_factors: list
) -> dict:
    """Generate comprehensive natural-language explanation of the assessment.

    This creates both:
    1. Applicant-facing summary (positive, encouraging, actionable)
    2. Servicer-facing analysis (detailed, technical, balanced)

    Returns:
        {
            "applicant_summary": "...",
            "servicer_analysis": "...",
            "key_strengths": [...],
            "key_risks": [...],
            "mitigating_factors": [...],
            "overall_narrative": "..."
        }
    """

# --- PROMPTS ---

SYSTEM_PROMPT = """You are the senior risk analyst synthesizing all assessment dimensions
into a final recommendation. Your output drives the lending decision.

SCORING WEIGHTS (adjustable by configuration):
- Credit History & Trajectory: 20%
- Employment & Income: 20%
- Financial Health (DTI, assets, savings): 15%
- Property & Collateral: 15%
- Applicant Profile (residency, education, career): 10%
- Behavioral Patterns (rent, utilities, banking): 10%
- Regulatory Compliance: 10%

RISK BANDS:
- Low Risk (75-100): Strong approval recommendation
- Medium Risk (50-74): Approve with conditions or manual review
- High Risk (25-49): Conditional approval possible with strong compensating factors
- Very High Risk (0-24): Likely deny, but provide specific improvement guidance

RECOMMENDATIONS:
- "approve": Clear approval, no significant conditions
- "approve_with_conditions": Approve pending verification of specific items
- "manual_review": Borderline case, needs human judgment
- "deny": Does not meet minimum requirements, provide adverse action reasons

CRITICAL RULES:
1. ALWAYS explain your reasoning. No black-box decisions.
2. ALWAYS identify compensating factors before recommending denial.
3. For applicants with non-traditional profiles, weight alternative data appropriately.
4. Your explanation must be understandable by a non-expert applicant.
5. Your servicer analysis must be detailed enough for an underwriter to agree or disagree."""
```

---

## 3. Agent Orchestration

### 3.1 Pipeline Execution

```python
# services/risk_assessment_service.py

async def run_risk_assessment(application_id: str) -> RiskAssessment:
    """Execute the full MCP agent pipeline for risk assessment."""

    # 1. Load application and document data
    app = await load_application(application_id)
    docs = await load_documents(application_id)

    # 2. Document Processing (sequential - must complete first)
    doc_results = await document_processing_agent.analyze(app, docs)

    # 3. Parallel Analysis Agents
    credit_task = credit_analysis_agent.analyze(app, doc_results)
    employment_task = employment_verification_agent.analyze(app, doc_results)
    financial_task = financial_health_agent.analyze(app, doc_results)
    property_task = property_valuation_agent.analyze(app)
    profile_task = applicant_profile_agent.analyze(app, doc_results)

    results = await asyncio.gather(
        credit_task, employment_task, financial_task,
        property_task, profile_task
    )

    # 4. Regulatory Compliance Check
    compliance_result = await regulatory_compliance_agent.analyze(
        app, results
    )

    # 5. Risk Aggregation (final synthesis)
    final_assessment = await risk_aggregation_agent.analyze(
        app, results, compliance_result
    )

    # 6. Store results
    await store_risk_assessment(application_id, final_assessment)
    await update_application_status(application_id, "under_review")
    await notify_servicer(application_id, final_assessment)

    return final_assessment
```

### 3.2 Error Handling

```python
# Each agent has retry logic and graceful degradation

async def run_agent_with_retry(agent, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await agent.analyze(*args)
        except LLMRateLimitError:
            await asyncio.sleep(2 ** attempt)
        except LLMProviderError:
            # Try fallback provider if configured
            if fallback_provider := get_fallback_provider():
                agent.switch_provider(fallback_provider)
                return await agent.analyze(*args)
            raise
        except Exception as e:
            if attempt == max_retries - 1:
                return AgentResult.error(agent.name, str(e))
            await asyncio.sleep(1)
```

### 3.3 Progress Tracking

Each agent reports progress via WebSocket:

```python
async def report_progress(application_id: str, agent_name: str, status: str):
    await websocket_manager.broadcast(
        f"application:{application_id}",
        {
            "type": "agent_progress",
            "data": {
                "agent": agent_name,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

---

## 4. LLM Provider Configuration

### 4.1 Provider Abstraction

```python
# services/llm_gateway.py

class LLMGateway:
    """Multi-provider LLM gateway."""

    def __init__(self, config: LLMConfig):
        self.provider = self._create_provider(config)

    def _create_provider(self, config: LLMConfig) -> LLMProvider:
        match config.provider:
            case "openai":
                return OpenAIProvider(
                    api_key=config.api_key,
                    base_url=config.base_url or "https://api.openai.com/v1",
                    model=config.default_model or "gpt-4o"
                )
            case "anthropic":
                return AnthropicProvider(
                    api_key=config.api_key,
                    base_url=config.base_url or "https://api.anthropic.com",
                    model=config.default_model or "claude-sonnet-4-20250514"
                )
            case "local":
                # OpenAI-compatible endpoint with custom base URL
                return OpenAIProvider(
                    api_key=config.api_key or "not-needed",
                    base_url=config.base_url,  # e.g., "http://llm.internal:8080/v1"
                    model=config.default_model
                )

    async def chat(self, messages: list, **kwargs) -> LLMResponse:
        """Send chat completion request."""
        return await self.provider.chat(messages, **kwargs)

    async def chat_with_tools(self, messages: list, tools: list, **kwargs) -> LLMResponse:
        """Send chat completion with tool/function calling."""
        return await self.provider.chat_with_tools(messages, tools, **kwargs)
```

### 4.2 Per-Agent LLM Configuration

Each agent can use a different model or provider:

```yaml
# config/agents.yaml
agents:
  document_processing:
    llm_provider: "openai"
    model: "gpt-4o"              # Best for document understanding
    temperature: 0.0
    max_tokens: 4096

  credit_analysis:
    llm_provider: "anthropic"
    model: "claude-sonnet-4-20250514"   # Good for nuanced analysis
    temperature: 0.1
    max_tokens: 4096

  risk_aggregation:
    llm_provider: "anthropic"
    model: "claude-sonnet-4-20250514"   # Needs strong reasoning
    temperature: 0.1
    max_tokens: 8192

  # Default for agents not explicitly configured
  default:
    llm_provider: "openai"
    model: "gpt-4o"
    temperature: 0.1
    max_tokens: 4096
```

---

## 5. Testing Strategy

### 5.1 Agent Unit Tests

Each agent has unit tests with mocked LLM responses:

```python
# tests/agents/test_credit_analysis.py

async def test_improving_credit_trajectory():
    """Applicant with improving credit should score higher than raw score suggests."""
    agent = CreditAnalysisAgent(mock_llm)
    result = await agent.analyze(
        application_with_improving_credit
    )
    assert result.score > 60  # Raw score would suggest ~50
    assert "improving" in result.trajectory
    assert len(result.positive_factors) > 0

async def test_thin_file_not_penalized():
    """Applicant with no credit history should not be treated same as bad credit."""
    agent = CreditAnalysisAgent(mock_llm)
    result = await agent.analyze(
        application_no_credit_history
    )
    assert result.score > 40  # Bad credit would score below 30
    assert "thin_file" in result.analysis or "no_history" in result.analysis
```

### 5.2 Integration Tests

Test the full pipeline with realistic scenarios:

```python
# tests/test_risk_assessment_pipeline.py

async def test_full_pipeline_strong_applicant():
    """Strong applicant should receive 'approve' recommendation."""
    result = await run_risk_assessment(strong_application_id)
    assert result.recommendation == "approve"
    assert result.overall_score >= 75

async def test_full_pipeline_non_citizen_compensating():
    """Non-citizen with strong compensating factors should not be auto-denied."""
    result = await run_risk_assessment(non_citizen_strong_app_id)
    assert result.recommendation != "deny"
    assert any("visa" in f.lower() for f in result.mitigating_factors)

async def test_compliance_agent_catches_violation():
    """Compliance agent should flag if prohibited factors leak into analysis."""
    result = await run_risk_assessment(test_application_id)
    assert result.compliance.compliant == True
```
