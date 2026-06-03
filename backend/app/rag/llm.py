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


def _extract_requested_country(
    question: str,
    customers: list[dict[str, str]],
) -> str | None:
    """
    Detects a country mentioned in the question by comparing it with
    countries available in the retrieved Dynamics customer profiles.

    Example:
    Question: Which customers are from Syria?
    Available countries: Syria, Qatar, Lebanon
    Returns: Syria
    """
    question_lower = question.lower()

    countries = sorted(
        {
            customer.get("country", "").strip()
            for customer in customers
            if customer.get("country", "").strip()
        },
        key=len,
        reverse=True,
    )

    for country in countries:
        if country.lower() in question_lower:
            return country

    patterns = [
        r"from\s+([a-zA-Z ]+)",
        r"in\s+([a-zA-Z ]+)",
        r"country\s+([a-zA-Z ]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, question_lower)

        if match:
            possible_country = match.group(1).strip()
            possible_country = possible_country.replace("?", "").strip()
            possible_country = possible_country.replace(".", "").strip()

            stop_words = [
                "customers",
                "customer",
                "are",
                "is",
                "who",
                "which",
                "the",
            ]

            for word in stop_words:
                possible_country = possible_country.replace(f" {word} ", " ")

            possible_country = possible_country.strip()

            for country in countries:
                if possible_country == country.lower():
                    return country

    return None


def _extract_requested_customer_name(
    question: str,
    customers: list[dict[str, str]],
) -> str | None:
    """
    Detects if the question mentions a specific customer name.

    Example:
    Question: Khaled gave SMS consent?
    Customer names: Ahmed Ali, Omar Hassan, Khaled
    Returns: Khaled
    """
    question_lower = question.lower()

    customer_names = sorted(
        {
            customer.get("name", "").strip()
            for customer in customers
            if customer.get("name", "").strip()
        },
        key=len,
        reverse=True,
    )

    for name in customer_names:
        if name.lower() in question_lower:
            return name

    # Support first-name matching like:
    # "Khaled gave SMS consent?"
    # "Did Ahmed give email consent?"
    for name in customer_names:
        first_name = name.split()[0].lower()

        if first_name and re.search(rf"\b{re.escape(first_name)}\b", question_lower):
            return name

    return None


def _find_customer_by_name(
    requested_customer_name: str,
    customers: list[dict[str, str]],
) -> dict[str, str] | None:
    """
    Finds a customer by full name or first name.
    """
    requested_lower = requested_customer_name.lower()
    requested_first_name = requested_lower.split()[0]

    for customer in customers:
        customer_name = customer.get("name", "")
        customer_lower = customer_name.lower()
        customer_first_name = customer_lower.split()[0] if customer_lower else ""

        if customer_lower == requested_lower:
            return customer

        if customer_first_name == requested_first_name:
            return customer

    return None


def _yes_no(value: str) -> str:
    """
    Converts stored text value into yes/no/unknown.
    """
    normalized = value.strip().lower()

    if normalized == "true":
        return "yes"

    if normalized == "false":
        return "no"

    return "unknown"


def _answer_specific_customer_question(
    question: str,
    customer: dict[str, str],
) -> str | None:
    """
    Handles questions about one specific customer.

    Example:
    Khaled gave SMS consent?
    Did Ahmed give email consent?
    What is Sara's complaint?
    Where is Omar from?
    """
    question_lower = question.lower()
    customer_name = customer.get("name") or "This customer"

    if "sms consent" in question_lower or "gave sms" in question_lower:
        sms_value = _yes_no(customer.get("sms_consent", ""))

        if sms_value == "yes":
            return (
                "[OPENAI FALLBACK - MOCK USED] "
                f"Yes, {customer_name} gave SMS consent."
            )

        if sms_value == "no":
            return (
                "[OPENAI FALLBACK - MOCK USED] "
                f"No, {customer_name} did not give SMS consent."
            )

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"The retrieved Dynamics data does not clearly show whether {customer_name} gave SMS consent."
        )

    if "email consent" in question_lower or "gave email" in question_lower:
        email_value = _yes_no(customer.get("email_consent", ""))

        if email_value == "yes":
            return (
                "[OPENAI FALLBACK - MOCK USED] "
                f"Yes, {customer_name} gave email consent."
            )

        if email_value == "no":
            return (
                "[OPENAI FALLBACK - MOCK USED] "
                f"No, {customer_name} did not give email consent."
            )

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"The retrieved Dynamics data does not clearly show whether {customer_name} gave email consent."
        )

    if "complaint" in question_lower or "issue" in question_lower:
        complaint = customer.get("recent_complaint") or "No complaint provided"

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"{customer_name}'s recent complaint is: {complaint}."
        )

    if "country" in question_lower or "from" in question_lower or "where" in question_lower:
        country = customer.get("country") or "No country provided"

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"{customer_name} is from {country}."
        )

    if "email" in question_lower:
        email = customer.get("email") or "No email provided"

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"{customer_name}'s email is: {email}."
        )

    if "phone" in question_lower:
        phone = customer.get("phone") or "No phone provided"

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"{customer_name}'s phone number is: {phone}."
        )

    if "last interaction" in question_lower or "recent interaction" in question_lower:
        last_interaction = customer.get("last_interaction_date") or "Not provided"

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"{customer_name}'s last interaction date is: {last_interaction}."
        )

    return (
        "[OPENAI FALLBACK - MOCK USED] "
        f"Here is the retrieved Dynamics profile for {customer_name}:\n"
        f"{_format_customer_list([customer])}"
    )


def _answer_dynamics_question(question: str, clean_context: str) -> str | None:
    question_lower = question.lower()
    customers = _extract_customer_blocks(clean_context)

    if not customers:
        return None

    # 1. Specific customer questions must be handled before generic questions.
    # Example:
    # "Khaled gave SMS consent?" should answer yes/no for Khaled,
    # not list all customers with SMS consent.
    requested_customer_name = _extract_requested_customer_name(question, customers)

    if requested_customer_name:
        matching_customer = _find_customer_by_name(requested_customer_name, customers)

        if not matching_customer:
            return (
                "[OPENAI FALLBACK - MOCK USED] "
                f"I could not find a customer named {requested_customer_name} in the retrieved Dynamics data."
            )

        specific_answer = _answer_specific_customer_question(question, matching_customer)

        if specific_answer:
            return specific_answer

    # 2. Country questions.
    # Example:
    # "Which customers are from Syria?"
    # "Which customers are from Qatar?"
    requested_country = _extract_requested_country(question, customers)

    if requested_country:
        matching = [
            customer
            for customer in customers
            if customer.get("country", "").lower() == requested_country.lower()
        ]

        if matching:
            return (
                "[OPENAI FALLBACK - MOCK USED] "
                f"The customers from {requested_country} are:\n"
                f"{_format_customer_list(matching)}\n\n"
                "Recommendation: review these customers based on their recent complaints and preferred contact channels."
            )

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"No customers from {requested_country} were found in the retrieved Dynamics data."
        )

    # 3. General complaint questions.
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

    # 4. General consent questions.
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

    if "email consent" in question_lower or "gave email" in question_lower:
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

    if "preferred channel" in question_lower or "preferred contact" in question_lower:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Here are the preferred contact channel values found in the retrieved Dynamics data:\n"
            f"{_format_customer_list(customers)}\n\n"
            "Recommendation: map Dynamics option-set numbers to readable labels for a cleaner business answer."
        )

    if "recent interaction" in question_lower or "last interaction" in question_lower:
        sorted_customers = sorted(
            customers,
            key=lambda customer: customer.get("last_interaction_date", ""),
            reverse=True,
        )

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Here are the customers ordered by last interaction date:\n"
            + "\n".join(
                [
                    f"- {customer.get('name') or 'Unknown customer'} — Last interaction: {customer.get('last_interaction_date') or 'Not provided'}; Country: {customer.get('country') or 'Unknown country'}"
                    for customer in sorted_customers
                ]
            )
        )

    if "summarize" in question_lower or "summary" in question_lower:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            f"The Dynamics CRM data contains {len(customers)} customer profiles:\n"
            f"{_format_customer_list(customers)}\n\n"
            "Recommendation: use this imported CRM data to identify customer location, contact details, consent preferences, and recent complaints."
        )

    if "follow-up" in question_lower or "follow up" in question_lower or "recommend" in question_lower:
        customers_with_complaints = [
            customer
            for customer in customers
            if customer.get("recent_complaint")
        ]

        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Recommended follow-up actions:\n"
            + "\n".join(
                [
                    f"- {customer.get('name') or 'Unknown customer'}: Follow up about '{customer.get('recent_complaint')}'. Use available contact details and respect consent preferences."
                    for customer in customers_with_complaints
                ]
            )
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
            "OpenAI integration, vector search, React, TypeScript, Dynamics 365 CRM integration, and future cloud deployment. "
            "Recommendation: he should clearly list these technologies in the README and show the full product flow with screenshots."
        )

    if "aws" in question_lower or "deploy" in question_lower or "deployment" in question_lower:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "Before deploying on AWS, Mohamad should finalize the frontend design, take professional screenshots, "
            "update the README, prepare production environment variables, dockerize the frontend, and verify that the backend, "
            "authentication, upload, indexing, Dynamics import, and Ask AI flows work end-to-end. "
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