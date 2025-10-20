import React, { createContext, useContext, useMemo } from "react";

const TssConfigCtx = createContext(null);

export function TssConfigProvider({
    children,
    // read from Vite env (fallback to OLS API + OEO)
    apiBase = import.meta.env.VITE_TSS_API_BASE ?? "https://api.terminology.tib.eu/api/",
    ontology = import.meta.env.VITE_TSS_DEFAULT_ONTOLOGY ?? "oeo",
    lang = import.meta.env.VITE_TSS_LANG ?? "en",
    requestHeaders = {},
}) {
    const value = useMemo(() => ({ apiBase, ontology, lang, requestHeaders }), [
        apiBase, ontology, lang, requestHeaders,
    ]);
    return <TssConfigCtx.Provider value={value}>{children}</TssConfigCtx.Provider>;
}

export function useTssConfigCtx() {
    const ctx = useContext(TssConfigCtx);
    if (!ctx) throw new Error("useTssConfigCtx must be used within <TssConfigProvider>");
    return ctx;
}
