import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";

import { QueryClient, QueryClientProvider } from "react-query";
import { EuiProvider } from "@elastic/eui";

import { appendIconComponentCache } from '@elastic/eui/es/components/icon/icon';
import { icon as arrowDown } from '@elastic/eui/es/components/icon/assets/arrow_down';
import { icon as cross } from '@elastic/eui/es/components/icon/assets/cross';
import { icon as search } from '@elastic/eui/es/components/icon/assets/search';
import { icon as check } from '@elastic/eui/es/components/icon/assets/check';
import { icon as arrowLeft } from '@elastic/eui/es/components/icon/assets/arrow_left';
import { icon as arrowRight } from '@elastic/eui/es/components/icon/assets/arrow_right';
import { icon as sortDown } from '@elastic/eui/es/components/icon/assets/sort_down';
import { icon as sortUp } from '@elastic/eui/es/components/icon/assets/sort_up';

appendIconComponentCache({
  arrowDown,
  cross,
  search,
  check,
  arrowLeft,
  arrowRight,
  sortDown,
  sortUp,
});


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
          <App />
        </EuiProvider>
      </QueryClientProvider>
    </StrictMode>
  );
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
else mount();
