"""
A basic fruitfly module. Sends an event once per second, and receives the same event.
"""

import fruitfly

class example(fruitfly.Module):
    def init(self):
        self.onesecond()

    @fruitfly.repeat(1)
    def onesecond(self):
        self.logger.info("Sending an event")
        self.send_event("foo.omg", ['test'])

    @fruitfly.event('foo.*')
    def foohandler(self, event, payload):
       self.logger.info("event handler for foo got %s, %s", event, repr(payload))

