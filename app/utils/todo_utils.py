from datetime import datetime
from sqlalchemy.orm import Session
import uuid
from app.models.todo import Todo, TodoStatus
import re
from app.models import Project
from app.models.team import Team
from sqlalchemy.orm import joinedload


def parse_and_get_assignee(
    db: Session, title: str, project_id: str
) -> tuple[str, str | None]:
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .options(
            joinedload(Project.team_members).joinedload(Team.user),
            joinedload(Project.user),
        )
        .first()
    )

    if not project:
        return title, None

    project_users = {tm.user for tm in project.team_members}
    project_users.add(project.user)

    all_mentions = re.findall(r"@(\w+)", title)
    if not all_mentions:
        return title, None

    mentioned_usernames = set(all_mentions)

    valid_mentioned_users = [
        user for user in project_users if user.username in mentioned_usernames
    ]

    if not valid_mentioned_users:
        return title, None

    last_mention_pos = -1
    assignee = None
    cleaned_title = title

    for user in valid_mentioned_users:
        mention_str = f"@{user.username}"
        pos = cleaned_title.rfind(mention_str)
        if pos > last_mention_pos:
            last_mention_pos = pos
            assignee = user

    assignee_id = assignee.id if assignee else None

    for user in valid_mentioned_users:
        cleaned_title = re.sub(rf"\s*@{re.escape(user.username)}\b", "", cleaned_title)

    return cleaned_title.strip(), assignee_id


def get_project_todos(db: Session, project_id: str):
    return db.query(Todo).filter(Todo.project_id == project_id).all()


def update_todo(db: Session, todo: Todo, data: dict) -> Todo:
    for key, value in data.items():
        setattr(todo, key, value)
    if "status" in data:
        if data["status"] == TodoStatus.DONE:
            todo.finished_at = datetime.utcnow()
        else:
            todo.finished_at = None
    db.commit()
    db.refresh(todo)
    return todo


def create_todo(db: Session, data: dict, user_id: str) -> Todo:
    new_todo = Todo(
        id=str(uuid.uuid4()),
        title=data.get("title"),
        description=data.get("description"),
        priority=data.get("priority"),
        due_date=data.get("due_date"),
        assigned_user_id=data.get("assigned_user_id"),
        status=TodoStatus.TODO,
        user_id=user_id,
        project_id=data.get("project_id"),
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo
