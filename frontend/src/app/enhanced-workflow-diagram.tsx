// components/workflow/enhanced-workflow-diagram.tsx
import { useEffect, useRef, useState } from 'react';
import { WorkflowSelection } from '@/types';
import * as d3 from 'd3';
import { titleCase } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { 
ZoomIn, 
ZoomOut, 
RefreshCw,
} from 'lucide-react';

interface WorkflowDiagramProps {
workflowInfo: WorkflowSelection;
intermediateSteps: {
agent_role: string;
content: string;
}[];
}

// Define types for diagram data
interface NodeData {
  id: string;
  label: string;
  x: number;
  y: number;
  status: 'completed' | 'pending' | 'skipped';
  description: string;
}

interface LinkData {
  source: string;
  target: string;
  label: string;
  curved?: boolean;
}

export default function EnhancedWorkflowDiagram({ workflowInfo, intermediateSteps }: WorkflowDiagramProps) {
const svgRef = useRef<SVGSVGElement>(null);
const [zoomLevel, setZoomLevel] = useState(1);
const [tooltipContent, setTooltipContent] = useState<{content: string, x: number, y: number} | null>(null);

// Format the workflow name for display
const formattedWorkflowName = workflowInfo && workflowInfo.selected_workflow ? 
titleCase(workflowInfo.selected_workflow.replace(/_/g, ' ')) : 
'Unknown Workflow';

useEffect(() => {
if (!svgRef.current || !workflowInfo) return;

// Clear previous diagram
d3.select(svgRef.current).selectAll('*').remove();

// Create diagram based on workflow type
const workflowType = workflowInfo.selected_workflow;
const svg = d3.select(svgRef.current);
const width = 700;
const height = 400;

// Create a group for zoom handling
const g = svg.append('g')
.attr('class', 'zoom-group');

// Set up diagram container
svg.attr('width', width)
.attr('height', height)
.attr('viewBox', `0 0 ${width} ${height}`)
.attr('style', 'max-width: 100%; height: auto;');

// Add arrow marker
svg.append('defs').append('marker')
.attr('id', 'arrow')
.attr('viewBox', '0 -5 10 10')
.attr('refX', 8)
.attr('refY', 0)
.attr('markerWidth', 6)
.attr('markerHeight', 6)
.attr('orient', 'auto')
.append('path')
.attr('d', 'M0,-5L10,0L0,5')
.attr('fill', '#333');

// Find if a step has been completed by a specific agent role
const isStepCompleted = (role: string): 'completed' | 'pending' | 'skipped' => {
const matchedStep = intermediateSteps.find(step => 
step.agent_role.toLowerCase().includes(role.toLowerCase()));

if (matchedStep) {
return 'completed';
}

// Check if subsequent steps exist (which would mean this one was skipped)
const roleIndex = getNodeSequence(workflowType).findIndex(n => 
n.toLowerCase().includes(role.toLowerCase()));

if (roleIndex >= 0) {
const laterSteps = getNodeSequence(workflowType).slice(roleIndex + 1);
const anyLaterStepCompleted = laterSteps.some(laterRole => 
intermediateSteps.some(step => 
step.agent_role.toLowerCase().includes(laterRole.toLowerCase())
)
);

if (anyLaterStepCompleted) {
return 'skipped';
}
}

return 'pending';
};

// Different diagram layouts based on workflow type
switch (workflowType) {
case 'prompt_chaining':
renderPromptChainingDiagram(g, isStepCompleted);
break;
case 'routing':
renderRoutingDiagram(g, isStepCompleted);
break;
case 'parallel_sectioning':
renderParallelSectioningDiagram(g, isStepCompleted);
break;
case 'parallel_voting':
renderParallelVotingDiagram(g, isStepCompleted);
break;
case 'orchestrator_workers':
renderOrchestratorWorkersDiagram(g, isStepCompleted);
break;
case 'evaluator_optimizer':
renderEvaluatorOptimizerDiagram(g, isStepCompleted);
break;
default:
renderDefaultDiagram(g, workflowType);
}

// Apply zoom transformation
g.attr('transform', `scale(${zoomLevel})`);

// eslint-disable-next-line react-hooks/exhaustive-deps
}, [workflowInfo, intermediateSteps, zoomLevel]);

// Handle zoom in
const handleZoomIn = () => {
setZoomLevel(prev => Math.min(prev + 0.2, 2));
};

// Handle zoom out
const handleZoomOut = () => {
setZoomLevel(prev => Math.max(prev - 0.2, 0.6));
};

// Reset zoom
const handleResetZoom = () => {
setZoomLevel(1);
};

// Helper function to get node color
function getNodeColor(status: 'completed' | 'pending' | 'skipped'): string {
switch (status) {
case 'completed': return '#4CAF50';  // Green
case 'pending': return '#FFC107';    // Yellow
case 'skipped': return '#9E9E9E';    // Gray
default: return '#9E9E9E';
}
}

// Helper function to get node sequence for a workflow
function getNodeSequence(workflowType: string): string[] {
switch (workflowType) {
case 'prompt_chaining':
return ['Initial Processor', 'Validator', 'Refiner'];
case 'routing':
return ['Classifier', 'Specialist 1', 'Specialist 2', 'Specialist 3'];
case 'parallel_sectioning':
return ['Task Divider', 'Section Worker', 'Results Integrator'];
case 'parallel_voting':
return ['Coordinator', 'Perspective', 'Consensus Builder'];
case 'orchestrator_workers':
return ['Task Coordinator', 'Worker', 'Results Integrator'];
case 'evaluator_optimizer':
return ['Content Creator', 'Quality Assessor', 'Refinement Specialist'];
default:
return [];
}
}

// Render Prompt Chaining Workflow
function renderPromptChainingDiagram(svg: d3.Selection<SVGGElement, unknown, null, undefined>, 
   getStepStatus: (role: string) => 'completed' | 'pending' | 'skipped') {
const nodes = [
{ id: 'user', label: 'User', x: 100, y: 50, status: 'completed' as const, description: 'The user query that initiated the workflow' },
{ id: 'step1', label: 'Initial Processor', x: 300, y: 50, status: getStepStatus('Initial Processor'), description: 'Analyzes and structures the query' },
{ id: 'gate', label: 'Validator', x: 300, y: 150, status: getStepStatus('Validator'), description: 'Validates the structured analysis before proceeding' },
{ id: 'step2', label: 'Refiner', x: 300, y: 250, status: getStepStatus('Refiner'), description: 'Creates the final response based on validated analysis' },
{ id: 'response', label: 'Final Response', x: 100, y: 250, status: 'completed' as const, description: 'The complete response delivered to the user' }
];

const links = [
{ source: 'user', target: 'step1', label: 'Query' },
{ source: 'step1', target: 'gate', label: 'Analysis' },
{ source: 'gate', target: 'step2', label: 'Validation' },
{ source: 'step2', target: 'response', label: 'Refinement' }
];

renderEnhancedNodes(svg, nodes);
renderEnhancedLinks(svg, links, nodes);
}

// Render Routing Workflow
function renderRoutingDiagram(svg: d3.Selection<SVGGElement, unknown, null, undefined>, 
getStepStatus: (role: string) => 'completed' | 'pending' | 'skipped') {
const nodes = [
{ id: 'user', label: 'User', x: 350, y: 50, status: 'completed' as const, description: 'The user query that initiated the workflow' },
{ id: 'classifier', label: 'Query Classifier', x: 350, y: 150, status: getStepStatus('Classifier'), description: 'Determines the category of the query' },
{ id: 'cat1', label: 'Specialist 1', x: 150, y: 250, status: getStepStatus('Specialist'), description: 'Handles technical support queries' },
{ id: 'cat2', label: 'Specialist 2', x: 350, y: 250, status: getStepStatus('Specialist'), description: 'Handles account management queries' },
{ id: 'cat3', label: 'Specialist 3', x: 550, y: 250, status: getStepStatus('Specialist'), description: 'Handles general inquiries' },
{ id: 'response', label: 'Final Response', x: 350, y: 350, status: 'completed' as const, description: 'The complete response delivered to the user' }
];

const links = [
{ source: 'user', target: 'classifier', label: 'Query' },
{ source: 'classifier', target: 'cat1', label: 'Route' },
{ source: 'classifier', target: 'cat2', label: 'Route' },
{ source: 'classifier', target: 'cat3', label: 'Route' },
{ source: 'cat1', target: 'response', label: 'Response' },
{ source: 'cat2', target: 'response', label: 'Response' },
{ source: 'cat3', target: 'response', label: 'Response' }
];

renderEnhancedNodes(svg, nodes);
renderEnhancedLinks(svg, links, nodes);
}

// Render Parallel Sectioning Workflow
function renderParallelSectioningDiagram(svg: d3.Selection<SVGGElement, unknown, null, undefined>, 
       getStepStatus: (role: string) => 'completed' | 'pending' | 'skipped') {
const nodes = [
{ id: 'user', label: 'User', x: 350, y: 50, status: 'completed' as const, description: 'The user query that initiated the workflow' },
{ id: 'sectioning', label: 'Task Divider', x: 350, y: 125, status: getStepStatus('Divider'), description: 'Breaks down the task into independent sections' },
{ id: 'worker1', label: 'Section Worker 1', x: 150, y: 200, status: getStepStatus('Section'), description: 'Processes the first section independently' },
{ id: 'worker2', label: 'Section Worker 2', x: 350, y: 200, status: getStepStatus('Section'), description: 'Processes the second section independently' },
{ id: 'worker3', label: 'Section Worker 3', x: 550, y: 200, status: getStepStatus('Section'), description: 'Processes the third section independently' },
{ id: 'aggregator', label: 'Results Integrator', x: 350, y: 275, status: getStepStatus('Integrator'), description: 'Combines the section results into a cohesive whole' },
{ id: 'response', label: 'Final Response', x: 350, y: 350, status: 'completed' as const, description: 'The complete response delivered to the user' }
];

const links = [
{ source: 'user', target: 'sectioning', label: 'Query' },
{ source: 'sectioning', target: 'worker1', label: 'Section 1' },
{ source: 'sectioning', target: 'worker2', label: 'Section 2' },
{ source: 'sectioning', target: 'worker3', label: 'Section 3' },
{ source: 'worker1', target: 'aggregator', label: 'Result' },
{ source: 'worker2', target: 'aggregator', label: 'Result' },
{ source: 'worker3', target: 'aggregator', label: 'Result' },
{ source: 'aggregator', target: 'response', label: 'Integration' }
];

renderEnhancedNodes(svg, nodes);
renderEnhancedLinks(svg, links, nodes);
}

// Render Parallel Voting Workflow
function renderParallelVotingDiagram(svg: d3.Selection<SVGGElement, unknown, null, undefined>, 
   getStepStatus: (role: string) => 'completed' | 'pending' | 'skipped') {
const nodes = [
{ id: 'user', label: 'User', x: 350, y: 50, status: 'completed' as const, description: 'The user query that initiated the workflow' },
{ id: 'coordinator', label: 'Perspective Coordinator', x: 350, y: 125, status: getStepStatus('Coordinator'), description: 'Defines the perspectives and evaluation criteria' },
{ id: 'voter1', label: 'Perspective 1', x: 125, y: 200, status: getStepStatus('Perspective'), description: 'Evaluates from the first perspective' },
{ id: 'voter2', label: 'Perspective 2', x: 350, y: 200, status: getStepStatus('Perspective'), description: 'Evaluates from the second perspective' },
{ id: 'voter3', label: 'Perspective 3', x: 575, y: 200, status: getStepStatus('Perspective'), description: 'Evaluates from the third perspective' },
{ id: 'consensus', label: 'Consensus Builder', x: 350, y: 275, status: getStepStatus('Consensus'), description: 'Determines consensus from multiple evaluations' },
{ id: 'response', label: 'Final Response', x: 350, y: 350, status: 'completed' as const, description: 'The complete response delivered to the user' }
];

const links = [
{ source: 'user', target: 'coordinator', label: 'Query' },
{ source: 'coordinator', target: 'voter1', label: 'Evaluation' },
{ source: 'coordinator', target: 'voter2', label: 'Evaluation' },
{ source: 'coordinator', target: 'voter3', label: 'Evaluation' },
{ source: 'voter1', target: 'consensus', label: 'Judgment' },
{ source: 'voter2', target: 'consensus', label: 'Judgment' },
{ source: 'voter3', target: 'consensus', label: 'Judgment' },
{ source: 'consensus', target: 'response', label: 'Decision' }
];

renderEnhancedNodes(svg, nodes);
renderEnhancedLinks(svg, links, nodes);
}

// Render Orchestrator-Workers Workflow
function renderOrchestratorWorkersDiagram(svg: d3.Selection<SVGGElement, unknown, null, undefined>, 
       getStepStatus: (role: string) => 'completed' | 'pending' | 'skipped') {
const nodes = [
{ id: 'user', label: 'User', x: 350, y: 30, status: 'completed' as const, description: 'The user query that initiated the workflow' },
{ id: 'orchestrator', label: 'Task Coordinator', x: 350, y: 100, status: getStepStatus('Coordinator'), description: 'Plans and coordinates the execution of subtasks' },
{ id: 'worker1', label: 'Worker 1', x: 160, y: 170, status: getStepStatus('Worker'), description: 'Executes the first subtask' },
{ id: 'worker2', label: 'Worker 2', x: 350, y: 170, status: getStepStatus('Worker'), description: 'Executes the second subtask' },
{ id: 'worker3', label: 'Worker 3', x: 540, y: 170, status: getStepStatus('Worker'), description: 'Executes the third subtask' },
{ id: 'worker4', label: 'Worker 4', x: 160, y: 240, status: getStepStatus('Worker'), description: 'Executes the fourth subtask' },
{ id: 'worker5', label: 'Worker 5', x: 350, y: 240, status: getStepStatus('Worker'), description: 'Executes the fifth subtask' },
{ id: 'worker6', label: 'Worker 6', x: 540, y: 240, status: getStepStatus('Worker'), description: 'Executes the sixth subtask' },
{ id: 'synthesizer', label: 'Results Integrator', x: 350, y: 310, status: getStepStatus('Integrator'), description: 'Synthesizes results into a cohesive solution' },
{ id: 'response', label: 'Final Response', x: 350, y: 380, status: 'completed' as const, description: 'The complete response delivered to the user' }
];

const links = [
{ source: 'user', target: 'orchestrator', label: 'Query' },
{ source: 'orchestrator', target: 'worker1', label: 'Subtask' },
{ source: 'orchestrator', target: 'worker2', label: 'Subtask' },
{ source: 'orchestrator', target: 'worker3', label: 'Subtask' },
{ source: 'orchestrator', target: 'worker4', label: 'Subtask' },
{ source: 'orchestrator', target: 'worker5', label: 'Subtask' },
{ source: 'orchestrator', target: 'worker6', label: 'Subtask' },
{ source: 'worker1', target: 'synthesizer', label: 'Result' },
{ source: 'worker2', target: 'synthesizer', label: 'Result' },
{ source: 'worker3', target: 'synthesizer', label: 'Result' },
{ source: 'worker4', target: 'synthesizer', label: 'Result' },
{ source: 'worker5', target: 'synthesizer', label: 'Result' },
{ source: 'worker6', target: 'synthesizer', label: 'Result' },
{ source: 'synthesizer', target: 'response', label: 'Synthesis' }
];

renderEnhancedNodes(svg, nodes);
renderEnhancedLinks(svg, links, nodes);
}

// Render Evaluator-Optimizer Workflow
function renderEvaluatorOptimizerDiagram(svg: d3.Selection<SVGGElement, unknown, null, undefined>, 
       getStepStatus: (role: string) => 'completed' | 'pending' | 'skipped') {
const nodes = [
{ id: 'user', label: 'User', x: 100, y: 50, status: 'completed' as const, description: 'The user query that initiated the workflow' },
{ id: 'criteria', label: 'Criteria Designer', x: 300, y: 50, status: getStepStatus('Designer'), description: 'Defines evaluation criteria for the content' },
{ id: 'generator', label: 'Content Creator', x: 300, y: 150, status: getStepStatus('Creator'), description: 'Generates initial content based on the query' },
{ id: 'evaluator', label: 'Quality Assessor', x: 450, y: 200, status: getStepStatus('Assessor'), description: 'Evaluates content against defined criteria' },
{ id: 'optimizer', label: 'Refinement Specialist', x: 300, y: 250, status: getStepStatus('Specialist'), description: 'Improves content based on evaluation feedback' },
{ id: 'response', label: 'Final Response', x: 100, y: 250, status: 'completed' as const, description: 'The complete response delivered to the user' }
];

const links = [
{ source: 'user', target: 'criteria', label: 'Query' },
{ source: 'criteria', target: 'generator', label: 'Criteria' },
{ source: 'generator', target: 'evaluator', label: 'Content' },
{ source: 'evaluator', target: 'optimizer', label: 'Feedback' },
{ source: 'optimizer', target: 'response', label: 'Refined Content' },
// Feedback loop
{ source: 'optimizer', target: 'evaluator', label: 'Iteration', curved: true }
];

renderEnhancedNodes(svg, nodes);
renderEnhancedLinks(svg, links, nodes);

// Add feedback loop label
svg.append('text')
.attr('x', 410)
.attr('y', 225)
.attr('text-anchor', 'middle')
.attr('font-size', '10px')
.attr('fill', '#666')
.text('Feedback Loop');
}

// Default diagram for unknown workflow types
function renderDefaultDiagram(svg: d3.Selection<SVGGElement, unknown, null, undefined>, workflowType: string) {
svg.append('text')
.attr('x', 350)
.attr('y', 200)
.attr('text-anchor', 'middle')
.attr('font-size', '16px')
.attr('fill', '#666')
.text(`No diagram available for ${workflowType}`);
}

// Helper function to render enhanced nodes
function renderEnhancedNodes(svg: d3.Selection<SVGGElement, unknown, null, undefined>, nodes: NodeData[]) {
const nodeGroup = svg.append('g').attr('class', 'nodes');

// Create node groups
const nodeElements = nodeGroup.selectAll('g')
.data(nodes)
.enter()
.append('g')
.attr('transform', (d: NodeData) => `translate(${d.x}, ${d.y})`)
.attr('class', 'node')
.on('mouseover', (event: MouseEvent, d: NodeData) => {
// Set tooltip content
const rect = svgRef.current?.getBoundingClientRect();
if (rect) {
const x = d.x + rect.left;
const y = d.y + rect.top - 10;
setTooltipContent({
content: d.description,
x: x,
y: y
});
}
})
.on('mouseout', () => {
setTooltipContent(null);
});

// Draw node circles with status colors
nodeElements.append('circle')
.attr('r', 30)
.attr('fill', (d: NodeData) => getNodeColor(d.status))
.attr('stroke', '#333')
.attr('stroke-width', 2);

// Add status icons to nodes
nodeElements.append('path')
.attr('d', (d: NodeData) => {
if (d.status === 'completed') {
return 'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z';
} else if (d.status === 'pending') {
return 'M12 6v6l4 2M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20z';
} else { // skipped
return 'M12 8v8m0 4a12 12 0 1 1 0-24 12 12 0 0 1 0 24z';
}
})
.attr('transform', 'translate(-10, -10) scale(0.8)')
.attr('fill', 'white')
.attr('stroke', 'white')
.attr('stroke-width', 1);

// Draw node labels
nodeElements.append('text')
.attr('y', 45)
.attr('text-anchor', 'middle')
.attr('font-family', 'Arial')
.attr('font-size', 12)
.attr('font-weight', 'bold')
.text((d: NodeData) => d.label);
}

// Helper function to render enhanced links
function renderEnhancedLinks(svg: d3.Selection<SVGGElement, unknown, null, undefined>, links: LinkData[], nodes: NodeData[]) {
const linkGroup = svg.append('g').attr('class', 'links');

// Function to find node by ID
const findNode = (id: string): NodeData | undefined => nodes.find(n => n.id === id);

// Draw links
links.forEach(link => {
const source = findNode(link.source);
const target = findNode(link.target);

if (source && target) {
// For curved links (used in feedback loops)
if (link.curved) {
// Calculate control point for curved path
const midX = (source.x + target.x) / 2;
const midY = (source.y + target.y) / 2;
const dx = target.x - source.x;
const dy = target.y - source.y;
const normalX = -dy;
const normalY = dx;
const length = Math.sqrt(normalX * normalX + normalY * normalY);
const unitX = normalX / length;
const unitY = normalY / length;
const controlX = midX + 50 * unitY;
const controlY = midY - 50 * unitX;

// Create curved path
const path = `M${source.x},${source.y} C${controlX},${controlY} ${controlX},${controlY} ${target.x},${target.y}`;

// Draw curved link
linkGroup.append('path')
.attr('d', path)
.attr('stroke', '#333')
.attr('stroke-width', 2)
.attr('fill', 'none');
} else {
// Draw straight link
linkGroup.append('line')
.attr('x1', source.x)
.attr('y1', source.y)
.attr('x2', target.x)
.attr('y2', target.y)
.attr('stroke', '#333')
.attr('stroke-width', 2);
}
}
});
}

return (
<div className="bg-white rounded-lg shadow-sm overflow-hidden">
<div className="p-4 border-b">
<div className="flex justify-between items-center">
<div>
<h3 className="text-lg font-medium flex items-center gap-2">
{formattedWorkflowName} Workflow
<Badge variant="outline" className="ml-2">
{intermediateSteps.length} Steps
</Badge>
</h3>
<p className="text-sm text-gray-600 mt-1 line-clamp-2">{workflowInfo?.reasoning}</p>
</div>

<div className="flex items-center gap-1">
<button 
onClick={handleZoomOut}
className="p-1 rounded hover:bg-gray-100"
aria-label="Zoom out"
>
<ZoomOut size={18} />
</button>
<span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
{Math.round(zoomLevel * 100)}%
</span>
<button 
onClick={handleZoomIn}
className="p-1 rounded hover:bg-gray-100"
aria-label="Zoom in"
>
<ZoomIn size={18} />
</button>
<button 
onClick={handleResetZoom}
className="p-1 rounded hover:bg-gray-100 ml-1"
aria-label="Reset zoom"
>
<RefreshCw size={18} />
</button>
</div>
</div>
</div>

<div className="p-4 overflow-auto relative">
<div className="flex flex-wrap mb-2 gap-3 text-xs">
<div className="flex items-center gap-1">
<div className="w-3 h-3 rounded-full bg-green-500"></div>
<span>Completed</span>
</div>
<div className="flex items-center gap-1">
<div className="w-3 h-3 rounded-full bg-yellow-500"></div>
<span>Pending</span>
</div>
<div className="flex items-center gap-1">
<div className="w-3 h-3 rounded-full bg-gray-300"></div>
<span>Skipped</span>
</div>
</div>

<svg 
ref={svgRef} 
className="mx-auto overflow-visible" 
onMouseLeave={() => setTooltipContent(null)}
/>

{tooltipContent && (
<div 
className="absolute bg-white p-2 shadow-lg rounded text-sm z-10 max-w-xs"
style={{
left: tooltipContent.x + 'px',
top: tooltipContent.y + 'px',
transform: 'translate(-50%, -100%)',
pointerEvents: 'none'
}}
>
{tooltipContent.content}
</div>
)}
</div>
</div>
);
}

