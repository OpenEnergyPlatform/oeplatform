// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { createContext, useContext, useMemo } from "react";

const TssConfigCtx = createContext(null);

export function TssConfigProvider({
    children,
    // read from Vite env at build time, else the TIB terminology service + OEO
    apiBase = import.meta.env.VITE_TSS_API_BASE || "https://api.terminology.tib.eu/api/",
    ontology = import.meta.env.VITE_TSS_DEFAULT_ONTOLOGY || "oeo",
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

export default TssConfigProvider;
