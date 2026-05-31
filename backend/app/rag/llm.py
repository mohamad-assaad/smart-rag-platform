import os
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


def generate_fallback_answer(question: str, context: Any) -> str:
    """
    Local fallback answer generator used when OpenAI is unavailable.

    It gives a short, clean product-style answer instead of returning a long
    raw context preview.
    """
    clean_context = _normalize_context(context)
    question_lower = question.lower()

    is_mohamad_question = any(
        name in question_lower
        for name in ["mohamad", "mhmad", "mohammed", "muhammad", "mohamad ali"]
    )

    if not clean_context:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "I could not find enough retrieved context to answer clearly. "
            "Recommendation: upload and index a more relevant document, then ask the question again."
        )

    if is_mohamad_question and "goal" in question_lower:
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