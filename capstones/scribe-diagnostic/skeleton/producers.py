"""Your producers. The route policies list them with their kinds and slots:

    clinical_policy(route) -> batch                 policy: governance.instructions and governance.output_contract (parser route)
    ehr_chart(request) -> batch                     state: state.task, the chart (problems, active medicines, allergies, labs); protected; no vitals
    telemetry(request) -> (batch, facts)            state: state.task, the room monitor's reading; asserts vitals.bp
    clinician_state(request) -> batch               state: state.user, who is asking and whether they prescribe; protected by the route
    ehr_notes(request) -> (batch, facts)            memory: interaction.memory, prior notes with the summary as a variant, expiring a year
                                                    after they were written, scoped to the patient (scope.task is the patient id); a note with a "fact" asserts it;
                                                    honour the notes-ignore-patient fault
    guidelines(request, top_k) -> batch             retrieval: evidence.knowledge, one scored item per paragraph
    capability_policy(request) -> (batch, grant)    capability_policy: the EHR's proposed tools granted by role, the rest reported
                                                    capability_not_allowed; the grant names the allowed ids
    ambient_scribe(request) -> batch                interaction: every transcript turn as untrusted history, the clinician's request as the query

common.py has the data loaders, the corpus and item()/batch(). W2, W5 and W9 module A are the references.
"""

from __future__ import annotations

from typing import Any

from common import Request

Facts = dict[str, str]


def clinical_policy(route: str) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: clinical_policy")


def ehr_chart(request: Request) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: ehr_chart")


def telemetry(request: Request) -> tuple[dict[str, Any], Facts]:
    raise NotImplementedError("skeleton/producers.py: telemetry")


def clinician_state(request: Request) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: clinician_state")


def ehr_notes(request: Request) -> tuple[dict[str, Any], Facts]:
    raise NotImplementedError("skeleton/producers.py: ehr_notes")


def guidelines(request: Request, top_k: int) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: guidelines")


def capability_policy(request: Request) -> tuple[dict[str, Any], dict[str, Any]]:
    raise NotImplementedError("skeleton/producers.py: capability_policy")


def ambient_scribe(request: Request) -> dict[str, Any]:
    raise NotImplementedError("skeleton/producers.py: ambient_scribe")
