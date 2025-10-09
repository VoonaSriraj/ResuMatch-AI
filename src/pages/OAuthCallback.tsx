import { useEffect } from "react";

export default function OAuthCallback() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    if (window.opener && code) {
      window.opener.postMessage({ code, state }, '*');
      window.close();
    }
  }, []);

  return null;
}


