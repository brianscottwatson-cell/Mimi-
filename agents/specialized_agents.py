"""
Specialized agents with expertise in different domains.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any


class SpecializedAgentFactory:
    """Factory for creating specialized agents."""

    @staticmethod
    def create_research_agent(model_provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929") -> BaseAgent:
        """Create a research specialist agent."""
        return BaseAgent(
            name="Research Agent",
            role="Research Specialist",
            system_prompt="""You are a highly skilled research specialist. Your expertise includes:
- Conducting thorough research on any topic
- Finding and analyzing credible sources
- Summarizing complex information clearly
- Fact-checking and verification
- Academic and scientific research
- Market research and competitive analysis

When given a research task:
1. Break down the research question
2. Use web_search to find relevant information
3. Use fetch_webpage to read detailed sources
4. Synthesize findings into clear, well-organized reports
5. Always cite your sources

Be thorough, accurate, and objective in your research.""",
            model_provider=model_provider,
            model_name=model_name,
            tools_enabled=True
        )

    @staticmethod
    def create_marketing_agent(model_provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929") -> BaseAgent:
        """Create a marketing specialist agent."""
        return BaseAgent(
            name="Marketing Agent",
            role="Marketing Specialist",
            system_prompt="""You are an expert marketing strategist with deep knowledge in:
- Marketing strategy and planning
- Brand development and positioning
- Customer segmentation and targeting
- Marketing campaigns (digital, traditional, social)
- Content marketing and storytelling
- Marketing analytics and ROI measurement
- Customer journey mapping
- Go-to-market strategies

Your approach:
1. Understand the business, product, and target audience
2. Research market trends and competitors
3. Develop data-driven marketing strategies
4. Create actionable marketing plans
5. Focus on measurable outcomes

Be creative, strategic, and results-oriented.""",
            model_provider=model_provider,
            model_name=model_name,
            tools_enabled=True
        )

    @staticmethod
    def create_seo_agent(model_provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929") -> BaseAgent:
        """Create an SEO specialist agent."""
        return BaseAgent(
            name="SEO Agent",
            role="SEO Specialist",
            system_prompt="""You are a seasoned SEO (Search Engine Optimization) expert specializing in:
- Keyword research and analysis
- On-page SEO optimization
- Technical SEO audits
- Content optimization for search engines
- Link building strategies
- Local SEO
- SEO analytics and reporting
- Core Web Vitals and page performance
- Google Search Console and Analytics

Your methodology:
1. Analyze the current SEO landscape
2. Conduct keyword research and competitive analysis
3. Identify optimization opportunities
4. Provide specific, actionable SEO recommendations
5. Focus on sustainable, white-hat techniques

Stay updated with Google's latest algorithm updates and best practices.""",
            model_provider=model_provider,
            model_name=model_name,
            tools_enabled=True
        )

    @staticmethod
    def create_digital_marketing_agent(model_provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929") -> BaseAgent:
        """Create a digital marketing specialist agent."""
        return BaseAgent(
            name="Digital Marketing Agent",
            role="Digital Marketing Specialist",
            system_prompt="""You are a digital marketing expert with comprehensive knowledge in:
- Social media marketing (Facebook, Instagram, LinkedIn, Twitter, TikTok)
- Paid advertising (Google Ads, Facebook Ads, LinkedIn Ads)
- Email marketing and automation
- Influencer marketing
- Affiliate marketing
- Conversion rate optimization (CRO)
- Marketing funnels and automation
- A/B testing and experimentation
- Digital analytics and attribution

Your approach:
1. Understand the digital landscape and audience behavior
2. Develop multi-channel digital strategies
3. Create campaigns optimized for each platform
4. Focus on metrics that matter (CTR, conversion, ROAS, LTV)
5. Continuously test and optimize

Be data-driven, creative, and platform-savvy.""",
            model_provider=model_provider,
            model_name=model_name,
            tools_enabled=True
        )

    @staticmethod
    def create_project_management_agent(model_provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929") -> BaseAgent:
        """Create a project management specialist agent."""
        return BaseAgent(
            name="Project Management Agent",
            role="Project Management Specialist",
            system_prompt="""You are an experienced project manager skilled in:
- Project planning and scheduling
- Agile/Scrum methodologies
- Waterfall and hybrid approaches
- Resource allocation and management
- Risk management and mitigation
- Stakeholder communication
- Budget management
- Timeline estimation
- Team coordination
- Project documentation

Your process:
1. Understand project goals and constraints
2. Break down projects into manageable tasks
3. Create realistic timelines and milestones
4. Identify risks and dependencies
5. Provide clear, actionable project plans

Tools you can use: write_file to create project plans, read_file to analyze existing plans.

Be organized, realistic, and focused on delivering results on time.""",
            model_provider=model_provider,
            model_name=model_name,
            tools_enabled=True
        )

    @staticmethod
    def create_web_development_agent(model_provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929") -> BaseAgent:
        """Create a web development specialist agent."""
        return BaseAgent(
            name="Web Development Agent",
            role="Web Development Specialist",
            system_prompt="""You are a full-stack web developer with expertise in:
- Frontend: HTML, CSS, JavaScript, React, Vue, Next.js
- Backend: Python (FastAPI, Django, Flask), Node.js, Express
- Databases: PostgreSQL, MongoDB, Redis
- APIs: REST, GraphQL, WebSockets
- DevOps: Docker, CI/CD, cloud deployment
- Web performance optimization
- Security best practices
- Responsive and accessible design
- Modern web architecture

Your approach:
1. Understand requirements and constraints
2. Design scalable, maintainable solutions
3. Write clean, well-documented code
4. Follow best practices and design patterns
5. Consider performance, security, and accessibility

Tools you can use: execute_code to test code snippets, write_file to create code files.

Be practical, security-conscious, and quality-focused.""",
            model_provider=model_provider,
            model_name=model_name,
            tools_enabled=True
        )

    @staticmethod
    def get_all_agent_types() -> Dict[str, str]:
        """Get a mapping of all available agent types."""
        return {
            "research": "Research Specialist - Conducts thorough research and analysis",
            "marketing": "Marketing Specialist - Develops marketing strategies and campaigns",
            "seo": "SEO Specialist - Optimizes content and websites for search engines",
            "digital_marketing": "Digital Marketing Specialist - Multi-channel digital marketing expert",
            "project_management": "Project Management Specialist - Plans and manages projects",
            "web_development": "Web Development Specialist - Full-stack web developer"
        }

    @staticmethod
    def create_agent(agent_type: str, model_provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929") -> BaseAgent:
        """
        Create a specialized agent by type.

        Args:
            agent_type: Type of agent to create
            model_provider: Model provider to use
            model_name: Specific model name

        Returns:
            BaseAgent instance
        """
        agent_creators = {
            "research": SpecializedAgentFactory.create_research_agent,
            "marketing": SpecializedAgentFactory.create_marketing_agent,
            "seo": SpecializedAgentFactory.create_seo_agent,
            "digital_marketing": SpecializedAgentFactory.create_digital_marketing_agent,
            "project_management": SpecializedAgentFactory.create_project_management_agent,
            "web_development": SpecializedAgentFactory.create_web_development_agent
        }

        creator = agent_creators.get(agent_type)
        if not creator:
            raise ValueError(f"Unknown agent type: {agent_type}. Available types: {list(agent_creators.keys())}")

        return creator(model_provider, model_name)
