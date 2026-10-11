"""The route's producers: policy, three state producers, the prior notes as memory with precomputed variants, the
guidelines, the capability policy, and the room's transcript. Each proposes; the route decides."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

import common
from common import Request, batch, item

Facts = dict[str, str]
GOVERNING = dict(authority="governing", trust="verified", conflict_policy="governs", lineage="verbatim", injection_risk="none")


def clinical_policy(route: str) -> dict[str, Any]:
    meta, body = common.front_matter(common.policy(route, "instructions.md"))
    cmeta, contract = common.front_matter(common.policy(route, "contract.md"))
    return batch("clinical-policy", "policy", [
        item(id=f"policy:{route}", slot="governance.instructions", source=f"app:policy/{route}/instructions.md", source_version=meta["version"], freshness=meta["updated"], body=body, **GOVERNING),
        item(id=f"contract:{route}", slot="governance.output_contract", source=f"app:policy/{route}/contract.md", source_version=cmeta["version"], freshness=cmeta["updated"], body=contract, **GOVERNING),
    ])


def ehr_chart(request: Request) -> dict[str, Any]:
    """The chart as the system of record: problems, active medicines, allergies, recent labs. Protected state (R-8).
    No vitals here: the current reading is telemetry's, and an earlier reading is a prior note's claim."""
    p = common.patients()[request.patient]
    e = common.encounters()[request.encounter]
    meds = "; ".join(f"{m['name']} {m['dose']} {m['frequency']} ({m['status']}, last filled {m['last_filled']})" for m in p["medications"]) or "none"
    labs = "; ".join(f"{l['name']} {l['value']} on {l['at']}" for l in p["labs"]) or "none on file"
    body = (f"Patient {request.patient}: {p['name']}, {p['age']}{p['sex']}. Encounter {request.encounter}, {e['type']}, room {e['room']}. "
            f"Problems: {', '.join(p['problems']) or 'none'}. Active medications: {meds}. Allergies: {', '.join(p['allergies']) or 'none known'}. Recent labs: {labs}.")
    return batch("ehr-chart", "state", [item(
        id=f"chart:{request.patient}", slot="state.task", source=f"ehr:patients/{request.patient}", source_version=str(p["version"]), authority="state",
        trust="verified", freshness=request.asked_at, scope={"tenant": common.TENANT, "task": request.patient}, conflict_policy="governs",
        lineage="extracted", injection_risk="none", body=body)])


def telemetry(request: Request) -> tuple[dict[str, Any], Facts]:
    """The room monitor's current reading, read at freeze time. It asserts vitals.bp, and the route puts it first."""
    r = common.telemetry()[request.encounter]
    vid = f"vitals:{request.encounter}"
    return batch("telemetry", "state", [item(
        id=vid, slot="state.task", source=f"telemetry:{r['device']}/{request.encounter}", source_version=r["at"], authority="state", trust="verified",
        freshness=r["at"], scope={"tenant": common.TENANT, "task": request.patient}, conflict_policy="governs", lineage="extracted", injection_risk="none",
        body=f"Vitals from {r['device']} at {r['at']}: BP {r['bp']}, HR {r['hr']}, SpO2 {r['spo2']}%, temperature {r['temp_c']} C.")]), {vid: "vitals.bp"}


def clinician_state(request: Request) -> dict[str, Any]:
    c = common.clinicians()[request.clinician]
    return batch("clinician-state", "state", [item(
        id=f"clinician:{request.clinician}", slot="state.user", source=f"staff-directory:{request.clinician}", source_version=str(c["version"]), authority="state",
        trust="verified", freshness=request.asked_at, scope={"tenant": common.TENANT, "user": request.clinician}, conflict_policy="governs", lineage="extracted",
        injection_risk="none", body=f"{c['name']} ({request.clinician}), {c['role']}, {'a prescriber' if c['prescriber'] else 'not a prescriber'}.")])


def ehr_notes(request: Request) -> tuple[dict[str, Any], Facts]:
    """Prior encounter notes about this patient: memory, with the hand-written summary as a variant, expiring a year after
    they were written, scoped to the patient. A note that recorded a vital asserts vitals.bp (R-9, R-18)."""
    ignores_patient = "notes-ignore-patient" in request.faults
    asked = common.instant(request.asked_at)
    items, excluded, facts = [], [], {}
    for note in common.ehr_notes():
        if note["patient"] != request.patient and not ignores_patient:
            continue
        expires = (common.instant(note["at"]) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if common.instant(expires) <= asked:
            excluded.append({"item_id": note["id"], "reason": "expired", "stage": "producer"})
            continue
        items.append(item(
            id=note["id"], slot="interaction.memory", source=note["id"], source_version="1", authority="generated", trust="unverified", freshness=note["at"],
            expires=expires, scope={"tenant": common.TENANT, "task": note["patient"]}, lineage="verbatim", injection_risk="untrusted_content",
            body=f"Note by {note['author']} on {note['at'][:10]} (encounter {note['encounter']}): {note['text']}",
            variants=[{"id": f"{note['id']}~summary", "body": note["summary"], "method": "clinician-written summary", "lineage": "summarised"}]))
        if "fact" in note:
            facts[note["id"]] = note["fact"]
    return batch("ehr-notes", "memory", items, excluded), facts


def guidelines(request: Request, top_k: int) -> dict[str, Any]:
    return batch("guidelines", "retrieval", [item(
        id=chunk.id, slot="evidence.knowledge", source=f"guide:{chunk.article}", source_version=chunk.version, authority="reference_only", trust="verified",
        freshness=chunk.updated, relevance=score, lineage="verbatim", injection_risk="untrusted_content", body=chunk.text,
    ) for chunk, score in common.bm25(request.question)[:top_k]])


def _schema_sha256(schema: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def capability_policy(request: Request) -> tuple[dict[str, Any], dict[str, Any]]:
    """The only producer of governance.capabilities (R-15): the EHR's proposals granted by the clinician's role, the
    rest reported capability_not_allowed. The grant names the offered ids, so nothing else in the slot is admitted."""
    rules, proposed = common.capabilities_policy(), common.tools()
    role = common.clinicians()[request.clinician]["role"]
    items, excluded = [], []
    for spec in sorted(proposed["tools"], key=lambda s: s["name"]):
        cap_id = f"cap:{spec['name']}"
        rule = rules["grants"].get(spec["name"])
        if rule is None or role not in rule["roles"]:
            excluded.append({"item_id": cap_id, "reason": "capability_not_allowed", "stage": "producer"})
            continue
        items.append(item(id=cap_id, slot="governance.capabilities", source=f"capability-policy:{proposed['server']}/{spec['name']}",
                          source_version=f"{rules['allow_list_version']}+{proposed['version']}", freshness=request.asked_at,
                          body=json.dumps({"name": spec["name"], "description": rule["description"], "input_schema": spec["input_schema"]}, sort_keys=True), **GOVERNING))
    grant = {"policy_producer": rules["policy_producer"], "allow_list_version": rules["allow_list_version"], "allowed_ids": sorted(i["id"] for i in items)}
    return batch(rules["policy_producer"], "capability_policy", items, excluded), grant


def ambient_scribe(request: Request) -> dict[str, Any]:
    """The room's transcript as history and the clinician's request as the query. Every transcript turn is speech-to-text
    of whoever was speaking: untrusted, marked, never an instruction (R-7, R-10). Only the request outside the
    transcript is the user's."""
    scope, source, items = {"session": request.session}, f"stt:{request.session}", []
    for n, turn in enumerate(request.turns, start=1):
        items.append(item(id=f"turn:{request.session}:{n:04d}", slot="interaction.history", source=source, source_version="1", authority="untrusted",
                          lineage="verbatim", trust="unverified", freshness=turn.at, scope=scope, injection_risk="untrusted_content",
                          body=f"[{turn.speaker}] {turn.text}"))
    items.append(item(id=f"turn:{request.session}:{len(request.turns) + 1:04d}", slot="interaction.query", source=f"console:{request.session}", source_version="1",
                      authority="user", lineage="verbatim", trust="unverified", freshness=request.asked_at, scope=scope, injection_risk="untrusted_content",
                      body=request.question))
    return batch("ambient-scribe", "interaction", items)
