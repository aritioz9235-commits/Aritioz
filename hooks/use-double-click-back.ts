'use client';

import { useCallback } from 'react';
import type { MouseEvent } from 'react';

import { handleDoubleClickBack } from '@/lib/double-click-back';

export function useDoubleClickBack(back: () => void) {
  return useCallback((event: MouseEvent<HTMLElement>) => {
    handleDoubleClickBack(event, back, window.getSelection()?.toString() ?? '');
  }, [back]);
}
