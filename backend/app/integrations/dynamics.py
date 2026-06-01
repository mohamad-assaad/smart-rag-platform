import os
from typing import Any

import httpx


DYNAMICS_TENANT_ID = os.getenv("DYNAMICS_TENANT_ID", "")
DYNAMICS_CLIENT_ID = os.getenv("DYNAMICS_CLIENT_ID", "")
DYNAMICS_CLIENT_SECRET = os.getenv("DYNAMICS_CLIENT_SECRET", "")
DYNAMICS_RESOURCE_URL = os.getenv(
    "DYNAMICS_RESOURCE_URL",
    "https://org62f5e36c.crm4.dynamics.com",
).rstrip("/")
DYNAMICS_API_VERSION = os.getenv("DYNAMICS_API_VERSION", "v9.2")
DYNAMICS_CUSTOMER_TABLE = os.getenv(
    "DYNAMICS_CUSTOMER_TABLE",
    "new_customerprofile",
)


CUSTOMER_PROFILE_FIELDS = [
    "new_customername",
    "new_email",
    "new_phone",
    "new_country",
    "new_customersegment",
    "new_preferredchannel",
    "new_emailconsent",
    "new_smsconsent",
    "new_lastinteractiondate",
    "new_recentcomplaint",
    "new_interestarea",
]


class DynamicsConfigError(Exception):
    pass


class DynamicsApiError(Exception):
    pass


def _require_config() -> None:
    missing = []

    if not DYNAMICS_TENANT_ID:
        missing.append("DYNAMICS_TENANT_ID")

    if not DYNAMICS_CLIENT_ID:
        missing.append("DYNAMICS_CLIENT_ID")

    if not DYNAMICS_CLIENT_SECRET:
        missing.append("DYNAMICS_CLIENT_SECRET")

    if not DYNAMICS_RESOURCE_URL:
        missing.append("DYNAMICS_RESOURCE_URL")

    if missing:
        raise DynamicsConfigError(
            "Missing Dynamics environment variables: " + ", ".join(missing)
        )


async def get_dynamics_access_token() -> str:
    """
    Gets an OAuth access token for Microsoft Dataverse / Dynamics CRM
    using client credentials.
    """
    _require_config()

    token_url = (
        f"https://login.microsoftonline.com/"
        f"{DYNAMICS_TENANT_ID}/oauth2/v2.0/token"
    )

    payload = {
        "client_id": DYNAMICS_CLIENT_ID,
        "client_secret": DYNAMICS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": f"{DYNAMICS_RESOURCE_URL}/.default",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(token_url, data=payload)

    if response.status_code >= 400:
        raise DynamicsApiError(
            f"Could not get Dynamics access token. "
            f"Status: {response.status_code}. Body: {response.text}"
        )

    data = response.json()
    access_token = data.get("access_token")

    if not access_token:
        raise DynamicsApiError("Dynamics token response did not include access_token.")

    return access_token


async def get_entity_set_name(access_token: str, logical_name: str) -> str:
    """
    Dataverse uses logical table names and entity set names.
    Example:
    logical name: new_customerprofile
    entity set name: usually new_customerprofiles

    This function asks Dataverse metadata for the correct EntitySetName,
    so we do not guess.
    """
    metadata_url = (
        f"{DYNAMICS_RESOURCE_URL}/api/data/{DYNAMICS_API_VERSION}/"
        f"EntityDefinitions(LogicalName='{logical_name}')?$select=LogicalName,EntitySetName"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(metadata_url, headers=headers)

    if response.status_code >= 400:
        raise DynamicsApiError(
            f"Could not read Dataverse metadata for {logical_name}. "
            f"Status: {response.status_code}. Body: {response.text}"
        )

    data = response.json()
    entity_set_name = data.get("EntitySetName")

    if not entity_set_name:
        raise DynamicsApiError(
            f"Dataverse metadata did not return EntitySetName for {logical_name}."
        )

    return entity_set_name


def normalize_dynamics_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Returns only the fields we care about, with safer key names for the frontend.
    """
    return {
        "customer_name": record.get("new_customername"),
        "email": record.get("new_email"),
        "phone": record.get("new_phone"),
        "country": record.get("new_country"),
        "customer_segment": record.get("new_customersegment"),
        "preferred_channel": record.get("new_preferredchannel"),
        "email_consent": record.get("new_emailconsent"),
        "sms_consent": record.get("new_smsconsent"),
        "last_interaction_date": record.get("new_lastinteractiondate"),
        "recent_complaint": record.get("new_recentcomplaint"),
        "interest_area": record.get("new_interestarea"),
        "raw": record,
    }


def dynamics_records_to_text(records: list[dict[str, Any]]) -> str:
    """
    Converts CRM records into clean text that can later be sent into the RAG pipeline.
    """
    if not records:
        return "No Dynamics customer profile records were found."

    sections: list[str] = []

    for index, record in enumerate(records, start=1):
        name = record.get("customer_name") or "Unknown customer"

        section = [
            f"Customer Profile {index}",
            f"Customer Name: {name}",
            f"Email: {record.get('email') or 'Not provided'}",
            f"Phone: {record.get('phone') or 'Not provided'}",
            f"Country: {record.get('country') or 'Not provided'}",
            f"Customer Segment: {record.get('customer_segment') or 'Not provided'}",
            f"Preferred Channel: {record.get('preferred_channel') or 'Not provided'}",
            f"Email Consent: {record.get('email_consent') or 'Not provided'}",
            f"SMS Consent: {record.get('sms_consent') or 'Not provided'}",
            f"Last Interaction Date: {record.get('last_interaction_date') or 'Not provided'}",
            f"Recent Complaint: {record.get('recent_complaint') or 'Not provided'}",
            f"Interest Area: {record.get('interest_area') or 'Not provided'}",
        ]

        sections.append("\n".join(section))

    return "\n\n---\n\n".join(sections)


async def fetch_customer_profiles(limit: int = 25) -> dict[str, Any]:
    """
    Fetches Customer Profile records from Dynamics CRM / Dataverse.
    """
    access_token = await get_dynamics_access_token()
    entity_set_name = await get_entity_set_name(
        access_token=access_token,
        logical_name=DYNAMICS_CUSTOMER_TABLE,
    )

    selected_fields = ",".join(CUSTOMER_PROFILE_FIELDS)

    url = (
        f"{DYNAMICS_RESOURCE_URL}/api/data/{DYNAMICS_API_VERSION}/"
        f"{entity_set_name}"
        f"?$select={selected_fields}"
        f"&$top={limit}"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers)

    if response.status_code >= 400:
        raise DynamicsApiError(
            f"Could not fetch Dynamics customer profiles. "
            f"Status: {response.status_code}. Body: {response.text}"
        )

    data = response.json()
    raw_records = data.get("value", [])

    records = [normalize_dynamics_record(record) for record in raw_records]
    rag_text = dynamics_records_to_text(records)

    return {
        "environment": DYNAMICS_RESOURCE_URL,
        "table_logical_name": DYNAMICS_CUSTOMER_TABLE,
        "entity_set_name": entity_set_name,
        "record_count": len(records),
        "records": records,
        "rag_text": rag_text,
    }


def get_dynamics_status() -> dict[str, Any]:
    return {
        "configured": all(
            [
                DYNAMICS_TENANT_ID,
                DYNAMICS_CLIENT_ID,
                DYNAMICS_CLIENT_SECRET,
                DYNAMICS_RESOURCE_URL,
                DYNAMICS_CUSTOMER_TABLE,
            ]
        ),
        "tenant_id_present": bool(DYNAMICS_TENANT_ID),
        "client_id_present": bool(DYNAMICS_CLIENT_ID),
        "client_secret_present": bool(DYNAMICS_CLIENT_SECRET),
        "resource_url": DYNAMICS_RESOURCE_URL,
        "api_version": DYNAMICS_API_VERSION,
        "customer_table": DYNAMICS_CUSTOMER_TABLE,
    }