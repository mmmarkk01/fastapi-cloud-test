"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [msg, setMsg] = useState("loading /api/hello …");

  useEffect(() => {
    fetch("/api/hello")
      .then((r) => r.json())
      .then((d) => setMsg(JSON.stringify(d)))
      .catch((e) => setMsg("error: " + e));
  }, []);

  return (
    <main
      style={{
        fontFamily: "system-ui, sans-serif",
        padding: "2rem",
        maxWidth: "36rem",
        margin: "0 auto",
      }}
    >
      <h1>FastAPI + Next.js static export</h1>
      <p>
        This static Next.js page is served by FastAPI via <code>app.frontend()</code>{" "}
        and calls the API:
      </p>
      <pre>{msg}</pre>
    </main>
  );
}
