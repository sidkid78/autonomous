'use client';

import { useState } from 'react';

// Define types for our agent's response to ensure type safety
interface AgentStep {
  agent_role: string;
  content: string;
  metadata?: Record<string, unknown>;
}

interface AgentExecutionResponse {
  final_response: string;
  intermediate_steps: AgentStep[];
}

export default function Home() {
  // --- 1. State Management ---
  // We'll use React's useState to manage the form and results
  const [query, setQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AgentExecutionResponse | null>(null);

  // --- 2. API Call Handler ---
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault(); // Prevent the browser from reloading the page
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const apiResponse = await fetch('http://localhost:8000/api/v1/agent/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_query: query, workflow_selection: { selected_workflow: "autonomous_agent" } }),
      });

      if (!apiResponse.ok) {
        throw new Error(`API Error: ${apiResponse.status} ${apiResponse.statusText}`);
      }

      const data: AgentExecutionResponse = await apiResponse.json();
      setResponse(data);
    } catch (err: unknown) {
      console.error('Error:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  // --- 3. UI Rendering ---
  return (
    <main className="flex min-h-screen flex-col items-center p-12 bg-gray-50 text-gray-800">
      <div className="w-full max-w-4xl">
        <h1 className="text-4xl font-bold mb-4 text-center">Autonomous Agent</h1>
        <p className="text-lg text-gray-600 mb-8 text-center">
          Give the agent a task and see it plan, act, and reflect to achieve the goal.
        </p>

        <form onSubmit={handleSubmit} className="mb-8">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Write a short poem to a file named 'poem.txt'"
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="mt-4 w-full bg-blue-600 text-white p-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400"
            disabled={isLoading}
          >
            {isLoading ? 'Agent is thinking...' : 'Execute Task'}
          </button>
        </form>

        {/* --- Display Area for Results --- */}
        {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">{error}</div>}
        
        {response && (
          <div className="space-y-8">
            {/* Final Response */}
            <div>
              <h2 className="text-2xl font-semibold mb-2 border-b-2 border-gray-200 pb-2">Final Response</h2>
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <p>{response.final_response}</p>
              </div>
            </div>

            {/* Intermediate Steps */}
            <div>
              <h2 className="text-2xl font-semibold mb-2 border-b-2 border-gray-200 pb-2">Execution Trace</h2>
              <div className="space-y-4">
                {response.intermediate_steps.map((step, index) => (
                  <div key={index} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                    <h3 className="font-bold text-blue-700 text-lg">{`Step ${index + 1}: ${step.agent_role}`}</h3>
                    <pre className="mt-2 whitespace-pre-wrap bg-gray-100 p-3 rounded text-sm font-mono">{step.content}</pre>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
