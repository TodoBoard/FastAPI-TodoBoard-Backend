from app.models.todo import Todo, TodoStatus
from sqlalchemy.orm import Session
import uuid


def get_project_todos(db: Session, project_id: str):
    return db.query(Todo).filter(Todo.project_id == project_id).all()


def update_todo(db: Session, todo: Todo, data: dict) -> Todo:
    for key, value in data.items():
        if value is not None:
            setattr(todo, key, value)
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
        status=TodoStatus.TODO,
        user_id=user_id,
        project_id=data.get("project_id"),
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo
