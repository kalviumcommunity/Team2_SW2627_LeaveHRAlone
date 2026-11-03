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
        if "=== POLICY CONTEXT ===" in prompt:
            context_section = prompt.split("=== POLICY CONTEXT ===")[1].split("=== USER QUESTION ===")[0].strip()
            if not context_section or "No relevant policy documents" in context_section:
                return json.dumps({
                    "answer": "I couldn't find this information in the official policy documents for your region. Please contact HR for assistance.",
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

        # Grounded factual generation: Clear Answer First + Highlighted Official Policy Excerpt
        # 1. Carry forward (must precede general annual leave check)
        if "carry forward" in question or "carry them forward" in question or "carry over" in question or "carried forward" in question:
            if "india" in prompt_lower:
                answer = (
                    "Yes, you can carry forward unused annual leave into the next year. "
                    "Employees in India are permitted to carry forward a maximum of 10 unused annual paid leave days into the subsequent calendar year. "
                    "Any balance exceeding 10 days will lapse automatically on December 31st without cash encashment.\n\n"
                    "> 📌 **Official Policy Excerpt (India Leave Policy, Section 2.0):**\n"
                    "> *\"2.3 A maximum of 10 unused annual paid leaves may be carried forward into the subsequent calendar year. "
                    "Any unused balance beyond 10 days will lapse automatically on December 31st without cash encashment.\"*"
                )
            elif "us" in prompt_lower:
                answer = (
                    "Yes, you can carry over unused PTO. Full-time US employees can carry over up to 5 unused PTO days into the following calendar year. "
                    "Any additional accrued PTO beyond 5 days must be utilized by December 31st.\n\n"
                    "> 📌 **Official Policy Excerpt (US Employee Handbook, Section 2.0):**\n"
                    "> *\"2.3 Employees may carry over a maximum of 5 unused PTO days into the subsequent calendar year. "
                    "Any additional accrued PTO must be utilized by December 31st.\"*"
                )
            else:
                answer = "Unused leave can be carried forward up to the regional policy limit."
            confidence = "high"
            requires_hr = False

        # 2. General annual leave / PTO entitlement
        elif "annual leave" in question or "annual paid leave" in question or "how many days of annual leave" in question or "annual leaves" in question or "pto" in question:
            if "india" in prompt_lower:
                answer = (
                    "Employees in India are entitled to 24 annual paid leaves per calendar year. "
                    "These leaves accrue at a rate of 2 days per completed month of service and can be requested through the HR self-service portal.\n\n"
                    "> 📌 **Official Policy Excerpt (India Leave Policy, Section 2.0):**\n"
                    "> *\"2.1 All full-time employees in India are entitled to 24 annual paid leaves per calendar year "
                    "(accrued at 2 days per completed month of service). 2.2 Annual leave must be requested at least 3 business days in advance "
                    "via the HR self-service portal for requests exceeding 2 consecutive days.\"*"
                )
            elif "us" in prompt_lower or "united states" in prompt_lower:
                answer = (
                    "Full-time US employees receive 15 days of Paid Time Off (PTO) per calendar year, accrued at 1.25 days per month of service, "
                    "in addition to 11 standard company-paid federal holidays.\n\n"
                    "> 📌 **Official Policy Excerpt (US Employee Handbook, Section 2.0):**\n"
                    "> *\"2.1 Full-time employees accrue 15 days of PTO annually at 1.25 days per completed month. "
                    "2.2 Company observes 11 federal holidays.\"*"
                )
            else:
                answer = "Employees are entitled to annual paid leave as per their regional policy."
            confidence = "high"
            requires_hr = False

        # 3. Parental, Maternity & Paternity Leave
        elif "maternity" in question or "parental" in question or "paternity" in question or "adoption" in question:
            if "india" in prompt_lower:
                answer = (
                    "In India, female employees are entitled to 26 weeks of fully paid maternity leave for up to two surviving children. "
                    "Male employees are entitled to 2 weeks (10 working days) of fully paid paternity leave to be taken within 6 months of the child's birth or legal adoption.\n\n"
                    "> 📌 **Official Policy Excerpt (India Leave Policy, Section 4.0):**\n"
                    "> *\"4.1 In accordance with the Maternity Benefit Act, female employees are entitled to 26 weeks of fully paid maternity leave "
                    "for up to two surviving children. 4.2 Male employees are entitled to 2 weeks (10 working days) of fully paid paternity leave, "
                    "which must be taken within 6 months of the child's birth or legal adoption.\"*"
                )
            elif "us" in prompt_lower:
                answer = (
                    "Under the US Family and Medical Leave Act (FMLA), eligible employees who have completed at least 12 months and 1,250 hours of service "
                    "are entitled to up to 12 weeks of unpaid, job-protected leave for childbirth, adoption, or serious health conditions.\n\n"
                    "> 📌 **Official Policy Excerpt (US Employee Handbook, Section 5.0):**\n"
                    "> *\"5.1 Under the Family and Medical Leave Act (FMLA), eligible employees who have completed at least 12 months "
                    "and 1,250 hours of service are entitled to up to 12 weeks of unpaid, job-protected leave.\"*"
                )
            else:
                answer = "Parental leave is provided according to local regional statutory requirements."
            confidence = "high"
            requires_hr = False

        # 4. Sick and Casual Leave
        elif "sick leave" in question or "casual leave" in question or "sick" in question:
            if "india" in prompt_lower:
                answer = (
                    "Employees in India receive 12 days of paid Sick and Casual Leave per calendar year, credited upfront on January 1st. "
                    "A medical certificate from a registered practitioner is required for absences exceeding 3 consecutive days. Unused sick and casual leave cannot be carried forward or encashed.\n\n"
                    "> 📌 **Official Policy Excerpt (India Leave Policy, Section 3.0):**\n"
                    "> *\"3.1 Employees receive 12 days of paid Sick and Casual Leave per year, credited on January 1st of each calendar year. "
                    "3.2 Sick leave exceeding 3 consecutive days requires a registered medical practitioner's certificate upon return to work. "
                    "3.3 Unused Sick and Casual Leave cannot be carried forward to the following year and cannot be encashed.\"*"
                )
            else:
                answer = "Sick leave is provided as per your regional employment terms."
            confidence = "high"
            requires_hr = False

        # 5. Group Health Insurance & Dependent Coverage
        elif "insurance" in question or "medical" in question or "health" in question or "dependent" in question or "gmc" in question or "opd" in question or "dental" in question:
            if "india" in prompt_lower:
                answer = (
                    "Yes, your group health insurance provides comprehensive family coverage up to ₹5,00,000 per policy year. "
                    "This covers you (the employee), your legally married spouse, up to 2 dependent children, and dependent parents or parents-in-law.\n\n"
                    "> 📌 **Official Policy Excerpt (India Benefits & Health Insurance, Section 1.0):**\n"
                    "> *\"1.1 All regular full-time employees are enrolled in the Group Medical Cover (GMC) with sum insured up to ₹5,00,000 per family per policy year. "
                    "Covered dependents include employee, legally married spouse, up to 2 dependent children, and dependent parents or parents-in-law.\"*"
                )
            elif "us" in prompt_lower:
                answer = (
                    "The company offers comprehensive medical, dental, and vision coverage through Blue Cross Blue Shield, with choices between a PPO plan and an HDHP with HSA matching up to $1,000 annually. "
                    "Eligible dependents include spouses and unmarried dependent children up to age 26.\n\n"
                    "> 📌 **Official Policy Excerpt (US Employee Handbook, Section 3.0):**\n"
                    "> *\"3.1 Full-time employees are eligible for group medical, dental, and vision coverage through Blue Cross Blue Shield. "
                    "3.2 Eligible dependents include spouses and dependent children up to age 26.\"*"
                )
            else:
                answer = "Health insurance coverage is provided for employees and eligible dependents."
            confidence = "high"
            requires_hr = False

        # 6. Bereavement Leave
        elif "bereavement" in question or "compassionate" in question:
            answer = (
                "Employees are eligible for up to 5 consecutive working days of fully paid bereavement leave in the event of the loss of an immediate family member.\n\n"
                "> 📌 **Official Policy Excerpt (India Leave Policy, Section 5.0):**\n"
                "> *\"5.1 Employees are eligible for up to 5 consecutive working days of paid bereavement leave in the event of the loss of an immediate family member (parent, spouse, child, or sibling).\"*"
            )
            confidence = "high"
            requires_hr = False

        # 7. Remote Work
        elif "remote" in question or "wfh" in question or "work from home" in question:
            if "expired" in prompt_lower or "2024" in prompt_lower:
                answer = "The available remote work documentation has expired as of December 31, 2024. Please contact HR for the updated active remote work policy."
                confidence = "low"
                requires_hr = True
            else:
                answer = (
                    "Remote work arrangements require managerial approval and adherence to company IT security guidelines.\n\n"
                    "> 📌 **Official Policy Excerpt (Workplace Policies):**\n"
                    "> *\"Remote work guidelines are subject to manager approval and regional office operational policy.\"*"
                )
                confidence = "medium"
                requires_hr = False

        # 8. Workplace Code of Conduct & Ethics
        elif "code of conduct" in question or "harassment" in question or "whistleblower" in question or "ethics" in question:
            answer = (
                "Under the Global Code of Conduct, the company enforces a zero-tolerance policy against any form of harassment, discrimination, or retaliation. "
                "Employees can confidentially and anonymously report concerns directly through the internal ethics hotline.\n\n"
                "> 📌 **Official Policy Excerpt (Global Code of Conduct, Section 2.0 & 4.0):**\n"
                "> *\"2.1 The company maintains strict zero tolerance for harassment, discrimination, or bullying in any form. "
                "4.1 Employees may report violations confidentially or anonymously via the ethics hotline: whistleblower@leavehralone.internal.\"*"
            )
            confidence = "high"
            requires_hr = False

        else:
            # Fallback for questions without exact template match
            answer = "I couldn't find this specific information in the official policy documents for your region. Please contact HR for assistance."
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
