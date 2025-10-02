'use client';

import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { WORKFLOW_TYPES, type AgentMessage, type WorkflowSelection, type IntermediateStep } from '@/types';
import EnhancedWorkflowDiagram from './enhanced-workflow-diagram';
import { 
  Send, 
  Bot, 
  User, 
  Settings, 
  History, 
  Zap,
  Brain,
  MessageSquare,
  Loader2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function Home() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowSelection | null>(null);
  const [intermediateSteps, setIntermediateSteps] = useState<IntermediateStep[]>([]);
  const [showWorkflowDetails, setShowWorkflowDetails] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Mock function to simulate agent response
  const simulateAgentResponse = async (userMessage: string): Promise<{
    response: string;
    workflow: WorkflowSelection;
    steps: IntermediateStep[];
  }> => {
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Mock workflow selection based on message content
    let selectedWorkflow = 'prompt_chaining';
    if (userMessage.toLowerCase().includes('compare') || userMessage.toLowerCase().includes('analyze')) {
      selectedWorkflow = 'parallel_voting';
    } else if (userMessage.toLowerCase().includes('complex') || userMessage.toLowerCase().includes('project')) {
      selectedWorkflow = 'orchestrator_workers';
    } else if (userMessage.toLowerCase().includes('route') || userMessage.toLowerCase().includes('category')) {
      selectedWorkflow = 'routing';
    }

    const workflow: WorkflowSelection = {
      selected_workflow: selectedWorkflow,
      reasoning: `Selected ${selectedWorkflow.replace('_', ' ')} workflow based on the complexity and nature of your request.`,
      confidence: 0.85
    };

    const steps: IntermediateStep[] = [
      {
        agent_role: 'Planner',
        content: 'Analyzing the user request and creating a structured plan...',
        timestamp: new Date().toISOString(),
        status: 'completed'
      },
      {
        agent_role: 'Executor',
        content: 'Processing the request using the selected workflow...',
        timestamp: new Date().toISOString(),
        status: 'completed'
      },
      {
        agent_role: 'Evaluator',
        content: 'Reviewing the results and ensuring quality...',
        timestamp: new Date().toISOString(),
        status: 'completed'
      }
    ];

    return {
      response: `I've processed your request using the ${workflow.selected_workflow.replace('_', ' ')} workflow. Here's a comprehensive response based on your query: "${userMessage}". The system analyzed your request and determined that this workflow would be most effective for providing you with accurate and detailed information.`,
      workflow,
      steps
    };
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const { response, workflow, steps } = await simulateAgentResponse(inputMessage);
      
      setCurrentWorkflow(workflow);
      setIntermediateSteps(steps);

      const assistantMessage: AgentMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
        workflow,
        intermediateSteps: steps
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                  Autonomous Agent System
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Intelligent workflow orchestration
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                title="Settings"
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button> 
              <button title="History" className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                <History className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 h-[600px] flex flex-col">
              {/* Chat Header */}
              <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                    <span className="font-medium text-slate-900 dark:text-white">Chat</span>
                  </div>
                  {currentWorkflow && (
                    <Badge variant="outline" className="text-xs">
                      {currentWorkflow.selected_workflow.replace('_', ' ')}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center py-12">
                    <Bot className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
                      Welcome to the Autonomous Agent System
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400 max-w-md mx-auto">
                      Start a conversation and watch as the system intelligently selects 
                      the best workflow to handle your request.
                    </p>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {message.role === 'assistant' && (
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                          <Bot className="w-4 h-4 text-white" />
                        </div>
                      )}
                      
                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-2 ${
                          message.role === 'user'
                            ? 'bg-blue-500 text-white'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </p>
                      </div>

                      {message.role === 'user' && (
                        <div className="w-8 h-8 rounded-full bg-slate-300 dark:bg-slate-600 flex items-center justify-center flex-shrink-0">
                          <User className="w-4 h-4 text-slate-600 dark:text-slate-300" />
                        </div>
                      )}
                    </div>
                  ))
                )}

                {isLoading && (
                  <div className="flex gap-3 justify-start">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-slate-100 dark:bg-slate-800 rounded-lg px-4 py-2">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          Processing your request...
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input */}
              <div className="p-4 border-t border-slate-200 dark:border-slate-700">
                <div className="flex gap-2">
                  <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything..."
                    className="flex-1 resize-none rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={1}
                    disabled={isLoading}
                  />
                  <button
                    title="Send Message"
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                    className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Workflow Types */}
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4">
              <h3 className="font-medium text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Available Workflows
              </h3>
              <div className="space-y-2">
                {WORKFLOW_TYPES.map((workflow) => (
                  <div
                    key={workflow.id}
                    className={`p-3 rounded-lg border transition-colors ${
                      currentWorkflow?.selected_workflow === workflow.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <span className="text-lg">{workflow.icon}</span>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm text-slate-900 dark:text-white">
                          {workflow.name}
                        </h4>
                        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                          {workflow.description}
                        </p>
                        <Badge variant="outline" className="mt-2 text-xs">
                          {workflow.category}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Current Workflow Details */}
            {currentWorkflow && (
              <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4">
                <button
                  onClick={() => setShowWorkflowDetails(!showWorkflowDetails)}
                  className="w-full flex items-center justify-between text-left"
                >
                  <h3 className="font-medium text-slate-900 dark:text-white">
                    Current Workflow
                  </h3>
                  {showWorkflowDetails ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>
                
                {showWorkflowDetails && (
                  <div className="mt-4 space-y-3">
                    <div>
                      <p className="text-sm font-medium text-slate-900 dark:text-white">
                        {currentWorkflow.selected_workflow.replace('_', ' ')}
                      </p>
                      <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                        {currentWorkflow.reasoning}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Confidence: {Math.round(currentWorkflow.confidence * 100)}%
                      </p>
                      <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${currentWorkflow.confidence * 100}%` }}
                        />
                      </div>
                    </div>

                    {intermediateSteps.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                          Processing Steps:
                        </p>
                        <div className="space-y-1">
                          {intermediateSteps.map((step, index) => (
                            <div key={index} className="flex items-center gap-2 text-xs">
                              <div className={`w-2 h-2 rounded-full ${
                                step.status === 'completed' ? 'bg-green-500' :
                                step.status === 'pending' ? 'bg-yellow-500' : 'bg-gray-400'
                              }`} />
                              <span className="text-slate-600 dark:text-slate-400">
                                {step.agent_role}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Workflow Visualization */}
        {currentWorkflow && (
          <div className="mt-6">
            <EnhancedWorkflowDiagram
              workflowInfo={currentWorkflow}
              intermediateSteps={intermediateSteps}
            />
          </div>
        )}
      </div>
    </div>
  );
}
