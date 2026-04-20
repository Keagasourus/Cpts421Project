/**
 * Frontend tests for ArtifactGrid component.
 * Covers Normal, Edge, and Extraordinary cases per testing rules.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ArtifactGrid from '../components/ArtifactGrid';

// Helper to render within a Router context (required for Link components)
const renderWithRouter = (ui) => render(<MemoryRouter>{ui}</MemoryRouter>);

// ---------------------------------------------------------------------------
// Normal Cases (Happy Path)
// ---------------------------------------------------------------------------

describe('ArtifactGrid', () => {
  describe('Normal Cases', () => {
    it('rendersArtifactCards_whenGivenValidData', () => {
      const artifacts = [
        {
          id: 1,
          object_type: 'Mosaic',
          date_display: 'c. 300 AD',
          images: [{ file_url: 'http://localhost:9000/uploads/test.jpg' }],
        },
        {
          id: 2,
          object_type: 'Coin',
          date_display: 'c. 500 AD',
          images: [{ file_url: 'http://localhost:9000/uploads/coin.jpg' }],
        },
      ];

      renderWithRouter(
        <ArtifactGrid artifacts={artifacts} loading={false} error={null} />
      );

      expect(screen.getByText('Mosaic')).toBeInTheDocument();
      expect(screen.getByText('Coin')).toBeInTheDocument();
      expect(screen.getByText('c. 300 AD')).toBeInTheDocument();
      expect(screen.getByText('c. 500 AD')).toBeInTheDocument();
    });

    it('rendersCorrectLinks_forEachArtifact', () => {
      const artifacts = [
        { id: 42, object_type: 'Bowl', date_display: 'c. 700 AD', images: [] },
      ];

      renderWithRouter(
        <ArtifactGrid artifacts={artifacts} loading={false} error={null} />
      );

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '/objects/42');
    });

    it('rendersLoadingState_whenLoading', () => {
      renderWithRouter(
        <ArtifactGrid artifacts={[]} loading={true} error={null} />
      );

      expect(screen.getByText('Loading artifacts...')).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Edge Cases (Boundary Conditions)
  // ---------------------------------------------------------------------------

  describe('Edge Cases', () => {
    it('rendersNoArtifactsMessage_whenEmptyArray', () => {
      renderWithRouter(
        <ArtifactGrid artifacts={[]} loading={false} error={null} />
      );

      expect(screen.getByText('No artifacts found.')).toBeInTheDocument();
    });

    it('rendersFallbackImage_whenNoImagesArray', () => {
      const artifacts = [
        { id: 1, object_type: 'Tile', date_display: 'c. 400 AD', images: [] },
      ];

      renderWithRouter(
        <ArtifactGrid artifacts={artifacts} loading={false} error={null} />
      );

      const img = screen.getByAltText('Tile');
      expect(img.src).toContain('placeholder');
    });

    it('rendersSingleArtifact_whenOnlyOneItem', () => {
      const artifacts = [
        {
          id: 99,
          object_type: 'Amulet',
          date_display: 'c. 250 AD',
          images: [{ file_url: 'http://localhost:9000/img.jpg' }],
        },
      ];

      renderWithRouter(
        <ArtifactGrid artifacts={artifacts} loading={false} error={null} />
      );

      expect(screen.getByText('Amulet')).toBeInTheDocument();
      expect(screen.getAllByRole('link')).toHaveLength(1);
    });
  });

  // ---------------------------------------------------------------------------
  // Extraordinary Cases (Sad Path)
  // ---------------------------------------------------------------------------

  describe('Extraordinary Cases', () => {
    it('rendersErrorMessage_whenErrorProvided', () => {
      renderWithRouter(
        <ArtifactGrid artifacts={[]} loading={false} error={new Error('Network fail')} />
      );

      expect(screen.getByText('Error loading artifacts.')).toBeInTheDocument();
    });

    it('rendersNoArtifactsMessage_whenNull', () => {
      renderWithRouter(
        <ArtifactGrid artifacts={null} loading={false} error={null} />
      );

      expect(screen.getByText('No artifacts found.')).toBeInTheDocument();
    });

    it('rendersNoArtifactsMessage_whenUndefined', () => {
      renderWithRouter(
        <ArtifactGrid artifacts={undefined} loading={false} error={null} />
      );

      expect(screen.getByText('No artifacts found.')).toBeInTheDocument();
    });
  });
});
