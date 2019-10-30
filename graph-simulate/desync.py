import random
from constants import INTERVAL

JITTER = 10
ALPHA = 50

class DesyncNode(object):
    """ DESYNC Node behaves in the following manner.
    1. When it starts, it broadcasts a beacon and reschedules a broadcast for
       INTERVAL after.
    2. Any reception before its first broadcast is ignored.
    3. If it broadcasts, it sets the fired variable to true. It reschedules a
       broadcast for INTERVAL after.
    4. If it receives a beacon, it first checks the fired variable.
    5. If the fired variable is false, it updates the prev variable that keeps
       track of the time difference between itself and its predecessor.
    6. If the fired variable is true, it calculates the time difference between
       its successor and itself. It adjusts its offset towards the midpoint of
       its predecessor and its successor. It delays the next broacast based on
       this adjustment. Lastly, the fired variable is set to false.
    """
    def __init__(self, node_id, pq):
        self.node_id = node_id
        self.pq = pq
        self.neighbor_map = {}
        self.links = set([])

        # State
        self.on = False
        self.fired = False
        self.prev = None
        self.time_task = None
        self.latest_broadcast = None
        self.next_broadcast = None

        # Logging related
        self.log = []
        self.log.append((0, self.node_id, "init", "None"))


    def set_links(self, node_list):
        self.links = set(node_list)


    def start(self, aux):
        self.on = True
        self.broadcast()
        self.set_timer(INTERVAL)
        self.next_broadcast = self.now() + INTERVAL


    def now(self):
        return self.pq.current


    def close_slot(self):
        now = self.now()
        target_share = self.target_share()
        my_share = now - self.latest_broadcast
        deficit = (target_share - my_share) / target_share
        self.log.append((now, self.node_id, "deficit", str(deficit)))
        self.fired = False


    def broadcast(self):
        now = self.now() 
        for neighbor in self.links:
            task = (neighbor.recv_callback, (self.node_id,))
            self.pq.add_task(task, now)
        
        self.log.append((now, self.node_id, "broadcast", "None"))
        if self.fired:
            self.close_slot()
        self.fired = True
        self.latest_broadcast = now


    def recv_callback(self, src):
        if not self.on:
            return
        
        now = self.now()
        self.neighbor_map[src] = now % INTERVAL

        if self.fired:
            self.close_slot()
            _next = now - self.latest_broadcast
            _prev = INTERVAL - _next if self.prev is None else self.prev
            adjustment = ALPHA * (_next - _prev) // 200
            self.log.append((now, self.node_id, "adjust", adjustment/INTERVAL))
            self.set_timer(self.next_broadcast + adjustment - now) 
        else:
            my_offset = self.next_broadcast % INTERVAL
            your_offset = now % INTERVAL
            self.prev = (my_offset + INTERVAL - your_offset) % INTERVAL
            #self.prev = self.next_broadcast - now


    def timer_callback(self, aux):
        self.broadcast()
        self.set_timer(INTERVAL)
        self.next_broadcast = self.now() + INTERVAL
   

    def set_timer(self, interval):
        self.timer_task = (self.timer_callback, (None,))
        interval += random.randint(-JITTER, JITTER)
        self.pq.add_task(self.timer_task, self.now() + interval)


    def target_share(self):
        return INTERVAL // (len(self.neighbor_map) + 1)
