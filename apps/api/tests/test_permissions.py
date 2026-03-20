from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.permissions import ensure_record_delete_access, ensure_record_write_access


def make_user(*, role: str = "researcher", user_id=None):
    return SimpleNamespace(id=user_id or uuid4(), role=role)


def make_project(*, owner_id=None):
    return SimpleNamespace(owner_id=owner_id or uuid4())


def make_record(*, status: str = "draft", created_by=None, project=None):
    return SimpleNamespace(status=status, created_by=created_by or uuid4(), project=project)


def test_project_owner_can_write_other_users_record():
    owner_id = uuid4()
    project = make_project(owner_id=owner_id)
    user = make_user(user_id=owner_id)
    record = make_record(status="draft", created_by=uuid4(), project=project)

    ensure_record_write_access(user, record, project=project)


def test_non_manager_cannot_write_record():
    project = make_project(owner_id=uuid4())
    user = make_user(user_id=uuid4())
    record = make_record(status="draft", created_by=uuid4(), project=project)

    with pytest.raises(HTTPException) as exc:
        ensure_record_write_access(user, record, project=project)

    assert exc.value.status_code == 403


def test_only_draft_records_can_be_deleted():
    owner_id = uuid4()
    project = make_project(owner_id=owner_id)
    user = make_user(user_id=owner_id)
    record = make_record(status="approved", created_by=uuid4(), project=project)

    with pytest.raises(HTTPException) as exc:
        ensure_record_delete_access(user, record, project=project)

    assert exc.value.status_code == 409
