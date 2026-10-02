// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import React from "react";
import { IriWidget } from "@ts4nfdi/terminology-service-suite";

export default function TssIriWidget({ iri }) {
    return (
        <IriWidget
            iri={iri}
            copyButton="left"
            color="text"
            externalIcon={true}
            className=""
            iriText=""
            urlPrefix=""
        />
    );
}
