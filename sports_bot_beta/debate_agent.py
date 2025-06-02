from openai import OpenAI

client = OpenAI()

class LLMDebateAgent:
    def __init__(self, model="gpt-4"):
        self.model = model

    def generate_dynamic_debate(self, playerA, playerB, evidence_list, debate_type):
        # Build the debate prompt
        prompt = f"""
You are a sports debate analyst. Compare {playerA['name']} and {playerB['name']} in the context of '{debate_type}'.
Here is the evidence:
"""
        for e in evidence_list:
            stat = e['stat']
            valueA = playerA['stats'].get(stat, 'unknown')
            valueB = playerB['stats'].get(stat, 'unknown')
            prompt += f"- {stat}: {playerA['name']} has {valueA}, {playerB['name']} has {valueB}\n"

        prompt += """
Generate a debate-style argument explaining who is better and why. Provide a balanced view, highlight the strengths of each, and deliver an engaging, fan-style take.
"""

        response = client.chat.completions.create(model=self.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7)

        return response.choices[0].message.content.strip()