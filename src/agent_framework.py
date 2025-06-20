# src/agent_framework.py

import inspect
from pydantic import BaseModel
from openai import OpenAI
import json
from typing import List, Type, Dict, Any, Optional

client = OpenAI()

class AgentOutputSchema(BaseModel):
    """Base model for agent outputs."""
    final_output: Any
    
    class Config:
        extra = "allow"

class Agent:
    def __init__(self, name: str, instructions: str, model: str, output_type: Type[BaseModel], handoffs: List['Agent'] = None):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.output_type = output_type
        self.handoffs = handoffs or []

    def _get_system_prompt(self):
        prompt = f"{self.instructions}\n\n"
        prompt += f"Your output must be a JSON object that strictly follows this Pydantic schema:\n"
        prompt += f"```json\n{json.dumps(self.output_type.model_json_schema(), indent=2)}\n```"
        return prompt

class Runner:
    @staticmethod
    async def run(agent: Agent, input: Any) -> Optional[BaseModel]:
        system_prompt = agent._get_system_prompt()
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if isinstance(input, str):
            messages.append({"role": "user", "content": input})
        elif isinstance(input, list):
            messages.extend(input)

        try:
            response = client.chat.completions.create(
                model=agent.model,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            response_content = response.choices[0].message.content
            parsed_json = json.loads(response_content)
            
            # Validate with Pydantic model
            validated_output = agent.output_type.model_validate(parsed_json)
            
            if agent.handoffs:
                # For simplicity, pass to the first handoff agent
                next_agent = agent.handoffs[0]
                # Pass the validated dict to the next agent
                return await Runner.run(next_agent, input=[{"role": "user", "content": json.dumps(validated_output.model_dump())}])
            
            return validated_output

        except Exception as e:
            print(f"Error running agent {agent.name}: {e}")
            return None 