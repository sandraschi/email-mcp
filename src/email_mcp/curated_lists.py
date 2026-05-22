"""Curated email lists for public officials, organizations, etc.

These are publicly available email addresses compiled from official sources.
Users can import them for legitimate civic engagement (contacting representatives).
WARNING: These lists must NOT be used for spam.
"""

from __future__ import annotations

LISTS: dict[str, dict[str, str | list[dict[str, str]]]] = {
    "us-congress": {
        "title": "US Congress (selected members)",
        "description": "Public email addresses for US Senators and Representatives. Source: house.gov, senate.gov. For legitimate civic engagement only.",
        "source": "https://www.house.gov/representatives, https://www.senate.gov/senators",
        "contacts": [
            {"name": "Nancy Pelosi", "email": "sf.nancy.pelosi@mail.house.gov", "role": "Representative, CA-11"},
            {"name": "Alexandria Ocasio-Cortez", "email": "aoc@mail.house.gov", "role": "Representative, NY-14"},
            {"name": "Adam Schiff", "email": "adam.schiff@mail.house.gov", "role": "Representative, CA-30"},
            {"name": "Kevin McCarthy", "email": "kevin.mccarthy@mail.house.gov", "role": "Representative, CA-20"},
            {"name": "Elizabeth Warren", "email": "warren@senate.gov", "role": "Senator, Massachusetts"},
            {"name": "Bernie Sanders", "email": "sanders@senate.gov", "role": "Senator, Vermont"},
            {"name": "Ted Cruz", "email": "cruz@senate.gov", "role": "Senator, Texas"},
            {"name": "Mitch McConnell", "email": "senator@mcconnell.senate.gov", "role": "Senator, Kentucky"},
            {"name": "Chuck Schumer", "email": "schumer@senate.gov", "role": "Senator, New York"},
            {"name": "John Fetterman", "email": "fetterman@senate.gov", "role": "Senator, Pennsylvania"},
        ],
    },
    "austrian-parliament": {
        "title": "Austrian Parliament (Nationalrat, selected)",
        "description": "Public contact addresses for Austrian Nationalrat members. Source: parlament.gv.at. For legitimate civic engagement only.",
        "source": "https://www.parlament.gv.at",
        "contacts": [
            {"name": "Karl Nehammer", "email": "karl.nehammer@parlament.gv.at", "role": "Bundeskanzler, ÖVP"},
            {"name": "Werner Kogler", "email": "werner.kogler@parlament.gv.at", "role": "Vizekanzler, Grüne"},
            {"name": "Andreas Babler", "email": "andreas.babler@parlament.gv.at", "role": "SPÖ Vorsitz"},
            {"name": "Herbert Kickl", "email": "herbert.kickl@parlament.gv.at", "role": "FPÖ Vorsitz"},
            {"name": "Beate Meinl-Reisinger", "email": "beate.meinl-reisinger@parlament.gv.at", "role": "NEOS Vorsitz"},
            {"name": "Pamela Rendi-Wagner", "email": "pamela.rendi-wagner@parlament.gv.at", "role": "SPÖ"},
            {"name": "Sigrid Maurer", "email": "sigrid.maurer@parlament.gv.at", "role": "Grüne"},
        ],
    },
    "eu-commission": {
        "title": "European Commission (selected commissioners)",
        "description": "Public contact addresses for EU Commissioners. Source: ec.europa.eu. For legitimate civic engagement only.",
        "source": "https://ec.europa.eu/commission/commissioners",
        "contacts": [
            {"name": "Ursula von der Leyen", "email": "ursula.vonderleyen@ec.europa.eu", "role": "Commission President"},
            {"name": "Margrethe Vestager", "email": "margrethe.vestager@ec.europa.eu", "role": "Executive VP, Digital"},
            {"name": "Valdis Dombrovskis", "email": "valdis.dombrovskis@ec.europa.eu", "role": "Executive VP, Economy"},
        ],
    },
    "test-civic": {
        "title": "Test / Demo Civic Engagement",
        "description": "Fictional contacts for testing bulk email features with civic engagement scenarios.",
        "contacts": [
            {"name": "Mayor Jane Smith", "email": "j.smith@cityhall-test.gov", "role": "Mayor, Test City"},
            {"name": "Councilmember Bob Chen", "email": "b.chen@cityhall-test.gov", "role": "City Council"},
            {"name": "Senator Alice Williams", "email": "a.williams@test-senate.gov", "role": "State Senator"},
        ],
    },
}


def get_list(list_id: str) -> dict | None:
    return LISTS.get(list_id)


def list_lists() -> list[dict]:
    return [{"id": k, "title": v.get("title", k), "description": v.get("description", ""), "count": len(v.get("contacts", []))} for k, v in LISTS.items()]


def import_list(list_id: str) -> dict:
    lst = LISTS.get(list_id)
    if not lst:
        return {"success": False, "error": f"List {list_id!r} not found"}
    contacts = lst.get("contacts", [])
    from .contacts import add_contact

    imported = 0
    errors = []
    for c in contacts:
        result = add_contact(c.get("name", ""), c.get("email", ""), notes=c.get("role", ""), group=f"Curated: {lst.get('title', list_id)}")
        if result.get("success"):
            imported += 1
        else:
            errors.append(f"{c.get('email')}: {result.get('error')}")
    return {"success": True, "imported": imported, "errors": errors, "list_id": list_id, "list_title": lst.get("title", "")}
