import { useState, useEffect } from "react";

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem("cookie-consent");
    if (!consent) setVisible(true);
  }, []);

  const accept = () => {
    localStorage.setItem("cookie-consent", "accepted");
    setVisible(false);
  };

  const refuse = () => {
    localStorage.setItem("cookie-consent", "refused");
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[100] bg-background border-t shadow-lg p-4 md:p-6">
      <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground max-w-2xl">
          Nous utilisons des cookies pour ameliorer votre experience et analyser le trafic.
          Consultez notre{" "}
          <a href="/politique-cookies" className="text-primary underline">politique de cookies</a>{" "}
          pour en savoir plus.
        </p>
        <div className="flex gap-3 flex-shrink-0">
          <button onClick={refuse}
            className="px-4 py-2 text-sm border rounded-md hover:bg-muted transition-colors">
            Refuser
          </button>
          <button onClick={accept}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity font-medium">
            Accepter
          </button>
        </div>
      </div>
    </div>
  );
}
