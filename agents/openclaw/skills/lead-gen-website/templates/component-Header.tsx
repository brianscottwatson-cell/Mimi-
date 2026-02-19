import { useState } from "react";

const navItems: { label: string; href: string }[] = {{NAV_ITEMS}};

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-background/95 backdrop-blur border-b">
      <div className="container mx-auto flex items-center justify-between py-3 px-4">
        {/* Logo / Brand */}
        <a href="/" className="flex items-center gap-2">
          <span className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg">
            {{SITE_INITIALS}}
          </span>
          <div>
            <span className="font-bold text-lg">{{SITE_NAME}}</span>
            <span className="block text-xs text-muted-foreground">{{SITE_TAGLINE}}</span>
          </div>
        </a>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6">
          {navItems.map((item) => (
            <a key={item.href} href={item.href} className="text-sm hover:text-primary transition-colors">
              {item.label}
            </a>
          ))}
        </nav>

        {/* CTA Buttons */}
        <div className="hidden md:flex items-center gap-3">
          <a href="tel:{{PHONE_NUMBER}}" className="text-sm font-medium hover:text-primary">
            {{PHONE_NUMBER}}
          </a>
          <a
            href="https://wa.me/{{WHATSAPP_NUMBER}}"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-green-500 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-600 transition-colors"
          >
            WhatsApp
          </a>
        </div>

        {/* Mobile Menu Toggle */}
        <button className="md:hidden p-2" onClick={() => setMenuOpen(!menuOpen)} aria-label="Menu">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="md:hidden border-t bg-background px-4 py-4 space-y-3">
          {navItems.map((item) => (
            <a key={item.href} href={item.href} className="block text-sm py-2 hover:text-primary">
              {item.label}
            </a>
          ))}
          <div className="flex gap-2 pt-2 border-t">
            <a href="tel:{{PHONE_NUMBER}}" className="flex-1 text-center bg-primary text-primary-foreground py-2 rounded-md text-sm font-medium">
              Appeler
            </a>
            <a href="https://wa.me/{{WHATSAPP_NUMBER}}" className="flex-1 text-center bg-green-500 text-white py-2 rounded-md text-sm font-medium">
              WhatsApp
            </a>
          </div>
        </div>
      )}

      {/* Sticky Mobile CTA */}
      <div className="fixed bottom-0 left-0 right-0 md:hidden bg-background border-t z-50 flex">
        <a href="tel:{{PHONE_NUMBER}}" className="flex-1 text-center py-3 bg-primary text-primary-foreground font-medium text-sm">
          Appeler maintenant
        </a>
        <a href="https://wa.me/{{WHATSAPP_NUMBER}}" className="flex-1 text-center py-3 bg-green-500 text-white font-medium text-sm">
          WhatsApp
        </a>
      </div>
    </header>
  );
}
