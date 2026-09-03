"""系统内部聊天 - 业务逻辑"""

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.chat.ws_manager import chat_ws_manager
from app.api.v1.module_system.user.model import UserModel
from app.core.base_schema import AuthSchema

from .crud import ChatGroupCRUD, ChatGroupMemberCRUD, ChatGroupReadCRUD, ChatMessageCRUD
from .model import ChatGroupMemberModel, ChatGroupModel, ChatGroupReadModel, ChatMessageModel
from .schema import (
    ChatConversationSchema,
    ChatGroupCreateSchema,
    ChatGroupDetailSchema,
    ChatGroupUpdateSchema,
    ChatMessageCreateSchema,
    ChatMessageOutSchema,
    ChatMessagePageSchema,
    ChatReadSchema,
    ChatUserItemSchema,
)

PAGE_SIZE = 20


class ChatService:
    """聊天服务"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db
        self.message_crud = ChatMessageCRUD(auth, db)
        self.group_crud = ChatGroupCRUD(auth, db)
        self.member_crud = ChatGroupMemberCRUD(auth, db)
        self.read_crud = ChatGroupReadCRUD(auth, db)

    @property
    def _user_id(self) -> int:
        return self.auth.user.id

    # ── 会话列表 ──────────────────────────────────────────────────

    async def conversations(self) -> list[ChatConversationSchema]:
        me = self._user_id
        conversations: list[ChatConversationSchema] = []
        conversations.extend(await self._private_conversations(me))
        conversations.extend(await self._group_conversations(me))
        conversations.sort(key=lambda item: item.last_time or "", reverse=True)
        return conversations

    async def _private_conversations(self, me: int) -> list[ChatConversationSchema]:
        peer_expr = case(
            (ChatMessageModel.sender_id == me, ChatMessageModel.receiver_id),
            else_=ChatMessageModel.sender_id,
        )
        rows = (
            await self.db.execute(
                select(peer_expr.label("peer_id"), func.max(ChatMessageModel.id).label("last_id"))
                .where(
                    ChatMessageModel.is_deleted == False,  # noqa: E712
                    ChatMessageModel.conversation_type == 1,
                    or_(ChatMessageModel.sender_id == me, ChatMessageModel.receiver_id == me),
                )
                .group_by(peer_expr)
            )
        ).all()
        if not rows:
            return []

        peer_ids = [r.peer_id for r in rows]
        last_ids = [r.last_id for r in rows]
        last_by_peer = {r.peer_id: r.last_id for r in rows}

        last_msgs = (
            (
                await self.db.execute(
                    select(ChatMessageModel).where(ChatMessageModel.id.in_(last_ids))
                )
            )
            .scalars()
            .all()
        )
        msg_by_id = {m.id: m for m in last_msgs}

        unread_rows = (
            await self.db.execute(
                select(ChatMessageModel.sender_id, func.count(ChatMessageModel.id))
                .where(
                    ChatMessageModel.is_deleted == False,  # noqa: E712
                    ChatMessageModel.conversation_type == 1,
                    ChatMessageModel.receiver_id == me,
                    ChatMessageModel.status == 0,
                )
                .group_by(ChatMessageModel.sender_id)
            )
        ).all()
        unread_by_peer = {int(sender_id): int(count) for sender_id, count in unread_rows}

        users = (
            (await self.db.execute(select(UserModel).where(UserModel.id.in_(peer_ids)))).scalars().all()
        )
        user_by_id = {u.id: u for u in users}

        items: list[ChatConversationSchema] = []
        for peer_id in peer_ids:
            user = user_by_id.get(peer_id)
            if user is None:
                continue
            last = msg_by_id.get(last_by_peer[peer_id])
            items.append(
                ChatConversationSchema(
                    id=peer_id,
                    conversation_type=1,
                    name=user.name,
                    avatar=user.avatar,
                    online=chat_ws_manager.is_online(peer_id),
                    member_count=0,
                    last_message=last.content if last else None,
                    last_time=last.created_time.isoformat() if last else None,
                    unread=unread_by_peer.get(peer_id, 0),
                )
            )
        return items

    async def _group_conversations(self, me: int) -> list[ChatConversationSchema]:
        groups = (
            (
                await self.db.execute(
                    select(ChatGroupModel)
                    .join(ChatGroupMemberModel, ChatGroupMemberModel.group_id == ChatGroupModel.id)
                    .where(
                        ChatGroupMemberModel.user_id == me,
                        ChatGroupModel.is_deleted == False,  # noqa: E712
                    )
                )
            )
            .scalars()
            .all()
        )
        if not groups:
            return []

        group_ids = [g.id for g in groups]
        group_by_id = {g.id: g for g in groups}

        last_rows = (
            await self.db.execute(
                select(ChatMessageModel.receiver_id, func.max(ChatMessageModel.id).label("last_id"))
                .where(
                    ChatMessageModel.is_deleted == False,  # noqa: E712
                    ChatMessageModel.conversation_type == 2,
                    ChatMessageModel.receiver_id.in_(group_ids),
                )
                .group_by(ChatMessageModel.receiver_id)
            )
        ).all()
        last_by_group = {r.receiver_id: r.last_id for r in last_rows}

        last_msgs = (
            (
                await self.db.execute(
                    select(ChatMessageModel).where(ChatMessageModel.id.in_(last_by_group.values()))
                )
            )
            .scalars()
            .all()
        )
        msg_by_id = {m.id: m for m in last_msgs}

        member_counts = (
            await self.db.execute(
                select(ChatGroupMemberModel.group_id, func.count(ChatGroupMemberModel.id))
                .where(ChatGroupMemberModel.group_id.in_(group_ids))
                .group_by(ChatGroupMemberModel.group_id)
            )
        ).all()
        count_by_group = {int(group_id): int(count) for group_id, count in member_counts}

        unread_rows = (
            await self.db.execute(
                select(
                    ChatGroupMemberModel.group_id,
                    func.count(ChatMessageModel.id).label("unread"),
                )
                .outerjoin(
                    ChatGroupReadModel,
                    and_(
                        ChatGroupReadModel.group_id == ChatGroupMemberModel.group_id,
                        ChatGroupReadModel.user_id == me,
                    ),
                )
                .outerjoin(
                    ChatMessageModel,
                    and_(
                        ChatMessageModel.conversation_type == 2,
                        ChatMessageModel.receiver_id == ChatGroupMemberModel.group_id,
                        ChatMessageModel.sender_id != me,
                        ChatMessageModel.is_deleted == False,  # noqa: E712
                        ChatMessageModel.id > func.coalesce(ChatGroupReadModel.last_read_msg_id, 0),
                    ),
                )
                .where(ChatGroupMemberModel.user_id == me)
                .group_by(ChatGroupMemberModel.group_id)
            )
        ).all()
        unread_by_group = {int(group_id): int(count) for group_id, count in unread_rows}

        items: list[ChatConversationSchema] = []
        for group_id in group_ids:
            group = group_by_id[group_id]
            last = msg_by_id.get(last_by_group.get(group_id, 0))
            items.append(
                ChatConversationSchema(
                    id=group_id,
                    conversation_type=2,
                    name=group.name,
                    avatar=group.avatar,
                    online=False,
                    member_count=count_by_group.get(group_id, 0),
                    last_message=last.content if last else None,
                    last_time=last.created_time.isoformat() if last else None,
                    unread=unread_by_group.get(group_id, 0),
                )
            )
        return items

    # ── 历史消息 ──────────────────────────────────────────────────

    async def messages(self, conversation_type: int, receiver_id: int, before_id: int | None, page_size: int) -> ChatMessagePageSchema:
        me = self._user_id
        stmt = select(ChatMessageModel).where(ChatMessageModel.is_deleted == False)  # noqa: E712
        if conversation_type == 1:
            stmt = stmt.where(
                ChatMessageModel.conversation_type == 1,
                or_(
                    and_(ChatMessageModel.sender_id == me, ChatMessageModel.receiver_id == receiver_id),
                    and_(ChatMessageModel.sender_id == receiver_id, ChatMessageModel.receiver_id == me),
                ),
            )
        else:
            stmt = stmt.where(
                ChatMessageModel.conversation_type == 2,
                ChatMessageModel.receiver_id == receiver_id,
            )
        if before_id:
            stmt = stmt.where(ChatMessageModel.id < before_id)
        stmt = stmt.order_by(ChatMessageModel.id.desc()).limit(page_size + 1)
        rows = (await self.db.execute(stmt)).scalars().all()

        has_more = len(rows) > page_size
        rows = list(rows[:page_size])
        rows.reverse()

        sender_ids = {m.sender_id for m in rows}
        senders = (
            (await self.db.execute(select(UserModel).where(UserModel.id.in_(sender_ids)))).scalars().all()
        )
        sender_by_id = {u.id: u for u in senders}

        items: list[ChatMessageOutSchema] = []
        for m in rows:
            sender = sender_by_id.get(m.sender_id)
            out = ChatMessageOutSchema.model_validate(m)
            out.sender_name = sender.name if sender else ""
            out.sender_avatar = sender.avatar if sender else None
            items.append(out)
        return ChatMessagePageSchema(items=items, has_more=has_more)

    # ── 发送消息 ──────────────────────────────────────────────────

    async def send_message(self, data: ChatMessageCreateSchema) -> ChatMessageOutSchema:
        me = self._user_id
        if data.conversation_type == 1:
            if data.receiver_id == me:
                raise ValueError("不能给自己发送私聊消息")
            user = (
                (
                    await self.db.execute(
                        select(UserModel).where(UserModel.id == data.receiver_id, UserModel.is_deleted == False)  # noqa: E712
                    )
                )
                .scalars()
                .first()
            )
            if user is None:
                raise ValueError("接收用户不存在")
            target_ids = [data.receiver_id]
        else:
            group = (
                (
                    await self.db.execute(
                        select(ChatGroupModel).where(
                            ChatGroupModel.id == data.receiver_id, ChatGroupModel.is_deleted == False  # noqa: E712
                        )
                    )
                )
                .scalars()
                .first()
            )
            if group is None:
                raise ValueError("群组不存在")
            member_ids = (
                (
                    await self.db.execute(
                        select(ChatGroupMemberModel.user_id).where(
                            ChatGroupMemberModel.group_id == data.receiver_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            if me not in member_ids:
                raise ValueError("您不在该群组中，无法发送消息")
            target_ids = list(member_ids)

        obj = await self.message_crud.create(
            data={
                "conversation_type": data.conversation_type,
                "sender_id": me,
                "receiver_id": data.receiver_id,
                "content": data.content.strip(),
            }
        )
        message = self._to_message(obj)
        await chat_ws_manager.send_to_users(target_ids, {"type": "message", "data": message.model_dump(mode="json")})
        return message

    def _to_message(self, m: ChatMessageModel) -> ChatMessageOutSchema:
        out = ChatMessageOutSchema.model_validate(m)
        out.sender_name = self.auth.user.name
        out.sender_avatar = self.auth.user.avatar
        return out

    # ── 标记已读 ──────────────────────────────────────────────────

    async def mark_read(self, data: ChatReadSchema) -> None:
        me = self._user_id
        if data.conversation_type == 1:
            await self.db.execute(
                update(ChatMessageModel)
                .where(
                    ChatMessageModel.conversation_type == 1,
                    ChatMessageModel.receiver_id == me,
                    ChatMessageModel.sender_id == data.receiver_id,
                    ChatMessageModel.status == 0,
                )
                .values(status=1)
            )
            await chat_ws_manager.send_to_user(
                data.receiver_id,
                {"type": "read", "conversation_type": 1, "peer_id": me, "target_id": me},
            )
        else:
            max_id = (
                await self.db.execute(
                    select(func.max(ChatMessageModel.id)).where(
                        ChatMessageModel.conversation_type == 2,
                        ChatMessageModel.receiver_id == data.receiver_id,
                        ChatMessageModel.is_deleted == False,  # noqa: E712
                    )
                )
            ).scalar() or 0
            existing = (
                (
                    await self.db.execute(
                        select(ChatGroupReadModel).where(
                            ChatGroupReadModel.user_id == me,
                            ChatGroupReadModel.group_id == data.receiver_id,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if existing:
                existing.last_read_msg_id = max_id
            else:
                await self.read_crud.create(
                    data={"user_id": me, "group_id": data.receiver_id, "last_read_msg_id": max_id}
                )

    # ── 用户选择器 ──────────────────────────────────────────────────

    async def users(self, keyword: str | None) -> list[ChatUserItemSchema]:
        me = self._user_id
        stmt = select(UserModel).where(UserModel.is_deleted == False)  # noqa: E712
        if keyword:
            stmt = stmt.where(or_(UserModel.name.like(f"%{keyword}%"), UserModel.username.like(f"%{keyword}%")))
        rows = (await self.db.execute(stmt.order_by(UserModel.id).limit(100))).scalars().all()
        return [ChatUserItemSchema.model_validate(u) for u in rows if u.id != me]

    # ── 群管理 ──────────────────────────────────────────────────

    async def create_group(self, data: ChatGroupCreateSchema) -> ChatGroupDetailSchema:
        me = self._user_id
        member_ids = {int(uid) for uid in data.member_ids if int(uid) != me}
        if member_ids:
            valid_ids = (
                (
                    await self.db.execute(
                        select(UserModel.id).where(UserModel.id.in_(member_ids), UserModel.is_deleted == False)  # noqa: E712
                    )
                )
                .scalars()
                .all()
            )
            member_ids = set(valid_ids)

        group = await self.group_crud.create(
            data={
                "name": data.name.strip(),
                "avatar": data.avatar,
                "announcement": data.announcement,
                "owner_id": me,
            }
        )
        await self.member_crud.create(data={"group_id": group.id, "user_id": me})
        for uid in member_ids:
            await self.member_crud.create(data={"group_id": group.id, "user_id": uid})
        return await self._group_detail(group.id)

    async def group_detail(self, group_id: int) -> ChatGroupDetailSchema:
        return await self._group_detail(group_id)

    async def _group_detail(self, group_id: int) -> ChatGroupDetailSchema:
        group = (
            (
                await self.db.execute(
                    select(ChatGroupModel).where(
                        ChatGroupModel.id == group_id, ChatGroupModel.is_deleted == False  # noqa: E712
                    )
                )
            )
            .scalars()
            .first()
        )
        if group is None:
            raise ValueError("群组不存在")
        members = (
            (
                await self.db.execute(
                    select(UserModel)
                    .join(ChatGroupMemberModel, ChatGroupMemberModel.user_id == UserModel.id)
                    .where(
                        ChatGroupMemberModel.group_id == group_id,
                        UserModel.is_deleted == False,  # noqa: E712
                    )
                )
            )
            .scalars()
            .all()
        )
        return ChatGroupDetailSchema(
            id=group.id,
            name=group.name,
            avatar=group.avatar,
            announcement=group.announcement,
            owner_id=group.owner_id,
            member_count=len(members),
            members=[ChatUserItemSchema.model_validate(u) for u in members],
        )

    async def update_group(self, group_id: int, data: ChatGroupUpdateSchema) -> None:
        group = await self._get_group_or_404(group_id)
        if group.owner_id != self._user_id:
            raise ValueError("仅群主可修改群信息")
        group.name = data.name.strip() if data.name else group.name
        if data.avatar is not None:
            group.avatar = data.avatar
        if data.announcement is not None:
            group.announcement = data.announcement

    async def delete_group(self, group_id: int) -> None:
        group = await self._get_group_or_404(group_id)
        if group.owner_id != self._user_id:
            raise ValueError("仅群主可解散群组")
        await self.group_crud.delete(ids=[group_id])
        members = (
            (
                await self.db.execute(
                    select(ChatGroupMemberModel).where(ChatGroupMemberModel.group_id == group_id)
                )
            )
            .scalars()
            .all()
        )
        for m in members:
            await self.member_crud.delete(ids=[m.id])

    async def add_members(self, group_id: int, member_ids: list[int]) -> None:
        group = await self._get_group_or_404(group_id)
        if group.owner_id != self._user_id:
            raise ValueError("仅群主可添加成员")
        ids = {int(uid) for uid in member_ids}
        ids.discard(self._user_id)
        if not ids:
            return
        existing = (
            (
                await self.db.execute(
                    select(ChatGroupMemberModel.user_id).where(
                        ChatGroupMemberModel.group_id == group_id,
                        ChatGroupMemberModel.user_id.in_(ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        for uid in ids - set(existing):
            await self.member_crud.create(data={"group_id": group_id, "user_id": uid})

    async def remove_members(self, group_id: int, member_ids: list[int]) -> None:
        group = await self._get_group_or_404(group_id)
        if group.owner_id != self._user_id:
            raise ValueError("仅群主可移除成员")
        members = (
            (
                await self.db.execute(
                    select(ChatGroupMemberModel).where(
                        ChatGroupMemberModel.group_id == group_id,
                        ChatGroupMemberModel.user_id.in_(member_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        for m in members:
            await self.member_crud.delete(ids=[m.id])

    async def quit_group(self, group_id: int) -> None:
        group = await self._get_group_or_404(group_id)
        me = self._user_id
        if group.owner_id == me:
            raise ValueError("群主不能退群，请解散群组或转让群主")
        member = (
            (
                await self.db.execute(
                    select(ChatGroupMemberModel).where(
                        ChatGroupMemberModel.group_id == group_id,
                        ChatGroupMemberModel.user_id == me,
                    )
                )
            )
            .scalars()
            .first()
        )
        if member is not None:
            await self.member_crud.delete(ids=[member.id])

    async def _get_group_or_404(self, group_id: int) -> ChatGroupModel:
        group = (
            (
                await self.db.execute(
                    select(ChatGroupModel).where(
                        ChatGroupModel.id == group_id, ChatGroupModel.is_deleted == False  # noqa: E712
                    )
                )
            )
            .scalars()
            .first()
        )
        if group is None:
            raise ValueError("群组不存在")
        return group
