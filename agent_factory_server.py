"""
Agent Factory Platform — FastAPI Server
Full REST API for agent management, chat, RAG, Twilio, xAI, analytics, plugins.
"""
import os
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Header, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

# ------------------------------------------------------------------ #
#  App init                                                            #
# ------------------------------------------------------------------ #

app = FastAPI(
    title="Agent Factory Platform",
    description="Build, configure, and deploy omni-channel AI agents",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
#  Platform services (lazy-init to avoid import errors at startup)    #
# ------------------------------------------------------------------ #

_factory = None
_analytics = None
_webhooks = None
_livekit = None


def get_factory():
    global _factory
    if _factory is None:
        from agent_factory.factory import AgentFactory
        _factory = AgentFactory()
    return _factory


def get_analytics():
    global _analytics
    if _analytics is None:
        from agent_factory.analytics.tracker import AnalyticsTracker
        _analytics = AnalyticsTracker()
    return _analytics


def get_webhooks():
    global _webhooks
    if _webhooks is None:
        from agent_factory.plugins.webhook import WebhookManager
        _webhooks = WebhookManager()
    return _webhooks


def get_livekit():
    global _livekit
    if _livekit is None:
        from agent_factory.integrations.livekit_int import LiveKitManager
        _livekit = LiveKitManager()
    return _livekit


# ------------------------------------------------------------------ #
#  Pydantic models                                                     #
# ------------------------------------------------------------------ #

class AgentCreateRequest(BaseModel):
    name: str
    description: str = ""
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"
    system_prompt: str = ""
    channels: List[str] = ["chat"]
    tools: List[str] = []
    soul: Optional[str] = None
    rag_enabled: bool = False
    twilio_enabled: bool = False
    livekit_enabled: bool = False
    plugins: List[str] = []
    analytics_enabled: bool = True
    max_tokens: int = 2048


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    system_prompt: Optional[str] = None
    channels: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    soul: Optional[str] = None
    rag_enabled: Optional[bool] = None
    twilio_enabled: Optional[bool] = None
    livekit_enabled: Optional[bool] = None
    max_tokens: Optional[int] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    channel: str = "chat"


class LLMSwitchRequest(BaseModel):
    provider: str
    model: str


class RAGIngestRequest(BaseModel):
    documents: List[Dict[str, Any]]  # [{text, source, metadata}]


class SMSRequest(BaseModel):
    to: str
    body: str
    from_number: Optional[str] = None


class CallRequest(BaseModel):
    to: str
    twiml_url: str
    record: bool = True


class ImageGenRequest(BaseModel):
    prompt: str
    n: int = 1
    size: str = "1024x1024"
    model: str = "grok-2-image-1212"


class GrokSearchRequest(BaseModel):
    query: str
    model: str = "grok-2"


class WebhookRegisterRequest(BaseModel):
    url: str
    events: List[str]
    name: str = ""
    secret: Optional[str] = None


class EmbedWidgetRequest(BaseModel):
    theme: str = "dark"
    position: str = "bottom-right"
    title: str = "Chat with AI"


class LiveKitSessionRequest(BaseModel):
    session_id: Optional[str] = None
    channel: str = "voice"


# ------------------------------------------------------------------ #
#  UI                                                                  #
# ------------------------------------------------------------------ #

@app.get("/", response_class=HTMLResponse)
async def serve_platform_ui():
    """Serve the Agent Factory Platform UI."""
    html_path = os.path.join(os.path.dirname(__file__), "web", "platform.html")
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return f.read()
    return HTMLResponse("<h1>Agent Factory</h1><p>UI not found. Check web/platform.html</p>", status_code=200)


@app.get("/widget/{agent_id}", response_class=HTMLResponse)
async def serve_widget(agent_id: str, theme: str = "dark"):
    """Serve the embeddable chat widget UI."""
    html_path = os.path.join(os.path.dirname(__file__), "web", "widget.html")
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            content = f.read()
            content = content.replace("{{AGENT_ID}}", agent_id).replace("{{THEME}}", theme)
            return content
    return HTMLResponse(f"<p>Widget for agent {agent_id}</p>")


# ------------------------------------------------------------------ #
#  Health                                                              #
# ------------------------------------------------------------------ #

@app.get("/health")
async def health():
    return {"status": "healthy", "platform": "Agent Factory", "timestamp": datetime.utcnow().isoformat()}


# ------------------------------------------------------------------ #
#  Agents CRUD                                                         #
# ------------------------------------------------------------------ #

@app.post("/api/agents", status_code=201)
async def create_agent(req: AgentCreateRequest):
    """Create a new agent with full configuration."""
    factory = get_factory()
    agent = factory.create_agent(req.dict())
    return agent


@app.get("/api/agents")
async def list_agents():
    """List all registered agents."""
    factory = get_factory()
    return {"agents": factory.list_agents()}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    factory = get_factory()
    agent = factory.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    safe = dict(agent)
    safe.pop("api_key", None)
    return safe


@app.patch("/api/agents/{agent_id}")
async def update_agent(agent_id: str, req: AgentUpdateRequest):
    factory = get_factory()
    updates = {k: v for k, v in req.dict().items() if v is not None}
    result = factory.update_agent(agent_id, updates)
    if not result:
        raise HTTPException(404, "Agent not found")
    safe = dict(result)
    safe.pop("api_key", None)
    return safe


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    factory = get_factory()
    if not factory.delete_agent(agent_id):
        raise HTTPException(404, "Agent not found")
    return {"status": "deleted", "agent_id": agent_id}


@app.post("/api/agents/{agent_id}/rotate-key")
async def rotate_api_key(agent_id: str):
    factory = get_factory()
    new_key = factory.registry.rotate_key(agent_id)
    if not new_key:
        raise HTTPException(404, "Agent not found")
    return {"agent_id": agent_id, "api_key": new_key, "message": "Key rotated successfully"}


# ------------------------------------------------------------------ #
#  Chat                                                                #
# ------------------------------------------------------------------ #

@app.post("/api/agents/{agent_id}/chat")
async def agent_chat(agent_id: str, req: ChatRequest):
    """Send a message to an agent (any channel)."""
    factory = get_factory()
    analytics = get_analytics()
    webhooks = get_webhooks()

    start = time.time()
    result = factory.chat(agent_id, req.message, req.session_id, req.channel)
    latency = (time.time() - start) * 1000

    if "error" in result:
        raise HTTPException(500, result["error"])

    # Analytics
    analytics.record_chat(
        agent_id=agent_id,
        session_id=req.session_id or "default",
        channel=req.channel,
        latency_ms=latency,
        provider=result.get("llm_provider", ""),
        model=result.get("llm_model", ""),
    )

    # Fire webhooks for "message" event
    webhooks.fire(agent_id, "message", {
        "user_message": req.message,
        "agent_response": result.get("response", ""),
        "channel": req.channel,
        "session_id": req.session_id,
    })

    return result


@app.post("/api/agents/{agent_id}/reset")
async def reset_chat(agent_id: str, session_id: str = "default"):
    factory = get_factory()
    factory.reset_session(agent_id, session_id)
    return {"status": "reset", "agent_id": agent_id, "session_id": session_id}


# ------------------------------------------------------------------ #
#  LLM switching                                                       #
# ------------------------------------------------------------------ #

@app.post("/api/agents/{agent_id}/llm")
async def switch_llm(agent_id: str, req: LLMSwitchRequest):
    """Switch the LLM provider/model for an agent."""
    factory = get_factory()
    result = factory.switch_llm(agent_id, req.provider, req.model)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@app.get("/api/llm/providers")
async def list_providers():
    """List all supported LLM providers and their models."""
    factory = get_factory()
    return factory.list_providers()


# ------------------------------------------------------------------ #
#  RAG                                                                 #
# ------------------------------------------------------------------ #

@app.post("/api/agents/{agent_id}/rag/ingest")
async def ingest_documents(agent_id: str, req: RAGIngestRequest):
    """Ingest documents into the agent's vector store."""
    factory = get_factory()
    result = factory.ingest_documents(agent_id, req.documents)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@app.post("/api/agents/{agent_id}/rag/upload")
async def upload_rag_file(agent_id: str, file: UploadFile = File(...)):
    """Upload a text/markdown file for RAG ingestion."""
    factory = get_factory()
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    result = factory.ingest_documents(agent_id, [{"text": text, "source": file.filename}])
    if "error" in result:
        raise HTTPException(400, result["error"])
    return {**result, "filename": file.filename}


@app.get("/api/agents/{agent_id}/rag/documents")
async def list_rag_documents(agent_id: str):
    factory = get_factory()
    docs = factory.list_rag_documents(agent_id)
    return {"documents": docs, "agent_id": agent_id}


@app.get("/api/agents/{agent_id}/rag/stats")
async def rag_stats(agent_id: str):
    factory = get_factory()
    return factory.rag_stats(agent_id)


# ------------------------------------------------------------------ #
#  Soul documents                                                      #
# ------------------------------------------------------------------ #

@app.post("/api/agents/{agent_id}/soul")
async def upload_soul(agent_id: str, soul_content: str = Form(...)):
    """Upload a .soul document to define agent personality."""
    factory = get_factory()
    result = factory.upload_soul(agent_id, soul_content)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@app.post("/api/agents/{agent_id}/soul/file")
async def upload_soul_file(agent_id: str, file: UploadFile = File(...)):
    """Upload a .soul file."""
    content = await file.read()
    soul_text = content.decode("utf-8", errors="replace")
    factory = get_factory()
    result = factory.upload_soul(agent_id, soul_text)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return {**result, "filename": file.filename}


@app.post("/api/soul/validate")
async def validate_soul_doc(soul_content: str = Form(...)):
    """Validate a soul document without attaching it to an agent."""
    from agent_factory.soul import validate_soul
    return validate_soul(soul_content)


# ------------------------------------------------------------------ #
#  xAI Grok                                                            #
# ------------------------------------------------------------------ #

@app.post("/api/grok/chat")
async def grok_chat(req: ChatRequest):
    """Direct Grok chat (not agent-specific)."""
    from agent_factory.integrations.xai import GrokChat
    grok = GrokChat()
    result = grok.complete(messages=[{"role": "user", "content": req.message}])
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


@app.post("/api/grok/search")
async def grok_search(req: GrokSearchRequest):
    """Real-time search via Grok."""
    from agent_factory.integrations.xai import GrokSearch
    searcher = GrokSearch(model=req.model)
    return searcher.search(req.query)


@app.post("/api/grok/image")
async def grok_image_gen(req: ImageGenRequest):
    """Generate images via Grok Imagine."""
    from agent_factory.integrations.xai import GrokImageGen
    gen = GrokImageGen(model=req.model)
    result = gen.generate(req.prompt, n=req.n, size=req.size)
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


@app.post("/api/grok/vision")
async def grok_vision(
    text: str = Form(...),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
):
    """Analyze an image with Grok Vision."""
    from agent_factory.integrations.xai import GrokVision
    vision = GrokVision()

    if image:
        import base64
        content = await image.read()
        b64 = base64.b64encode(content).decode()
        result = vision.analyze(text, image_base64=b64, media_type=image.content_type or "image/jpeg")
    elif image_url:
        result = vision.analyze(text, image_url=image_url)
    else:
        raise HTTPException(400, "Provide image file or image_url")

    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


# ------------------------------------------------------------------ #
#  Twilio                                                              #
# ------------------------------------------------------------------ #

@app.post("/api/agents/{agent_id}/sms/send")
async def send_sms(agent_id: str, req: SMSRequest):
    """Send an SMS via Twilio."""
    from agent_factory.integrations.twilio_int import TwilioSMS
    sms = TwilioSMS()
    result = sms.send(req.to, req.body, req.from_number)
    if "error" in result:
        raise HTTPException(500, result["error"])
    analytics = get_analytics()
    analytics.record_sms(agent_id, result.get("sid", ""), "outbound")
    return result


@app.get("/api/twilio/messages")
async def list_twilio_messages():
    from agent_factory.integrations.twilio_int import TwilioSMS
    return {"messages": TwilioSMS().list_messages()}


@app.post("/api/agents/{agent_id}/calls/make")
async def make_call(agent_id: str, req: CallRequest):
    """Initiate an outbound voice call."""
    from agent_factory.integrations.twilio_int import TwilioVoice
    voice = TwilioVoice()
    result = voice.make_call(req.to, req.twiml_url, record=req.record)
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


@app.get("/api/twilio/calls")
async def list_calls():
    from agent_factory.integrations.twilio_int import TwilioVoice
    return {"calls": TwilioVoice().list_calls()}


@app.post("/api/twilio/webhook/inbound-sms")
async def twilio_inbound_sms(request: Request):
    """
    Twilio webhook for inbound SMS.
    Routes message to the matching agent and replies via TwiML.
    """
    form = await request.form()
    from_number = form.get("From", "")
    body = form.get("Body", "")
    to_number = form.get("To", "")

    # Find agent configured for this Twilio number (simplified: use first active agent)
    factory = get_factory()
    agents = factory.list_agents()
    agent_id = agents[0]["id"] if agents else None

    reply_text = "Agent Factory received your message."
    if agent_id and body:
        result = factory.chat(agent_id, body, session_id=from_number, channel="sms")
        reply_text = result.get("response", reply_text)

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>{reply_text[:1600]}</Message></Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.post("/api/twilio/webhook/inbound-voice")
async def twilio_inbound_voice(request: Request):
    """
    Twilio webhook for inbound voice calls.
    Returns TwiML to gather speech and route to agent.
    """
    host = str(request.base_url).rstrip("/")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Welcome to Agent Factory. How can I help you today?</Say>
    <Gather input="speech" timeout="5" action="{host}/api/twilio/webhook/voice-response" method="POST">
    </Gather>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.post("/api/twilio/webhook/voice-response")
async def twilio_voice_response(request: Request):
    """Process spoken input and reply via TTS."""
    form = await request.form()
    speech_result = form.get("SpeechResult", "")
    from_number = form.get("From", "")

    factory = get_factory()
    agents = factory.list_agents()
    agent_id = agents[0]["id"] if agents else None

    reply_text = "I heard you. Please hold."
    if agent_id and speech_result:
        result = factory.chat(agent_id, speech_result, session_id=from_number, channel="voice")
        reply_text = result.get("response", reply_text)

    # Truncate for TTS
    tts_text = reply_text[:500]
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>{tts_text}</Say>
    <Gather input="speech" timeout="5" action="/api/twilio/webhook/voice-response" method="POST">
    </Gather>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


# ------------------------------------------------------------------ #
#  LiveKit                                                             #
# ------------------------------------------------------------------ #

@app.post("/api/agents/{agent_id}/livekit/session")
async def create_livekit_session(agent_id: str, req: LiveKitSessionRequest):
    """Create a LiveKit voice/video session for an agent."""
    import secrets
    livekit = get_livekit()
    session_id = req.session_id or secrets.token_urlsafe(8)
    result = livekit.create_agent_session(agent_id, session_id, req.channel)
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


@app.get("/api/livekit/status")
async def livekit_status():
    return get_livekit().status()


# ------------------------------------------------------------------ #
#  Analytics                                                           #
# ------------------------------------------------------------------ #

@app.get("/api/analytics/summary")
async def analytics_summary(agent_id: Optional[str] = None, hours: int = 24):
    return get_analytics().summary(agent_id=agent_id, hours=hours)


@app.get("/api/analytics/events")
async def analytics_events(
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    hours: int = 24,
    limit: int = 100,
):
    return {"events": get_analytics().get_events(agent_id, event_type, hours, limit)}


# ------------------------------------------------------------------ #
#  Plugins / Webhooks                                                  #
# ------------------------------------------------------------------ #

@app.post("/api/agents/{agent_id}/webhooks")
async def register_webhook(agent_id: str, req: WebhookRegisterRequest):
    wh = get_webhooks().register_webhook(
        agent_id=agent_id,
        url=req.url,
        events=req.events,
        secret=req.secret,
        name=req.name,
    )
    return wh


@app.get("/api/agents/{agent_id}/webhooks")
async def list_webhooks(agent_id: str):
    return {"webhooks": get_webhooks().list_webhooks(agent_id)}


@app.delete("/api/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    if not get_webhooks().delete_webhook(webhook_id):
        raise HTTPException(404, "Webhook not found")
    return {"status": "deleted", "webhook_id": webhook_id}


@app.post("/api/agents/{agent_id}/embed")
async def get_embed_snippet(agent_id: str, req: EmbedWidgetRequest, request: Request):
    """Get the JavaScript embed snippet for a website."""
    base_url = str(request.base_url).rstrip("/")
    snippet = get_webhooks().generate_embed_snippet(
        agent_id=agent_id,
        api_base_url=base_url,
        theme=req.theme,
        position=req.position,
        title=req.title,
    )
    return {"snippet": snippet, "agent_id": agent_id}


# ------------------------------------------------------------------ #
#  Platform info                                                       #
# ------------------------------------------------------------------ #

@app.get("/api/platform/info")
async def platform_info():
    factory = get_factory()
    return {
        "platform": "Agent Factory",
        "version": "1.0.0",
        "providers": factory.list_providers(),
        "features": {
            "rag": True,
            "soul_documents": True,
            "twilio_sms": bool(os.getenv("TWILIO_ACCOUNT_SID")),
            "twilio_voice": bool(os.getenv("TWILIO_ACCOUNT_SID")),
            "xai_grok": bool(os.getenv("XAI_API_KEY")),
            "livekit": bool(os.getenv("LIVEKIT_API_KEY")),
            "pinecone_rag": bool(os.getenv("PINECONE_API_KEY")),
            "elk_analytics": bool(os.getenv("ELASTICSEARCH_URL")),
        },
        "channels": ["chat", "voice", "video", "sms", "phone"],
        "timestamp": datetime.utcnow().isoformat(),
    }


# ------------------------------------------------------------------ #
#  Startup                                                             #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"\n🏭 Agent Factory Platform starting on http://0.0.0.0:{port}")
    print(f"📚 API Docs: http://0.0.0.0:{port}/api/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)
