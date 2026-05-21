"""Policy diff — compare two policy versions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from verdictcore.policies.model import DecisionPolicy


class CriterionChange(BaseModel):

    criterion: str
    field: str
    from_value: Any
    to_value: Any


class ConstraintChange(BaseModel):

    change_type: str  # "added", "removed", "modified"
    field: str
    from_value: dict[str, Any] | None = None
    to_value: dict[str, Any] | None = None


class PolicyDiff(BaseModel):

    from_policy: str
    from_version: str
    to_policy: str
    to_version: str
    criteria_changes: list[CriterionChange] = []
    constraint_changes: list[ConstraintChange] = []
    interpretation: list[str] = []


def diff_policies(old: DecisionPolicy, new: DecisionPolicy) -> PolicyDiff:
    criteria_changes = _diff_criteria(old, new)
    constraint_changes = _diff_constraints(old, new)
    interpretation = _interpret(criteria_changes, constraint_changes)

    return PolicyDiff(
        from_policy=old.policy_id,
        from_version=old.version,
        to_policy=new.policy_id,
        to_version=new.version,
        criteria_changes=criteria_changes,
        constraint_changes=constraint_changes,
        interpretation=interpretation,
    )


def _diff_criteria(
    old: DecisionPolicy, new: DecisionPolicy,
) -> list[CriterionChange]:
    changes: list[CriterionChange] = []
    old_map = old.criteria_map
    new_map = new.criteria_map

    all_names = set(old_map.keys()) | set(new_map.keys())
    for name in sorted(all_names):
        old_c = old_map.get(name)
        new_c = new_map.get(name)

        if old_c is None and new_c is not None:
            changes.append(CriterionChange(
                criterion=name, field="added",
                from_value=None, to_value=new_c.weight,
            ))
        elif old_c is not None and new_c is None:
            changes.append(CriterionChange(
                criterion=name, field="removed",
                from_value=old_c.weight, to_value=None,
            ))
        elif old_c is not None and new_c is not None:
            if old_c.weight != new_c.weight:
                changes.append(CriterionChange(
                    criterion=name, field="weight",
                    from_value=old_c.weight, to_value=new_c.weight,
                ))
            if old_c.direction != new_c.direction:
                changes.append(CriterionChange(
                    criterion=name, field="direction",
                    from_value=old_c.direction, to_value=new_c.direction,
                ))

    return changes


def _diff_constraints(
    old: DecisionPolicy, new: DecisionPolicy,
) -> list[ConstraintChange]:
    changes: list[ConstraintChange] = []

    old_map = {
        (c.field, c.operator): c for c in old.constraints
    }
    new_map = {
        (c.field, c.operator): c for c in new.constraints
    }

    for key, c in new_map.items():
        if key not in old_map:
            changes.append(ConstraintChange(
                change_type="added", field=c.field,
                to_value={"operator": c.operator, "value": c.value},
            ))
        else:
            old_c = old_map[key]
            if old_c.value != c.value or old_c.action != c.action:
                changes.append(ConstraintChange(
                    change_type="modified", field=c.field,
                    from_value={
                        "operator": old_c.operator, "value": old_c.value,
                    },
                    to_value={
                        "operator": c.operator, "value": c.value,
                    },
                ))

    for key, c in old_map.items():
        if key not in new_map:
            changes.append(ConstraintChange(
                change_type="removed", field=c.field,
                from_value={
                    "operator": c.operator, "value": c.value,
                },
            ))

    return changes


def _interpret(
    criteria_changes: list[CriterionChange],
    constraint_changes: list[ConstraintChange],
) -> list[str]:
    notes: list[str] = []

    increased = [
        c for c in criteria_changes
        if c.field == "weight"
        and c.from_value is not None
        and c.to_value is not None
        and c.to_value > c.from_value
    ]
    decreased = [
        c for c in criteria_changes
        if c.field == "weight"
        and c.from_value is not None
        and c.to_value is not None
        and c.to_value < c.from_value
    ]

    if increased:
        names = ", ".join(c.criterion for c in increased)
        notes.append(f"Increased emphasis on: {names}.")
    if decreased:
        names = ", ".join(c.criterion for c in decreased)
        notes.append(f"Decreased emphasis on: {names}.")

    added_constraints = [
        c for c in constraint_changes if c.change_type == "added"
    ]
    if added_constraints:
        fields = ", ".join(c.field for c in added_constraints)
        notes.append(f"New constraints added for: {fields}.")

    tightened = [
        c for c in constraint_changes if c.change_type == "modified"
    ]
    if tightened:
        fields = ", ".join(c.field for c in tightened)
        notes.append(f"Constraint thresholds modified for: {fields}.")

    return notes
