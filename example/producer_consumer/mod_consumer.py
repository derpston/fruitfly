# Example consumer module, receives messages from another module.
import fruitfly

class consumer(fruitfly.Module):
    @fruitfly.event("test.*")
    def handler(self, event, payload):
        self.logger.info("Got event %s with payload %s", event, payload)
