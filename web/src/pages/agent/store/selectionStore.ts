/**
 * Selection Store - Manages node and edge selection state
 */
import type { RAGFlowNodeType } from '@/interfaces/database/agent';
import type {} from '@redux-devtools/extension';
import {
  Edge,
  OnSelectionChangeFunc,
  OnSelectionChangeParams,
} from '@xyflow/react';
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export interface SelectionState {
  selectedNodeIds: string[];
  selectedEdgeIds: string[];
  onSelectionChange: OnSelectionChangeFunc;
  selectNodeIds: (nodeIds: string[]) => void;
}

export const useSelectionStore = create<SelectionState>()(
  devtools(
    immer((set) => ({
      selectedNodeIds: [] as string[],
      selectedEdgeIds: [] as string[],
      onSelectionChange: ({ nodes, edges }: OnSelectionChangeParams) => {
        set({
          selectedEdgeIds: edges.map((x) => x.id),
          selectedNodeIds: nodes.map((x) => x.id),
        });
      },
      selectNodeIds: (nodeIds) => {
        set({ selectedNodeIds: nodeIds });
      },
    })),
    { name: 'selection', trace: true },
  ),
);
