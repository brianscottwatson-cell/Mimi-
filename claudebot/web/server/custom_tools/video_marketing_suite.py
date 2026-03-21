"""
Video Marketing Suite for short-form content creation and optimization.
Handles TikTok, Instagram Reels, YouTube Shorts strategy and production.
"""

import json
from typing import Dict, List, Optional


def generate_short_form_video_strategy(
    platform: str,
    brand_category: str,
    target_demographic: str,
    campaign_goal: str = "awareness"
) -> Dict:
    """Generate comprehensive short-form video marketing strategy."""
    
    platform_specs = {
        "tiktok": {
            "optimal_length": "15-30 seconds",
            "aspect_ratio": "9:16",
            "trending_formats": ["challenges", "tutorials", "behind_scenes", "trends"],
            "best_posting_times": ["6-10am", "7-9pm"],
            "hashtag_strategy": "3-5 trending + 2-3 branded"
        },
        "instagram_reels": {
            "optimal_length": "15-30 seconds", 
            "aspect_ratio": "9:16",
            "trending_formats": ["tutorials", "before/after", "trends", "product_demos"],
            "best_posting_times": ["6-9am", "6-8pm"],
            "hashtag_strategy": "5-10 mix of trending and niche"
        },
        "youtube_shorts": {
            "optimal_length": "15-60 seconds",
            "aspect_ratio": "9:16", 
            "trending_formats": ["how_to", "quick_tips", "reactions", "mini_tutorials"],
            "best_posting_times": ["2-4pm", "8-11pm"],
            "hashtag_strategy": "3-5 keyword-focused tags"
        }
    }
    
    platform_data = platform_specs.get(platform, platform_specs["tiktok"])
    
    return {
        "status": "success",
        "platform": platform,
        "campaign_goal": campaign_goal,
        "content_strategy": {
            "platform_specs": platform_data,
            "content_pillars": [
                "Educational/How-to (40%)",
                "Behind-the-scenes (30%)", 
                "Trending/Entertainment (20%)",
                "Product/Service showcase (10%)"
            ],
            "production_requirements": {
                "equipment": "Smartphone + ring light + microphone",
                "editing_software": "CapCut, InShot, or Adobe Premiere Rush",
                "templates": "Brand-consistent intro/outro templates"
            }
        },
        "content_calendar": {
            "posting_frequency": "1-2 videos per day",
            "batch_production": "Film 5-7 videos per session",
            "trend_monitoring": "Daily trend analysis and adaptation"
        },
        "engagement_tactics": [
            "Respond to comments within 2 hours",
            "Use trending sounds and effects",
            "Create interactive content (polls, Q&A)",
            "Collaborate with micro-influencers"
        ]
    }


def create_video_content_brief(
    video_type: str,
    topic: str,
    target_audience: str,
    key_message: str,
    duration: int = 30
) -> Dict:
    """Create detailed content briefs for video production."""
    
    video_structures = {
        "tutorial": {
            "hook": "0-3 seconds: Problem statement",
            "body": "4-20 seconds: Step-by-step solution", 
            "cta": "21-30 seconds: Call to action + follow"
        },
        "product_demo": {
            "hook": "0-3 seconds: Before/problem state",
            "body": "4-20 seconds: Product in action",
            "cta": "21-30 seconds: Results + where to buy"
        },
        "behind_scenes": {
            "hook": "0-3 seconds: Teaser of what's coming",
            "body": "4-25 seconds: Process/journey",
            "cta": "26-30 seconds: Connect with brand"
        },
        "trend_adaptation": {
            "hook": "0-3 seconds: Trending sound/format",
            "body": "4-20 seconds: Brand-specific twist",
            "cta": "21-30 seconds: Brand message + follow"
        }
    }
    
    structure = video_structures.get(video_type, video_structures["tutorial"])
    
    return {
        "status": "success",
        "video_brief": {
            "type": video_type,
            "topic": topic,
            "duration": f"{duration} seconds",
            "target_audience": target_audience,
            "key_message": key_message,
            "video_structure": structure,
            "visual_elements": [
                "Strong opening visual hook",
                "Clear, readable text overlays",
                "Brand colors and fonts",
                "High-quality audio/trending sound"
            ],
            "technical_specs": {
                "resolution": "1080x1920 (9:16)",
                "frame_rate": "30fps minimum",
                "audio": "Clear, balanced audio levels",
                "captions": "Auto-generated + manual review"
            }
        },
        "production_checklist": [
            "Script and storyboard completed",
            "Location and lighting secured", 
            "Equipment and props ready",
            "Trending sounds/music selected",
            "Post-production timeline set"
        ],
        "optimization_strategy": {
            "thumbnail": "Eye-catching frame from video",
            "title": "Keyword-optimized, curiosity-driven",
            "description": "Value proposition + relevant hashtags",
            "posting_schedule": "Peak engagement times"
        }
    }


def analyze_video_performance(
    platform: str,
    video_metrics: Dict,
    benchmark_data: Optional[Dict] = None
) -> Dict:
    """Analyze video performance and provide optimization recommendations."""
    
    # Extract metrics
    views = video_metrics.get("views", 0)
    engagement_rate = video_metrics.get("engagement_rate", 0)
    completion_rate = video_metrics.get("completion_rate", 0)
    shares = video_metrics.get("shares", 0)
    
    # Platform benchmarks
    benchmarks = benchmark_data or {
        "tiktok": {"avg_engagement": 5.3, "avg_completion": 45},
        "instagram_reels": {"avg_engagement": 3.8, "avg_completion": 40},
        "youtube_shorts": {"avg_engagement": 2.1, "avg_completion": 35}
    }
    
    platform_benchmark = benchmarks.get(platform, benchmarks["tiktok"])
    
    return {
        "status": "success",
        "performance_summary": {
            "platform": platform,
            "views": views,
            "engagement_rate": f"{engagement_rate}%",
            "completion_rate": f"{completion_rate}%",
            "shares": shares,
            "performance_vs_benchmark": {
                "engagement": "above" if engagement_rate > platform_benchmark["avg_engagement"] else "below",
                "completion": "above" if completion_rate > platform_benchmark["avg_completion"] else "below"
            }
        },
        "optimization_recommendations": [
            "Improve hook in first 3 seconds" if completion_rate < 30 else "Strong opening hook working well",
            "Add more interactive elements" if engagement_rate < 3 else "Good engagement levels",
            "Test different posting times" if views < 1000 else "Reach performing well",
            "Experiment with trending sounds" if shares < 10 else "Content shareability is good"
        ],
        "next_content_strategy": {
            "double_down_on": "High-performing content themes",
            "test_new": "Trending formats and sounds",
            "optimize": "Hook timing and call-to-action placement"
        }
    }


# --- Required exports ---

TOOLS = [
    {
        "name": "generate_short_form_video_strategy", 
        "description": "Generate comprehensive short-form video marketing strategy for TikTok, Instagram Reels, YouTube Shorts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "Video platform",
                    "enum": ["tiktok", "instagram_reels", "youtube_shorts"]
                },
                "brand_category": {
                    "type": "string",
                    "description": "Brand category or industry"
                },
                "target_demographic": {
                    "type": "string", 
                    "description": "Primary target demographic (e.g., Gen Z, Millennials, professionals)"
                },
                "campaign_goal": {
                    "type": "string",
                    "description": "Primary campaign goal",
                    "enum": ["awareness", "engagement", "conversions", "followers"],
                    "default": "awareness"
                }
            },
            "required": ["platform", "brand_category", "target_demographic"]
        }
    },
    {
        "name": "create_video_content_brief",
        "description": "Create detailed content briefs for video production with structure, specs, and optimization strategy.", 
        "input_schema": {
            "type": "object",
            "properties": {
                "video_type": {
                    "type": "string",
                    "description": "Type of video content",
                    "enum": ["tutorial", "product_demo", "behind_scenes", "trend_adaptation"]
                },
                "topic": {
                    "type": "string",
                    "description": "Video topic or subject matter"
                },
                "target_audience": {
                    "type": "string",
                    "description": "Specific target audience for the video"
                },
                "key_message": {
                    "type": "string",
                    "description": "Primary message or takeaway"
                },
                "duration": {
                    "type": "integer",
                    "description": "Target video duration in seconds",
                    "default": 30
                }
            },
            "required": ["video_type", "topic", "target_audience", "key_message"]
        }
    },
    {
        "name": "analyze_video_performance",
        "description": "Analyze video performance metrics and provide optimization recommendations.",
        "input_schema": {
            "type": "object", 
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "Platform where video was published"
                },
                "video_metrics": {
                    "type": "object",
                    "description": "Video performance metrics (views, engagement_rate, completion_rate, shares)"
                },
                "benchmark_data": {
                    "type": "object",
                    "description": "Optional benchmark data for comparison"
                }
            },
            "required": ["platform", "video_metrics"]
        }
    }
]

HANDLERS = {
    "generate_short_form_video_strategy": generate_short_form_video_strategy,
    "create_video_content_brief": create_video_content_brief,
    "analyze_video_performance": analyze_video_performance,
}