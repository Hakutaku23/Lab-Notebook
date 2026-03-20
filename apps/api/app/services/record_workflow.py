from __future__ import annotations

from typing import Literal

from fastapi import HTTPException, status

from app.models.project import Project
from app.models.record import ExperimentRecord
from app.models.user import User

RECORD_STATUS_DRAFT = "draft"
RECORD_STATUS_SUBMITTED = "submitted"
RECORD_STATUS_APPROVED = "approved"

RECORD_STATUSES = {
    RECORD_STATUS_DRAFT,
    RECORD_STATUS_SUBMITTED,
    RECORD_STATUS_APPROVED,
}

RecordWorkflowAction = Literal["submit", "withdraw", "approve", "reopen"]

WORKFLOW_ACTION_META: dict[RecordWorkflowAction, dict[str, str]] = {
    "submit": {
        "from": RECORD_STATUS_DRAFT,
        "to": RECORD_STATUS_SUBMITTED,
        "label": "提交审核",
        "audit_action": "record.workflow.submit",
    },
    "withdraw": {
        "from": RECORD_STATUS_SUBMITTED,
        "to": RECORD_STATUS_DRAFT,
        "label": "撤回为草稿",
        "audit_action": "record.workflow.withdraw",
    },
    "approve": {
        "from": RECORD_STATUS_SUBMITTED,
        "to": RECORD_STATUS_APPROVED,
        "label": "审核通过",
        "audit_action": "record.workflow.approve",
    },
    "reopen": {
        "from": RECORD_STATUS_APPROVED,
        "to": RECORD_STATUS_DRAFT,
        "label": "重新打开",
        "audit_action": "record.workflow.reopen",
    },
}


def _project_owner_id(record: ExperimentRecord, project: Project | None = None):
    if project is not None:
        return project.owner_id
    if record.project is not None:
        return record.project.owner_id
    return None


def ensure_valid_record_status(status_value: str) -> str:
    if status_value not in RECORD_STATUSES:
        raise HTTPException(status_code=400, detail=f"非法记录状态：{status_value}")
    return status_value


def can_manage_record_workflow(
    user: User,
    record: ExperimentRecord,
    project: Project | None = None,
) -> bool:
    if user.role == "admin":
        return True
    if record.created_by == user.id:
        return True
    return _project_owner_id(record, project) == user.id


def can_approve_record(
    user: User,
    record: ExperimentRecord,
    project: Project | None = None,
) -> bool:
    if user.role == "admin":
        return True
    owner_id = _project_owner_id(record, project)
    if owner_id != user.id:
        return False
    return record.created_by != user.id


def ensure_record_editable(record: ExperimentRecord) -> None:
    ensure_valid_record_status(record.status)
    if record.status != RECORD_STATUS_DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="只有 draft 状态的实验记录允许直接编辑；请先撤回或重新打开记录。",
        )


def get_allowed_record_actions(
    user: User,
    record: ExperimentRecord,
    project: Project | None = None,
) -> list[RecordWorkflowAction]:
    current_status = record.status
    if current_status not in RECORD_STATUSES:
        return []

    actions: list[RecordWorkflowAction] = []

    if current_status == RECORD_STATUS_DRAFT:
        if can_manage_record_workflow(user, record, project=project):
            actions.append("submit")

    elif current_status == RECORD_STATUS_SUBMITTED:
        if can_manage_record_workflow(user, record, project=project):
            actions.append("withdraw")
        if can_approve_record(user, record, project=project):
            actions.append("approve")

    elif current_status == RECORD_STATUS_APPROVED:
        if can_approve_record(user, record, project=project):
            actions.append("reopen")

    return actions




def workflow_comment_required(action: RecordWorkflowAction) -> bool:
    return action in {"withdraw", "approve", "reopen"}


def validate_workflow_comment(action: RecordWorkflowAction, comment: str | None) -> None:
    if workflow_comment_required(action) and not (comment or "").strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="当前流程动作必须填写审核意见或流转说明。",
        )

def get_workflow_action_label(action: RecordWorkflowAction) -> str:
    return WORKFLOW_ACTION_META[action]["label"]


def get_workflow_audit_action(action: RecordWorkflowAction) -> str:
    return WORKFLOW_ACTION_META[action]["audit_action"]


def transition_record_status(
    user: User,
    record: ExperimentRecord,
    action: RecordWorkflowAction,
    project: Project | None = None,
    comment: str | None = None,
) -> tuple[str, str]:
    meta = WORKFLOW_ACTION_META.get(action)
    if meta is None:
        raise HTTPException(status_code=400, detail="不支持的工作流动作。")

    validate_workflow_comment(action, comment)
    current_status = ensure_valid_record_status(record.status)
    expected_from = meta["from"]
    next_status = meta["to"]

    if current_status != expected_from:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"当前状态为 {current_status}，不能执行 {action}。",
        )

    if action in {"approve", "reopen"}:
        if not can_approve_record(user, record, project=project):
            raise HTTPException(status_code=403, detail="无权执行该审核动作。")
    else:
        if not can_manage_record_workflow(user, record, project=project):
            raise HTTPException(status_code=403, detail="无权执行该流转动作。")

    record.status = next_status
    return current_status, next_status
