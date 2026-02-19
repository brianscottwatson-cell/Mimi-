import SEOHead from "../components/SEOHead";
import Breadcrumbs from "../components/Breadcrumbs";
import ContactForm from "../components/ContactForm";

export default function {{COMPONENT_NAME}}() {
  return (
    <>
      <SEOHead
        title="{{PAGE_TITLE}}"
        description="{{META_DESCRIPTION}}"
        canonical="{{CANONICAL_PATH}}"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "Service",
          name: "{{SERVICE_NAME}}",
          description: "{{META_DESCRIPTION}}",
          provider: {
            "@type": "LocalBusiness",
            name: "{{BUSINESS_NAME}}",
          },
          areaServed: "{{AREA_SERVED}}",
        }}
      />

      <div className="container mx-auto px-4 py-8">
        <Breadcrumbs items={[
          { label: "Services", href: "/services" },
          { label: "{{SERVICE_NAME}}" },
        ]} />

        {/* Hero */}
        <section className="py-12">
          <h1 className="text-4xl font-bold mb-4">{{H1_TITLE}}</h1>
          <p className="text-lg text-muted-foreground max-w-2xl">{{HERO_DESCRIPTION}}</p>
        </section>

        {/* Content */}
        <section className="prose max-w-none py-8">
          {{MAIN_CONTENT}}
        </section>

        {/* Why Choose Us */}
        <section className="py-12 bg-muted/50 -mx-4 px-4 rounded-lg">
          <h2 className="text-2xl font-bold mb-6">Pourquoi nous choisir ?</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {{TRUST_SIGNALS}}
          </div>
        </section>

        {/* Service Area */}
        <section className="py-12">
          <h2 className="text-2xl font-bold mb-4">Zone d'intervention</h2>
          <p className="text-muted-foreground">{{AREA_DESCRIPTION}}</p>
        </section>

        {/* Contact Form */}
        <section className="py-12">
          <h2 className="text-2xl font-bold mb-6">Demander un devis gratuit</h2>
          <div className="max-w-xl">
            <ContactForm />
          </div>
        </section>
      </div>
    </>
  );
}
