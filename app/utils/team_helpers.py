from app.models.team import Team
from app.models.project import Project
from app.models.user import User


def build_team_members_for_non_owner(project: Project, current_user: User):
    members = []
    if project.user:
        members.append(
            {
                "id": project.user.id,
                "username": (
                    "You"
                    if project.user.id == current_user.id
                    else project.user.username
                ),
                "avatar_id": project.user.avatar_id,
            }
        )
    for team in project.team_members:
        if team.user and team.user.id != project.user.id:
            members.append(
                {
                    "id": team.user.id,
                    "username": (
                        "You" if team.user.id == current_user.id else team.user.username
                    ),
                    "avatar_id": team.user.avatar_id,
                }
            )
    return members


def build_team_members_for_owner(project: Project, current_user: User):
    members = []
    if project.user:
        members.append(
            {
                "id": project.user.id,
                "username": (
                    "You"
                    if project.user.id == current_user.id
                    else project.user.username
                ),
                "avatar_id": project.user.avatar_id,
            }
        )
    for team in project.team_members:
        if team.user and team.user.id != project.user.id:
            members.append(
                {
                    "id": team.user.id,
                    "username": team.user.username,
                    "avatar_id": team.user.avatar_id,
                }
            )
    return members
