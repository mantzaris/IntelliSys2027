"""Public task structures. Evaluator labels live in separate pair records."""
from dataclasses import asdict, dataclass, field
from typing import Any
import hashlib
import json


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Job:
    identifier: str
    duration: int
    demands: dict[str, int]
    release: int = 0
    deadline: int | None = None


@dataclass(frozen=True)
class Candidate:
    identifier: str
    starts: dict[str, int]


@dataclass(frozen=True)
class ScheduleWorld:
    jobs: list[Job]
    capacities: dict[str, int]
    precedence: list[tuple[str, str]]
    candidates: list[Candidate]
    tie_order: list[str]
    downtime: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    version: str = "current"
    kind: str = "schedule"


@dataclass(frozen=True)
class Claim:
    task_identifier: str
    candidate_identifier: str
    entity_identifier: str
    predicate_identifier: str
    asserted_value: Any
    units: str
    applicability_condition: str = "always"
    effective_time_or_version: str = "current"
    source_identifiers: tuple[str, ...] = ()
    parent_report_identifiers: tuple[str, ...] = ()
    verification_execution_identifier: str = ""
    operation_type: str = "verification"
    identifier_format: str = "opaque_v1"

    def scope(self) -> dict:
        excluded = {"asserted_value", "source_identifiers", "parent_report_identifiers",
                    "verification_execution_identifier", "operation_type", "identifier_format"}
        return {k: v for k, v in asdict(self).items() if k not in excluded}

    @property
    def key(self) -> str:
        if self.identifier_format == "descriptive_v4":
            return "/".join([self.candidate_identifier,self.predicate_identifier,self.entity_identifier,
                             self.effective_time_or_version,digest([self.applicability_condition,self.units])[:4]])
        return "k" + digest(self.scope())[:7]


@dataclass(frozen=True)
class Report:
    identifier: str
    claim: Claim
    text: str
    parent_report_identifiers: tuple[str, ...] = ()
    operation_type: str = "verification"
    additional_claims: tuple[Claim, ...] = ()

    def claims(self) -> tuple[Claim, ...]:
        return (self.claim,) + self.additional_claims

    def visible(self, ancestry: bool = True) -> dict:
        out = {"report": self.identifier, "key": self.claim.key, "text": self.text}
        if self.additional_claims:
            out["keys"] = [c.key for c in self.claims()]
        if ancestry:
            out.update(sources=list(self.claim.source_identifiers),
                       execution=self.claim.verification_execution_identifier,
                       parents=list(self.parent_report_identifiers), operation=self.operation_type)
            if self.additional_claims:
                out['claim_ancestry']={c.key:{'sources':list(c.source_identifiers),
                                      'execution':c.verification_execution_identifier} for c in self.claims()}
        return out


def world_from_dict(d: dict) -> ScheduleWorld:
    return ScheduleWorld(jobs=[Job(**j) for j in d["jobs"]],
                         candidates=[Candidate(**c) for c in d["candidates"]],
                         capacities=d["capacities"], precedence=[tuple(e) for e in d["precedence"]],
                         tie_order=d["tie_order"], downtime=d.get("downtime", {}),
                         version=d.get("version", "current"))
