/**
 * Node Form Store - Manages form data for nodes
 */
import type { IAgentForm, IAgentFormType } from '@/interfaces/database/agent';
import type { RAGFlowNodeType } from '@/interfaces/database/agent';
import type {} from '@redux-devtools/extension';
import {
  Connection,
  Edge,
  NodeHandleId,
  Operator,
  SwitchElseTo,
} from '@/pages/agent/constant';
import {
  duplicateNodeForm,
  generateDuplicateNode,
  generateNodeNamesWithIncreasingIndex,
  getAgentNodeTools,
  getOperatorIndex,
} from '@/pages/agent/utils';
import { deleteAllDownstreamAgentsAndTool } from '@/pages/agent/utils/delete-node';
import type {} from '@redux-devtools/extension';
import {
  addEdge,
  OnConnect,
} from '@xyflow/react';
import humanId from 'human-id';
import {
  cloneDeep,
  get as lodashGet,
  set as lodashSet,
  omit,
} from 'lodash';
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { useGraphStore } from './graphStore';

type IAgentTool = IAgentForm['tools'][number];

export interface NodeFormState {
  clickedNodeId: string;
  clickedToolId: string;
  onConnect: OnConnect;
  updateNodeForm: (
    nodeId: string,
    values: Partial<IAgentFormType> | Record<string, unknown>,
    path?: (string | number)[]
  ) => RAGFlowNodeType[];
  replaceNodeForm: (nodeId: string, values: Partial<IAgentFormType>) => void;
  duplicateNode: (id: string, name: string) => void;
  duplicateIterationNode: (id: string, name: string) => void;
  deleteAgentDownstreamNodesById: (id: string) => void;
  deleteAgentToolNodeById: (id: string) => void;
  deleteIterationNodeById: (id: string) => void;
  updateMutableNodeFormItem: (id: string, field: string, value: Record<string, unknown>) => void;
  updateNodeName: (id: string, name: string) => void;
  generateNodeName: (name: string) => string;
  generateAgentToolName: (id: string, name: string) => string;
  generateAgentToolId: (prefix: string) => string;
  getAllAgentTools: () => IAgentTool[];
  getAgentToolById: (id: string, agentNode?: RAGFlowNodeType | string) => IAgentTool | undefined;
  updateAgentToolById: (agentNodeId: RAGFlowNodeType | string, id: string, value?: Partial<IAgentTool>) => void;
  setClickedNodeId: (id?: string) => void;
  setClickedToolId: (id?: string) => void;
  findAgentToolNodeById: (id: string | null) => string | undefined;
  updateSwitchFormData: (
    source: string,
    sourceHandle?: string | null,
    target?: string | null,
    isConnecting?: boolean
  ) => void;
  updateFormDataOnConnect: (connection: Connection) => void;
}

export const useNodeFormStore = create<NodeFormState>()(
  devtools(
    immer((set, get) => ({
      clickedNodeId: '',
      clickedToolId: '',
      onConnect: (connection: Connection) => {
        const { updateFormDataOnConnect } = get();
        const { addEdge: addGraphEdge } = useGraphStore.getState();
        const newEdges = addEdge(connection, useGraphStore.getState().edges);
        set({ edges: newEdges });
        useGraphStore.setState({ edges: newEdges });
        updateFormDataOnConnect(connection);
      },
      updateNodeForm: (
        nodeId: string,
        values: Partial<IAgentFormType> | Record<string, unknown>,
        path: (string | number)[] = [],
      ) => {
        const { nodes } = useGraphStore.getState();
        const nextNodes = nodes.map((node) => {
          if (node.id === nodeId) {
            let nextForm: Record<string, unknown> = { ...node.data.form };
            if (path.length === 0) {
              nextForm = Object.assign(nextForm, values);
            } else {
              lodashSet(nextForm, path, values);
            }
            return {
              ...node,
              data: {
                ...node.data,
                form: nextForm,
              },
            } as RAGFlowNodeType;
          }
          return node;
        });
        useGraphStore.setState({ nodes: nextNodes });
        return nextNodes;
      },
      replaceNodeForm(nodeId, values) {
        const { nodes } = useGraphStore.getState();
        if (nodeId) {
          const nextNodes = nodes.map((node) => {
            if (node.id === nodeId) {
              return {
                ...node,
                data: {
                  ...node.data,
                  form: cloneDeep(values),
                },
              } as RAGFlowNodeType;
            }
            return node;
          });
          useGraphStore.setState({ nodes: nextNodes });
        }
      },
      duplicateNode: (id: string, name: string) => {
        const { getNode, addNode, generateNodeName, duplicateIterationNode } =
          get();
        const node = getNode(id);

        if (node?.data.label === Operator.Iteration) {
          duplicateIterationNode(id, name);
          return;
        }

        addNode({
          ...(node || {}),
          data: {
            ...duplicateNodeForm(node?.data),
            name: generateNodeName(name),
          },
          ...generateDuplicateNode(node?.position, node?.data?.label),
        });
      },
      duplicateIterationNode: (id: string, name: string) => {
        const { getNode, generateNodeName } = get();
        const { nodes, addNode } = useGraphStore.getState();
        const node = getNode(id);

        const iterationNode: RAGFlowNodeType = {
          ...(node || {}),
          data: {
            ...(node?.data || { label: Operator.Iteration, form: {} }),
            name: generateNodeName(name),
          },
          ...generateDuplicateNode(node?.position, node?.data?.label),
        };

        const children = nodes
          .filter((x) => x.parentId === node?.id)
          .map((x) => ({
            ...(x || {}),
            data: {
              ...duplicateNodeForm(x?.data),
              name: generateNodeName(x.data.name),
            },
            ...omit(generateDuplicateNode(x?.position, x?.data?.label), [
              'position',
            ]),
            parentId: iterationNode.id,
          }));

        useGraphStore.setState({ nodes: nodes.concat(iterationNode, ...children) });
      },
      deleteAgentDownstreamNodesById: (id) => {
        const { edges, nodes } = useGraphStore.getState();

        const { downstreamAgentAndToolNodeIds, downstreamAgentAndToolEdges } =
          deleteAllDownstreamAgentsAndTool(id, edges);

        useGraphStore.setState({
          nodes: nodes.filter(
            (node) =>
              !downstreamAgentAndToolNodeIds.some((x) => x === node.id) &&
              node.id !== id,
          ),
          edges: edges.filter(
            (edge) =>
              edge.source !== id &&
              edge.target !== id &&
              !downstreamAgentAndToolEdges.some((x) => x.id === edge.id),
          ),
        });
      },
      deleteAgentToolNodeById: (id) => {
        const { edges, deleteEdgeById, deleteNodeById } = get();

        const edge = edges.find(
          (x) => x.source === id && x.sourceHandle === NodeHandleId.Tool,
        );

        if (edge) {
          deleteEdgeById(edge.id);
          deleteNodeById(edge.target);
        }
      },
      deleteIterationNodeById: (id: string) => {
        const { nodes, edges } = useGraphStore.getState();
        const children = nodes.filter((node) => node.parentId === id);
        useGraphStore.setState({
          nodes: nodes.filter((node) => node.id !== id && node.parentId !== id),
          edges: edges.filter(
            (edge) =>
              edge.source !== id &&
              edge.target !== id &&
              !children.some(
                (child) => edge.source === child.id && edge.target === child.id,
              ),
          ),
        });
      },
      updateMutableNodeFormItem: (id: string, field: string, value: Record<string, unknown>) => {
        const { nodes } = useGraphStore.getState();
        const idx = nodes.findIndex((x) => x.id === id);
        if (idx) {
          lodashSet(nodes, [idx, 'data', 'form', field], value);
        }
      },
      updateNodeName: (id, name) => {
        const { nodes } = useGraphStore.getState();
        if (id) {
          const nextNodes = nodes.map((node) => {
            if (node.id === id) {
              return {
                ...node,
                data: {
                  ...node.data,
                  name,
                },
              } as RAGFlowNodeType;
            }
            return node;
          });
          useGraphStore.setState({ nodes: nextNodes });
        }
      },
      setClickedNodeId: (id?: string) => {
        set({ clickedNodeId: id });
      },
      generateNodeName: (name: string) => {
        const { nodes } = useGraphStore.getState();
        return generateNodeNamesWithIncreasingIndex(name, nodes);
      },
      generateAgentToolName: (id: string, name: string) => {
        const node = useGraphStore.getState().getNode(id) as RAGFlowNodeType;

        if (!node) {
          return '';
        }

        const tools = (node.data.form!.tools as any[]).filter(
          (x) => x.component_name === name,
        );
        const lastIndex = tools.length
          ? (tools
              .map((x) => {
                const idx = x.name.match(/(\d+)$/)?.[1];
                return idx && isNaN(idx) ? -1 : Number(idx);
              })
              .sort((a, b) => a - b)
              .at(-1) ?? -1)
          : -1;

        return `${name}_${lastIndex + 1}`;
      },
      generateAgentToolId: (prefix: string) => {
        const allAgentToolIds = get()
          .getAllAgentTools()
          .map((t) => t.id || t.component_name);

        let id: string;

        do {
          id = `${prefix}:${humanId()}`;
        } while (allAgentToolIds.includes(id));

        return id;
      },
      getAllAgentTools: () => {
        return useGraphStore.getState()
          .nodes.filter((n) => n?.data?.label === Operator.Agent)
          .flatMap((n) => n?.data?.form?.tools);
      },
      getAgentToolById: (
        id: string,
        nodeOrNodeId?: RAGFlowNodeType | string,
      ) => {
        const tools =
          nodeOrNodeId != null
            ? getAgentNodeTools(
                typeof nodeOrNodeId === 'string'
                  ? useGraphStore.getState().getNode(nodeOrNodeId)
                  : nodeOrNodeId,
              )
            : get().getAllAgentTools();

        return tools.find((t) => (t.id || t.component_name) === id);
      },
      updateAgentToolById: (
        nodeOrNodeId: RAGFlowNodeType | string,
        id: string,
        value?: Partial<IAgentTool>,
      ) => {
        const { getNode, updateNodeForm } = get();

        const agentNode =
          typeof nodeOrNodeId === 'string'
            ? getNode(nodeOrNodeId)
            : nodeOrNodeId;

        if (!agentNode) {
          return;
        }

        const toolIndex = getAgentNodeTools(agentNode).findIndex(
          (t) => (t.id || t.component_name) === id,
        );

        updateNodeForm(
          agentNode.id,
          {
            ...lodashGet(agentNode.data.form, ['tools', toolIndex], {}),
            ...(value ?? {}),
          },
          ['tools', toolIndex],
        );
      },
      setClickedToolId: (id?: string) => {
        set({ clickedToolId: id });
      },
      findAgentToolNodeById: (id) => {
        const { edges } = useGraphStore.getState();
        return edges.find(
          (edge) =>
            edge.source === id && edge.sourceHandle === NodeHandleId.Tool,
        )?.target;
      },
      updateSwitchFormData: (source, sourceHandle, target, isConnecting) => {
        const { updateNodeForm } = get();
        const { edges, getOperatorTypeFromId } = useGraphStore.getState();
        if (sourceHandle) {
          const currentHandleTargets = edges
            .filter(
              (x) =>
                x.source === source &&
                x.sourceHandle === sourceHandle &&
                typeof x.target === 'string' &&
                getOperatorTypeFromId(x.target) !== Operator.Placeholder,
            )
            .map((x) => x.target);

          let targets: string[] = currentHandleTargets;
          if (target) {
            if (!isConnecting) {
              targets = currentHandleTargets.filter((x) => x !== target);
            }
          }

          if (sourceHandle === SwitchElseTo) {
            updateNodeForm(source, targets, [SwitchElseTo]);
          } else {
            const operatorIndex = getOperatorIndex(sourceHandle);
            if (operatorIndex) {
              updateNodeForm(source, targets, [
                'conditions',
                Number(operatorIndex) - 1,
                'to',
              ]);
            }
          }
        }
      },
      updateFormDataOnConnect: (connection: Connection) => {
        const { getOperatorTypeFromId, updateSwitchFormData } = useGraphStore.getState();
        const { source, target, sourceHandle } = connection;
        const operatorType = getOperatorTypeFromId(source);
        if (source) {
          switch (operatorType) {
            case Operator.Switch: {
              updateSwitchFormData(source, sourceHandle, target, true);
              break;
            }
            default:
              break;
          }
        }
      },
    })),
    { name: 'nodeForm', trace: true },
  ),
);
