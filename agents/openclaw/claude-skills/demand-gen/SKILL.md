---
name: demand-gen
description: Multi-channel demand generation campaigns and lead pipeline management. Use when the user needs to generate qualified leads, run paid/organic campaigns, build nurture sequences, or optimize conversion funnels.
---

# Demand Generation Skill

Design, launch, and optimize multi-channel campaigns that generate qualified pipeline.

---

## Why

Demand generation is not lead generation. Lead gen captures existing intent. Demand gen *creates* intent by educating the market, building trust, and making the buying decision feel inevitable. This skill exists to build the full-funnel engine — from awareness through to pipeline — using coordinated campaigns across channels, with measurement at every stage.

**Core belief:** The best demand gen makes selling unnecessary. When done right, buyers arrive pre-educated, pre-qualified, and ready to act.

---

## Map

### Inputs
- ICP and buyer personas (from GTM work or provided)
- Current funnel metrics (traffic, MQLs, SQLs, opportunities, win rate)
- Budget (monthly/quarterly, by channel)
- Content assets available (blog, whitepapers, case studies, webinars)
- Tech stack (CRM, email platform, ad platforms, analytics)
- Sales cycle length and deal size

### Outputs
- **Campaign briefs** — objective, audience, channel, creative, budget, timeline, success metrics
- **Content calendar** — mapped to funnel stages and buyer journey
- **Email nurture sequences** — trigger-based, persona-specific
- **Ad campaign specs** — targeting, creative, budget, bid strategy
- **Landing page specs** — headline, copy, form, CTA, social proof
- **Funnel dashboard** — stage-by-stage conversion rates with targets
- **Attribution model** — how credit is assigned across touchpoints

### Agent Roles
| Agent | Responsibility |
|-------|---------------|
| Mia   | Campaign strategy, channel mix, budget allocation, optimization |
| Rex   | Audience research, keyword data, competitive ad intel |
| Cora  | Ad copy, email sequences, landing page copy, content pieces |
| Dax   | Ad creatives, landing page design, visual assets |
| Finn  | Budget modeling, ROAS tracking, unit economics |
| Pax   | Campaign calendar, cross-channel coordination, launch sequencing |

---

## Rules

1. **Full-funnel or nothing.** Every campaign must address awareness, consideration, and conversion. Single-stage campaigns waste budget.
2. **Audience before channel.** Define who you're reaching before deciding where to reach them.
3. **One CTA per asset.** Landing pages, emails, and ads get one clear call-to-action. No menu of options.
4. **Test creative, not just targeting.** Most campaign failures are creative failures, not targeting failures.
5. **Attribution honesty.** Use multi-touch attribution. Never claim 100% credit for any single channel.
6. **Minimum viable budget.** Don't spread budget across 5 channels at $500 each. Concentrate on 1-2 channels with enough budget to reach statistical significance.
7. **Nurture is not spam.** Email sequences must provide value in every message. If you can't articulate the value, don't send it.
8. **Weekly optimization cadence.** Review performance weekly. Pause underperformers at 2x target CAC. Scale winners by 20% increments.
9. **Content repurposing.** Every long-form piece must be planned for 5+ derivative formats (social posts, email snippets, ad copy, video scripts).

---

## Workflows

### Workflow 1: Campaign Launch

End-to-end campaign from brief to live.

1. **Brief** — Define objective (awareness/pipeline/activation), audience segment, budget, timeline
2. **Research** (Rex) — Audience behavior, keyword opportunities, competitor campaigns, seasonal trends
3. **Strategy** (Mia) — Channel selection, budget allocation, bidding strategy, targeting parameters
4. **Content Creation** (Cora + Dax) — Ad copy variants (min 3), landing page, email sequence, supporting content
5. **Technical Setup** — UTM parameters, tracking pixels, CRM integration, lead scoring rules
6. **Launch Checklist** (Pax):
   - [ ] Tracking verified (UTM, pixels, conversion events)
   - [ ] Landing page live and mobile-tested
   - [ ] Email sequence loaded and trigger-tested
   - [ ] Budget caps set in ad platform
   - [ ] Lead routing confirmed in CRM
7. **Go live** — Stagger channel launches by 24-48 hours for clean attribution
8. **Day 1-3 monitoring** — Check for delivery issues, disapprovals, tracking gaps
9. **Week 1 review** — First optimization pass

### Workflow 2: Email Nurture Sequence

Build a trigger-based nurture sequence for a defined segment.

1. Define entry trigger (form fill, content download, event attendance, etc.)
2. Map the buyer journey for this segment (what questions do they ask at each stage?)
3. Design sequence (typically 5-7 emails over 2-4 weeks):
   - Email 1: Value delivery (give them what they signed up for)
   - Email 2: Problem education (deepen understanding of the problem)
   - Email 3: Social proof (case study, testimonial, data)
   - Email 4: Solution framing (how to evaluate solutions)
   - Email 5: Direct offer (demo, trial, consultation)
   - Email 6-7: Objection handling / urgency (optional, based on engagement)
4. Write copy (Cora) — subject lines (3 variants each), body, CTAs
5. Set branching logic — engagement-based paths (opened/clicked vs. didn't)
6. Define exit criteria — converted, unsubscribed, or completed sequence
7. Load into email platform, test all triggers and links

### Workflow 3: Funnel Optimization

Diagnose and fix conversion bottlenecks.

1. Pull current funnel data: visitors → leads → MQLs → SQLs → opportunities → closed-won
2. Calculate stage-by-stage conversion rates
3. Identify the biggest drop-off (largest absolute gap from benchmark)
4. Diagnose root cause:
   - Top of funnel: traffic quality, ad relevance, landing page alignment
   - Middle of funnel: nurture quality, lead scoring accuracy, content gaps
   - Bottom of funnel: sales handoff, demo quality, proposal timing
5. Design intervention (A/B test, new content, process change)
6. Implement and measure over 2-week sprint
7. Report results and next bottleneck

### Workflow 4: Content Repurposing Engine

Turn one asset into a multi-channel campaign.

1. Identify source asset (webinar, whitepaper, case study, podcast)
2. Extract key insights (3-5 standalone points)
3. Generate derivatives:
   - 5 social posts (LinkedIn, Twitter/X — format-specific)
   - 3 email snippets (for nurture sequences)
   - 2 ad copy variants (for paid social)
   - 1 blog post (SEO-optimized expansion of key point)
   - 1 video script (60-90 seconds)
   - 1 infographic brief
4. Map each derivative to funnel stage and channel
5. Schedule in content calendar

---

## Templates

### Campaign Brief Template
```yaml
campaign_name: ""
objective: ""  # awareness | pipeline | activation
audience_segment: ""
channels: []
budget: ""
timeline:
  start: ""
  end: ""
success_metrics:
  primary: ""  # e.g., "50 MQLs at <$200 CAC"
  secondary: ""
creative_requirements: []
tracking:
  utm_source: ""
  utm_medium: ""
  utm_campaign: ""
```

### Email Sequence Template
```yaml
sequence_name: ""
entry_trigger: ""
exit_criteria: ""
emails:
  - day: 0
    subject_variants: ["", "", ""]
    purpose: ""
    cta: ""
  - day: 3
    subject_variants: ["", "", ""]
    purpose: ""
    cta: ""
```
