const serviceLinks: { label: string; href: string }[] = {{SERVICE_LINKS}};
const utilityLinks: { label: string; href: string }[] = {{UTILITY_LINKS}};

export default function Footer() {
  return (
    <footer className="bg-foreground/5 border-t mt-auto">
      <div className="container mx-auto px-4 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <h3 className="font-bold text-lg mb-2">{{SITE_NAME}}</h3>
            <p className="text-sm text-muted-foreground">{{SITE_DESCRIPTION}}</p>
          </div>

          {/* Services */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase tracking-wider">Services</h4>
            <ul className="space-y-2">
              {serviceLinks.map((link) => (
                <li key={link.href}>
                  <a href={link.href} className="text-sm text-muted-foreground hover:text-primary transition-colors">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Useful Links */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase tracking-wider">Informations</h4>
            <ul className="space-y-2">
              {utilityLinks.map((link) => (
                <li key={link.href}>
                  <a href={link.href} className="text-sm text-muted-foreground hover:text-primary transition-colors">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase tracking-wider">Contact</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="tel:{{PHONE_NUMBER}}" className="hover:text-primary">{{PHONE_NUMBER}}</a>
              </li>
              <li>
                <a href="mailto:{{EMAIL}}" className="hover:text-primary">{{EMAIL}}</a>
              </li>
              <li>{{LOCATION}}</li>
            </ul>
          </div>
        </div>

        <div className="border-t mt-8 pt-6 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-muted-foreground">
          <p>&copy; {new Date().getFullYear()} {{SITE_NAME}}. Tous droits reserves.</p>
          <div className="flex gap-4">
            <a href="/mentions-legales" className="hover:text-primary">Mentions legales</a>
            <a href="/politique-confidentialite" className="hover:text-primary">Confidentialite</a>
            <a href="/politique-cookies" className="hover:text-primary">Cookies</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
