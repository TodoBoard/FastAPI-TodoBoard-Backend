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
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import case, asc, desc
from sqlalchemy.sql.expression import nullslast
from app.models.todo import TodoPriority
from app.utils.project import get_user_projects

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
    return new_todo


@router.put("/todo/{todo_id}", response_model=TodoResponse)
def update_todo_endpoint(
    todo_update: TodoUpdateSchema,
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
    return updated_todo


@router.delete("/todo/{todo_id}")
def delete_todo_endpoint(
    todo: Todo = Depends(require_todo_permission),
    db: Session = Depends(get_db),
):
    db.delete(todo)
    db.commit()
    return {"message": "Todo deleted successfully"}
