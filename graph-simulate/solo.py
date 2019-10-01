import random
from constants import INTERVAL

JITTER = 10
ALPHA = 50

class SoloNode(object):
    """ Solo Node behaves in the following manner.
        1. When it starts, it broadcasts a beacon and reschedules a broadcast
           for INTERVAL after.
        2. Any reception before its first broadcast is ignored.
        3. Whenever it broadcasts, it sends is node id and degree.
        4. If it receives a beacon, it updates the source node's offset in the
           neighbor map. If the node does not exist in the map, it is added.
        5. After the sender node's offset is updated, it checks the offset
           distance between the sender's offset and its offset. If the sender
           has a deficit, the node (the receiver) reschedules the pending
           broadcast with a delay between 0 and INTERVAL/2.
    """
    def __init__(self, node_id, pq):
        self.node_id = node_id
        self.pq = pq
        self.neighbor_map = {}
        self.links = set([])

        # State
        self.on = False
        self.my_slot = False
        self.latest_broadcast = None
        self.next_broadcast = None
        self.timer_task = None
        
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
        self.my_slot = False

    
    def broadcast(self):
        now = self.now()
        degree = len(self.neighbor_map)
        for neighbor in self.links:
            task = (neighbor.recv_callback, (self.node_id, degree))
            self.pq.add_task(task, now)
         
        self.latest_broadcast = now
        self.log.append((now, self.node_id, "broadcast", "None"))
        if self.my_slot:
            self.close_slot()
        self.my_slot = True


    def recv_callback(self, src, deg):
        if not self.on:
            return

        if self.my_slot:
            self.close_slot()
        
        now = self.now()
        self.neighbor_map[src] = now % INTERVAL
        delay = self.adjust(deg)
        if delay > 0:
            self.next_broadcast = self.next_broadcast + delay
            self.set_timer(self.next_broadcast - now)


    def timer_callback(self, aux):
        self.broadcast()
        self.set_timer(INTERVAL)
        self.next_broadcast = self.now() + INTERVAL


    def set_timer(self, interval):
        self.timer_task = (self.timer_callback, (None,))
        interval += random.randint(-JITTER, JITTER)
        self.pq.add_task(self.timer_task, self.now() + interval)


    def adjust(self, your_degree): 
        now = self.now() 
        next_bc = self.next_broadcast

        target_share = INTERVAL // (max(your_degree, 1) + 1)
        your_share = next_bc - now
        if your_share - target_share > -1e-3 * INTERVAL:
            return 0 
        
        target_bc = now + target_share
        new_bc = (next_bc * (100 - ALPHA) + target_bc * ALPHA) // 100
        return new_bc - next_bc


    def target_share(self):
        return INTERVAL // (len(self.neighbor_map) + 1)
    def target_share(self):
        return INTERVAL // (len(self.neighbor_map) + 1)
