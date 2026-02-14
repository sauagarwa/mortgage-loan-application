"""
Applicant Profile Agent — evaluates overall borrower profile and stability.
"""

from .base import ApplicationData, BaseAgent


class ApplicantProfileAgent(BaseAgent):
    dimension_name = "applicant_profile"
    agent_name = "applicant_profile"
    weight = 0.05

    def build_prompt(self, data: ApplicationData) -> list[dict[str, str]]:
        personal = data.personal_info
        emp = data.employment_info
        financial = data.financial_info
        declarations = data.declarations

        # Identity documents
        id_docs = [
            d for d in data.documents
            if d["document_type"] == "government_id"
        ]
        doc_summary = ""
        if id_docs:
            doc_lines = [f"- {d['document_type']}: {d['status']}" for d in id_docs]
            doc_summary = "\n".join(doc_lines)
        else:
            doc_summary = "No identity documents uploaded"

        # Calculate age-related factors
        dob = personal.get("date_of_birth", "Not provided")
        marital = personal.get("marital_status", "Not provided")
        dependents = personal.get("dependents", "Not provided")
        citizenship = personal.get("citizenship_status", "Not provided")

        system_msg = f"""You are a mortgage applicant profile analyst AI. Evaluate the overall borrower
profile considering stability indicators, completeness of application, and holistic risk factors.

{self.RESULT_SCHEMA_INSTRUCTION}

Applicant profile scoring considerations:
- First-time homebuyer: neutral to slightly positive (government programs available)
- Complete documentation: positive indicator
- Stable residential history: positive indicator
- US citizen or permanent resident: standard processing
- Consistent information across all sections: positive indicator
- Co-borrower present: can strengthen application

Note: Do NOT discriminate based on protected classes. Focus only on financial
stability indicators and application completeness."""

        user_msg = f"""Analyze this mortgage applicant's overall profile:

**Personal Information:**
- Name: {personal.get("first_name", "")} {personal.get("last_name", "")}
- Date of Birth: {dob}
- Marital Status: {marital}
- Dependents: {dependents}
- Citizenship: {citizenship}

**Residential History:**
- Current Address: {personal.get("current_address", "Not provided")}
- Years at Current Address: {personal.get("years_at_address", "Not provided")}

**Employment Summary:**
- Status: {emp.get("employment_status", "Not provided")}
- Years at Current Job: {emp.get("years_at_job", "Not provided")}

**Financial Summary:**
- Annual Income: {self._format_currency(emp.get("annual_income") or financial.get("annual_income"))}
- Credit Score: {financial.get("credit_score", "Not provided")}
- Total Assets: {self._format_currency(financial.get("total_assets"))}

**Declarations:**
- First-time Homebuyer: {declarations.get("is_first_time_buyer", "Not specified")}
- Primary Residence: {declarations.get("will_occupy_as_primary", "Not specified")}
- Outstanding Judgments: {declarations.get("has_judgments", False)}
- Party to Lawsuit: {declarations.get("is_party_to_lawsuit", False)}
- Alimony/Child Support Obligations: {declarations.get("has_alimony_obligation", False)}

**Identity Documents:**
{doc_summary}

**Application Completeness:**
- Personal info: {"Complete" if personal.get("first_name") else "Incomplete"}
- Employment: {"Complete" if emp.get("employment_status") else "Incomplete"}
- Financial: {"Complete" if financial.get("annual_income") or financial.get("credit_score") else "Incomplete"}
- Property: {"Complete" if data.property_info.get("property_type") else "Incomplete"}

Provide your applicant profile assessment as JSON."""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
