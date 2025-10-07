import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class UserRateLimit:
    """Tracks rate limit data for a single user"""
    requests: list = field(default_factory=list)
    last_request: float = 0
    blocked_until: float = 0


class RateLimiter:
    """Manages rate limiting for users and platform-wide concurrency"""
    
    def __init__(
        self,
        requests_per_minute: int = 5,
        requests_per_hour: int = 50,
        max_concurrent_platform: int = 200,
        cooldown_seconds: int = 0,  # Disabled by default
        block_duration_seconds: int = 300
    ):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests per user per minute
            requests_per_hour: Maximum requests per user per hour
            max_concurrent_platform: Maximum concurrent queries platform-wide
            cooldown_seconds: Minimum seconds between requests per user
            block_duration_seconds: How long to block abusive users
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.max_concurrent_platform = max_concurrent_platform
        self.cooldown_seconds = cooldown_seconds
        self.block_duration_seconds = block_duration_seconds
        
        # User-specific tracking
        self.user_limits: Dict[str, UserRateLimit] = defaultdict(UserRateLimit)
        
        # Platform-wide tracking
        self.concurrent_queries = 0
        self.concurrent_lock = asyncio.Lock()
        
        # Cleanup task
        self._cleanup_task = None
    
    def _cleanup_old_requests(self):
        """Removes old request timestamps from memory"""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        for user_id, limit_data in list(self.user_limits.items()):
            # Remove requests older than 1 hour
            limit_data.requests = [
                req_time for req_time in limit_data.requests
                if req_time > hour_ago
            ]
            
            # Remove user entry if no recent requests
            if not limit_data.requests and current_time - limit_data.last_request > 3600:
                del self.user_limits[user_id]
    
    async def start_cleanup_task(self):
        """Starts periodic cleanup of old data"""
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            self._cleanup_old_requests()
    
    def _is_blocked(self, user_id: str) -> tuple[bool, Optional[int]]:
        """
        Checks if user is currently blocked
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Tuple of (is_blocked, seconds_remaining)
        """
        limit_data = self.user_limits[user_id]
        current_time = time.time()
        
        if limit_data.blocked_until > current_time:
            seconds_remaining = int(limit_data.blocked_until - current_time)
            return True, seconds_remaining
        
        return False, None
    
    def _check_cooldown(self, user_id: str) -> tuple[bool, Optional[int]]:
        """
        Checks if user is in cooldown period
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Tuple of (in_cooldown, seconds_remaining)
        """
        # Skip cooldown check if disabled (cooldown_seconds = 0)
        if self.cooldown_seconds == 0:
            return False, None
            
        limit_data = self.user_limits[user_id]
        current_time = time.time()
        
        # Only enforce cooldown if user has made at least one request
        if limit_data.last_request > 0 and len(limit_data.requests) > 0:
            time_since_last = current_time - limit_data.last_request
            if time_since_last < self.cooldown_seconds:
                seconds_remaining = int(self.cooldown_seconds - time_since_last)
                return True, seconds_remaining
        
        return False, None
    
    def _check_rate_limits(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Checks if user has exceeded rate limits
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        limit_data = self.user_limits[user_id]
        current_time = time.time()
        
        # Remove old requests
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        recent_requests = [t for t in limit_data.requests if t > hour_ago]
        limit_data.requests = recent_requests
        
        # Check per-minute limit
        requests_last_minute = sum(1 for t in recent_requests if t > minute_ago)
        if requests_last_minute >= self.requests_per_minute:
            # Block user for repeated violations
            limit_data.blocked_until = current_time + self.block_duration_seconds
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute. You have been temporarily blocked."
        
        # Check per-hour limit
        if len(recent_requests) >= self.requests_per_hour:
            limit_data.blocked_until = current_time + self.block_duration_seconds
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour. You have been temporarily blocked."
        
        return True, None
    
    async def check_platform_capacity(self) -> tuple[bool, Optional[str]]:
        """
        Checks if platform has capacity for new query
        
        Returns:
            Tuple of (has_capacity, error_message)
        """
        async with self.concurrent_lock:
            if self.concurrent_queries >= self.max_concurrent_platform:
                return False, f"Platform is at capacity ({self.max_concurrent_platform} concurrent queries). Please try again in a moment."
            return True, None
    
    async def acquire(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Attempts to acquire permission for a new request
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Check if user is blocked
        is_blocked, block_time = self._is_blocked(user_id)
        if is_blocked:
            return False, f"You are temporarily blocked. Try again in {block_time} seconds."
        
        # Check cooldown
        in_cooldown, cooldown_time = self._check_cooldown(user_id)
        if in_cooldown:
            return False, f"Please wait {cooldown_time} seconds before making another request."
        
        # Check rate limits
        is_allowed, error = self._check_rate_limits(user_id)
        if not is_allowed:
            return False, error
        
        # Check platform capacity
        has_capacity, error = await self.check_platform_capacity()
        if not has_capacity:
            return False, error
        
        # Acquire resources
        async with self.concurrent_lock:
            self.concurrent_queries += 1
        
        # Record request
        current_time = time.time()
        limit_data = self.user_limits[user_id]
        limit_data.requests.append(current_time)
        limit_data.last_request = current_time
        
        return True, None
    
    async def release(self):
        """Releases a concurrent query slot"""
        async with self.concurrent_lock:
            if self.concurrent_queries > 0:
                self.concurrent_queries -= 1
    
    def get_user_stats(self, user_id: str) -> Dict[str, any]:
        """
        Gets current rate limit stats for a user
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Dict with user's current rate limit status
        """
        limit_data = self.user_limits[user_id]
        current_time = time.time()
        
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        recent_requests = [t for t in limit_data.requests if t > hour_ago]
        requests_last_minute = sum(1 for t in recent_requests if t > minute_ago)
        
        is_blocked, block_time = self._is_blocked(user_id)
        in_cooldown, cooldown_time = self._check_cooldown(user_id)
        
        return {
            'user_id': user_id,
            'requests_last_minute': requests_last_minute,
            'requests_last_hour': len(recent_requests),
            'remaining_minute': max(0, self.requests_per_minute - requests_last_minute),
            'remaining_hour': max(0, self.requests_per_hour - len(recent_requests)),
            'is_blocked': is_blocked,
            'block_seconds_remaining': block_time,
            'in_cooldown': in_cooldown,
            'cooldown_seconds_remaining': cooldown_time
        }
    
    def get_platform_stats(self) -> Dict[str, any]:
        """
        Gets platform-wide statistics
        
        Returns:
            Dict with platform rate limit status
        """
        return {
            'concurrent_queries': self.concurrent_queries,
            'max_concurrent': self.max_concurrent_platform,
            'available_slots': max(0, self.max_concurrent_platform - self.concurrent_queries),
            'active_users': len(self.user_limits),
            'utilization_percent': round((self.concurrent_queries / self.max_concurrent_platform) * 100, 2)
        }