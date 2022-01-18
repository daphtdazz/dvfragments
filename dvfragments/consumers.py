import json
import logging
from asgiref.sync import sync_to_async
from asyncio import Task

from channels.generic.websocket import AsyncWebsocketConsumer

from fgame.models import GameUser

from .notification_backend import get_backend


log = logging.getLogger(__name__)


class DVFragmentChangeNotifyingConsumer(AsyncWebsocketConsumer):
    @property
    def key(self):
        return self.scope['url_route']['kwargs'][self.view_class.pk_url_kwarg]

    @property
    def queue_name(self):
        return self.view_class.notification_queue_name

    def __init__(self, view_class):
        super().__init__()
        self.view_class = view_class
        self.streaming_task: Task = None

    async def handle_change(self, event):
        log.info(f'Change detected on {self}: {event}')
        await self.send(text_data=json.dumps(event))

    async def accept(self, **kwargs):
        await super().accept(**kwargs)
        backend = get_backend()

        await backend.subscribe(self.queue_name, self.key, self.handle_change)
        await sync_to_async(self._update_presence)(True)

    async def disconnect(self, code):
        await sync_to_async(self._update_presence)(False)
        await get_backend().unsubscribe(self.queue_name, self.key, self.handle_change)

    def _update_presence(self, present):
        gu = GameUser.objects.get(game_id=self.key, user=self.scope['user'])
        gu.connected = present
        gu.save(update_fields=['connected'])
