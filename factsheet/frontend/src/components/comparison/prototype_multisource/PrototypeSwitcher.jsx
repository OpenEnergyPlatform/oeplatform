// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07) — floating variant switcher. Obviously not part
// of the design under evaluation; dev builds only. ←/→ also cycle (unless an
// input is focused).

import React, { useEffect } from "react";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";

export default function PrototypeSwitcher({
  variants,
  current,
  names,
  onChange,
}) {
  const idx = Math.max(0, variants.indexOf(current));
  const go = (delta) =>
    onChange(variants[(idx + delta + variants.length) % variants.length]);

  useEffect(() => {
    const onKey = (e) => {
      const t = e.target;
      if (
        t &&
        (t.tagName === "INPUT" ||
          t.tagName === "TEXTAREA" ||
          t.isContentEditable)
      )
        return;
      if (e.key === "ArrowLeft") go(-1);
      if (e.key === "ArrowRight") go(1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  return (
    <Box
      sx={{
        position: "fixed",
        bottom: 16,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 2000,
        display: "flex",
        alignItems: "center",
        gap: 1,
        bgcolor: "grey.900",
        color: "grey.100",
        px: 1.5,
        py: 0.5,
        borderRadius: 99,
        boxShadow: 6,
      }}
    >
      <IconButton size="small" sx={{ color: "inherit" }} onClick={() => go(-1)}>
        <ChevronLeftIcon fontSize="small" />
      </IconButton>
      <Typography variant="caption" sx={{ minWidth: 260, textAlign: "center" }}>
        PROTOTYPE {current} — {names[current] || ""}
      </Typography>
      <IconButton size="small" sx={{ color: "inherit" }} onClick={() => go(1)}>
        <ChevronRightIcon fontSize="small" />
      </IconButton>
    </Box>
  );
}
