import time

class CircuitBreaker:
    def __init__(self):
        self.door_status = "CLOSED"        # "CLOSED", "OPEN", "HALF_OPEN"
        self.troublemaker_tally = 0         # scratch marks
        self.rule = 3                       # lock after 3 troublemakers
        self.time_i_locked_the_door = None  # when did I lock it?
        self.wait_time = 5                  # seconds before cracking the door

    def call(self, func):
        # Check door status and decide what to do
        # If you let someone through, try calling func()
        # Handle success (Part A) and failure (Part B)
        if self.door_status == "CLOSED":
            try:
                result = func()
            except:
                raise Exception("")

            return func()
        
        if time.time() - self.time_i_locked_the_door == self.wait_time:
            self.door_status = "HALF_OPEN"
        
        if self.door_status == "HALF_OPEN":
            try:
                result = func()
                self.door_status = "CLOSED"
            except:
                self.door_status = "OPEN"
        
        self.troublemaker_tally += 1
        if self.troublemaker_tally >= self.rule:
            self.door_status = "OPEN"
            self.time_i_locked_the_door = time.time()
            return "ERROR - DOOR IS CLOSED"

breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

def unreliable_api():
    """Simulates the Claude API. Works at first, then starts failing."""
    global call_count
    call_count += 1
    
    if call_count > 5:
        # API is "down" — takes 3 seconds to timeout, then fails
        time.sleep(3)
        raise Exception("503 Service Unavailable")
    
    # API is healthy — responds in 100ms
    time.sleep(0.1)
    return "Here is your generated passage about quantum physics..."


def handle_user_request(user_id):
    start = time.time()
    try:
        result = breaker.call(unreliable_api)  # Bouncer wraps the API
        elapsed = time.time() - start
        print(f"  User {user_id}: ✅ Got passage in {elapsed:.1f}s")
    except Exception as e:
        elapsed = time.time() - start        
        print(f"  User {user_id}: ❌ Failed after {elapsed:.1f}s — {e}")