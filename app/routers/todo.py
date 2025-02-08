from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models import Todo, Project
from app.schemas import TodoResponse, TodoListResponse, TodoUpdateSchema, TodoCreate
from app.utils.todo_utils import get_project_todos, update_todo, create_todo
from app.auth.token import get_current_user
from app.utils.project import get_project
from app.models.user import User

router = APIRouter()


@router.get("/todos", response_model=TodoListResponse)
def get_todos(
    project_id: str = Query(..., description="Project ID to filter todos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id and not any(
        tm.user_id == current_user.id for tm in project.team_members
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access todos for this project",
        )
    todos = get_project_todos(db, project_id)
    return TodoListResponse(todos=todos)


@router.post("/todo", response_model=TodoResponse)
def create_todo_endpoint(
    todo: TodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project(db, todo.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id and not any(
        tm.user_id == current_user.id for tm in project.team_members
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add todos to this project",
        )
    new_todo = create_todo(db, todo.dict(), current_user.id)
    return new_todo


@router.put("/todo/{todo_id}", response_model=TodoResponse)
def update_todo_endpoint(
    todo_id: str,
    todo_update: TodoUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    project = todo.project
    if project.user_id != current_user.id and not any(
        tm.user_id == current_user.id for tm in project.team_members
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this todo",
        )
    updated_todo = update_todo(db, todo, todo_update.dict(exclude_unset=True))
    return updated_todo
