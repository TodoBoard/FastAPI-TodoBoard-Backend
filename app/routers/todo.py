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
from app.utils.todo_utils import create_todo, update_todo
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import case, asc, desc
from sqlalchemy.sql.expression import nullslast
from app.models.todo import TodoPriority
from app.utils.project import get_user_projects

router = APIRouter()


@router.get("/todos", response_model=TodoListResponse)
def get_all_todos(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    projects = get_user_projects(db, current_user.id)
    project_ids = [project.id for project in projects]

    order_priority = case(
        (Todo.priority == TodoPriority.HIGH, 1),
        (Todo.priority == TodoPriority.MEDIUM, 2),
        (Todo.priority == TodoPriority.LOW, 3),
        else_=4,
    )

    todos = (
        db.query(Todo)
        .filter(Todo.project_id.in_(project_ids))
        .order_by(order_priority, nullslast(asc(Todo.due_date)), desc(Todo.updated_at))
        .all()
    )

    todos_response = []
    for todo in todos:
        user = todo.user
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
                "username": user.username,
                "avatar_id": user.avatar_id,
                "project_id": todo.project_id,
            }
        )

    return {"todos": todos_response}


@router.get("/todos/{project_id}", response_model=TodoListResponse)
def get_todos(
    project: Project = Depends(require_project_member), db: Session = Depends(get_db)
):
    order_priority = case(
        (Todo.priority == TodoPriority.HIGH, 1),
        (Todo.priority == TodoPriority.MEDIUM, 2),
        (Todo.priority == TodoPriority.LOW, 3),
        else_=4,
    )

    todos = (
        db.query(Todo)
        .filter(Todo.project_id == project.id)
        .order_by(order_priority, nullslast(asc(Todo.due_date)), desc(Todo.updated_at))
        .all()
    )

    todos_response = []
    for todo in todos:
        user = todo.user
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
                "username": user.username,
                "avatar_id": user.avatar_id,
                "project_id": todo.project_id,
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
    new_todo = create_todo(db, todo.dict(), current_user.id)
    return new_todo


@router.put("/todo/{todo_id}", response_model=TodoResponse)
def update_todo_endpoint(
    todo_update: TodoUpdateSchema,
    todo: Todo = Depends(require_todo_permission),
    db: Session = Depends(get_db),
):
    updated_todo = update_todo(db, todo, todo_update.dict(exclude_unset=True))
    return updated_todo


@router.delete("/todo/{todo_id}")
def delete_todo_endpoint(
    todo: Todo = Depends(require_todo_permission),
    db: Session = Depends(get_db),
):
    db.delete(todo)
    db.commit()
    return {"message": "Todo deleted successfully"}
