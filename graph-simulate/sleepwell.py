import random
from constants import INTERVAL

MAX_DEFICIT_COUNT = 100
JITTER = 10

class SleepWellNode(object):
    """ SleepWellNode behaves in the following manner.
        1. When it starts, it broadcasts a beacon and reschedules a broadcast
           for INTERVAL after.
        2. Right before its broadcast (except for the first), it checks its
           neighbor map. If it is in deficit, it schedules another broadcast
           to the appropriate time between INTERVAL/2 and 3*INTERVAL/2 after.
           The current broadcast is not cancelled and is still performed.
        3. If it receives a beacon, it updates the source node's offset in the
           neighbor neighbor map. If the node does not exist in the map, it is
           added.
        4. When share is checked, it increments the deficit counter if it is in
           deficit. If the deficit count reaches MAX_DEFICIT_COUNT, offset is
           set to random for the next beacon broadcast. The deficit count
           resets to 0.
    """
    def __init__(self, node_id, pq):
        self.node_id = node_id
        self.pq = pq
        self.offset = None
        self.neighbor_map = {}
        self.links = set([])

        # State
        self.on = False
        self.my_slot = False
        self.latest_broadcast = None
        self.deficit_count = 0
        
        # Logging related
        self.log = []
        self.log.append((0, self.node_id, "init", "None"))


    def set_links(self, node_list):
        self.links = set(node_list)


    def start(self, aux):
        self.on = True
        self.broadcast()
        self.set_timer(INTERVAL)


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
        for neighbor in self.links:
            task = (neighbor.recv_callback, (self.node_id,))
            self.pq.add_task(task, now)
         
        self.latest_broadcast = now
        self.log.append((now, self.node_id, "broadcast", "None"))
        if self.my_slot:
            self.close_slot()
        self.my_slot = True


    def recv_callback(self, src):
        if not self.on:
            return
            
        self.neighbor_map[src] = self.now() % INTERVAL

        if self.my_slot:
            self.close_slot()


    def timer_callback(self, aux):
        self.broadcast()
        interval = self.adjust()
        self.set_timer(interval) 


    def set_timer(self, interval):
        task = (self.timer_callback, (None,))
        interval += random.randint(-JITTER, JITTER)
        self.pq.add_task(task,  self.now() + interval)


    def adjust(self):
        now = self.now()
        my_offset = now % INTERVAL

        nmap_offsets = self.neighbor_map.values()
        my_share = min([self.diff(o, my_offset) for o in nmap_offsets])
        target_share = self.target_share()
        if my_share - target_share > -1e-3 * INTERVAL:
            return INTERVAL

        self.log.append((now, self.node_id, "nmap", str(nmap_offsets)))
        self.log.append((now, self.node_id, "short", str((target_share -
            my_share) / INTERVAL)))

        self.deficit_count += 1
        if self.deficit_count == MAX_DEFICIT_COUNT:
            new_offset = random.randint(0, INTERVAL - 1)
            self.deficit_count = 0
            self.log.append((now, self.node_id, "reset", "None"))
        else: 
            start, end = self.largest_gap()
            half_gap = self.diff(end, start) // 2
            if half_gap > target_share:
                new_offset = self.sum(start, half_gap)
            else:
                new_offset = self.diff(end, target_share)
            
        interval = self.diff(new_offset, my_offset)
        if interval <= INTERVAL // 2:
            interval += INTERVAL

        self.log.append((now, self.node_id, "adjustment", str(new_offset)))
        return interval


    def target_share(self):
        return INTERVAL // (len(self.neighbor_map) + 1)
    

    def largest_gap(self):
        starts = sorted(self.neighbor_map.values())
        ends = starts[1:] + [starts[0]]
        gaps = [self.diff(e, s) for s, e in zip(starts, ends)]
        index = max(range(len(gaps)), key=gaps.__getitem__)
        return starts[index], ends[index]

    
    def sum(self, a, b):
        return (a + b) % INTERVAL


    def diff(self, a, b):
        return (a + INTERVAL - b) % INTERVAL

