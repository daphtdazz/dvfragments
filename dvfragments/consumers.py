import json
import logging
from asyncio import Task

from channels.generic.websocket import AsyncWebsocketConsumer

from .notification_backend import get_backend


log = logging.getLogger(__name__)


class DVFragmentChangeNotifyingConsumer(AsyncWebsocketConsumer):
    def __init__(self, view_class):
        super().__init__()
        self.view_class = view_class
        self.streaming_task: Task = None

    async def handle_change(self, event):
        log.info(f'Change detected on {self}: {event}')
        await self.send(text_data=json.dumps(event))

    async def accept(self, **kwargs):
        await super().accept(**kwargs)
        key = self.scope['url_route']['kwargs'][self.view_class.pk_url_kwarg]

        backend = get_backend()

        queue_name = self.view_class.notification_queue_name
        await backend.subscribe(queue_name, key, self.handle_change)
        await backend.notify(
            queue_name, {'key': key, 'action': 'onpage', 'user': str(self.scope['user'].id)}
        )

        # in order to get presence working: need to set presence on game user, then trigger
        # fragment to reload.
