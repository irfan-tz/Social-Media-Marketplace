import json
import time
from collections import defaultdict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.html import escape
from django.db.models import Q

message_counts = defaultdict(lambda: {"count": 0, "reset_time": time.time()})
MAX_MESSAGES = 10  # Max messages per 10 seconds
RATE_LIMIT_WINDOW = 10

class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close(code=4001)
            return

        self.user = self.scope['user']
        self.user_id = getattr(self.user, 'id', None)

        # For anonymous users, accept but don't create a room
        if self.user.is_anonymous:
            await self.accept()
            return

        # For authenticated users, create a personal room
        self.room_name = f"user_{self.user_id}"

        # Join personal room
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

        # Accept the connection
        await self.accept()

    async def disconnect(self, close_code):
        # Only leave room if we actually joined one (authenticated user)
        if hasattr(self, 'room_name') and hasattr(self, 'channel_layer'):
            try:
                await self.channel_layer.group_discard(
                    self.room_name,
                    self.channel_name
                )
            except Exception as e:
                pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "")

            # Special case: handle authentication messages
            if message_type == "authenticate":
                return

            # Handle ping messages
            if message_type == "ping":
                await self.send(text_data=json.dumps({
                    "type": "ping",
                    "message": "pong"
                }))
                return

            # Reject messages from anonymous users
            if self.user.is_anonymous:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "Authentication required"
                }))
                return

            if message_type == "chat_message":
                # Rate limiting check
                current_time = time.time()
                if not hasattr(self, 'user_id'):
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Authentication required for messaging"
                    }))
                    return

                # Reset counter if time window has passed
                if current_time - message_counts[self.user_id]["reset_time"] > RATE_LIMIT_WINDOW:
                    message_counts[self.user_id] = {"count": 0, "reset_time": current_time}

                # Check rate limit
                if message_counts[self.user_id]["count"] >= MAX_MESSAGES:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Rate limit exceeded. Please try again shortly."
                    }))
                    return

                # Increment counter
                message_counts[self.user_id]["count"] += 1

                receiver_id = data.get("receiver_id")
                content = data.get("message", "")

                # Message length validation
                if len(content) > 5000:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Message too long (maximum 5000 characters)"
                    }))
                    return

                # Validate friend relationship
                from django.contrib.auth.models import User
                from myapp.models import Friendship

                if not await self.are_friends(self.user_id, receiver_id):
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "You can only message friends"
                    }))
                    return

                # Save the message to database
                from myapp.models import Message
                message = await self.save_message(
                    sender_id=self.user_id,
                    receiver_id=receiver_id,
                    content=escape(content)
                )

                # Send to sender's channel
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        "type": "chat_message",
                        "message": {
                            "id": message.id,
                            "sender_id": self.user_id,
                            "sender_username": self.user.username,
                            "receiver_id": receiver_id,
                            "content": content,
                            "timestamp": message.timestamp.isoformat()
                        }
                    }
                )

                # Send to receiver's channel
                receiver_room = f"user_{receiver_id}"
                await self.channel_layer.group_send(
                    receiver_room,
                    {
                        "type": "chat_message",
                        "message": {
                            "id": message.id,
                            "sender_id": self.user_id,
                            "sender_username": self.user.username,
                            "receiver_id": receiver_id,
                            "content": content,
                            "timestamp": message.timestamp.isoformat()
                        }
                    }
                )
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            }))

    async def chat_message(self, event):
        # Send message to WebSocket client
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        from django.contrib.auth.models import User
        from myapp.models import Message

        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        # If content is empty, use an empty string instead of None
        actual_content = content if content else ""

        message = Message(
            sender=sender,
            receiver=receiver,
            content=actual_content
        )
        message.save()
        return message

    @database_sync_to_async
    def are_friends(self, user_id, other_user_id):
        from myapp.models import Friendship
        from django.db.models import Q

        return Friendship.objects.filter(
            status='accepted'
        ).filter(
            (Q(sender_id=user_id) & Q(receiver_id=other_user_id)) |
            (Q(sender_id=other_user_id) & Q(receiver_id=user_id))
        ).exists()
