import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path


class CacheManager:
    """Manages caching of video summaries"""
    
    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 168):  # 7 days default
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Creates cache directory if it doesn't exist"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, video_id: str) -> str:
        """
        Generates a cache key from video ID
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Hashed cache key
        """
        return hashlib.sha256(video_id.encode()).hexdigest()
    
    def _get_cache_path(self, video_id: str) -> Path:
        """
        Gets the file path for a cached summary
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to cache file
        """
        cache_key = self._get_cache_key(video_id)
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_expired(self, timestamp: str) -> bool:
        """
        Checks if a cache entry has expired
        
        Args:
            timestamp: ISO format timestamp string
            
        Returns:
            True if expired, False otherwise
        """
        try:
            cached_time = datetime.fromisoformat(timestamp)
            expiry_time = cached_time + timedelta(hours=self.ttl_hours)
            return datetime.now() > expiry_time
        except Exception:
            return True
    
    def get(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a cached summary if available and not expired
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Cached summary dict or None if not found/expired
        """
        cache_path = self._get_cache_path(video_id)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if expired
            if self._is_expired(data.get('timestamp', '')):
                # Remove expired cache
                cache_path.unlink()
                return None
            
            return data
        
        except Exception as e:
            # If there's any error reading cache, remove it
            if cache_path.exists():
                cache_path.unlink()
            return None
    
    def set(self, video_id: str, summary: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Stores a summary in cache
        
        Args:
            video_id: YouTube video ID
            summary: Generated summary text
            metadata: Optional metadata to store with summary
        """
        cache_path = self._get_cache_path(video_id)
        
        cache_data = {
            'video_id': video_id,
            'summary': summary,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Silently fail on cache write errors
            pass
    
    def clear(self, video_id: Optional[str] = None):
        """
        Clears cache entries
        
        Args:
            video_id: If provided, clears only this video's cache. Otherwise clears all.
        """
        if video_id:
            cache_path = self._get_cache_path(video_id)
            if cache_path.exists():
                cache_path.unlink()
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Returns statistics about the cache
        
        Returns:
            Dict with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        valid_count = 0
        expired_count = 0
        
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if self._is_expired(data.get('timestamp', '')):
                        expired_count += 1
                    else:
                        valid_count += 1
            except Exception:
                expired_count += 1
        
        return {
            'total_entries': len(cache_files),
            'valid_entries': valid_count,
            'expired_entries': expired_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
    
    def cleanup_expired(self) -> int:
        """
        Removes all expired cache entries
        
        Returns:
            Number of entries removed
        """
        removed_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if self._is_expired(data.get('timestamp', '')):
                        cache_file.unlink()
                        removed_count += 1
            except Exception:
                # Remove corrupted cache files
                cache_file.unlink()
                removed_count += 1
        
        return removed_count