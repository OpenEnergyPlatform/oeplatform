// SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
//
// SPDX-License-Identifier: MIT

import { render, screen } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  render(<App />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
