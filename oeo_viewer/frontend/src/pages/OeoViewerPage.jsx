import React, { useState } from "react";
import TssAutocomplete from "../features/terminology/components/TssAutocomplete";
import TssMetadata from "../features/terminology/components/TssMetadata";

export default function OeoViewerPage() {
  const [selection, setSelection] = useState(null);

  return (
    <div style={{ padding: 16, maxWidth: 800 }}>
      <h1>OEO Viewer</h1>

      <TssAutocomplete
        // api defaults to the gateway, override if you host your own
        // ontology="OEO"
        onChange={(sel) => setSelection(sel)}
      />
      <TssMetadata/>

      <pre style={{ marginTop: 12, padding: 12, background: "#f6f6f6" }}>
        {JSON.stringify(selection, null, 2)}
      </pre>
    </div>
  );
}
