from channels.generic.websocket import AsyncWebsocketConsumer


class DVFragmentChangeNotifyingConsumer(AsyncWebsocketConsumer):
    def __init__(self, view_class):
        super().__init__()
        self.view_class = view_class

    async def connect(self):
        await super().connect()
