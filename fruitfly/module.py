import time
import heapq
import logging
import fnmatch
import threading
import collections
# Py2 vs 3 compatibility.
try:
    import queue
except ImportError:
    import Queue as queue

scheduled_functions = collections.defaultdict(list)
event_handlers = collections.defaultdict(list)

# Functions that crash will have their next invocation delayed by this
# long, but only if they run more frequently than this anyway.
default_crashpenalty = 5.0

# This is a magic hacky variable that will be set by the module loader
# in fruitfly.py just before it loads a new copy of each module.
# We only need to care about this when loading multiple copies of the
# same module. See fruitfly.py's module loader for a more detailed comment.
current_modname = None

class repeat:
    """Decorator for repeatedly calling a function in a fruitfly module
    at a regular interval."""
    def __init__(self, interval):
        self._interval = float(interval)

    def __call__(self, func):
        # Add this function to the schedule.
        heapq.heappush(scheduled_functions[current_modname], (time.time() + self._interval, (func, self._interval)))

        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapped

class event:
    """Decorator for registering a function in a fruitfly module as a
    handler for events."""
    def __init__(self, spec):
        self._spec = spec

    def __call__(self, func):
        # Add this function to the event handlers.
        event_handlers[current_modname].append((self._spec, func))

        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapped

class Module(threading.Thread): 
    def __init__(self, parent_app, modname, config):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        
        self._parent_app = parent_app
        self._modname = modname
        self.config = config
        self.logger = logging.getLogger(self._modname)

        self._eventqueue = queue.Queue(maxsize = 1000)

        if getattr(self, "init", None):
            # If an init function exists, run it.
            try:
                self.init()
            except Exception as ex:
                self.logger.error("init crashed: %s (module disabled)", repr(ex))
                return

        self.start()

    def _observe_event(self, event, payload):
        self._eventqueue.put_nowait((event, payload))

    def run(self):
        while True:
            # Find out which function is scheduled next.
            try:
                (target_time, (func, interval)) = scheduled_functions[self._modname][0]
            except IndexError:
                # No scheduled functions. Set an event timeout of 100ms to prevent busy spinning.
                target_time = time.time() + 0.1
                func = None

            # Sleep until it is due to be invoked.
            timedelta = target_time - time.time()
            if timedelta > 0:
                try:
                    (event, payload) = self._eventqueue.get(timeout = timedelta)

                    # Find and execute all handlers for this event.
                    for (spec, handler) in event_handlers[self._modname]:
                        if fnmatch.fnmatch(event, spec):
                            try:
                                handler(self, event, payload)
                            except Exception as ex:
                                self.logger.error("%s handling %s event with payload '%s' crashed: %s", handler.__name__, event, payload, repr(ex))

                    continue
                except queue.Empty:
                    pass

            if func is None:
                continue

            heapq.heappop(scheduled_functions[self._modname])

            # Invoke it.
            crashpenalty = 0
            try:
                func(self)
            except Exception as ex:
                # Delay the next execution by some amount if it is scheduled
                # more frequently than the penalty amount.
                if interval < default_crashpenalty:
                    crashpenalty = default_crashpenalty

                self.logger.error("%s crashed: %s (next run delayed by %2.2fs)", func.__name__, repr(ex), crashpenalty)

            # Re-schedule it by putting it back on the heap.
            heapq.heappush(scheduled_functions[self._modname], (time.time() + interval + crashpenalty, (func, interval)))

    def send_event(self, event, payload = None):
        """Pass an event (with optional payload) up to the parent fruitfly
        instance so that it can be distributed to other modules."""
        self.logger.debug("event: %s '%s'", event, repr(payload))
        self._parent_app.send_event(event, payload)
