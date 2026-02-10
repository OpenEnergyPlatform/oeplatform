// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";

import { QueryClient, QueryClientProvider } from "react-query";
import { EuiProvider } from "@elastic/eui";

import { TssConfigProvider } from "./features/terminology/config/TssConfigProvider";



// one client for the whole app
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function mount() {
  const el = document.getElementById("main");
  if (!el || el.dataset.mounted) return;
  el.dataset.mounted = "1";
  createRoot(el).render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <EuiProvider colorMode="light">
          <TssConfigProvider>
            <App />
          </TssConfigProvider>
        </EuiProvider>
      </QueryClientProvider>
    </StrictMode>
  );
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
else mount();
