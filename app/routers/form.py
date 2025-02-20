from fastapi import APIRouter
from app.schemas.form import Form
from dotenv import load_dotenv
import os
import aiohttp

router = APIRouter()


@router.post("/form/submit")
async def form(form: Form):
    load_dotenv()

    embed = {
        "embeds": [
            {
                "title": "New Form Submission",
                "color": 3447003,
                "fields": [
                    {"name": "Title", "value": form.title, "inline": True},
                    {"name": "Contact", "value": form.contact, "inline": True},
                    {
                        "name": "Stars",
                        "value": f"{form.stars}/5 ({'⭐' * form.stars})",
                        "inline": True,
                    },
                    {"name": "Message", "value": form.message, "inline": False},
                ],
                "timestamp": "now",
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        await session.post(os.getenv("DISCORD_WEBHOOK_URL"), json=embed)

    return {"message": "Form submitted successfully"}
