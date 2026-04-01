/**
 * Graph Store - Manages the agent flow graph state
 *
 * This store handles graph-level state: nodes, edges, and their CRUD operations.
 */
import type { RAGFlowNodeType } from '@/interfaces/database/agent';
import type {} from '@redux-devtools/extension';
import {
  Connection,
  Edge,
  EdgeChange,
  EdgeMouseHandler,
  OnEdgesChange,
  OnNodesChange,
  applyEdgeChanges,
  applyNodeChanges,
} from '@xyflow/react';
import humanId from 'human-id';
import { cloneDeep, differenceWith, intersectionWith } from 'lodash';
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { Operator } from './constant';
import { isEdgeEqual, mapEdgeMouseEvent } from './utils';

export interface GraphState {
  nodes: RAGFlowNodeType[];
  edges: Edge[];
  onNodesChange: OnNodesChange<RAGFlowNodeType>;
  onEdgesChange: OnEdgesChange;
  onEdgeMouseEnter?: EdgeMouseHandler<Edge>;
  onEdgeMouseLeave?: EdgeMouseHandler<Edge>;
  setNodes: (nodes: RAGFlowNodeType[]) => void;
  setEdges: (edges: Edge[]) => void;
  setEdgesByNodeId: (nodeId: string, edges: Edge[]) => void;
  addNode: (node: RAGFlowNodeType) => void;
  getNode: (id?: string | null) => RAGFlowNodeType | undefined;
  updateNode: (node: RAGFlowNodeType) => void;
  getEdge: (id: string) => Edge | undefined;
  deleteEdge: () => void;
  deleteEdgeById: (id: string) => void;
  deleteNodeById: (id: string) => void;
  findNodeByName: (operatorName: Operator) => RAGFlowNodeType | undefined;
  getOperatorTypeFromId: (id?: string | null) => string | undefined;
  getParentIdById: (id?: string | null) => string | undefined;
  findUpstreamNodeById: (id?: string | null) => RAGFlowNodeType | undefined;
  deleteEdgesBySourceAndSourceHandle: (source: string, sourceHandle: string) => void;
  hasChildNode: (nodeId: string) => boolean;
}

export const useGraphStore = create<GraphState>()(
  devtools(
    immer((set, get) => ({
      nodes: [] as RAGFlowNodeType[],
      edges: [] as Edge[],
      onNodesChange: (changes) => {
        set({
          nodes: applyNodeChanges(
            changes,
            cloneDeep(get().nodes) as RAGFlowNodeType[],
          ),
        });
      },
      onEdgesChange: (changes: EdgeChange[]) => {
        set({
          edges: applyEdgeChanges(changes, get().edges),
        });
      },
      onEdgeMouseEnter: (event, edge) => {
        const { edges, setEdges } = get();
        setEdges(mapEdgeMouseEvent(edges, edge.id, true));
      },
      onEdgeMouseLeave: (event, edge) => {
        const { edges, setEdges } = get();
        setEdges(mapEdgeMouseEvent(edges, edge.id, false));
      },
      setNodes: (nodes: RAGFlowNodeType[]) => {
        set({ nodes });
      },
      setEdges: (edges: Edge[]) => {
        set({ edges });
      },
      setEdgesByNodeId: (nodeId: string, currentDownstreamEdges: Edge[]) => {
        const { edges, setEdges } = get();
        const previousDownstreamEdges = edges.filter(
          (x) => x.source === nodeId,
        );
        const isDifferent =
          previousDownstreamEdges.length !== currentDownstreamEdges.length ||
          !previousDownstreamEdges.every((x) =>
            currentDownstreamEdges.some(
              (y) =>
                y.source === x.source &&
                y.target === x.target &&
                y.sourceHandle === x.sourceHandle,
            ),
          ) ||
          !currentDownstreamEdges.every((x) =>
            previousDownstreamEdges.some(
              (y) =>
                y.source === x.source &&
                y.target === x.target &&
                y.sourceHandle === x.sourceHandle,
            ),
          );

        const intersectionDownstreamEdges = intersectionWith(
          previousDownstreamEdges,
          currentDownstreamEdges,
          isEdgeEqual,
        );
        if (isDifferent) {
          const irrelevantEdges = edges.filter((x) => x.source !== nodeId);
          const selfAddedDownstreamEdges = differenceWith(
            currentDownstreamEdges,
            intersectionDownstreamEdges,
            isEdgeEqual,
          );
          setEdges([
            ...irrelevantEdges,
            ...intersectionDownstreamEdges,
            ...selfAddedDownstreamEdges,
          ]);
        }
      },
      addNode: (node: RAGFlowNodeType) => {
        set({ nodes: get().nodes.concat(node) });
      },
      updateNode: (node) => {
        const { nodes } = get();
        const nextNodes = nodes.map((x) => {
          if (x.id === node.id) {
            return node;
          }
          return x;
        });
        set({ nodes: nextNodes });
      },
      getNode: (id?: string | null) => {
        return get().nodes.find((x) => x.id === id);
      },
      getOperatorTypeFromId: (id?: string | null) => {
        return get().getNode(id)?.data?.label;
      },
      getParentIdById: (id?: string | null) => {
        return get().getNode(id)?.parentId;
      },
      getEdge: (id: string) => {
        return get().edges.find((x) => x.id === id);
      },
      deleteEdge: () => {
        const { edges, selectedEdgeIds } = get();
        set({
          edges: edges.filter((edge) =>
            selectedEdgeIds.every((x) => x !== edge.id),
          ),
        });
      },
      deleteEdgeById: (id: string) => {
        set({
          edges: get().edges.filter((edge) => edge.id !== id),
        });
      },
      deleteNodeById: (id: string) => {
        const { nodes, edges } = get();
        set({
          nodes: nodes.filter((node) => node.id !== id),
          edges: edges
            .filter((edge) => edge.source !== id)
            .filter((edge) => edge.target !== id),
        });
      },
      findNodeByName: (name: Operator) => {
        return get().nodes.find((x) => x.data.label === name);
      },
      findUpstreamNodeById: (id) => {
        const { edges, getNode } = get();
        const edge = edges.find((x) => x.target === id);
        return getNode(edge?.source);
      },
      deleteEdgesBySourceAndSourceHandle: (source, sourceHandle) => {
        const { edges, setEdges } = get();
        setEdges(
          edges.filter(
            (edge) =>
              !(edge.source === source && edge.sourceHandle === sourceHandle),
          ),
        );
      },
      hasChildNode: (nodeId) => {
        const { edges } = get();
        return edges.some((edge) => edge.source === nodeId);
      },
    })),
    { name: 'graph', trace: true },
  ),
);
