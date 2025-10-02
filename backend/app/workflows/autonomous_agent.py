"""
Autonomous Agent Workflow Module

This module implements a multi-agent autonomous workflow system that uses planning,
action, and reflection phases to accomplish complex tasks. The agent operates in
an iterative loop, breaking down tasks into manageable steps and executing them
using available tools.

The workflow consists of three main phases:
1. Planning: Creates a detailed plan for accomplishing the task
2. Acting: Executes actions or uses tools to work toward task completion
3. Reflection: Evaluates progress and determines next steps

The agent maintains memory across iterations and can adapt its approach based on
observations and reflections from previous steps.
"""

# Correctly import everything from the single schemas file
from app.models.schemas import WorkflowSelection, AgentResponse, ToolDefinition 
from app.core.llm_client import get_llm_client
from google.genai import types as genai_types
from typing import Tuple, List, Dict, Any 
import logging 
import json 
import asyncio 

# The ToolDefinition class has been removed from this file

async def execute(
    workflow_selection: WorkflowSelection, 
    user_query: str,
    max_iterations: int = 10,
    available_tools: List[ToolDefinition] = None
) -> Tuple[str, List[AgentResponse]]:
    """
    Execute the autonomous agent workflow to accomplish a user's task.
    
    This function implements a multi-phase iterative approach where the agent:
    1. Plans how to accomplish the task
    2. Takes actions (using tools or reasoning)
    3. Reflects on progress and decides next steps
    
    The process continues until the task is complete or max_iterations is reached.
    
    Args:
        workflow_selection (WorkflowSelection): Configuration containing agent personas
            and workflow settings
        user_query (str): The user's task or question to be accomplished
        max_iterations (int, optional): Maximum number of planning-action-reflection
            cycles to perform. Defaults to 10.
        available_tools (List[ToolDefinition], optional): List of tools the agent
            can use during execution. Defaults to None (empty list).
    
    Returns:
        Tuple[str, List[AgentResponse]]: A tuple containing:
            - str: The final response or summary of task completion
            - List[AgentResponse]: List of intermediate steps showing the agent's
              reasoning, actions, and observations throughout execution
    
    Raises:
        Exception: May raise exceptions from LLM client or tool execution, which
            are caught and handled internally with fallback behavior
    """
    
    # ... the rest of your execute function remains exactly the same
    client = get_llm_client()
    personas = workflow_selection.personas.get("autonomous_agent", {})
    intermediate_steps = []
    
    available_tools = available_tools or []
    
    agent_memory = {
        "task": user_query,
        "tools": [tool.dict() for tool in available_tools],
        "iterations": [],
        "observations": [],
        "task_complete": False
    }
    
    planning_function = {
        "name": "create_task_plan",
        "description": "Creates a plan for how to accomplish the given task",
        "parameters": {
            "type": "object",
            "properties": {
                "task_understanding": {
                    "type": "string",
                    "description": "Detailed understanding of the task requirements"
                },
                "plan_steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_number": {
                                "type": "integer",
                                "description": "The step number in the plan"
                            },
                            "step_description": {
                                "type": "string",
                                "description": "Description of what this step will accomplish"
                            },
                            "required_tools": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Tools needed for this step"
                            }
                        },
                        "required": ["step_number", "step_description"]
                    },
                    "description": "Ordered steps to accomplish the task"
                },
                "expected_outcome": {
                    "type": "string",
                    "description": "What success looks like for this task"
                }
            },
            "required": ["task_understanding", "plan_steps", "expected_outcome"]
        }
    }
    
    action_function = {
        "name": "execute_action",
        "description": "Executes an action or tool to work toward task completion",
        "parameters": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["use_tool", "reasoning", "intermediate_result", "final_result"],
                    "description": "Type of action to take"
                },
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool to use (if action_type is use_tool)"
                },
                "tool_parameters": {
                    "type": "object",
                    "description": "Parameters to pass to the tool (if action_type is use_tool)"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Reasoning about the current state (if action_type is reasoning)"
                },
                "result": {
                    "type": "string",
                    "description": "Intermediate or final result (if action_type is intermediate_result or final_result)"
                }
            },
            "required": ["action_type"]
        }
    }
    
    reflection_function = {
        "name": "reflect_on_progress",
        "description": "Evaluates progress toward task completion and decides next steps",
        "parameters": {
            "type": "object",
            "properties": {
                "progress_assessment": {
                    "type": "string",
                    "description": "Assessment of current progress toward the goal"
                },
                "completed_steps": {
                    "type": "array",
                    "items": {
                        "type": "integer"
                    },
                    "description": "Which steps of the plan have been completed"
                },
                "unexpected_observations": {
                    "type": "string",
                    "description": "Any unexpected findings or obstacles encountered"
                },
                "task_complete": {
                    "type": "boolean",
                    "description": "Whether the overall task is now complete"
                },
                "next_step": {
                    "type": "string",
                    "description": "Description of the next step to take (if task is not complete)"
                }
            },
            "required": ["progress_assessment", "task_complete"]
        }
    }
    
    iteration = 0
    final_response = "Task processed, but no specific result was generated."
    
    while iteration < max_iterations and not agent_memory["task_complete"]:
        iteration += 1
        logging.info(f"Starting iteration {iteration} of autonomous agent")
        
        # Step 1: Planning Phase
        planner_agent = personas.get("planner_agent", {})
        
        history_context = ""
        if agent_memory["iterations"]:
            history_context = "Previous iterations:\n" + "\n".join([
                f"Iteration {i+1}:\n"
                f"Plan: {memory.get('plan', 'No plan')}\n"
                f"Action: {memory.get('action', 'No action')}\n"
                f"Observation: {memory.get('observation', 'No observation')}\n"
                f"Reflection: {memory.get('reflection', 'No reflection')}\n"
                for i, memory in enumerate(agent_memory["iterations"])
            ])
        
        planning_prompt = f"""
        {generate_agent_context(planner_agent)}
        
        TASK: {user_query}
        
        {history_context}
        
        Available tools:
        {json.dumps([tool.dict() for tool in available_tools], indent=2)}
        
        Your task is to create a detailed plan for accomplishing the user's request.
        Think carefully about the steps needed, which tools might be useful at each step,
        and what success looks like for this task.
        
        If this is not the first iteration, consider what has been learned in previous
        iterations and adjust your plan accordingly.
        """
        
        try:
            planning_tool_config = genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(
                    mode='ANY',
                    allowed_function_names=["create_task_plan"]
                )
            )
            planning_response = await client.generate_with_tools_async(
                prompt=planning_prompt,
                function_declarations=[planning_function],
                temperature=0.4,
                tool_config=planning_tool_config
            )
            
            if planning_response.get("type") == "tool_call" and planning_response.get("name") == "create_task_plan":
                plan = planning_response["arguments"]
            else:
                logging.warning("Planning function call not returned, using fallback.")
                plan = { "task_understanding": "Fallback plan", "plan_steps": [], "expected_outcome": "Best effort." }

        except Exception as e:
            logging.error(f"Error in planning phase: {e}")
            plan = { "task_understanding": f"Error: {e}", "plan_steps": [], "expected_outcome": "Error occurred." }
            
        current_iteration = {"plan": plan}
        agent_memory["iterations"].append(current_iteration)
        intermediate_steps.append(AgentResponse(agent_role="Task Planner", content=f"Plan created: {plan.get('task_understanding', 'N/A')}", metadata=plan))
        
        # Step 2: Acting Phase
        actor_agent = personas.get("actor_agent", {})
        actor_prompt = f"""
        {generate_agent_context(actor_agent)}
        
        TASK: {user_query}
        
        Current Plan:
        {json.dumps(plan, indent=2)}
        
        Previous Observations:
        {json.dumps(agent_memory["observations"], indent=2)}
        
        Available tools:
        {json.dumps([tool.dict() for tool in available_tools], indent=2)}
        
        Your task is to execute the next appropriate step in the plan.
        You can use available tools, perform reasoning, or generate intermediate or final results.
        
        Think step-by-step and take the most appropriate action to move closer to completing the task.
        """
        
        try:
            action_tool_config = genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(
                    mode='ANY',
                    allowed_function_names=["execute_action"]
                )
            )
            
            action_response = await client.generate_with_tools_async(
                prompt=actor_prompt,
                function_declarations=[action_function],
                temperature=0.5,
                tool_config=action_tool_config
            )
            
            if action_response.get("type") == "tool_call" and action_response.get("name") == "execute_action":
                action = action_response["arguments"]
            else:
                logging.warning("Action function call not returned, using fallback.")
                action = {"action_type": "reasoning", "reasoning": "Unable to determine next action."}

        except Exception as e:
            logging.error(f"Error in action phase: {e}")
            action = {"action_type": "reasoning", "reasoning": f"Error occurred: {e}"}
        
        observation = "No observation recorded."
        
        if action.get("action_type") == "use_tool":
            tool_name = action.get("tool_name", "")
            tool_parameters = action.get("tool_parameters", {})
            
            tool_found = False
            for tool in available_tools:
                if tool.name == tool_name and tool.function:
                    try:
                        observation = await tool.function(**tool_parameters)
                        tool_found = True
                    except Exception as e:
                        observation = f"Error executing tool {tool_name}: {str(e)}"
                        logging.error(observation)
                    break
                    
            if not tool_found:
                observation = f"Tool '{tool_name}' not found or not executable."
        elif action.get("action_type") == "reasoning":
            observation = f"Reasoning: {action.get('reasoning', 'No reasoning provided.')}"
        elif action.get("action_type") in ["intermediate_result", "final_result"]:
            observation = f"Result: {action.get('result', 'No result provided.')}"
            
            if action["action_type"] == "final_result":
                agent_memory["task_complete"] = True
                final_response = action.get("result", "Task completed successfully.")

        
        current_iteration["action"] = action
        current_iteration["observation"] = observation
        agent_memory["observations"].append(observation)
        
        intermediate_steps.append(AgentResponse(
            agent_role="Action Executor",
            content=format_action_content(action, observation),
            metadata={
                "action": action,
                "observation": observation
            }
        ))
        
        if agent_memory["task_complete"]:
            break
            
        # Step 3: Reflection Phase
        reflector_agent = personas.get("reflector_agent", {})
        reflection_prompt = f"""
        {generate_agent_context(reflector_agent)}
        
        TASK: {user_query}
        
        Current Plan:
        {json.dumps(plan, indent=2)}
        
        Recent Action:
        {json.dumps(action, indent=2)}
        
        Observation from Action:
        {observation}
        
        Previous Iterations:
        {json.dumps(agent_memory["iterations"], indent=2)}
        
        Your task is to reflect on the current progress toward completing the overall task.
        Evaluate what has been accomplished, what steps have been completed, and what remains to be done.
        Determine if the task is now complete or what should be the next steps.
        """
        
        try:
            reflection_tool_config = genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(
                    mode='ANY',
                    allowed_function_names=["reflect_on_progress"]
                )
            )
            
            reflection_response = await client.generate_with_tools_async(
                prompt=reflection_prompt,
                function_declarations=[reflection_function],
                temperature=0.4,
                tool_config=reflection_tool_config
            )
            
            if reflection_response.get("type") == "tool_call" and reflection_response.get("name") == "reflect_on_progress":
                reflection = reflection_response["arguments"]
            else:
                logging.warning("Reflection function call not returned, using fallback.")
                reflection = {"progress_assessment": "Unable to assess progress.", "task_complete": False}

        except Exception as e:
            logging.error(f"Error in reflection phase: {e}")
            reflection = {"progress_assessment": f"Error occurred: {e}", "task_complete": False}
        
        agent_memory["task_complete"] = reflection.get("task_complete", False)
        
        current_iteration["reflection"] = reflection
        
        intermediate_steps.append(AgentResponse(
            agent_role="Progress Reflector",
            content=f"Progress Assessment:\n{reflection.get('progress_assessment', 'N/A')}",
            metadata=reflection
        ))
        
        if agent_memory["task_complete"]:
            logging.info(f"Task marked as complete after {iteration} iterations")
            break
    
    if not agent_memory["task_complete"]:
        logging.warning(f"Maximum iterations ({max_iterations}) reached without task completion")
        
        summary_prompt = f"""
        TASK: {user_query}
        
        EXECUTION HISTORY:
        {json.dumps(agent_memory["iterations"], indent=2)}
        
        Based on the above execution history, please provide a comprehensive summary
        of the findings and results to address the user's original request.
        """
        
        try:
            final_response = await client.generate_text_async(summary_prompt, temperature=0.7)
        except Exception as e:
            logging.error(f"Error generating summary response: {str(e)}")
            final_response += f" Error generating summary: {str(e)}"
    
    intermediate_steps.append(AgentResponse(
        agent_role="Task Summarizer",
        content=f"Summary of execution:\n" +
                f"- Completed {iteration} iterations\n" +
                f"- Task complete: {'Yes' if agent_memory['task_complete'] else 'No'}\n" +
                f"- Final response generated",
        metadata={
            "iterations": iteration,
            "task_complete": agent_memory["task_complete"],
            "memory": agent_memory
        }
    ))
    
    return final_response, intermediate_steps


def format_action_content(action, observation):
    """
    Format action content for human-readable display.
    
    Args:
        action (Dict[str, Any]): The action dictionary containing action_type and related fields
        observation (str): The observation or result from executing the action
        
    Returns:
        str: Formatted string representation of the action and observation
    """
    if action["action_type"] == "use_tool":
        return (
            f"Tool Used: {action.get('tool_name', 'Unknown')}\n\n"
            f"Parameters: {json.dumps(action.get('tool_parameters', {}), indent=2)}\n\n"
            f"Observation: {observation}"
        )
    elif action["action_type"] == "reasoning":
        return (
            f"Reasoning:\n{action.get('reasoning', 'No reasoning provided.')}\n\n"
            f"Observation: {observation}"
        )
    elif action["action_type"] in ["intermediate_result", "final_result"]:
        return (
            f"{'Final' if action['action_type'] == 'final_result' else 'Intermediate'} Result:\n"
            f"{action.get('result', 'No result provided.')}\n\n"
            f"Observation: {observation}"
        )
    else:
        return f"Unknown action type: {action['action_type']}\n\nObservation: {observation}"

def generate_agent_context(agent_persona: dict) -> str:
    """
    Generate a context prompt section based on an agent persona configuration.
    
    This function creates a formatted prompt section that establishes the agent's
    role, personality, function, and strengths for use in LLM prompts.
    
    Args:
        agent_persona (dict): Dictionary containing persona configuration with keys:
            - role (str): The agent's role (e.g., "Task Planner")
            - persona (str): Personality description (e.g., "Methodical and thorough")
            - description (str): Functional description of what the agent does
            - strengths (List[str]): List of the agent's key strengths
            
    Returns:
        str: Formatted context string for inclusion in prompts, or empty string
            if agent_persona is empty or None
    """
    if not agent_persona:
        return ""
        
    role = agent_persona.get("role", "Assistant")
    persona = agent_persona.get("persona", "Helpful and knowledgeable")
    description = agent_persona.get("description", "Provides helpful responses")
    strengths = ", ".join(agent_persona.get("strengths", ["Assistance"]))
    
    return f"""
    === AGENT CONTEXT ===
    ROLE: {role}
    CHARACTER: {persona}
    FUNCTION: {description}
    STRENGTHS: {strengths}
    ==================
    
    You are acting as the {role}. Your personality is {persona}
    """