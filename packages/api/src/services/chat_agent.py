"""
Conversational chat agent for mortgage applications.

Uses LLM tool calling to collect application data, recommend loans,
handle document uploads, and guide users through the mortgage process.
"""

import json
import logging
import random
import string
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from db import Application, Conversation, Document, LoanProduct, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .llm_gateway import call_llm

logger = logging.getLogger(__name__)


@dataclass
class ChatEvent:
    """Event yielded during chat response generation."""

    event_type: str  # text, tool_start, structured, file_request, auth_required, done
    data: dict[str, Any]


# ── Tool definitions (OpenAI function calling format) ─────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_loan_products",
            "description": (
                "Fetch available mortgage loan products. Use this to show the user "
                "what loan options are available based on their situation."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_loan_eligibility",
            "description": (
                "Check if the user meets basic eligibility for a specific loan product "
                "based on their credit score, income, down payment, and purchase price."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "loan_product_id": {
                        "type": "string",
                        "description": "ID of the loan product to check eligibility for.",
                    },
                    "credit_score": {"type": "integer", "description": "Applicant's credit score."},
                    "annual_income": {
                        "type": "number",
                        "description": "Applicant's annual income.",
                    },
                    "purchase_price": {
                        "type": "number",
                        "description": "Property purchase price.",
                    },
                    "down_payment": {"type": "number", "description": "Down payment amount."},
                },
                "required": ["loan_product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_application_data",
            "description": (
                "Save collected application data. Call this whenever you have gathered "
                "information from the user (personal info, employment, financial, property, "
                "declarations). Creates a draft application if one doesn't exist yet."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "loan_product_id": {
                        "type": "string",
                        "description": "Selected loan product ID.",
                    },
                    "personal_info": {
                        "type": "object",
                        "description": "Personal details: first_name, last_name, email, phone, date_of_birth, ssn_last_four, citizenship_status, address (street, city, state, zip_code).",
                    },
                    "employment_info": {
                        "type": "object",
                        "description": "Employment details: employment_status, employer_name, job_title, years_at_current_job, years_in_field, annual_income, additional_income, additional_income_source, is_self_employed.",
                    },
                    "financial_info": {
                        "type": "object",
                        "description": "Financial details: credit_score_self_reported, monthly_debts (car_loan, student_loans, credit_cards, other), total_assets, liquid_assets, checking_balance, savings_balance, retirement_accounts, investment_accounts, bankruptcy_history, foreclosure_history.",
                    },
                    "property_info": {
                        "type": "object",
                        "description": "Property details: property_type (single_family, condo, townhouse, multi_family, manufactured), property_use (primary_residence, second_home, investment), purchase_price, down_payment, address (street, city, state, zip_code).",
                    },
                    "declarations": {
                        "type": "object",
                        "description": "Yes/no declarations: outstanding_judgments, party_to_lawsuit, federal_debt_delinquent, alimony_obligation, co_signer_on_other_loan, us_citizen, primary_residence.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_document_upload",
            "description": (
                "Ask the user to upload a specific type of document. The UI will show "
                "a file upload widget in the chat."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "document_type": {
                        "type": "string",
                        "enum": [
                            "government_id",
                            "pay_stub",
                            "w2",
                            "tax_return",
                            "bank_statement",
                            "employment_letter",
                            "proof_of_assets",
                            "purchase_agreement",
                        ],
                        "description": "Type of document to request.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why this document is needed.",
                    },
                },
                "required": ["document_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_document_status",
            "description": "Check the processing status of uploaded documents for the current application.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_application_summary",
            "description": "Get a summary of all data collected so far for the current application.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_application",
            "description": (
                "Submit the completed application for review. The user must be "
                "authenticated before this can succeed."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# ── System prompts by phase ──────────────────────────────────────────────

SYSTEM_PROMPT_BASE = """\
You are a friendly, knowledgeable mortgage advisor chatbot for MortgageAI. \
Your job is to help users apply for a home loan through a conversational experience.

Key guidelines:
- Be warm, professional, and concise. Keep responses short (2-4 sentences typically).
- Ask one topic at a time. Don't overwhelm with multiple questions.
- Use the tools available to you to save data, check eligibility, and manage documents.
- When you have enough info for a section, save it immediately using save_application_data.
- Guide the user step by step through the process.
- If the user seems unsure, explain things simply without jargon.
- Never make up or assume financial data — always ask the user.

Current application data collected so far:
{collected_data}
"""

PHASE_PROMPTS = {
    "greeting": (
        "Welcome the user and ask what brings them here today. "
        "Ask if they're looking to purchase a home, refinance, or just exploring options. "
        "Keep it brief and friendly."
    ),
    "needs_assessment": (
        "Collect key information to recommend loan products: "
        "approximate annual income, credit score range, target property price, "
        "and how much they can put down. Ask naturally, one or two items at a time. "
        "Once you have enough info, use get_loan_products to fetch options and "
        "check_loan_eligibility to see what they qualify for."
    ),
    "loan_recommendation": (
        "Present the loan products that match the user's situation. "
        "Explain the key differences (rate type, term, down payment requirement). "
        "Help them choose the best option. Once they decide, save the loan_product_id "
        "using save_application_data."
    ),
    "info_collection": (
        "Collect the remaining application details. Go through these sections in order, "
        "asking a few fields at a time:\n"
        "1. Personal info (name, email, phone, DOB, SSN last 4, address, citizenship)\n"
        "2. Employment (status, employer, title, years, income)\n"
        "3. Financial (credit score, monthly debts, assets, savings, bankruptcy/foreclosure history)\n"
        "4. Property (type, use, price, down payment, address)\n"
        "5. Declarations (judgments, lawsuits, federal debt, alimony, co-signer, citizenship, primary residence)\n\n"
        "Save data as you collect each section using save_application_data. "
        "Don't ask for everything at once — be conversational."
    ),
    "documents": (
        "Guide the user to upload supporting documents. Key documents needed:\n"
        "- Government ID\n"
        "- Recent pay stubs (last 2)\n"
        "- W-2 forms (last 2 years)\n"
        "- Bank statements (last 2 months)\n\n"
        "Use request_document_upload to prompt for each document type. "
        "Use get_document_status to check processing status. "
        "Confirm when documents are received."
    ),
    "review": (
        "Use get_application_summary to show the user their complete application. "
        "Ask them to review and confirm everything is correct. "
        "If they want to change anything, update it with save_application_data. "
        "When they're ready, proceed to submission."
    ),
    "submission": (
        "The user is ready to submit. Call submit_application. "
        "If it returns auth_required, let the user know they need to log in first "
        "and the UI will show them a login button. "
        "After successful submission, congratulate them and let them know "
        "they can track their application on the dashboard."
    ),
}


def _build_system_prompt(phase: str, collected_data: dict) -> str:
    """Build the full system prompt for the current conversation phase."""
    data_summary = json.dumps(collected_data, indent=2) if collected_data else "{}"
    base = SYSTEM_PROMPT_BASE.format(collected_data=data_summary)
    phase_instruction = PHASE_PROMPTS.get(phase, PHASE_PROMPTS["greeting"])
    return f"{base}\n\nCurrent phase: {phase}\nInstructions: {phase_instruction}"


def _generate_application_number() -> str:
    year = datetime.now(UTC).year
    suffix = "".join(random.choices(string.digits, k=5))
    return f"MA-{year}-{suffix}"


# ── Tool execution ───────────────────────────────────────────────────────


async def _execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    conversation: Conversation,
    session: AsyncSession,
) -> tuple[dict[str, Any], list[ChatEvent]]:
    """Execute a tool and return (result_dict, extra_events)."""
    events: list[ChatEvent] = []

    if tool_name == "get_loan_products":
        result = await session.execute(
            select(LoanProduct).where(LoanProduct.is_active == True)  # noqa: E712
        )
        products = result.scalars().all()
        product_list = []
        for p in products:
            product_list.append(
                {
                    "id": str(p.id),
                    "name": p.name,
                    "type": p.type,
                    "term_years": p.term_years,
                    "rate_type": p.rate_type,
                    "min_down_payment_pct": float(p.min_down_payment_pct)
                    if p.min_down_payment_pct
                    else None,
                    "min_credit_score": p.min_credit_score,
                    "max_dti_ratio": float(p.max_dti_ratio) if p.max_dti_ratio else None,
                    "max_loan_amount": float(p.max_loan_amount) if p.max_loan_amount else None,
                    "description": p.description,
                    "features": p.features,
                }
            )
        events.append(
            ChatEvent(
                event_type="structured",
                data={"type": "loan_cards", "products": product_list},
            )
        )
        return {"products": product_list}, events

    elif tool_name == "check_loan_eligibility":
        loan_id = arguments.get("loan_product_id")
        if not loan_id:
            return {"eligible": False, "reason": "No loan product specified."}, events
        result = await session.execute(select(LoanProduct).where(LoanProduct.id == UUID(loan_id)))
        product = result.scalar_one_or_none()
        if not product:
            return {"eligible": False, "reason": "Loan product not found."}, events

        issues = []
        credit = arguments.get("credit_score")
        if credit and product.min_credit_score and credit < product.min_credit_score:
            issues.append(f"Credit score {credit} below minimum {product.min_credit_score}.")
        purchase = arguments.get("purchase_price", 0)
        dp = arguments.get("down_payment", 0)
        if purchase > 0 and product.min_down_payment_pct:
            required_dp = float(product.min_down_payment_pct) / 100 * purchase
            if dp < required_dp:
                issues.append(
                    f"Down payment ${dp:,.0f} below required "
                    f"{float(product.min_down_payment_pct)}% (${required_dp:,.0f})."
                )
        income = arguments.get("annual_income", 0)
        if income > 0 and product.max_dti_ratio:
            # Rough DTI check
            loan_amount = purchase - dp
            monthly_payment_est = (
                loan_amount / (product.term_years * 12) * 1.5
            )  # rough with interest
            dti = (monthly_payment_est / (income / 12)) * 100
            if dti > float(product.max_dti_ratio):
                issues.append(f"Estimated DTI {dti:.0f}% exceeds maximum {product.max_dti_ratio}%.")

        if issues:
            return {
                "eligible": False,
                "product_name": product.name,
                "issues": issues,
                "suggestion": "You may still qualify with adjustments. Let's discuss options.",
            }, events
        return {
            "eligible": True,
            "product_name": product.name,
            "message": "You appear to meet the basic eligibility requirements!",
        }, events

    elif tool_name == "save_application_data":
        collected = conversation.collected_data or {}

        # Merge provided data into collected_data
        for key in [
            "personal_info",
            "employment_info",
            "financial_info",
            "property_info",
            "declarations",
        ]:
            if key in arguments and arguments[key]:
                existing = collected.get(key, {})
                existing.update(arguments[key])
                collected[key] = existing

        if "loan_product_id" in arguments:
            collected["loan_product_id"] = arguments["loan_product_id"]

        conversation.collected_data = collected

        # Create or update the draft application
        if conversation.application_id:
            result = await session.execute(
                select(Application).where(Application.id == conversation.application_id)
            )
            app = result.scalar_one_or_none()
            if app:
                if "personal_info" in collected:
                    app.personal_info = collected["personal_info"]
                if "employment_info" in collected:
                    app.employment_info = collected["employment_info"]
                if "financial_info" in collected:
                    app.financial_info = collected["financial_info"]
                if "property_info" in collected:
                    app.property_info = collected["property_info"]
                if "declarations" in collected:
                    app.declarations = collected["declarations"]
                if "loan_product_id" in collected:
                    app.loan_product_id = UUID(collected["loan_product_id"])
                # Recalculate computed fields
                prop = collected.get("property_info", {})
                if prop.get("purchase_price") and prop.get("down_payment"):
                    app.loan_amount = prop["purchase_price"] - prop["down_payment"]
                    app.down_payment = prop["down_payment"]
                emp = collected.get("employment_info", {})
                fin = collected.get("financial_info", {})
                debts = fin.get("monthly_debts", {})
                total_debt = sum(
                    debts.get(k, 0) for k in ["car_loan", "student_loans", "credit_cards", "other"]
                )
                income = emp.get("annual_income", 0)
                if income > 0 and total_debt > 0:
                    app.dti_ratio = (total_debt / (income / 12)) * 100
        elif "loan_product_id" in collected:
            # Need a loan product to create an application — create a placeholder user-less app
            app = Application(
                application_number=_generate_application_number(),
                applicant_id=UUID("00000000-0000-0000-0000-000000000000"),  # placeholder
                loan_product_id=UUID(collected["loan_product_id"]),
                status="draft",
                personal_info=collected.get("personal_info", {}),
                employment_info=collected.get("employment_info", {}),
                financial_info=collected.get("financial_info", {}),
                property_info=collected.get("property_info", {}),
                declarations=collected.get("declarations", {}),
            )
            session.add(app)
            await session.flush()
            conversation.application_id = app.id

        # Auto-advance phase based on what's been collected
        if collected.get("loan_product_id") and conversation.current_phase in (
            "greeting",
            "needs_assessment",
            "loan_recommendation",
        ):
            conversation.current_phase = "info_collection"
        sections_done = sum(
            1
            for k in [
                "personal_info",
                "employment_info",
                "financial_info",
                "property_info",
                "declarations",
            ]
            if collected.get(k)
        )
        if sections_done >= 4 and conversation.current_phase == "info_collection":
            conversation.current_phase = "documents"

        await session.flush()
        return {"saved": True, "sections_collected": sections_done}, events

    elif tool_name == "request_document_upload":
        doc_type = arguments.get("document_type", "other")
        reason = arguments.get("reason", "")
        events.append(
            ChatEvent(
                event_type="file_request",
                data={"document_type": doc_type, "reason": reason},
            )
        )
        return {"requested": True, "document_type": doc_type}, events

    elif tool_name == "get_document_status":
        if not conversation.application_id:
            return {"documents": [], "message": "No application created yet."}, events
        result = await session.execute(
            select(Document).where(Document.application_id == conversation.application_id)
        )
        docs = result.scalars().all()
        doc_list = [
            {
                "id": str(d.id),
                "type": d.document_type,
                "filename": d.original_filename,
                "status": d.status,
                "confidence": float(d.extraction_confidence) if d.extraction_confidence else None,
            }
            for d in docs
        ]
        return {"documents": doc_list}, events

    elif tool_name == "get_application_summary":
        collected = conversation.collected_data or {}
        summary = {
            "has_application": conversation.application_id is not None,
            "collected_sections": {
                k: bool(collected.get(k))
                for k in [
                    "loan_product_id",
                    "personal_info",
                    "employment_info",
                    "financial_info",
                    "property_info",
                    "declarations",
                ]
            },
            "data": collected,
        }
        if conversation.application_id:
            result = await session.execute(
                select(Document).where(Document.application_id == conversation.application_id)
            )
            docs = result.scalars().all()
            summary["documents"] = [
                {
                    "type": d.document_type,
                    "filename": d.original_filename,
                    "status": d.status,
                }
                for d in docs
            ]
        events.append(
            ChatEvent(
                event_type="structured",
                data={"type": "summary", "summary": summary},
            )
        )
        return summary, events

    elif tool_name == "submit_application":
        if not conversation.user_id:
            events.append(ChatEvent(event_type="auth_required", data={}))
            return {
                "submitted": False,
                "reason": "auth_required",
                "message": "The user needs to log in before submitting.",
            }, events

        if not conversation.application_id:
            return {"submitted": False, "reason": "No application created yet."}, events

        result = await session.execute(
            select(Application).where(Application.id == conversation.application_id)
        )
        app = result.scalar_one_or_none()
        if not app:
            return {"submitted": False, "reason": "Application not found."}, events

        # Update applicant and submit
        app.applicant_id = UUID(conversation.user_id)
        app.status = "submitted"
        app.submitted_at = datetime.now(UTC)
        conversation.status = "completed"
        conversation.current_phase = "submission"
        await session.flush()

        # Trigger risk assessment (lazy import to avoid circular dependency)
        try:
            from ..worker.tasks.risk_assessment import run_risk_assessment

            run_risk_assessment.apply_async(args=[str(app.id)], countdown=5, queue="risk")
        except Exception as e:
            logger.warning(f"Failed to trigger risk assessment: {e}")

        return {
            "submitted": True,
            "application_number": app.application_number,
            "message": "Application submitted successfully!",
        }, events

    return {"error": f"Unknown tool: {tool_name}"}, events


# ── Main chat handler ────────────────────────────────────────────────────


async def handle_chat_message(
    conversation: Conversation,
    user_message: str,
    session: AsyncSession,
) -> list[ChatEvent]:
    """Process a user message and return a list of chat events.

    Runs the LLM tool-calling loop: send message -> if tool_calls, execute
    them and send results back -> repeat until the LLM produces a text response.
    """
    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=user_message,
        message_type="text",
    )
    session.add(user_msg)
    await session.flush()

    # Build message history for LLM
    system_prompt = _build_system_prompt(
        conversation.current_phase,
        conversation.collected_data or {},
    )
    llm_messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
    ]

    # Load conversation history (last 50 messages to stay within context)
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    history = result.scalars().all()
    for msg in history[-50:]:
        if msg.role == "tool":
            llm_messages.append(
                {
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": (msg.metadata_ or {}).get("tool_call_id", ""),
                }
            )
        elif msg.role == "assistant" and msg.metadata_ and msg.metadata_.get("tool_calls"):
            llm_messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or None,
                    "tool_calls": msg.metadata_["tool_calls"],
                }
            )
        else:
            llm_messages.append({"role": msg.role, "content": msg.content})

    # Tool-calling loop
    all_events: list[ChatEvent] = []
    max_iterations = 8

    for _ in range(max_iterations):
        response = call_llm(
            messages=llm_messages,
            tools=TOOLS,
            temperature=0.4,
            max_tokens=2048,
        )

        if response.tool_calls:
            # Save assistant message with tool calls
            tool_calls_raw = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in response.tool_calls
            ]
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=response.content or "",
                message_type="text",
                metadata_={"tool_calls": tool_calls_raw},
            )
            session.add(assistant_msg)
            await session.flush()

            llm_messages.append(
                {
                    "role": "assistant",
                    "content": response.content or None,
                    "tool_calls": tool_calls_raw,
                }
            )

            # Execute each tool call
            for tc in response.tool_calls:
                all_events.append(
                    ChatEvent(
                        event_type="tool_start",
                        data={"tool": tc.name},
                    )
                )

                try:
                    args = json.loads(tc.arguments)
                except json.JSONDecodeError:
                    args = {}

                tool_result, extra_events = await _execute_tool(
                    tc.name,
                    args,
                    conversation,
                    session,
                )
                all_events.extend(extra_events)

                tool_result_str = json.dumps(tool_result)
                tool_msg = Message(
                    conversation_id=conversation.id,
                    role="tool",
                    content=tool_result_str,
                    message_type="text",
                    metadata_={"tool_call_id": tc.id, "tool_name": tc.name},
                )
                session.add(tool_msg)
                await session.flush()

                llm_messages.append(
                    {
                        "role": "tool",
                        "content": tool_result_str,
                        "tool_call_id": tc.id,
                    }
                )

            # Continue loop — LLM needs to process tool results
            continue

        # No tool calls — this is the final text response
        all_events.append(
            ChatEvent(
                event_type="text",
                data={"content": response.content},
            )
        )

        # Save assistant response
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response.content,
            message_type="text",
        )
        session.add(assistant_msg)
        await session.flush()
        break

    all_events.append(ChatEvent(event_type="done", data={}))
    return all_events
