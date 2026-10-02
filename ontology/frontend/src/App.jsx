// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { EuiProvider } from '@elastic/eui';
import TssConfigProvider from './features/terminology/config/TssConfigProvider';

// Your Pages
import EntitySearchPage from './pages/EntitySearchPage';
import OeoIriPages from './pages/OeoIriPages'; // Reusing your IRI page

// // Helper to extract parameters for the detail page
// const EntityDetailWrapper = () => {
//   const { ontology, short_form } = useParams();
//   // Construct the full IRI or pass the short_form to your component
//   const iri = `https://openenergyplatform.org/ontology/${ontology}/${short_form}`;
//   return <OeoIriPages iri={iri} />;
// };

const EntityDetailWrapper = () => {
  // We no longer construct the IRI here!
  // We let OeoIriPages do the smart resolution.
  return <OeoIriPages />;
};

export default function App() {
  return (
    <EuiProvider colorMode="light">
      <TssConfigProvider>
        {/* Base must match the Django app mount point */}
        <BrowserRouter basename="/ontology">
          <Routes>
            {/* Captured Variables:
                :ontology -> "oeo"
            */}
            <Route path=":ontology/entities" element={<EntitySearchPage />} />

            {/* Captured Variables:
                :ontology -> "oeo"
                :short_form -> "OEO_00000040"
            */}
            <Route path=":ontology/:short_form" element={<EntityDetailWrapper />} />

            <Route path="*" element={<div>Page not found</div>} />
          </Routes>
        </BrowserRouter>
      </TssConfigProvider>
    </EuiProvider>
  );
};
