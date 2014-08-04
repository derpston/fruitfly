# Example producer module, sends an event every second.
import fruitfly

class producer(fruitfly.Module):
    @fruitfly.repeat(1)
    def everysecond(self):
      self.send_event("test.bar", (123, self.config['message']))
