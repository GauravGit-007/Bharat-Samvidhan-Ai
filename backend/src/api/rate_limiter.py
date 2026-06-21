import time
import threading

class TokenBucketRateLimiter:
    def __init__(self, refill_rate: float, capacity: int, daily_limit: int = 50):
        """
        refill_rate: refill rate in tokens per second (e.g. 1/15.0 for 4 RPM)
        capacity: max burst capacity (e.g. 3 tokens)
        daily_limit: max requests per rolling 24 hours
        """
        self.refill_rate = refill_rate
        self.capacity = capacity
        self.daily_limit = daily_limit
        self.buckets = {}      # IP -> (tokens, last_update_time)
        self.daily_history = {} # IP -> list of timestamps
        self.lock = threading.Lock()

    def check_limit(self, ip: str) -> tuple[bool, str]:
        with self.lock:
            now = time.time()
            
            # 1. Daily limit check (sliding window)
            one_day_ago = now - 86400
            timestamps = self.daily_history.get(ip, [])
            # Filter timestamps
            timestamps = [t for t in timestamps if t > one_day_ago]
            self.daily_history[ip] = timestamps
            
            if len(timestamps) >= self.daily_limit:
                return False, f"Daily quota limit of {self.daily_limit} cloud requests exceeded for this IP. Please try again tomorrow."
                
            # 2. Token bucket burst check
            tokens, last_update = self.buckets.get(ip, (self.capacity, now))
            
            # Calculate refills
            elapsed = now - last_update
            refill = elapsed * self.refill_rate
            new_tokens = min(self.capacity, tokens + refill)
            
            if new_tokens < 1.0:
                wait_time = int((1.0 - new_tokens) / self.refill_rate)
                # Keep it at least 1 second
                wait_time = max(1, wait_time)
                return False, f"Rate limit exceeded. Please wait {wait_time} seconds before making another request."
                
            # Deduct 1 token and update state
            self.buckets[ip] = (new_tokens - 1.0, now)
            self.daily_history[ip].append(now)
            return True, ""

# Export a single global rate limiter instance
# Refill rate of 1 token per 15s (4 requests per minute max), capacity/burst of 3 requests, daily limit of 50 requests per IP.
groq_rate_limiter = TokenBucketRateLimiter(refill_rate=1.0/15.0, capacity=3, daily_limit=50)
