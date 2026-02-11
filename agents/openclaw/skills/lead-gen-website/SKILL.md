# Lead Generation Website Builder

Build conversion-optimized local service websites with complete SEO, tracking, and RGPD compliance — avec garde-fous anti-spam (Google Spam Policies + March 2024), local SEO (GBP) et micro-budget ads.

## When to Use This Skill

Use this skill when the user requests a website for:
- Local service businesses (home services, repairs, professional services)
- Lead generation focused on specific geographic areas
- Sites requiring 10-20+ pages with service pages, blog, and legal pages
- SEO-optimized content targeting local keywords
- Conversion tracking (phone, WhatsApp, forms with UTM parameters)
- RGPD/GDPR compliance (cookie banner, privacy policy, legal pages)

## Workflow Overview

Follow these phases sequentially. Do NOT skip phases or combine them without clear reason.

### Policy / Risk Check (mandatory)
1. Read `references/google-spam-guardrails-2024.md`
2. Explicitly verify: no doorway pages, no scaled generic content, no fake address/avis, no misleading claims.
3. If the project is mise en relation (leadgen): require clear disclosure on all key pages.
4. Then continue with Phases 1-7.

### Phase 1: Analysis and Planning
Gather project requirements from the user or specifications document.

**Required information:**
- Business niche and services offered
- Geographic target area (city + radius)
- Target keywords for SEO
- Contact information (phone, WhatsApp, email)
- Number and types of pages needed
- Competitor websites (for differentiation)

**Output:** Clear understanding of project scope, target audience, and conversion goals.

### Phase 2: Design Brainstorming
Create `ideas.md` in the project root with THREE distinct design approaches.

Use `templates/design-ideas-template.md` as structure. Each approach must define:
- Design movement and aesthetic philosophy
- Color palette with hex codes and emotional intent
- Typography system (headings + body fonts)
- Layout paradigm (avoid generic centered layouts)
- Signature visual elements
- Animation guidelines
- Interaction philosophy

Consult `references/design-philosophies.md` for inspiration, but create original combinations.

**Selection:** Choose ONE approach and document the rationale. This design philosophy will guide ALL subsequent design decisions.

### Phase 3: Visual Assets Generation
Generate 3-5 high-quality images. These images MUST:
- Align with the chosen design philosophy (colors, mood, style)
- Cover key visual needs: hero background, service illustrations, local landmarks, team/artisan photos

Plan strategic usage:
- Hero section: Most impactful image
- Service pages: Relevant illustrations
- About/Trust sections: Team or local landmark photos

Do NOT generate images on-the-fly during development. Generate all at once for efficiency.

### Phase 4: Content Structure
Create detailed content structure for all pages.

**Option A (Manual):** Write `content-structure.md` directly with sections for each page including title, meta description, H1, and main content outline.

**Option B (Script):** Create `specs.json` with page data, then run:
```
python scripts/generate_content_structure.py specs.json content-structure.md
```

**Content requirements:**
- Minimum 500 words per main page (homepage, main services)
- Minimum 1000 words per blog article
- Include target keywords naturally (no stuffing)
- Answer user intent (what, why, how, cost, area)
- Local focus (mention city/region frequently)

### Phase 5: Development
Initialize project and build all pages.

#### 5.1 Initialize Project
Create project directory with standard structure.

#### 5.2 Configure Design Tokens
Edit `client/src/index.css` with chosen design philosophy:
- Update CSS variables for colors (primary, secondary, accent, background, foreground)
- Configure typography (font-family for sans, serif)
- Adjust shadows, radius, animations

#### 5.3 Create Reusable Components
Use templates from `templates/` directory. Replace placeholders with project-specific values:

**Header** (`templates/component-Header.tsx`):
- `{{SITE_NAME}}`, `{{SITE_TAGLINE}}`, `{{SITE_INITIALS}}`
- `{{PHONE_NUMBER}}`, `{{WHATSAPP_NUMBER}}`
- `{{NAV_ITEMS}}` (JSON array of {label, href})

**Footer** (`templates/component-Footer.tsx`):
- `{{SITE_NAME}}`, `{{SITE_DESCRIPTION}}`
- `{{SERVICE_LINKS}}`, `{{UTILITY_LINKS}}`
- `{{PHONE_NUMBER}}`, `{{EMAIL}}`, `{{LOCATION}}`

**SEOHead** (`templates/component-SEOHead.tsx`):
- Replace `{{DOMAIN}}` with actual domain

Other components: Breadcrumbs, ContactForm, CookieBanner (copy as-is, minimal customization needed)

#### 5.4 Build Pages
- **Similar pages** (services, blog): Use template + data JSON + batch generation script
- **Unique pages** (homepage, pricing, FAQ, contact): Build manually with rich content
- **Legal pages**: Use `templates/page-legal-template.tsx` with standard legal content

#### 5.5 Update App.tsx
Add all routes and integrate Header, Footer, and CookieBanner in App layout.

### Phase 6: SEO, Tracking, GBP, Ads

#### 6.1 Generate SEO Files
Create `pages.json` with all URLs and priorities, then run:
```
python scripts/create_seo_files.py yourdomain.com pages.json client/public/
```

#### 6.2 Add Structured Data
Add JSON-LD structured data to key pages (LocalBusiness, Service schemas).

#### 6.3 RGPD Compliance
Verify: CookieBanner, privacy policy, cookie policy, legal mentions, form consent links.

#### 6.4 GBP / Local SEO
Read and apply: `references/gbp-local-seo-playbook.md`

Deliverables:
- GBP setup checklist
- 30-day photo/post/review plan
- NAP citations list (quality-first, no spam)

#### 6.5 Micro-budget Ads (4EUR/day)
Read and apply: `references/ads-micro-budget-4eur-playbook.md`

Deliverables:
- 1 ultra-tight campaign (exact/phrase keywords, geo, schedule, negatives)
- 1 dedicated landing page + tracking

#### 6.6 Conversion Tracking
ContactForm component captures UTM parameters (source, campaign, adset, ad) for attribution.

### Phase 7: Validation and Delivery

#### 7.1 Test in Browser
Verify: all pages load, navigation works, forms submit, mobile responsive, cookie banner, images load.

#### 7.2 SEO Validation
Check against `references/seo-checklist.md`: unique titles, H1 hierarchy, alt tags, robots.txt, sitemap.xml, structured data.

#### 7.3 Deliver
Summary of what was built, page count, SEO optimizations, next steps.

## Bundled Resources

### Scripts
- `scripts/generate_pages_batch.py` — Generate multiple similar pages from template and data file
- `scripts/create_seo_files.py` — Generate robots.txt and sitemap.xml
- `scripts/generate_content_structure.py` — Create content structure from specs JSON

### Templates
**Components:**
- `component-Header.tsx` — Sticky header with logo, nav, CTA
- `component-Footer.tsx` — Footer with links and contact info
- `component-SEOHead.tsx` — SEO meta tags and structured data
- `component-Breadcrumbs.tsx` — Navigation breadcrumbs
- `component-ContactForm.tsx` — Form with UTM tracking
- `component-CookieBanner.tsx` — RGPD cookie consent banner

**Pages:**
- `page-service-template.tsx` — Service page template
- `page-legal-template.tsx` — Legal page template
- `design-ideas-template.md` — Design brainstorming structure

### References
- `seo-checklist.md` — Complete SEO checklist
- `conversion-best-practices.md` — CTA, trust signals, form optimization
- `rgpd-compliance.md` — Full RGPD/GDPR compliance guide
- `design-philosophies.md` — Five example design approaches
- `google-spam-guardrails-2024.md` — Anti-spam policy compliance
- `gbp-local-seo-playbook.md` — Google Business Profile playbook
- `ads-micro-budget-4eur-playbook.md` — Low-budget Google Ads guide
- `whatsapp-ops-qualification.md` — WhatsApp lead qualification ops
