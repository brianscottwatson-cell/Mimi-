---
name: customer-onboarding
description: Post-sale customer onboarding journeys and activation workflows. Use when the user needs to design onboarding experiences, build activation sequences, create training materials, or reduce time-to-value for new customers.
---

# Customer Onboarding Skill

Design and execute structured onboarding journeys that accelerate time-to-value and drive long-term retention.

---

## Why

The moment after a customer signs is the highest-risk, highest-opportunity window in the entire relationship. Buyers have peak motivation but also peak anxiety ("did I make the right choice?"). This skill exists to convert that energy into momentum — getting the customer to their first meaningful outcome as fast as possible, then building the habits that drive retention.

**Core belief:** Onboarding is not training. It is the systematic elimination of every barrier between the customer and their first success.

---

## Map

### Inputs
- Product/service being onboarded to
- Customer segment (SMB, mid-market, enterprise, consumer)
- Expected time-to-value (days/weeks)
- Key activation milestones (what does "success" look like in week 1, month 1?)
- Customer data available at signup (industry, role, goals, company size)
- Support channels available (email, chat, phone, in-app, dedicated CSM)
- Tech stack for delivery (product analytics, email, in-app messaging, LMS)

### Outputs
- **Onboarding journey map** — phased timeline with milestones, touchpoints, and owners
- **Welcome sequence** — emails + in-app messages for first 14 days
- **Activation checklist** — key actions the customer must complete
- **Training materials** — guides, videos, walkthroughs (scoped to essentials only)
- **Health score definition** — leading indicators of successful vs. at-risk onboarding
- **Escalation triggers** — when to involve a human (CSM, support, executive)
- **Handoff protocol** — from onboarding to ongoing success/support

### Agent Roles
| Agent | Responsibility |
|-------|---------------|
| Pax   | Journey design, milestone sequencing, coordination |
| Cora  | Welcome emails, help docs, training copy, in-app messages |
| Dax   | Onboarding UI flows, visual guides, video storyboards |
| Vex   | Walkthrough videos, tutorial recordings |
| Mia   | Activation campaigns, re-engagement triggers, behavioral emails |
| Finn  | Onboarding cost analysis, retention impact modeling |
| Dev   | In-app onboarding flows, API integrations, automation |

---

## Rules

1. **First value in first session.** The customer must experience a meaningful outcome in their first interaction. If this takes more than 30 minutes, simplify.
2. **Progressive disclosure.** Don't teach everything at once. Introduce features as they become relevant to the customer's journey stage.
3. **Action over education.** Every onboarding touchpoint should end with a specific action, not just information.
4. **Segment the journey.** Different customer segments need different paths. An enterprise customer and a self-serve SMB cannot share an onboarding flow.
5. **Measure activation, not completion.** "Completed onboarding" is vanity. "Achieved first [outcome]" is the metric that matters.
6. **Human touch at friction points.** Automate the easy parts. Insert human contact at the moments that cause the most drop-off.
7. **48-hour rule.** If a new customer hasn't taken their first key action within 48 hours, trigger an intervention (automated or human).
8. **Don't onboard to features, onboard to outcomes.** Frame everything around what the customer is trying to achieve, not what buttons to click.

---

## Workflows

### Workflow 1: Full Onboarding Journey Design

Design a complete onboarding experience from scratch.

1. **Discovery**
   - What does the customer need to achieve? (their goal, not your product's features)
   - What are the 3-5 activation milestones?
   - What are the common failure points in current onboarding?
   - What data do we have at signup to personalize?

2. **Journey Mapping** (Pax)
   - Define phases: Welcome (Day 0-1) → Setup (Day 1-3) → First Value (Day 3-7) → Habit Building (Day 7-30) → Handoff (Day 30+)
   - For each phase: entry criteria, key actions, success indicators, exit criteria
   - Map touchpoints: email, in-app, video, human

3. **Activation Checklist** — Define the 5-7 actions that correlate with long-term retention
   - Example: "Created first project" → "Invited a team member" → "Completed first [workflow]" → "Connected integration" → "Achieved first [outcome]"

4. **Content Creation** (Cora + Dax + Vex)
   - Welcome email sequence (5-7 emails over 14 days)
   - In-app onboarding checklist
   - 2-3 short video walkthroughs (< 3 minutes each)
   - Quick-start guide (1-page, scannable)

5. **Automation Setup** (Dev + Mia)
   - Behavioral triggers (if user hasn't done X by day Y, send Z)
   - Health score calculation (composite of activation milestones completed)
   - Escalation rules (health score < threshold → alert CSM)

6. **Segmentation** — Adapt the journey for each customer segment
   - Self-serve: fully automated, in-app guided
   - Mid-market: automated + scheduled check-in call at Day 7
   - Enterprise: dedicated CSM, custom kickoff, weekly syncs

7. **Measurement**
   - Time to first value (median, by segment)
   - Activation rate (% completing all checklist items by Day 30)
   - Day 7 / Day 30 / Day 90 retention rates
   - Onboarding NPS or CSAT

8. **Review checkpoint** — Present journey map for human approval

### Workflow 2: Welcome Email Sequence

Build the post-signup email series.

1. Define sequence goal (activate, educate, or retain)
2. Map to activation milestones
3. Design sequence:
   - **Email 1 (Day 0):** Welcome + single most important first action
   - **Email 2 (Day 1):** Quick win tutorial (show the fastest path to value)
   - **Email 3 (Day 3):** Social proof (customer story achieving what they want)
   - **Email 4 (Day 5):** Feature spotlight (the one feature that drives retention)
   - **Email 5 (Day 7):** Check-in (how's it going? + offer help)
   - **Email 6 (Day 10):** Advanced tip (reward engaged users)
   - **Email 7 (Day 14):** Milestone celebration or re-engagement
4. Write copy (Cora) — personal, helpful, action-oriented
5. Set behavioral branching — skip ahead if milestone already completed
6. Define re-engagement path for non-responders

### Workflow 3: At-Risk Customer Intervention

Detect and recover customers showing signs of churn during onboarding.

1. Define risk signals:
   - No login in 48+ hours after signup
   - Activation checklist < 50% complete by Day 7
   - Support ticket filed and unresolved
   - Health score declining
2. Design intervention ladder:
   - **Level 1 (automated):** Behavioral email with specific help offer
   - **Level 2 (automated + human):** In-app message + CSM notification
   - **Level 3 (human):** Direct outreach (call/video) from CSM
   - **Level 4 (executive):** Exec-to-exec outreach for high-value accounts
3. Set SLAs for each level (e.g., Level 2 within 24 hours of trigger)
4. Track intervention success rate and iterate

---

## Templates

### Onboarding Journey Template
```yaml
journey_name: ""
customer_segment: ""
time_to_value_target: ""
phases:
  - name: "Welcome"
    days: "0-1"
    goal: ""
    touchpoints: []
    success_indicator: ""
  - name: "Setup"
    days: "1-3"
    goal: ""
    touchpoints: []
    success_indicator: ""
  - name: "First Value"
    days: "3-7"
    goal: ""
    touchpoints: []
    success_indicator: ""
  - name: "Habit Building"
    days: "7-30"
    goal: ""
    touchpoints: []
    success_indicator: ""
activation_checklist:
  - action: ""
    target_day: ""
    tracking_event: ""
health_score:
  metrics: []
  at_risk_threshold: ""
```
