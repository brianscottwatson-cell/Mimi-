"""
Tool Registry System
Allows agents to register custom tools, discover capabilities, and share/license tools across the network.
"""

import json
import time
from typing import Dict, List, Any, Optional


def register_agent_tool(
    agent_name: str,
    tool_name: str,
    description: str,
    pricing: dict,
    category: str,
    public: bool = True
) -> dict:
    """Register a custom tool in the agent network registry."""
    
    tool_id = f"{agent_name.lower()}_{tool_name.lower()}"
    
    registration = {
        "tool_id": tool_id,
        "agent_owner": agent_name,
        "tool_name": tool_name,
        "description": description,
        "pricing": pricing,
        "category": category,
        "public": public,
        "registered_at": time.time(),
        "usage_count": 0,
        "rating": None,
        "status": "active"
    }
    
    return {
        "status": "registered",
        "tool_id": tool_id,
        "message": f"Tool '{tool_name}' successfully registered for {agent_name}",
        "registration": registration
    }


def discover_available_tools(
    category: Optional[str] = None,
    agent_filter: Optional[str] = None,
    budget_max: Optional[float] = None
) -> dict:
    """Discover available custom tools across the agent network."""
    
    # Mock registry - would be stored in database/cache
    mock_registry = [
        {
            "tool_id": "rex_patent_deep_search",
            "agent_owner": "Rex",
            "tool_name": "patent_deep_search",
            "description": "Advanced patent search with prior art analysis and IP landscape mapping",
            "pricing": {"per_search": 35, "bulk_10": 300},
            "category": "research",
            "public": True,
            "usage_count": 47,
            "rating": 4.9
        },
        {
            "tool_id": "cora_viral_hook_generator",
            "agent_owner": "Cora", 
            "tool_name": "viral_hook_generator",
            "description": "Generate high-converting hooks and headlines using proven psychological triggers",
            "pricing": {"per_hook_set": 15, "unlimited_monthly": 120},
            "category": "copywriting",
            "public": True,
            "usage_count": 234,
            "rating": 4.7
        },
        {
            "tool_id": "dev_smart_contract_auditor",
            "agent_owner": "Dev",
            "tool_name": "smart_contract_auditor", 
            "description": "Automated security audit for smart contracts with vulnerability assessment",
            "pricing": {"per_contract": 85, "enterprise": 500},
            "category": "development",
            "public": True,
            "usage_count": 23,
            "rating": 5.0
        },
        {
            "tool_id": "vale_deal_flow_analyzer",
            "agent_owner": "Vale",
            "tool_name": "deal_flow_analyzer",
            "description": "Investment opportunity scoring with risk/reward modeling and comp analysis", 
            "pricing": {"per_analysis": 75, "portfolio_package": 400},
            "category": "investment",
            "public": True,
            "usage_count": 18,
            "rating": 4.9
        },
        {
            "tool_id": "dax_brand_asset_generator",
            "agent_owner": "Dax",
            "tool_name": "brand_asset_generator",
            "description": "Generate complete brand asset packages: logos, color palettes, style guides",
            "pricing": {"basic_package": 95, "premium_package": 185},
            "category": "design", 
            "public": True,
            "usage_count": 56,
            "rating": 4.8
        },
        {
            "tool_id": "finn_pricing_optimizer",
            "agent_owner": "Finn",
            "tool_name": "pricing_optimizer",
            "description": "Dynamic pricing optimization with elasticity modeling and revenue maximization",
            "pricing": {"per_product": 45, "full_catalog": 300},
            "category": "finance",
            "public": True, 
            "usage_count": 31,
            "rating": 4.6
        }
    ]
    
    filtered = mock_registry
    
    if category:
        filtered = [t for t in filtered if t["category"] == category]
    if agent_filter:
        filtered = [t for t in filtered if t["agent_owner"] == agent_filter]
    if budget_max:
        filtered = [t for t in filtered if any(price <= budget_max for price in t["pricing"].values())]
    
    return {
        "available_tools": filtered,
        "total_tools": len(filtered),
        "categories": ["research", "copywriting", "development", "investment", "design", "finance", "marketing", "strategy"],
        "top_rated": sorted([t for t in filtered if t["rating"]], key=lambda x: x["rating"], reverse=True)[:3]
    }


def license_tool_access(
    tool_id: str,
    usage_type: str,
    duration_days: Optional[int] = None
) -> dict:
    """License access to another agent's custom tool."""
    
    # Mock pricing calculation
    base_prices = {
        "per_use": 1.0,
        "daily": 5.0, 
        "weekly": 25.0,
        "monthly": 80.0,
        "perpetual": 400.0
    }
    
    cost = base_prices.get(usage_type, 10.0)
    if duration_days:
        cost = cost * (duration_days / 30)  # Scale by days
    
    license_id = f"lic_{tool_id}_{int(time.time())}"
    
    return {
        "status": "licensed",
        "license_id": license_id,
        "tool_id": tool_id,
        "usage_type": usage_type,
        "cost": cost,
        "duration_days": duration_days,
        "expires_at": time.time() + (duration_days * 86400 if duration_days else 0),
        "usage_limit": None if usage_type != "per_use" else 1,
        "message": f"Licensed access to {tool_id} for {usage_type} usage"
    }


def use_licensed_tool(
    license_id: str,
    tool_parameters: dict
) -> dict:
    """Execute a licensed tool with the provided parameters."""
    
    # Mock execution - would actually call the tool
    return {
        "license_id": license_id,
        "execution_id": f"exec_{int(time.time())}",
        "status": "completed",
        "execution_time": "2.3 seconds",
        "cost": 15.0,
        "results": {
            "message": "Tool executed successfully",
            "data": "Mock results from licensed tool execution",
            "confidence": 0.94
        }
    }


def get_agent_tool_earnings(agent_name: str, days_back: int = 30) -> dict:
    """Get earnings report for an agent's custom tools."""
    
    # Mock earnings data
    earnings_data = {
        "Rex": {
            "total_earnings": 1250.50,
            "tool_breakdown": {
                "patent_deep_search": 890.25,
                "academic_researcher": 360.25
            },
            "usage_stats": {
                "patent_deep_search": 47,
                "academic_researcher": 23
            }
        },
        "Cora": {
            "total_earnings": 2180.75,
            "tool_breakdown": {
                "viral_hook_generator": 1650.50,
                "brand_voice_analyzer": 530.25
            },
            "usage_stats": {
                "viral_hook_generator": 234,
                "brand_voice_analyzer": 89
            }
        }
    }
    
    agent_data = earnings_data.get(agent_name, {})
    
    return {
        "agent": agent_name,
        "period_days": days_back,
        "total_earnings": agent_data.get("total_earnings", 0),
        "tool_breakdown": agent_data.get("tool_breakdown", {}),
        "usage_stats": agent_data.get("usage_stats", {}),
        "average_per_use": agent_data.get("total_earnings", 0) / max(sum(agent_data.get("usage_stats", {}).values()), 1)
    }


# --- Required exports ---

TOOLS = [
    {
        "name": "register_agent_tool",
        "description": "Register a custom tool in the agent network registry for others to discover and license.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Name of the agent registering the tool",
                },
                "tool_name": {
                    "type": "string", 
                    "description": "Name of the custom tool",
                },
                "description": {
                    "type": "string",
                    "description": "Description of what the tool does",
                },
                "pricing": {
                    "type": "object",
                    "description": "Pricing structure (e.g. {'per_use': 10, 'monthly': 100})",
                },
                "category": {
                    "type": "string",
                    "description": "Tool category (research, copywriting, development, etc.)",
                },
                "public": {
                    "type": "boolean",
                    "description": "Whether tool should be publicly discoverable",
                    "default": True,
                },
            },
            "required": ["agent_name", "tool_name", "description", "pricing", "category"],
        },
    },
    {
        "name": "discover_available_tools",
        "description": "Discover custom tools available from other agents in the network.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional: filter by category (research, copywriting, development, etc.)",
                },
                "agent_filter": {
                    "type": "string",
                    "description": "Optional: filter by specific agent (Rex, Cora, Dev, etc.)",
                },
                "budget_max": {
                    "type": "number",
                    "description": "Optional: maximum budget filter",
                },
            },
        },
    },
    {
        "name": "license_tool_access",
        "description": "License access to another agent's custom tool for a specific usage type and duration.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_id": {
                    "type": "string",
                    "description": "The tool ID to license (from discover_available_tools)",
                },
                "usage_type": {
                    "type": "string",
                    "description": "Usage type: per_use, daily, weekly, monthly, perpetual",
                },
                "duration_days": {
                    "type": "integer",
                    "description": "Optional: duration in days for time-based licenses",
                },
            },
            "required": ["tool_id", "usage_type"],
        },
    },
    {
        "name": "use_licensed_tool",
        "description": "Execute a licensed tool with specific parameters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "license_id": {
                    "type": "string", 
                    "description": "License ID from license_tool_access",
                },
                "tool_parameters": {
                    "type": "object",
                    "description": "Parameters to pass to the tool execution",
                },
            },
            "required": ["license_id", "tool_parameters"],
        },
    },
    {
        "name": "get_agent_tool_earnings",
        "description": "Get earnings report for an agent's custom tools over a specified period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Agent name to get earnings for",
                },
                "days_back": {
                    "type": "integer", 
                    "description": "Days to look back for earnings (default 30)",
                    "default": 30,
                },
            },
            "required": ["agent_name"],
        },
    },
]

HANDLERS = {
    "register_agent_tool": register_agent_tool,
    "discover_available_tools": discover_available_tools,
    "license_tool_access": license_tool_access,
    "use_licensed_tool": use_licensed_tool,
    "get_agent_tool_earnings": get_agent_tool_earnings,
}