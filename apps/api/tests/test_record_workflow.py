from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.record_workflow import (
    can_approve_record,
    get_allowed_record_actions,
    transition_record_status,
)


def make_user(*, role: str = "researcher", user_id=None):
    return SimpleNamespace(id=user_id or uuid4(), role=role)


def make_project(*, owner_id=None):
    return SimpleNamespace(owner_id=owner_id or uuid4())


def make_record(*, status: str = "draft", created_by=None, project=None):
    return SimpleNamespace(status=status, created_by=created_by or uuid4(), project=project)


def test_non_admin_project_owner_cannot_approve_own_record():
    owner_id = uuid4()
    user = make_user(user_id=owner_id)
    project = make_project(owner_id=owner_id)
    record = make_record(status="submitted", created_by=owner_id, project=project)

    assert can_approve_record(user, record, project=project) is False
    assert get_allowed_record_actions(user, record, project=project) == ["withdraw"]


@pytest.mark.parametrize("action", ["withdraw", "approve", "reopen"])
def test_workflow_comment_is_required_for_review_actions(action: str):
    owner_id = uuid4()
    creator_id = uuid4()
    user = make_user(user_id=owner_id)
    project = make_project(owner_id=owner_id)
    status = "submitted" if action in {"withdraw", "approve"} else "approved"
    record = make_record(status=status, created_by=creator_id, project=project)

    with pytest.raises(HTTPException) as exc:
        transition_record_status(user, record, action, project=project, comment="")

    assert exc.value.status_code == 422


def test_project_owner_can_approve_other_users_record_with_comment():
    owner_id = uuid4()
    creator_id = uuid4()
    user = make_user(user_id=owner_id)
    project = make_project(owner_id=owner_id)
    record = make_record(status="submitted", created_by=creator_id, project=project)

    before_status, after_status = transition_record_status(
        user,
        record,
        "approve",
        project=project,
        comment="实验数据与附件已复核，同意通过。",
    )

    assert before_status == "submitted"
    assert after_status == "approved"
    assert record.status == "approved"
