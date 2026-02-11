import { useState, useEffect } from "react";

interface FormData {
  name: string;
  phone: string;
  email: string;
  service: string;
  message: string;
  consent: boolean;
  // UTM tracking
  utm_source: string;
  utm_campaign: string;
  utm_adset: string;
  utm_ad: string;
}

export default function ContactForm() {
  const [form, setForm] = useState<FormData>({
    name: "", phone: "", email: "", service: "", message: "", consent: false,
    utm_source: "", utm_campaign: "", utm_adset: "", utm_ad: "",
  });
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");

  // Capture UTM parameters from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setForm((prev) => ({
      ...prev,
      utm_source: params.get("utm_source") || "",
      utm_campaign: params.get("utm_campaign") || "",
      utm_adset: params.get("utm_adset") || "",
      utm_ad: params.get("utm_ad") || "",
    }));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.consent) return;
    setStatus("sending");
    try {
      // Replace with your form endpoint (Formspree, Netlify Forms, custom API, etc.)
      const resp = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      setStatus(resp.ok ? "sent" : "error");
    } catch {
      setStatus("error");
    }
  };

  if (status === "sent") {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <h3 className="text-lg font-semibold text-green-800 mb-2">Message envoye !</h3>
        <p className="text-green-700">Nous vous recontactons dans les plus brefs delais.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid md:grid-cols-2 gap-4">
        <input name="name" value={form.name} onChange={handleChange} required placeholder="Votre nom *"
          className="w-full px-4 py-3 border rounded-md bg-background" />
        <input name="phone" value={form.phone} onChange={handleChange} required placeholder="Telephone *" type="tel"
          className="w-full px-4 py-3 border rounded-md bg-background" />
      </div>
      <input name="email" value={form.email} onChange={handleChange} placeholder="Email" type="email"
        className="w-full px-4 py-3 border rounded-md bg-background" />
      <select name="service" value={form.service} onChange={handleChange}
        className="w-full px-4 py-3 border rounded-md bg-background">
        <option value="">-- Choisir un service --</option>
        {/* Add service options dynamically */}
      </select>
      <textarea name="message" value={form.message} onChange={handleChange} rows={4}
        placeholder="Decrivez votre besoin..." className="w-full px-4 py-3 border rounded-md bg-background" />

      <label className="flex items-start gap-2 text-sm">
        <input type="checkbox" checked={form.consent}
          onChange={(e) => setForm((prev) => ({ ...prev, consent: e.target.checked }))}
          className="mt-1" required />
        <span>
          J'accepte que mes donnees soient traitees conformement a la{" "}
          <a href="/politique-confidentialite" className="text-primary underline">politique de confidentialite</a>.
        </span>
      </label>

      {/* Hidden UTM fields */}
      <input type="hidden" name="utm_source" value={form.utm_source} />
      <input type="hidden" name="utm_campaign" value={form.utm_campaign} />
      <input type="hidden" name="utm_adset" value={form.utm_adset} />
      <input type="hidden" name="utm_ad" value={form.utm_ad} />

      <button type="submit" disabled={status === "sending" || !form.consent}
        className="w-full bg-primary text-primary-foreground py-3 rounded-md font-semibold hover:opacity-90 transition-opacity disabled:opacity-50">
        {status === "sending" ? "Envoi en cours..." : "Envoyer ma demande"}
      </button>

      {status === "error" && (
        <p className="text-red-500 text-sm text-center">Une erreur est survenue. Veuillez reessayer.</p>
      )}
    </form>
  );
}
