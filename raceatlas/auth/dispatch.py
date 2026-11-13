"""One bounded best-effort worker per process. No raw outbox or automatic retry."""

import atexit
from collections import Counter, deque
from dataclasses import dataclass
from threading import Condition, Lock, Thread
from time import monotonic
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from raceatlas.email import EmailService

from .flows import AccountFlowSession, EmailIntent, email_intent_is_active

CAPACITY = 16
MAX_CHANNELS = 16
INTERVAL = 0.2


class DispatcherUnavailable(RuntimeError):
    def __init__(self):
        super().__init__("Email dispatcher unavailable.")


@dataclass(repr=False)
class Channel:
    manager: object
    engine: Engine
    service: EmailService
    identity: str
    closed: bool = False

    def enqueue(self, intent):
        return self.manager.enqueue(self, intent)

    def cancel_pending(self, account_id):
        return self.manager.cancel_pending(self, account_id)

    def drain(self, timeout=5):
        return self.manager.drain(self, timeout)

    def close(self, timeout=1):
        return self.manager.close_channel(self, timeout)


@dataclass(repr=False)
class _Job:
    channel: Channel
    intent: EmailIntent


def _active(job):
    try:
        with AccountFlowSession(job.channel.engine) as session:
            session.execute(select(func.set_config("statement_timeout", "3000", True)))
            session.execute(select(func.set_config("lock_timeout", "1000", True)))
            valid = email_intent_is_active(session, job.intent)
        # Context exit closes the read transaction BEFORE any provider operation.
        return valid
    except SQLAlchemyError:
        return False


class _Dispatcher:
    def __init__(self):
        self.condition = Condition()
        self.channels = {}
        self.pending = deque()
        self.active = None
        self.stopping = False
        self.last_attempt = None
        self.counts = Counter()
        self.thread = Thread(target=self._run, name="raceatlas-email", daemon=True)
        self.thread.start()

    def register(self, engine, service):
        with self.condition:
            if self.stopping or len(self.channels) >= MAX_CHANNELS:
                raise DispatcherUnavailable()
            channel = Channel(self, engine, service, str(uuid4()))
            self.channels[channel.identity] = channel
            return channel

    def enqueue(self, channel, intent):
        with self.condition:
            if (
                self.stopping
                or channel.closed
                or self.channels.get(channel.identity) is not channel
                or len(self.pending) >= CAPACITY
                or not isinstance(intent, EmailIntent)
                or intent._status != "committed"
                or not isinstance(intent.account_id, str)
                or not 1 <= len(intent.account_id) <= 64
                or any(not character.isprintable() for character in intent.account_id)
            ):
                self.counts["refused"] += 1
                return False
            self.pending.append(_Job(channel, intent))
            self.counts["queued"] += 1
            self.condition.notify_all()
            return True

    def cancel_pending(self, channel, account_id):
        with self.condition:
            keep = deque(
                job
                for job in self.pending
                if not (job.channel is channel and job.intent.account_id == account_id)
            )
            removed = len(self.pending) - len(keep)
            self.pending = keep
            self.counts["cancelled"] += removed
            self.condition.notify_all()
            return removed

    def _has_work(self, channel):
        return (self.active is not None and self.active.channel is channel) or any(
            job.channel is channel for job in self.pending
        )

    def drain(self, channel, timeout):
        deadline = monotonic() + max(0, min(timeout, 10))
        with self.condition:
            while self._has_work(channel):
                remaining = deadline - monotonic()
                if remaining <= 0:
                    return False
                self.condition.wait(remaining)
            return True

    def close_channel(self, channel, timeout):
        with self.condition:
            channel.closed = True
            self.channels.pop(channel.identity, None)
            self.pending = deque(job for job in self.pending if job.channel is not channel)
            if not self.channels:
                self.stopping = True
            self.condition.notify_all()
            stopping = self.stopping
        if stopping:
            self.thread.join(max(0, min(timeout, 10)))
            return not self.thread.is_alive()
        return self.drain(channel, timeout)

    def close_all(self, timeout=1):
        with self.condition:
            for channel in self.channels.values():
                channel.closed = True
            self.channels.clear()
            self.pending.clear()
            self.stopping = True
            self.condition.notify_all()
        self.thread.join(max(0, min(timeout, 10)))
        return not self.thread.is_alive()

    def _wait_turn(self, job):
        with self.condition:
            while not self.stopping and not job.channel.closed:
                remaining = (
                    0 if self.last_attempt is None else self.last_attempt + INTERVAL - monotonic()
                )
                if remaining <= 0:
                    return True
                self.condition.wait(remaining)
            return False

    def _run(self):
        while True:
            with self.condition:
                while not self.pending and not self.stopping:
                    self.condition.wait()
                if self.stopping:
                    return
                job = self.pending.popleft()
                self.active = job
            outcome = "dropped"
            attempted = False
            try:
                if self._wait_turn(job) and _active(job):
                    with self.condition:
                        allowed = not self.stopping and not job.channel.closed
                        if allowed:
                            attempted = True
                    if allowed:
                        job.intent.dispatch_after_commit(job.channel.service)
                        outcome = "accepted"
            except Exception:
                # Background boundary: never retain/log native exceptions or PII.
                outcome = "failed"
            finally:
                with self.condition:
                    if attempted:
                        # A completion-based gap is conservatively stronger than
                        # 0.2s between starts, including slow/error providers.
                        self.last_attempt = monotonic()
                    self.counts[outcome] += 1
                    self.active = None
                    job = None
                    self.condition.notify_all()


_registry_lock = Lock()
_dispatcher = None


def open_channel(engine, service):
    global _dispatcher
    if not isinstance(engine, Engine) or not isinstance(service, EmailService):
        raise DispatcherUnavailable()
    with _registry_lock:
        if _dispatcher is None or not _dispatcher.thread.is_alive():
            _dispatcher = _Dispatcher()
        return _dispatcher.register(engine, service)


def stop_process_dispatcher(timeout=1):
    with _registry_lock:
        manager = _dispatcher
    return True if manager is None else manager.close_all(timeout)


atexit.register(stop_process_dispatcher)
