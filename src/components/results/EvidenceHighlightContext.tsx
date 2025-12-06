'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface EvidenceHighlightContextType {
    highlightedRowIndex: number | null;
    highlightRow: (index: number) => void;
    clearHighlight: () => void;
}

const EvidenceHighlightContext = createContext<EvidenceHighlightContextType | undefined>(undefined);

export function EvidenceHighlightProvider({ children }: { children: ReactNode }) {
    const [highlightedRowIndex, setHighlightedRowIndex] = useState<number | null>(null);

    const highlightRow = (index: number) => {
        setHighlightedRowIndex(index);
        // Auto-clear after some time? Optional. For now per spec "Clicking again clears highlight"
    };

    const clearHighlight = () => {
        setHighlightedRowIndex(null);
    };

    return (
        <EvidenceHighlightContext.Provider value={{ highlightedRowIndex, highlightRow, clearHighlight }}>
            {children}
        </EvidenceHighlightContext.Provider>
    );
}

export function useEvidenceHighlight() {
    const context = useContext(EvidenceHighlightContext);
    if (context === undefined) {
        throw new Error('useEvidenceHighlight must be used within a EvidenceHighlightProvider');
    }
    return context;
}
