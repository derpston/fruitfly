[![pypi](https://pypip.in/v/fruitfly/badge.svg?style=flat)](https://pypi.python.org/pypi/fruitfly)

Fruitfly
========
Python framework for minimalist, modular, event-driven embedded applications.


Architecture
============
Fruitfly is intended to be used in embedded systems where fault tolerance and low overheads are desirable properties.

The user is encouraged to create a series of small modules with clear responsibilities, and to pass events between these modules. A module can register to have several callbacks at varying intervals, and to be notified when another module sends an event matching a pattern.


Features
========
* Takes care of logging (syslog, stderr) and configuration. (one YAML file)
* Simple module loading.
* Easy event handler registration, with glob syntax. (match events like foo.*)
* Module crash detection and retrying, with execution frequency backoff after an uncaught exception.
* Supports python 2 and 3.
* Only one non-stdlib dependency, ```yaml```


Intended use
============
It is hoped that Fruitfly will be a useful base to build upon for projects like:
* In-car entertainment or data logging.
* Interactive/installation art.
* Home automation, perhaps as a lighting controller.


Examples
========
```yaml
# A simple YAML configuration file defining two modules.
modules:
  producer:
    message: foo
  consumer:
```
```python
# Example producer module, sends an event every second.
import fruitfly

class producer(fruitfly.Module):
    @fruitfly.repeat(1)
    def everysecond(self):
      self.send_event("test.bar", (123, self.config['message']))
```
```python
# Example consumer module, receives messages from another module.
import fruitfly

class consumer(fruitfly.Module):
    @fruitfly.event("test.*")
    def handler(self, event, payload):
        self.logger.info("Got event %s with payload %s", event, payload)
```
```
# An example session.
/home/user/fruitfly/example/producer_consumer $ python -m fruitfly
fruitfly[3724] INFO fruitfly Using /home/user/fruitfly/example/producer_consumer to find config and modules.
fruitfly[3724] INFO fruitfly Loaded config from /home/user/fruitfly/example/producer_consumer/fruitfly.yaml
fruitfly[3724] INFO fruitfly Loading modules from /home/user/fruitfly/example/producer_consumer/mod_*.py
fruitfly[3724] DEBUG fruitfly Loading module consumer from /home/user/fruitfly/example/producer_consumer/mod_consumer.py with config None
fruitfly[3724] INFO fruitfly Enabled module consumer
fruitfly[3724] DEBUG fruitfly Loading module producer from /home/user/fruitfly/example/producer_consumer/mod_producer.py with config {'message': 'foo'}
fruitfly[3724] INFO fruitfly Enabled module producer
fruitfly[3724] DEBUG producer event: test.bar '(123, 'foo')'
fruitfly[3724] DEBUG fruitfly Distributing event test.bar '(123, 'foo')'
fruitfly[3724] INFO consumer Got event test.bar with payload (123, 'foo')
fruitfly[3724] DEBUG producer event: test.bar '(123, 'foo')'
fruitfly[3724] DEBUG fruitfly Distributing event test.bar '(123, 'foo')'
fruitfly[3724] INFO consumer Got event test.bar with payload (123, 'foo')
```

Crash behaviour
===============
When a module raises an exception handling an event, it is logged:
```
fruitfly[4247] ERROR consumer handler handling test.bar event with payload '(123, 'foo')' crashed: ZeroDivisionError('float division by zero',)
```
... but the event handler remains registered for future events.

When a repeatedly called function raises an exception, it is logged and the next run delayed:
```
fruitfly[4283] ERROR producer everysecond crashed: ZeroDivisionError('float division by zero',) (next run delayed by 5.00s)
```

The objective is to allow users to easily write robust systems that won't need a restart or fiddling to get back to normal operation.


TODO
====
* Tests.
* Continuous integration.
* Debian packaging with an init script.


Bugs
====
* Probably!


Contributing
============
Contributions are welcome. Open an issue or send a pull request.


License
=======
See LICENSE file.
