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
from app.utils.todo_utils import create_todo, get_project_todos, update_todo
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/todos/{project_id}", response_model=TodoListResponse)
def get_todos(
    project: Project = Depends(require_project_member), db: Session = Depends(get_db)
):
    todos = get_project_todos(db, project.id)
    return TodoListResponse(todos=todos)


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
