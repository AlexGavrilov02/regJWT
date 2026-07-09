import time
from collections import defaultdict
from typing import Dict, Tuple

from config import settings


class BruteForceProtection:
    def __init__(self):
        self.attempts: Dict[str, list] = defaultdict(list)

    def check_attempt(self, identifier: str) -> bool:
        now = time.time()
        window_start = now - settings.LOCKOUT_TIME_SECONDS

        self.attempts[identifier] = [
            t for t in self.attempts[identifier] if t > window_start
        ]

        if len(self.attempts[identifier]) >= settings.MAX_LOGIN_ATTEMPTS:
            return False
        return True

    def record_attempt(self, identifier: str):
        self.attempts[identifier].append(time.time())

    def reset_attempts(self, identifier: str):
        self.attempts[identifier] = []


brute_force_protection = BruteForceProtection()