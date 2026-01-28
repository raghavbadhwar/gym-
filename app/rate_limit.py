from fastapi import Request, HTTPException, status
from time import time
from collections import deque
from typing import Dict

class RateLimiter:
    """
    Simple in-memory rate limiter based on sliding window.
    """
    def __init__(self, requests: int = 10, window: int = 60):
        self.requests = requests
        self.window = window
        self.clients: Dict[str, deque] = {}

    async def __call__(self, request: Request):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        now = time()

        if client_ip not in self.clients:
            self.clients[client_ip] = deque()

        history = self.clients[client_ip]

        # Remove old timestamps (those older than window)
        while history and history[0] <= now - self.window:
            history.popleft()

        # Check if limit exceeded
        if len(history) >= self.requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

        # Record this request
        history.append(now)
        return True
