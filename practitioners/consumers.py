# practitioners/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

from practitioners.models import Conversation, Message
from channels.db import database_sync_to_async
from .models import Conversation, Message
from clients.models import Client 

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'video_call_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        message = json.loads(text_data)
        
        # Send message to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video_call_message',
                'message': message,
                'sender_channel_name': self.channel_name
            }
        )

    # Receive message from room group
    async def video_call_message(self, event):
        message = event['message']
        sender_channel_name = event['sender_channel_name']

        # Only send the message to the WebSocket if it's not the original sender
        if self.channel_name != sender_channel_name:
            await self.send(text_data=json.dumps(message))

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.client = self.scope.get("client")
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'

        # --- START DEBUG LOGGING ---
        print("--- [DEBUG] WebSocket Connection Attempt ---")
        print(f"Trying to connect to conversation_id: {self.conversation_id}")
        print(f"User from scope: {self.user} (Authenticated: {self.user.is_authenticated})")
        print(f"Client from scope: {self.client}")
        # --- END DEBUG LOGGING ---

        is_authorized = await self.check_authorization()
        if not is_authorized:
            print(f"--- [DEBUG] Authorization FAILED for conversation {self.conversation_id}. Closing connection.")
            await self.close(code=403)
            return

        print(f"--- [DEBUG] Authorization SUCCEEDED for conversation {self.conversation_id}. Accepting connection.")
        await self.channel_layer.group_add(self.conversation_group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'user_status',
                'status': 'online',
                'user_type': 'practitioner' if self.user and not self.client else 'client'
            }
        )

    @database_sync_to_async
    def check_authorization(self):
        # This method now includes its own logging
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            conv_practitioner_user = conversation.practitioner.user

            print(f"--- [DEBUG] Auth Check for Conv {self.conversation_id} ---")
            print(f"DB Practitioner User: {conv_practitioner_user}")
            print(f"Comparing with Scope User: {self.user}")

            if self.client:
                return conversation.client == self.client
            if self.user and self.user.is_authenticated:
                is_match = (conv_practitioner_user == self.user)
                print(f"Comparison result: {is_match}")
                return is_match
            return False
        except Conversation.DoesNotExist:
            print(f"--- [DEBUG] Conversation {self.conversation_id} DoesNotExist.")
            return False

    # ... (the rest of the consumer can remain the same) ...
    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'user_status',
                'status': 'offline',
                'user_type': 'practitioner' if self.user and not self.client else 'client'
            }
        )
        await self.channel_layer.group_discard(
            self.conversation_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message', '')
        attachment_url = data.get('attachment_url', None)
        sender_type = 'practitioner' if self.user and not self.client else 'client'
        message = await self.save_message(message_content, sender_type, attachment_url)
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender_type': sender_type,
                'attachment_url': message.attachment.url if message.attachment else None,
                'timestamp': message.timestamp.isoformat()
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'content': event['message'],
            'sender_type': event['sender_type'],
            'attachment_url': event.get('attachment_url')
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'status',
            'status': event['status'],
            'user_type': event['user_type']
        }))

    @database_sync_to_async
    def save_message(self, content, sender_type, attachment_url=None):
        return Message.objects.create(
            conversation_id=self.conversation_id,
            content=content,
            sender_type=sender_type
        )
