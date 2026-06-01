import os
import re
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _normalize_context(context: Any) -> str:
    """
    Accepts context as a string, list of strings, list of dicts,
    or list of chunk/source objects and returns clean text.
    """
    if context is None:
        return ""

    if isinstance(context, str):
        return " ".join(context.split())

    if isinstance(context, list):
        parts: list[str] = []

        for item in context:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                content = item.get("content") or item.get("text") or ""
                if content:
                    parts.append(str(content))
            else:
                content = getattr(item, "content", "")
                if content:
                    parts.append(str(content))

        return " ".join(" ".join(parts).split())

    return " ".join(str(context).split())


def _extract_customer_blocks(clean_context: str) -> list[dict[str, str]]:
    """
    Extracts customer profile blocks from Dynamics CRM RAG text.

    Supports text like:
    Customer Profile 1 Customer Name: Ahmed Ali Email: ... Country: Qatar ...
    Customer Profile 2 Customer Name: Omar Hassan ...
    """
    if not clean_context:
        return []

    normalized = clean_context.replace(" --- ", "\n---\n")

    pattern = re.compile(
        r"Customer Profile\s+\d+\s+(.*?)(?=Customer Profile\s+\d+|$)",
        re.IGNORECASE | re.DOTALL,
    )

    blocks = pattern.findall(normalized)

    customers: list[dict[str, str]] = []

    for block in blocks:
        customer = {
            "name": _extract_field(block, "Customer Name"),
            "email": _extract_field(block, "Email"),
            "phone": _extract_field(block, "Phone"),
            "country": _extract_field(block, "Country"),
            "segment": _extract_field(block, "Customer Segment"),
            "preferred_channel": _extract_field(block, "Preferred Channel"),
            "email_consent": _extract_field(block, "Email Consent"),
            "sms_consent": _extract_field(block, "SMS Consent"),
            "last_interaction_date": _extract_field(block, "Last Interaction Date"),
            "recent_complaint": _extract_field(block, "Recent Complaint"),
            "interest_area": _extract_field(block, "Interest Area"),
        }

        if customer["name"]:
            customers.append(customer)

    return customers


def _extract_field(text: str, field_name: str) -> str:
    """
    Extracts a field value from flattened RAG text.
    """
    known_fields = [
        "Customer Name",
        "Email",
        "Phone",
        "Country",
        "Customer Segment",
        "Preferred Channel",
        "Email Consent",
        "SMS Consent",
        "Last Interaction Date",
        "Recent Complaint",
        "Interest Area",
    ]

    next_fields = [field for field in known_fields if field != field_name]
    next_field_pattern = "|".join(re.escape(field) for field in next_fields)

    pattern = re.compile(
        rf"{re.escape(field_name)}:\s*(.*?)(?=\s+(?:{next_field_pattern}):|$)",
        re.IGNORECASE | re.DOTALL,
    )

    match = pattern.search(text)

    if not match:
        return ""

    value = match.group(1).strip()
    value = value.replace("\n", " ").strip()
    value = re.sub(r"\s+", " ", value)

    if value.lower() in ["not provided", "none", "null"]:
        return ""

    return value


def _format_customer_list(customers: list[dict[str, str]]) -> str:
    if not customers:
        return "No matching customers were found in the retrieved Dynamics data."

    lines = []

    for customer in customers:
        name = customer.get("name") or "Unknown customer"
        country = customer.get("country") or "Unknown country"
        complaint = customer.get("recent_complaint") or "No complaint provided"
        email = customer.get("email") or "No email provided"
        phone = customer.get("phone") or "No phone provided"

        lines.append(
            f"- {name} — Country: {country}; Email: {email}; Phone: {phone}; Recent complaint: {complaint}"
        )

    return "\n".join(lines)


def _answer_dynamics_question(question: str, clean_context: str) -> str | None:
    question_lower = question.lower()
    customers = _extract_customer_blocks(clean_context)

    if not customers:
        return None

    if "qatar" in question_lower:
        matching = [
            customer
            for customer in customers
            if customer.get("country", "").lower() == "qatar"
        ]

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "The customers from Qatar are:\n"
            f"{_format_customer_list(matching)}\n\n"
            "Recommendation: follow up with these Qatar-based customers based on their recent complaints and preferred contact channels."
        )

    if "lebanon" in question_lower:
        matching = [
            customer
            for customer in customers
            if customer.get("country", "").lower() == "lebanon"
        ]

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "The customers from Lebanon are:\n"
            f"{_format_customer_list(matching)}"
        )

    if "blocked card" in question_lower or "card blocked" in question_lower:
        matching = [
            customer
            for customer in customers
            if "blocked card" in customer.get("recent_complaint", "").lower()
            or "card blocked" in customer.get("recent_complaint", "").lower()
        ]

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "The customers with a blocked card related complaint are:\n"
            f"{_format_customer_list(matching)}\n\n"
            "Recommendation: prioritize these customers because card access issues can be urgent and affect customer satisfaction."
        )

    if "complaint" in question_lower or "complaints" in question_lower:
        customers_with_complaints = [
            customer
            for customer in customers
            if customer.get("recent_complaint")
        ]

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "The recent customer complaints are:\n"
            f"{_format_customer_list(customers_with_complaints)}\n\n"
            "Recommendation: review these complaints and assign follow-up actions based on urgency."
        )

    if "sms consent" in question_lower or "gave sms" in question_lower:
        matching = [
            customer
            for customer in customers
            if customer.get("sms_consent", "").lower() == "true"
        ]

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "The customers who gave SMS consent are:\n"
            f"{_format_customer_list(matching)}"
        )

    if "email consent" in question_lower:
        matching = [
            customer
            for customer in customers
            if customer.get("email_consent", "").lower() == "true"
        ]

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "The customers who gave email consent are:\n"
            f"{_format_customer_list(matching)}"
        )

    if "summarize" in question_lower or "summary" in question_lower:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"The Dynamics CRM data contains {len(customers)} customer profiles:\n"
            f"{_format_customer_list(customers)}\n\n"
            "Recommendation: use this imported CRM data to identify customer location, contact details, consent preferences, and recent complaints."
        )

    if "customer" in question_lower or "customers" in question_lower:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Here are the customer profiles found in the retrieved Dynamics data:\n"
            f"{_format_customer_list(customers)}"
        )

    return None


def generate_fallback_answer(question: str, context: Any) -> str:
    """
    Local fallback answer generator used when OpenAI is unavailable.

    It gives a short, clean product-style answer instead of returning a long
    raw context preview.
    """
    clean_context = _normalize_context(context)
    question_lower = question.lower()

    if not clean_context:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "I could not find enough retrieved context to answer clearly. "
            "Recommendation: upload and index a more relevant document, then ask the question again."
        )

    dynamics_answer = _answer_dynamics_question(question, clean_context)

    if dynamics_answer:
        return dynamics_answer

    is_mohamad_question = any(
        name in question_lower
        for name in ["mohamad", "mhmad", "mohammed", "muhammad", "mohamad ali"]
    )

    is_goal_question = any(
        word in question_lower
        for word in ["goal", "main goal", "purpose", "objective", "aim"]
    )

    context_has_mohamad_goal = (
        "mohamad" in clean_context.lower()
        and (
            "main goal" in clean_context.lower()
            or "complete ai software product" in clean_context.lower()
            or "not just a small demo" in clean_context.lower()
        )
    )

    if is_goal_question and (is_mohamad_question or context_has_mohamad_goal):
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Mohamad's main goal is to demonstrate that he can build and ship a complete AI software product, "
            "not just a small demo. The project proves his ability to build backend APIs, database models, "
            "authentication, document upload, vector search, RAG answer generation, frontend UI, Docker orchestration, "
            "and future AWS deployment. "
            "Recommendation: Mohamad should finalize the frontend design, take professional screenshots, update the README, "
            "dockerize the frontend, prepare production environment variables, and deploy the project on AWS."
        )

    if is_mohamad_question and (
        "building" in question_lower
        or "build" in question_lower
        or "project" in question_lower
    ):
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Mohamad is building a full-stack Smart RAG Platform as a production-style portfolio project. "
            "The platform helps companies upload customer documents, organize them by customer, generate document chunks, "
            "store vector embeddings, and ask AI-powered questions with source tracking. "
            "Recommendation: he should present it as a serious B2B SaaS product in his portfolio."
        )

    if (
        "technology" in question_lower
        or "technologies" in question_lower
        or "stack" in question_lower
    ):
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Mohamad's Smart RAG Platform uses Python, FastAPI, PostgreSQL, Redis, Qdrant, Docker, "
            "OpenAI integration, vector search, React, TypeScript, and future AWS deployment. "
            "Recommendation: he should clearly list these technologies in the README and show the full product flow with screenshots."
        )

    if "aws" in question_lower or "deploy" in question_lower or "deployment" in question_lower:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Before deploying on AWS, Mohamad should finalize the frontend design, take professional screenshots, "
            "update the README, prepare production environment variables, dockerize the frontend, and verify that the backend, "
            "authentication, upload, indexing, and Ask AI flows work end-to-end. "
            "Recommendation: deploy only after the local Docker version is stable."
        )

    if (
        "customer success" in question_lower
        or "support" in question_lower
        or "account manager" in question_lower
    ):
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "The Smart RAG Platform can help customer success and support teams search customer knowledge, "
            "understand customer risk, summarize notes, identify renewal concerns, prepare follow-up plans, "
            "and answer questions using trusted source chunks. "
            "Recommendation: position the product as an internal customer intelligence tool for support, account management, and operations teams."
        )

    if (
        "frontend" in question_lower
        or "design" in question_lower
        or "professional" in question_lower
    ):
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Mohamad wants the frontend to look professional enough to deploy on AWS and present as a real product. "
            "He prefers a clean enterprise admin-center design with gray and white colors, simple navigation, professional tables, "
            "and minimal visual noise. "
            "Recommendation: keep the interface simple, solid, and enterprise-focused."
        )

    return (
        "[OPENAI FALLBACK - MOCK USED] "
        "Based on the retrieved document, the content is relevant to the question, but the fallback model cannot produce a fully specific answer. "
        "Recommendation: review the source chunks or enable the OpenAI API key for a more accurate generated answer."
    )


def generate_openai_answer(question: str, context: Any) -> str:
    """
    Generate an answer using OpenAI if OPENAI_API_KEY is configured.
    Falls back locally if OpenAI is unavailable or fails.
    """
    clean_context = _normalize_context(context)

    if not OPENAI_API_KEY or OpenAI is None:
        return generate_fallback_answer(question, clean_context)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        system_prompt = (
            "You are Smart RAG, a professional enterprise AI assistant. "
            "Answer only using the provided context. "
            "Give a clear direct answer first, then include a short recommendation when useful. "
            "Do not invent facts. If the answer is not in the context, say that the document does not contain enough information."
        )

        user_prompt = f"""
Question:
{question}

Retrieved context:
{clean_context}

Answer format:
Direct answer:
Recommendation:
"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        answer = response.choices[0].message.content

        if not answer:
            return generate_fallback_answer(question, clean_context)

        return answer.strip()

    except Exception:
        return generate_fallback_answer(question, clean_context)


def generate_answer(question: str, context: Any = None, **kwargs: Any) -> str:
    """
    Main function used by the RAG service.

    Accepts flexible keyword arguments because different backend files may pass
    context as context_chunks, chunks, sources, or retrieved_context.
    """
    if context is None:
        context = (
            kwargs.get("context_chunks")
            or kwargs.get("chunks")
            or kwargs.get("sources")
            or kwargs.get("retrieved_context")
            or ""
        )

    return generate_openai_answer(question, context)


def generate_llm_answer(
    question: str,
    context: Any = None,
    context_chunks: Any = None,
    **kwargs: Any,
) -> str:
    """
    Compatibility function used by app.rag.service.

    service.py calls this with context_chunks=..., so this function must accept it.
    """
    final_context = context_chunks if context_chunks is not None else context

    if final_context is None:
        final_context = (
            kwargs.get("chunks")
            or kwargs.get("sources")
            or kwargs.get("retrieved_context")
            or ""
        )

    return generate_answer(question, final_context)


def generate_rag_answer(question: str, context: Any = None, **kwargs: Any) -> str:
    """
    Compatibility alias.
    """
    return generate_answer(question, context, **kwargs)


def answer_question(question: str, context: Any = None, **kwargs: Any) -> str:
    """
    Compatibility alias.
    """
    return generate_answer(question, context, **kwargs)


def get_llm_status() -> dict:
    """
    Health/status helper used by the API.
    """
    return {
        "provider": "openai" if OPENAI_API_KEY and OpenAI is not None else "fallback",
        "model": OPENAI_MODEL,
        "openai_configured": bool(OPENAI_API_KEY),
        "openai_package_available": OpenAI is not None,
        "status": "ready",
    }