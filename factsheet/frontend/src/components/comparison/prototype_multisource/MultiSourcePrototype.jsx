// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07) — multi-source selection for the Registry
// (beta) view. Three structurally different variants on the existing route,
// switchable via ?variant= (A|B|C, plus 0 = today's single-source view for
// contrast). Shared state lives in useMultiSource so switching variants
// keeps the selection. Dev builds only — production falls back to the
// current RegistryComparison.
//
// Plan: "Three variants of multi-source selection, switchable via ?variant=,
// mounted on the Registry (beta) tab of the comparison route."

import React from "react";
import { useSearchParams } from "react-router-dom";
import Alert from "@mui/material/Alert";
import LinearProgress from "@mui/material/LinearProgress";
import RegistryComparison from "../RegistryComparison.jsx";
import useMultiSource from "./useMultiSource.js";
import PrototypeSwitcher from "./PrototypeSwitcher.jsx";
import VariantA, { VARIANT_NAME as NAME_A } from "./VariantA_Gallery.jsx";
import VariantB, { VARIANT_NAME as NAME_B } from "./VariantB_Rail.jsx";
import VariantC, { VARIANT_NAME as NAME_C } from "./VariantC_Sentence.jsx";

const VARIANTS = ["A", "B", "C", "0"];
const NAMES = {
  A: NAME_A,
  B: NAME_B,
  C: NAME_C,
  0: "today's single-source view",
};

export default function MultiSourcePrototype() {
  const [params, setParams] = useSearchParams();
  const variant = params.get("variant") || "A";
  const ms = useMultiSource();

  // stray-merge safety: outside dev builds this IS the current view
  if (!import.meta.env.DEV) return <RegistryComparison />;

  const setVariant = (v) => {
    const next = new URLSearchParams(params);
    next.set("variant", v);
    setParams(next, { replace: true });
  };

  let body = null;
  if (variant === "0") body = <RegistryComparison />;
  else if (ms.registryLoading) body = <LinearProgress />;
  else if (ms.registryError)
    body = (
      <Alert severity="error">Could not load the registry contract.</Alert>
    );
  else if (variant === "B") body = <VariantB ms={ms} />;
  else if (variant === "C") body = <VariantC ms={ms} />;
  else body = <VariantA ms={ms} />;

  return (
    <>
      {body}
      <PrototypeSwitcher
        variants={VARIANTS}
        current={VARIANTS.includes(variant) ? variant : "A"}
        names={NAMES}
        onChange={setVariant}
      />
    </>
  );
}
