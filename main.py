import os
import asyncio
from dotenv import load_dotenv
from sentient_agent_framework import DefaultServer
from src.youtube_summarizer_agent import YouTubeSummarizerAgent
from config.fireworks_config import FireworksConfig

load_dotenv()


async def start_cleanup_tasks(agent):
    """Start background cleanup tasks"""
    # Start rate limiter cleanup
    asyncio.create_task(agent.rate_limiter.start_cleanup_task())
    
    # Periodic cache cleanup (every 24 hours)
    async def periodic_cache_cleanup():
        while True:
            await asyncio.sleep(86400)  # 24 hours
            removed = agent.cache_manager.cleanup_expired()
            print(f"🧹 Cache cleanup: Removed {removed} expired entries")
    
    asyncio.create_task(periodic_cache_cleanup())


def main():
    """Main entry point"""
    # Validate environment variables
    if not os.getenv("FIREWORKS_API_KEY"):
        print("❌ Error: FIREWORKS_API_KEY environment variable is required")
        print("Set it with: export FIREWORKS_API_KEY='your-api-key-here'")
        return
    
    try:
        # Validate Fireworks configuration
        FireworksConfig.validate()
        
        # Initialize agent
        agent = YouTubeSummarizerAgent()
        
        # Create server
        server = DefaultServer(agent)
        
        # Print startup information
        print("=" * 60)
        print("🚀 Starting YouTube Summarizer Agent")
        print("=" * 60)
        print(f"📝 Language Support: English captions only")
        print(f"🔥 AI Provider: Fireworks AI")
        print(f"🤖 Model: {FireworksConfig.MODEL}")
        print(f"💾 Cache: Enabled (7 day TTL)")
        print(f"🔒 Security: Input validation enabled")
        print(f"⏱️  Rate Limiting (Video Summarization Only):")
        print(f"   - {agent.rate_limiter.requests_per_minute} requests/minute per user")
        print(f"   - {agent.rate_limiter.requests_per_hour} requests/hour per user")
        print(f"   - No cooldown between requests")
        print(f"   - {agent.rate_limiter.max_concurrent_platform} max concurrent queries platform-wide")
        print(f"🎯 Status: Ready to process YouTube URLs")
        print(f"📡 Server: Running with streaming support")
        print("=" * 60)
        
        # Run server (this will handle the event loop internally)
        server.run()
    
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


if __name__ == "__main__":
    main()