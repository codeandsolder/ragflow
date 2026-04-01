/**
 * RAGFlow Agent Graph Store - Facade
 *
 * This store maintains backward compatibility by delegating to the new modular stores.
 * For new code, import directly from the modular stores:
 * - useGraphStore: Graph state, node/edge management
 * - useSelectionStore: Selection state for nodes/edges
 * - useNodeFormStore: Form data management, validation, node operations
 */
import type { IAgentForm, IAgentFormType, RAGFlowNodeType } from '@/interfaces/database/agent';
import type {} from '@redux-devtools/extension';
import {
  Connection,
  Edge,
  EdgeChange,
  EdgeMouseHandler,
  OnConnect,
  OnEdgesChange,
  OnNodesChange,
  OnSelectionChangeFunc,
  OnSelectionChangeParams,
  addEdge,
} from '@xyflow/react';
import humanId from 'human-id';
import { cloneDeep, get as lodashGet, set as lodashSet } from 'lodash';
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { NodeHandleId, Operator, SwitchElseTo } from './constant';
import {
  duplicateNodeForm,
  generateDuplicateNode,
  generateNodeNamesWithIncreasingIndex,
  getAgentNodeTools,
  getOperatorIndex,
  mapEdgeMouseEvent,
} from './utils';
import { deleteAllDownstreamAgentsAndTool } from './utils/delete-node';
import { useGraphStore, useSelectionStore, useNodeFormStore } from './store';

type IAgentTool = IAgentForm['tools'][number];

interface GetAgentToolByIdFunc {
  (id: string): IAgentTool | undefined;
  (id: string, agentNode: RAGFlowNodeType): IAgentTool | undefined;
  (id: string, agentNodeId: string): IAgentTool | undefined;
}

interface UpdateAgentToolByIdFunc {
  (agentNode: RAGFlowNodeType, id: string, value?: Partial<IAgentTool>): void;
  (agentNodeId: string, id: string, value?: Partial<IAgentTool>): void;
}

export type RFState = {
  nodes: RAGFlowNodeType[];
  edges: Edge[];
  selectedNodeIds: string[];
  selectedEdgeIds: string[];
  clickedNodeId: string;
  clickedToolId: string;
  onNodesChange: OnNodesChange<RAGFlowNodeType>;
  onEdgesChange: OnEdgesChange;
  onEdgeMouseEnter?: EdgeMouseHandler<Edge>;
  onEdgeMouseLeave?: EdgeMouseHandler<Edge>;
  onConnect: OnConnect;
  setNodes: (nodes: RAGFlowNodeType[]) => void;
  setEdges: (edges: Edge[]) => void;
  setEdgesByNodeId: (nodeId: string, edges: Edge[]) => void;
  updateNodeForm: (
    nodeId: string,
    values: Partial<IAgentFormType> | Record<string, unknown>,
    path?: (string | number)[]
  ) => RAGFlowNodeType[];
  replaceNodeForm: (nodeId: string, values: Partial<IAgentFormType>) => void;
  onSelectionChange: OnSelectionChangeFunc;
  addNode: (node: RAGFlowNodeType) => void;
  getNode: (id?: string | null) => RAGFlowNodeType | undefined;
  updateNode: (node: RAGFlowNodeType) => void;
  addEdge: (connection: Connection) => void;
  getEdge: (id: string) => Edge | undefined;
  updateFormDataOnConnect: (connection: Connection) => void;
  updateSwitchFormData: (
    source: string,
    sourceHandle?: string | null,
    target?: string | null,
    isConnecting?: boolean
  ) => void;
  duplicateNode: (id: string, name: string) => void;
  duplicateIterationNode: (id: string, name: string) => void;
  deleteEdge: () => void;
  deleteEdgeById: (id: string) => void;
  deleteNodeById: (id: string) => void;
  deleteAgentDownstreamNodesById: (id: string) => void;
  deleteAgentToolNodeById: (id: string) => void;
  deleteIterationNodeById: (id: string) => void;
  findNodeByName: (operatorName: Operator) => RAGFlowNodeType | undefined;
  updateMutableNodeFormItem: (id: string, field: string, value: Record<string, unknown>) => void;
  getOperatorTypeFromId: (id?: string | null) => string | undefined;
  getParentIdById: (id?: string | null) => string | undefined;
  updateNodeName: (id: string, name: string) => void;
  generateNodeName: (name: string) => string;
  generateAgentToolName: (id: string, name: string) => string;
  generateAgentToolId: (prefix: string) => string;
  getAllAgentTools: () => IAgentTool[];
  getAgentToolById: GetAgentToolByIdFunc;
  updateAgentToolById: UpdateAgentToolByIdFunc;
  setClickedNodeId: (id?: string) => void;
  setClickedToolId: (id?: string) => void;
  findUpstreamNodeById: (id?: string | null) => RAGFlowNodeType | undefined;
  deleteEdgesBySourceAndSourceHandle: (
    source: string,
    sourceHandle: string
  ) => void;
  findAgentToolNodeById: (id: string | null) => string | undefined;
  selectNodeIds: (nodeIds: string[]) => void;
  hasChildNode: (nodeId: string) => boolean;
};

const useStore = create<RFState>()(
  devtools(
    immer((set, get) => ({
      nodes: [] as RAGFlowNodeType[],
      edges: [] as Edge[],
      selectedNodeIds: [] as string[],
      selectedEdgeIds: [] as string[],
      clickedNodeId: '',
      clickedToolId: '',
      onNodesChange: (changes) => {
        useGraphStore.getState().onNodesChange(changes);
        set({ nodes: useGraphStore.getState().nodes });
      },
      onEdgesChange: (changes: EdgeChange[]) => {
        useGraphStore.getState().onEdgesChange(changes);
        set({ edges: useGraphStore.getState().edges });
      },
      onEdgeMouseEnter: (event, edge) => {
        useGraphStore.getState().onEdgeMouseEnter?.(event, edge);
        set({ edges: useGraphStore.getState().edges });
      },
      onEdgeMouseLeave: (event, edge) => {
        useGraphStore.getState().onEdgeMouseLeave?.(event, edge);
        set({ edges: useGraphStore.getState().edges });
      },
      onConnect: (connection) => {
        const { updateFormDataOnConnect } = useNodeFormStore.getState();
        const newEdges = addEdge(connection, useGraphStore.getState().edges);
        useGraphStore.getState().setEdges(newEdges);
        set({ edges: newEdges });
        updateFormDataOnConnect(connection);
      },
      onSelectionChange: ({ nodes, edges }: OnSelectionChangeParams) => {
        useSelectionStore.getState().onSelectionChange({ nodes, edges });
        set({
          selectedNodeIds: nodes.map((x) => x.id),
          selectedEdgeIds: edges.map((x) => x.id),
        });
      },
      setNodes: (nodes) => {
        useGraphStore.getState().setNodes(nodes);
        set({ nodes });
      },
      setEdges: (edges) => {
        useGraphStore.getState().setEdges(edges);
        set({ edges });
      },
      setEdgesByNodeId: (nodeId, edges) => {
        useGraphStore.getState().setEdgesByNodeId(nodeId, edges);
        set({ edges: useGraphStore.getState().edges });
      },
      updateNodeForm: (nodeId, values, path) => {
        const result = useNodeFormStore.getState().updateNodeForm(nodeId, values, path);
        set({ nodes: result });
        return result;
      },
      replaceNodeForm: (nodeId, values) => {
        useNodeFormStore.getState().replaceNodeForm(nodeId, values);
        set({ nodes: useGraphStore.getState().nodes });
      },
      addNode: (node) => {
        useGraphStore.getState().addNode(node);
        set({ nodes: useGraphStore.getState().nodes });
      },
      getNode: (id) => useGraphStore.getState().getNode(id),
      updateNode: (node) => {
        useGraphStore.getState().updateNode(node);
        set({ nodes: useGraphStore.getState().nodes });
      },
      addEdge: (connection) => {
        const { updateFormDataOnConnect } = useNodeFormStore.getState();
        const newEdges = addEdge(connection, useGraphStore.getState().edges);
        useGraphStore.getState().setEdges(newEdges);
        updateFormDataOnConnect(connection);
        set({ edges: newEdges });
      },
      getEdge: (id) => useGraphStore.getState().getEdge(id),
      updateFormDataOnConnect: (connection) => {
        useNodeFormStore.getState().updateFormDataOnConnect(connection);
      },
      updateSwitchFormData: (source, sourceHandle, target, isConnecting) => {
        useNodeFormStore.getState().updateSwitchFormData(source, sourceHandle, target, isConnecting);
        set({ nodes: useGraphStore.getState().nodes });
      },
      duplicateNode: (id, name) => {
        useNodeFormStore.getState().duplicateNode(id, name);
        set({ nodes: useGraphStore.getState().nodes });
      },
      duplicateIterationNode: (id, name) => {
        useNodeFormStore.getState().duplicateIterationNode(id, name);
        set({ nodes: useGraphStore.getState().nodes });
      },
      deleteEdge: () => {
        const { selectedEdgeIds, edges } = {
          selectedEdgeIds: useSelectionStore.getState().selectedEdgeIds,
          edges: useGraphStore.getState().edges,
        };
        const newEdges = edges.filter((edge) => !selectedEdgeIds.includes(edge.id));
        useGraphStore.getState().setEdges(newEdges);
        set({ edges: newEdges });
      },
      deleteEdgeById: (id) => {
        const { getOperatorTypeFromId } = useGraphStore.getState();
        const { updateSwitchFormData } = useNodeFormStore.getState();
        const currentEdge = useGraphStore.getState().getEdge(id);

        if (currentEdge) {
          const { source, sourceHandle, target } = currentEdge;
          const operatorType = getOperatorTypeFromId(source);
          switch (operatorType) {
            case Operator.Switch: {
              updateSwitchFormData(source, sourceHandle, target, false);
              break;
            }
            default:
              break;
          }
        }
        useGraphStore.getState().deleteEdgeById(id);
        set({
          edges: useGraphStore.getState().edges,
          nodes: useGraphStore.getState().nodes,
        });
      },
      deleteNodeById: (id) => {
        const { getOperatorTypeFromId } = useGraphStore.getState();
        if (getOperatorTypeFromId(id) === Operator.Agent) {
          useNodeFormStore.getState().deleteAgentDownstreamNodesById(id);
        } else {
          useGraphStore.getState().deleteNodeById(id);
        }
        set({
          nodes: useGraphStore.getState().nodes,
          edges: useGraphStore.getState().edges,
        });
      },
      deleteAgentDownstreamNodesById: (id) => {
        useNodeFormStore.getState().deleteAgentDownstreamNodesById(id);
        set({
          nodes: useGraphStore.getState().nodes,
          edges: useGraphStore.getState().edges,
        });
      },
      deleteAgentToolNodeById: (id) => {
        useNodeFormStore.getState().deleteAgentToolNodeById(id);
        set({
          nodes: useGraphStore.getState().nodes,
          edges: useGraphStore.getState().edges,
        });
      },
      deleteIterationNodeById: (id) => {
        useNodeFormStore.getState().deleteIterationNodeById(id);
        set({
          nodes: useGraphStore.getState().nodes,
          edges: useGraphStore.getState().edges,
        });
      },
      findNodeByName: (name) => useGraphStore.getState().findNodeByName(name),
      updateMutableNodeFormItem: (id, field, value) => {
        useNodeFormStore.getState().updateMutableNodeFormItem(id, field, value);
        set({ nodes: useGraphStore.getState().nodes });
      },
      getOperatorTypeFromId: (id) => useGraphStore.getState().getOperatorTypeFromId(id),
      getParentIdById: (id) => useGraphStore.getState().getParentIdById(id),
      updateNodeName: (id, name) => {
        useNodeFormStore.getState().updateNodeName(id, name);
        set({ nodes: useGraphStore.getState().nodes });
      },
      generateNodeName: (name) => useNodeFormStore.getState().generateNodeName(name),
      generateAgentToolName: (id, name) => useNodeFormStore.getState().generateAgentToolName(id, name),
      generateAgentToolId: (prefix) => useNodeFormStore.getState().generateAgentToolId(prefix),
      getAllAgentTools: () => useNodeFormStore.getState().getAllAgentTools(),
      getAgentToolById: (id, agentNode) => useNodeFormStore.getState().getAgentToolById(id, agentNode as any),
      updateAgentToolById: (agentNode, id, value) => useNodeFormStore.getState().updateAgentToolById(agentNode as any, id, value),
      setClickedNodeId: (id) => {
        useNodeFormStore.getState().setClickedNodeId(id);
        set({ clickedNodeId: id ?? '' });
      },
      setClickedToolId: (id) => {
        useNodeFormStore.getState().setClickedToolId(id);
        set({ clickedToolId: id ?? '' });
      },
      findUpstreamNodeById: (id) => useGraphStore.getState().findUpstreamNodeById(id),
      deleteEdgesBySourceAndSourceHandle: (source, sourceHandle) => {
        useGraphStore.getState().deleteEdgesBySourceAndSourceHandle(source, sourceHandle);
        set({ edges: useGraphStore.getState().edges });
      },
      findAgentToolNodeById: (id) => useNodeFormStore.getState().findAgentToolNodeById(id),
      selectNodeIds: (nodeIds) => {
        useSelectionStore.getState().selectNodeIds(nodeIds);
        set({ selectedNodeIds: nodeIds });
      },
      hasChildNode: (nodeId) => useGraphStore.getState().hasChildNode(nodeId),
    })),
    { name: 'graph', trace: true },
  ),
);

export default useStore;
