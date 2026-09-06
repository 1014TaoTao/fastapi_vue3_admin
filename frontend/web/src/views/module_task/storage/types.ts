import type { CSSProperties } from "vue";

export type NodeType =
  | "input"
  | "output"
  | "trigger"
  | "action"
  | "condition"
  | "control"
  | "integration"
  | "custom";

export type EdgeType = "default" | "straight" | "step" | "smoothstep" | "bezier";

export type HandlePosition = "left" | "right" | "top" | "bottom";

export interface NodeConfigSchema {
  type: string;
  properties: Record<string, PropertySchema>;
}

export interface PropertySchema {
  type: "string" | "number" | "boolean" | "select" | "textarea" | "json" | "code";
  label: string;
  description?: string;
  default?: any;
  required?: boolean;
  options?: Array<{ label: string; value: any }>;
  placeholder?: string;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
  };
}

export interface DynamicNodeData {
  label: string;
  nodeTypeCode: string;
  config: Record<string, any>;
  description?: string;
}

export interface Node {
  id: string;
  position: { x: number; y: number };
  type?: NodeType;
  data?: DynamicNodeData;
  label?: string;
  style?: CSSProperties;
  class?: string | string[];
  sourcePosition?: HandlePosition;
  targetPosition?: HandlePosition;
  hidden?: boolean;
  selected?: boolean;
  draggable?: boolean;
  connectable?: boolean;
  deletable?: boolean;
  selectable?: boolean;
  focusable?: boolean;
  dragHandle?: string;
  extent?: "parent" | [number, number] | [[number, number], [number, number]];
  parentNode?: string;
  expandParent?: boolean;
  zIndex?: number;
}

export interface Edge {
  id?: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: EdgeType;
  label?: string;
  labelStyle?: CSSProperties;
  labelShowBg?: boolean;
  labelBgStyle?: CSSProperties;
  labelBgPadding?: [number, number];
  labelBgBorderRadius?: number;
  style?: CSSProperties;
  class?: string | string[];
  animated?: boolean;
  hidden?: boolean;
  selected?: boolean;
  deletable?: boolean;
  selectable?: boolean;
  focusable?: boolean;
  updatable?: boolean | "source" | "target";
  markerStart?: Marker | string;
  markerEnd?: Marker | string;
  pathOptions?: {
    offset?: number;
    borderRadius?: number;
    curvature?: number;
  };
  interactionWidth?: number;
}

export interface Marker {
  type: "arrow" | "arrowclosed";
  color?: string;
  width?: number;
  height?: number;
  orient?: "auto" | "auto-start-reverse";
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description?: string;
  nodes: Node[];
  edges: Edge[];
}

export interface WorkflowStats {
  totalNodes: number;
  totalEdges: number;
  nodeTypes: Record<NodeType, number>;
}

export interface NodeConfig {
  id: string;
  type: NodeType;
  data: DynamicNodeData;
}

export interface EdgeConfig {
  id: string;
  source: string;
  target: string;
  label?: string;
  type?: EdgeType;
  animated?: boolean;
}

export interface NodeTypeDefinition {
  code: string;
  name: string;
  category: "trigger" | "action" | "condition" | "control" | "integration" | "custom";
  description?: string;
  icon?: string;
  color?: string;
  configSchema: NodeConfigSchema;
  inputSchema?: Record<string, any>;
  outputSchema?: Record<string, any>;
  handler: string;
  isSystem: boolean;
  isActive: boolean;
  sortOrder: number;
}

export interface NodeTemplate {
  id: string;
  nodeTypeCode: string;
  name: string;
  description?: string;
  defaultConfig: Record<string, any>;
  isPublic: boolean;
  tags?: string[];
  thumbnail?: string;
}
