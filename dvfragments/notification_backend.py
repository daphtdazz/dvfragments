import asyncio
import atexit
import logging
from asyncio import FIRST_COMPLETED, Queue, create_task, sleep, wait
from queue import Queue as ThreadSafeQueue
from typing import Any, Callable, Dict, List, Tuple

from lib.utils import Singleton


log = logging.getLogger(__name__)


STOP = Singleton('StopSentry')


class DVFragmentsNotificationBackend:
    """This was designed with kafka in mind."""

    # ----------------------------------------------------------------------------------------------
    # Instance API
    # ----------------------------------------------------------------------------------------------
    def __init__(self):
        self.subscription_loop_task = None  # create_task(self.subscription_loop())
        self.subscriptions: Dict[Tuple[str, Any], List[Callable]] = {}

        atexit.register(self.atexit)

    async def subscribe(self, queue_name, key, callback_coro):
        cbks_by_id = self.subscriptions.setdefault(queue_name, {})
        callbacks = cbks_by_id.setdefault(key, [])
        callbacks.append(callback_coro)

        if not any(cbk != callback_coro for cbks in cbks_by_id.values() for cbk in cbks):
            # first stop the subscribe loop if it was running
            if self.subscription_loop_task is not None:
                self.subscription_loop_task.cancel()
                self.subscription_loop_task = None

            await self.update_queue_subscriptions()

        self.subscription_loop_task = create_task(self.subscription_loop())

    async def unsubscribe(self, queue_name, key, callback_coro):
        self.subscriptions[queue_name][key].remove(callback_coro)
        if len(self.subscriptions[queue_name][key]) == 0:
            pass

    # ----------------------------------------------------------------------------------------------
    # Subclasses to implement
    # ----------------------------------------------------------------------------------------------
    async def get_next_notification(self) -> Tuple[str, dict]:
        """
        Returns the name of the queue that had the next notification and the event, which subclasses
        should ensure is a dictionary which includes at least a key called "key" which will
        correspond to one of the keys in the self.subscriptions dictionary
        """
        raise NotImplementedError('Implement in subclasses')

    async def notify(self, queue_name, event):
        raise NotImplementedError('Implement in subclasses')

    async def update_queue_subscriptions(self):
        """
        Should get the queues we should be subscribed to and subscribe to them as necessary.
        """
        raise NotImplementedError('Implement in subclasses')

    def atexit(self):
        """Subclasses may override this but they should call super()"""
        if self.subscription_loop_task:
            self.subscription_loop_task.cancel()

    # ----------------------------------------------------------------------------------------------
    # Internal
    # ----------------------------------------------------------------------------------------------
    async def subscription_loop(self):
        while True:
            queue_names = list(self.subscriptions)
            log.info('subscription loop on queues %s', queue_names)
            if len(queue_names) == 0:
                # i.e. we haven't been subscribed yet. We will be kicked if the subscription changes
                await sleep(10)
                continue
            queue_name, next_event = await self.get_next_notification()
            key = next_event['key']

            cbks = self.subscriptions[queue_name].get(key, [])
            for cbk in cbks:
                await cbk(next_event)


class QueueBasedNotificationBackend(DVFragmentsNotificationBackend):
    """
    This backend is only appropriate when there is a single instance serving all requests, i.e.
    when developing and running manage.py runserver, because the queues are held in the memory of
    the server process.
    """

    def __init__(self):
        super().__init__()
        self.queues: Dict[str, Queue] = {}
        self.internal_queue = ThreadSafeQueue()
        self.internal_queue_monitoring_task = None

    async def get_next_notification(self):
        tasks_to_name = {
            create_task(queue.get(), name=f'Get next from queue {name}'): name
            for name, queue in self.queues.items()
        }
        log.info('getting next notification from %s', list(tasks_to_name.values()))
        done, _ = await wait(tasks_to_name.keys(), return_when=FIRST_COMPLETED)
        assert len(done) == 1
        task = list(done)[0]
        task_name = tasks_to_name[task]
        log.info('Got a notification %s', task_name)
        return tasks_to_name[task], task.result()

    async def notify(self, queue_name, event):
        assert isinstance(event, dict)
        log.info('putting event on internal queue %d for %s', id(self.internal_queue), queue_name)
        self.internal_queue.put((queue_name, event))

    async def update_queue_subscriptions(self):
        if self.internal_queue_monitoring_task is None:
            self.internal_queue_monitoring_task = create_task(self._monitor_internal_queue())

        # first remove old queues
        for qname, queue in dict(self.queues).items():
            if not any(
                coro
                for coros_by_id in self.subscriptions.get(qname, {}).values()
                for coros in coros_by_id.values()
                for coro in coros
            ):
                log.info('No longer subscribed to queue %s', qname)
                del self.queues[qname]

        # now add new ones
        for qname in self.subscriptions:
            if qname in self.queues:
                continue

            self.queues[qname] = Queue()

        log.info('Now subscribed to queues %s', list(self.queues.keys()))

    def atexit(self):
        super().atexit()
        self.internal_queue.put(STOP)

    def _get_next_internal_queue_item(self):
        log.info(
            'getting from internal queue %d', id(self.internal_queue),
        )
        item = self.internal_queue.get()
        log.info('Got item from internal queue %s', item)
        return item

    async def _monitor_internal_queue(self):
        loop = asyncio.get_running_loop()
        while True:
            item = await loop.run_in_executor(None, self._get_next_internal_queue_item)
            if item is STOP:
                break
            (queue_name, event) = item
            queue = self.queues.get(queue_name)
            if queue is None:
                log.info('Queue %s no longer exists, event dropped', queue_name)
                continue
            log.info('Putting event on queue %d', id(queue))
            await queue.put(event)


class KafkaNotificationBackend(DVFragmentsNotificationBackend):
    def __init__(self):
        pass

        # should be able to use consumer.poll(timeout=float('inf')) via loop.run_in_executor()


_queue_based_backend = QueueBasedNotificationBackend()


def get_backend() -> DVFragmentsNotificationBackend:
    return _queue_based_backend
