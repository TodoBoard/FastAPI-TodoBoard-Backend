from app.auth.token import get_current_user
from app.database.db import get_db
from app.dependencies.permissions import require_project_member, require_todo_permission
from app.models import Todo, Project
from app.models.user import User
from app.schemas.todo import (
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdateSchema,
)
from app.utils.todo_utils import create_todo, update_todo, parse_and_get_assignee
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import case, asc, desc
from sqlalchemy.sql.expression import nullslast
from app.models.todo import TodoPriority
from app.utils.project import get_user_projects
from app.websockets.connection_manager import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/todos", response_model=TodoListResponse)
def get_all_todos(
    assigned_only: bool = Query(False, description="Return only todos assigned to the current user"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = get_user_projects(db, current_user.id)
    project_ids = [project.id for project in projects]

    order_priority = case(
        (Todo.priority == TodoPriority.HIGH, 1),
        (Todo.priority == TodoPriority.MEDIUM, 2),
        (Todo.priority == TodoPriority.LOW, 3),
        else_=4,
    )

    query = db.query(Todo).filter(Todo.project_id.in_(project_ids))

    if assigned_only:
        query = query.filter(Todo.assigned_user_id == current_user.id)

    order_assigned = case((Todo.assigned_user_id.isnot(None), 0), else_=1)

    todos = (
        query.order_by(order_priority, order_assigned, nullslast(asc(Todo.due_date)), desc(Todo.updated_at)).all()
    )

    todos_response = []
    for todo in todos:
        creator = todo.user
        assignee = todo.assignee
        todos_response.append(
            {
                "id": todo.id,
                "title": todo.title,
                "description": todo.description,
                "status": todo.status,
                "priority": todo.priority,
                "due_date": todo.due_date,
                "created_at": todo.created_at,
                "updated_at": todo.updated_at,
                "finished_at": todo.finished_at,
                "username": creator.username,
                "avatar_id": creator.avatar_id,
                "project_id": todo.project_id,
                "assigned_user_id": todo.assigned_user_id,
                "assignee_username": assignee.username if assignee else None,
                "assignee_avatar_id": assignee.avatar_id if assignee else None,
            }
        )

    return {"todos": todos_response}


@router.get("/todos/{project_id}", response_model=TodoListResponse)
def get_todos(
    assigned_only: bool = Query(False, description="Return only todos assigned to the current user"),
    project: Project = Depends(require_project_member),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order_priority = case(
        (Todo.priority == TodoPriority.HIGH, 1),
        (Todo.priority == TodoPriority.MEDIUM, 2),
        (Todo.priority == TodoPriority.LOW, 3),
        else_=4,
    )

    query = db.query(Todo).filter(Todo.project_id == project.id)
    if assigned_only:
        query = query.filter(Todo.assigned_user_id == current_user.id)

    order_assigned = case((Todo.assigned_user_id.isnot(None), 0), else_=1)

    todos = (
        query.order_by(order_priority, order_assigned, nullslast(asc(Todo.due_date)), desc(Todo.updated_at)).all()
    )

    todos_response = []
    for todo in todos:
        creator = todo.user
        assignee = todo.assignee
        todos_response.append(
            {
                "id": todo.id,
                "title": todo.title,
                "description": todo.description,
                "status": todo.status,
                "priority": todo.priority,
                "due_date": todo.due_date,
                "created_at": todo.created_at,
                "updated_at": todo.updated_at,
                "finished_at": todo.finished_at,
                "username": creator.username,
                "avatar_id": creator.avatar_id,
                "project_id": todo.project_id,
                "assigned_user_id": todo.assigned_user_id,
                "assignee_username": assignee.username if assignee else None,
                "assignee_avatar_id": assignee.avatar_id if assignee else None,
            }
        )

    return {"todos": todos_response}


@router.post("/todo", response_model=TodoResponse)
def create_todo_endpoint(
    todo: TodoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = require_project_member(todo.project_id, db=db, current_user=current_user)

    todo_data = todo.dict()
    cleaned_title, parsed_assignee_id = parse_and_get_assignee(
        db, todo_data["title"], todo_data["project_id"]
    )

    todo_data["title"] = cleaned_title
    if todo_data.get("assigned_user_id") is None and parsed_assignee_id:
        todo_data["assigned_user_id"] = parsed_assignee_id

    new_todo = create_todo(db, todo_data, current_user.id)

    recipients = {project.user_id}
    for tm in project.team_members:
        recipients.add(tm.user_id)
    if new_todo.assigned_user_id:
        recipients.add(new_todo.assigned_user_id)

    message = {
        "event": "todo.created",
        "todo": {
            "id": new_todo.id,
            "title": new_todo.title,
            "description": new_todo.description,
            "status": new_todo.status.value,
            "priority": new_todo.priority.value if new_todo.priority else None,
            "due_date": new_todo.due_date.isoformat() if new_todo.due_date else None,
            "created_at": new_todo.created_at.isoformat(),
            "updated_at": new_todo.updated_at.isoformat(),
            "finished_at": new_todo.finished_at.isoformat() if new_todo.finished_at else None,
            "project_id": new_todo.project_id,
            "assigned_user_id": new_todo.assigned_user_id,
            "assignee_username": new_todo.assignee.username if new_todo.assignee else None,
            "assignee_avatar_id": new_todo.assignee.avatar_id if new_todo.assignee else None,
        },
    }
    logger.info("Broadcasting 'todo.created' for todo_id %s to recipients %s", new_todo.id, list(recipients))
    background_tasks.add_task(manager.ts_broadcast, list(recipients), message)
    return new_todo


@router.put("/todo/{todo_id}", response_model=TodoResponse)
def update_todo_endpoint(
    todo_update: TodoUpdateSchema,
    background_tasks: BackgroundTasks,
    todo: Todo = Depends(require_todo_permission),
    db: Session = Depends(get_db),
):
    update_data = todo_update.dict(exclude_unset=True)

    if "title" in update_data:
        cleaned_title, parsed_assignee_id = parse_and_get_assignee(
            db, update_data["title"], todo.project_id
        )
        update_data["title"] = cleaned_title

        if "assigned_user_id" not in update_data and parsed_assignee_id:
            update_data["assigned_user_id"] = parsed_assignee_id

    updated_todo = update_todo(db, todo, update_data)

    project = db.query(Project).filter(Project.id == updated_todo.project_id).first()
    recipients = {project.user_id}
    for tm in project.team_members:
        recipients.add(tm.user_id)
    if updated_todo.assigned_user_id:
        recipients.add(updated_todo.assigned_user_id)

    message = {
        "event": "todo.updated",
        "todo": {
            "id": updated_todo.id,
            "title": updated_todo.title,
            "description": updated_todo.description,
            "status": updated_todo.status.value,
            "priority": updated_todo.priority.value if updated_todo.priority else None,
            "due_date": updated_todo.due_date.isoformat() if updated_todo.due_date else None,
            "created_at": updated_todo.created_at.isoformat(),
            "updated_at": updated_todo.updated_at.isoformat(),
            "finished_at": updated_todo.finished_at.isoformat() if updated_todo.finished_at else None,
            "project_id": updated_todo.project_id,
            "assigned_user_id": updated_todo.assigned_user_id,
            "assignee_username": updated_todo.assignee.username if updated_todo.assignee else None,
            "assignee_avatar_id": updated_todo.assignee.avatar_id if updated_todo.assignee else None,
        },
    }
    logger.info("Broadcasting 'todo.updated' for todo_id %s to recipients %s", updated_todo.id, list(recipients))
    background_tasks.add_task(manager.ts_broadcast, list(recipients), message)
    return updated_todo


@router.delete("/todo/{todo_id}")
def delete_todo_endpoint(
    background_tasks: BackgroundTasks,
    todo: Todo = Depends(require_todo_permission),
    db: Session = Depends(get_db),
):
    db.delete(todo)
    db.commit()

    project = db.query(Project).filter(Project.id == todo.project_id).first()
    recipients = {project.user_id}
    for tm in project.team_members:
        recipients.add(tm.user_id)

    message = {
        "event": "todo.deleted",
        "todo_id": todo.id,
        "project_id": todo.project_id,
    }
    logger.info("Broadcasting 'todo.deleted' for todo_id %s to recipients %s", todo.id, list(recipients))
    background_tasks.add_task(manager.ts_broadcast, list(recipients), message)
    return {"message": "Todo deleted successfully"}
