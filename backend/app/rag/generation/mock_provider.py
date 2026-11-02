import json
import re
from typing import Optional

from app.rag.generation.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Deterministic LLM Provider for offline tests, CI, and local dev."""

    NON_HR_KEYWORDS = [
        "world cup", "football", "cricket", "weather", "recipe", "python code",
        "capital of", "prime minister", "president of", "stock price", "bitcoin"
    ]

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> str:
        prompt_lower = prompt.lower()

        # Guardrail 1: Non-HR / Out of scope refusal (PRD Section 38, Case 5)
        for keyword in self.NON_HR_KEYWORDS:
            if keyword in prompt_lower:
                return json.dumps({
                    "answer": "I'm designed to help with company HR policies and benefits. Please ask an HR-related question regarding leaves, health insurance, remote work, or employee handbooks.",
                    "confidence": "none",
                    "sources": [],
                    "requires_hr": False,
                    "refusal": True,
                })

        # Guardrail 2: No relevant context found in prompt
        # Inspect context section in prompt
        if "=== POLICY CONTEXT ===" in prompt:
            context_section = prompt.split("=== POLICY CONTEXT ===")[1].split("=== USER QUESTION ===")[0].strip()
            if not context_section or "No relevant policy documents" in context_section:
                return json.dumps({
                    "answer": "I couldn't find this information in the available HR policies. Please contact HR for clarification.",
                    "confidence": "low",
                    "sources": [],
                    "requires_hr": True,
                    "refusal": False,
                })

        # Extract user question from prompt
        question = ""
        if "=== USER QUESTION ===" in prompt:
            question = prompt.split("=== USER QUESTION ===")[1].strip().lower()
        else:
            question = prompt_lower

        # Extract sources from context if available
        sources = []
        doc_matches = re.findall(r"\[Document:\s*([^,\]]+),\s*Section:\s*([^,\]]+),\s*Page:\s*(\d+),\s*Version:\s*([^,\]]+)\]", prompt)
        for match in doc_matches:
            sources.append({
                "document": match[0].strip(),
                "section": match[1].strip(),
                "page": int(match[2].strip()),
                "version": match[3].strip(),
            })

        # Grounded factual generation based on policy context keywords
        if "annual leave" in question or "annual paid leave" in question or "how many days of annual leave" in question or "annual leaves" in question:
            if "india" in prompt_lower:
                answer = "Employees in India are entitled to 24 annual paid leaves per calendar year, accrued at 2 days per completed month of service."
            elif "us" in prompt_lower or "united states" in prompt_lower:
                answer = "Full-time US employees receive 15 days of Paid Time Off (PTO) per calendar year, accrued at 1.25 days per month of service."
            else:
                answer = "Employees are entitled to annual paid leave as per their regional policy."
            confidence = "high"
            requires_hr = False

        elif "carry forward" in question or "carry them forward" in question or "carry over" in question:
            if "india" in prompt_lower:
                answer = "According to the India Leave Policy, a maximum of 10 unused annual paid leaves may be carried forward into the subsequent calendar year. Any unused balance beyond 10 days will lapse automatically on December 31st without cash encashment."
            elif "us" in prompt_lower:
                answer = "US employees can carry over a maximum of 5 unused PTO days into the following calendar year. Any additional accrued PTO must be utilized by December 31st."
            else:
                answer = "Unused leave can be carried forward up to the regional policy limit."
            confidence = "high"
            requires_hr = False

        elif "maternity" in question or "parental" in question or "paternity" in question:
            if "india" in prompt_lower:
                answer = "In accordance with the Maternity Benefit Act, female employees in India are entitled to 26 weeks of fully paid maternity leave for up to two surviving children. Male employees are entitled to 2 weeks (10 working days) of paid paternity leave."
            elif "us" in prompt_lower:
                answer = "Eligible US employees are entitled to up to 12 weeks of unpaid, job-protected leave under the Family and Medical Leave Act (FMLA)."
            else:
                answer = "Parental leave is provided according to local regional statutory requirements."
            confidence = "high"
            requires_hr = False

        elif "sick leave" in question or "casual leave" in question:
            if "india" in prompt_lower:
                answer = "Employees in India receive 12 days of paid Sick and Casual Leave per year, credited on January 1st. Leave exceeding 3 consecutive days requires a registered medical practitioner's certificate."
            else:
                answer = "Sick leave is provided as per your regional employment terms."
            confidence = "high"
            requires_hr = False

        elif "insurance" in question or "medical" in question or "health" in question or "dependent" in question:
            if "india" in prompt_lower:
                answer = "Under the India Group Medical Insurance (GMC) plan, employees and their eligible dependents (spouse, up to 2 children, and dependent parents or in-laws) are covered up to ₹5,00,000 per policy year."
            elif "us" in prompt_lower:
                answer = "The company offers comprehensive medical, dental, and vision coverage through Blue Cross Blue Shield, with choices between a PPO plan and an HDHP with HSA matching up to $1,000 annually. Dependent coverage covers spouses and children up to age 26."
            else:
                answer = "Health insurance coverage is provided for employees and eligible dependents."
            confidence = "high"
            requires_hr = False

        elif "remote" in question or "wfh" in question or "work from home" in question:
            if "expired" in prompt_lower or "2024" in prompt_lower:
                answer = "The available remote work documentation has expired as of December 31, 2024. Please contact HR for the updated active remote work policy."
                confidence = "low"
                requires_hr = True
            else:
                answer = "Remote work guidelines are subject to manager approval and regional office policy."
                confidence = "medium"
                requires_hr = False

        elif "code of conduct" in question or "harassment" in question or "whistleblower" in question:
            answer = "Under the Global Code of Conduct, PolicyPilot AI maintains a zero-tolerance policy towards harassment and discrimination. A confidential, anonymous whistleblower hotline is available at whistleblower@policypilot.internal."
            confidence = "high"
            requires_hr = False

        else:
            # Fallback for unrecognized questions
            answer = "I couldn't find this specific information in the active HR policies. Please contact HR for clarification."
            confidence = "low"
            requires_hr = True

        return json.dumps({
            "answer": answer,
            "confidence": confidence,
            "sources": sources[:3],
            "requires_hr": requires_hr,
            "refusal": False,
        })

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> str:
        return self.generate(prompt, system_prompt, temperature, max_tokens)
