import SEOHead from "../components/SEOHead";
import Breadcrumbs from "../components/Breadcrumbs";

export default function {{COMPONENT_NAME}}() {
  return (
    <>
      <SEOHead
        title="{{PAGE_TITLE}}"
        description="{{META_DESCRIPTION}}"
        canonical="{{CANONICAL_PATH}}"
      />

      <div className="container mx-auto px-4 py-8">
        <Breadcrumbs items={[{ label: "{{BREADCRUMB_LABEL}}" }]} />

        <article className="prose max-w-3xl mx-auto py-8">
          <h1>{{H1_TITLE}}</h1>
          <p className="text-sm text-muted-foreground">Derniere mise a jour : {{LAST_UPDATED}}</p>

          {{LEGAL_CONTENT}}
        </article>
      </div>
    </>
  );
}
