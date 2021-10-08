import uuid
import os
from enum import Enum, auto
from threading import Thread
from time import sleep
import threading

class QueueException(Exception):
    pass

class STATUS(Enum):
    TODO = auto()
    STARTED = auto()
    DONE = auto()
    FAILED = auto()

class QueueWorker:
    def run():
        pass

class Queue:
    queue = []

    results = {}
    running = False
    worker = None

    def event_loop(self):
        # NOTE Jax requires using the context of the thread. 
        # Creating the worker within this context allows the user of 
        # this Queue to define their requirements in their QueueWorker
        self.worker: QueueWorker = self._worker_class()
        self.running = True
        while self.running:
            if self.queue:
                job = self.queue.pop()
                job()

            else:
                sleep(2) 

    def __start_event_loop(self):       
        
        event_loop = self.event_loop
        t = Thread(target=event_loop, args=())
        t.start()

    def __init__(self, worker_class):
        self._worker_class = worker_class
    
    def stop(self):
        self.running = False

    def start(self):
        self.__start_event_loop()


    def get_result(self, base_key):
        if base_key in self.results:
            return str(self.results[base_key]['result'])
        else:
            raise QueueException("Invalid basekey!")

    def push(self, data) -> str:
        base_key = str(uuid.uuid4())
        self.results[base_key] = {
            'status': STATUS.TODO,
            'result': None
        }
        def job():
            print(f"Starting work on {base_key}")
            self.results[base_key]['status'] = STATUS.STARTED
            try:
                self.results[base_key]['result'] = self.worker.run(data)
                self.results[base_key]['status'] = STATUS.DONE
            except Exception as e:
                print(f"Ran into an exception {e}")
                self.results[base_key]['status'] = STATUS.FAILED
        self.queue.append(job)
        return base_key


    def get_status(self, base_key) -> str:
        print(self.results)
        return str(self.results[base_key]['status'])


