// Types for the Autonomous Agent System

export interface WorkflowSelection {
  selected_workflow: string;
  reasoning: string;
  confidence: number;
}

export interface IntermediateStep {
  agent_role: string;
  content: string;
  timestamp?: string;
  status?: 'completed' | 'pending' | 'skipped';
}

export interface AgentMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  workflow?: WorkflowSelection;
  intermediateSteps?: IntermediateStep[];
}

export interface ChatSession {
  id: string;
  title: string;
  messages: AgentMessage[];
  createdAt: string;
  updatedAt: string;
}

export interface AgentConfig {
  model: string;
  temperature: number;
  maxTokens: number;
  enableWorkflowVisualization: boolean;
}

export interface WorkflowType {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'sequential' | 'parallel' | 'conditional' | 'iterative';
}

export const WORKFLOW_TYPES: WorkflowType[] = [
  {
    id: 'prompt_chaining',
    name: 'Prompt Chaining',
    description: 'Sequential processing through multiple specialized prompts',
    icon: '🔗',
    category: 'sequential'
  },
  {
    id: 'routing',
    name: 'Routing',
    description: 'Route queries to specialized agents based on content',
    icon: '🚦',
    category: 'conditional'
  },
  {
    id: 'parallel_sectioning',
    name: 'Parallel Sectioning',
    description: 'Break tasks into parallel sections for concurrent processing',
    icon: '⚡',
    category: 'parallel'
  },
  {
    id: 'parallel_voting',
    name: 'Parallel Voting',
    description: 'Multiple agents vote on the best approach or solution',
    icon: '🗳️',
    category: 'parallel'
  },
  {
    id: 'orchestrator_workers',
    name: 'Orchestrator Workers',
    description: 'Central orchestrator coordinates multiple worker agents',
    icon: '🎭',
    category: 'parallel'
  },
  {
    id: 'evaluator_optimizer',
    name: 'Evaluator Optimizer',
    description: 'Iterative improvement through evaluation and optimization',
    icon: '🔄',
    category: 'iterative'
  }
]; 