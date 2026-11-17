# Chat memory: the turns of a saved chat, read from the chat tables before an answer and saved
# after it. These tables are the only store of chat history. The state of a running request
# is not kept here

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from mrag import db
from mrag.harness.context import Turn


def history(s: Session, chat_id: uuid.UUID) -> list[Turn]:
    # Oldest first. A failed answer and an empty one are left out: the model did not give them
    query = (
        select(db.Message)
        .where(db.Message.chat_id == chat_id, db.Message.status != "failed")
        .order_by(db.Message.id)
    )
    return [
        Turn("user" if row.role == "user" else "assistant", row.content)
        for row in s.scalars(query)
        if row.content
    ]


def save_turn(
    s: Session, chat_id: uuid.UUID, role: str, content: str, status: str = "done"
) -> db.Message:
    message = db.Message(chat_id=chat_id, role=role, content=content, status=status)
    s.add(message)
    s.flush()
    return message
