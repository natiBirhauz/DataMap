import React from 'react';
import { render, screen } from '@testing-library/react';

// Mock react-leaflet and leaflet for Jest's CommonJS environment
jest.mock('react-leaflet', () => ({
  MapContainer: ({ children }) => <div data-testid="map-container">{children}</div>,
  TileLayer: (props) => <div data-testid="tile-layer" data-url={props.url} data-attribution={props.attribution} />,
  useMap: () => ({
    removeLayer: jest.fn(),
    addLayer: jest.fn(),
  }),
}));

jest.mock('leaflet', () => ({
  geoJSON: () => ({
    addTo: jest.fn(),
  }),
}));

import App from './App';

test('renders DataMap title and search input without API key requirements', () => {
  render(<App />);

  // Check header logo/title
  const titleElement = screen.getByText(/DataMap/i);
  expect(titleElement).toBeInTheDocument();

  // Check search input placeholder
  const searchInput = screen.getByPlaceholderText(/Ask a question about the world/i);
  expect(searchInput).toBeInTheDocument();

  // Verify that the tile layer uses OpenStreetMap (no CARTO watermark)
  const tileLayer = screen.getByTestId('tile-layer');
  expect(tileLayer.getAttribute('data-url')).toContain('openstreetmap.org');

  // Verify that there is NO API key button or modal prompt anywhere in the DOM
  expect(screen.queryByText(/Your OpenAI API Key/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/Add API key/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/Key saved/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/Limit Reached/i)).not.toBeInTheDocument();
});
