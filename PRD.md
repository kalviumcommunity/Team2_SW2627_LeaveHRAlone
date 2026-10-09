PolicyPilot AIAI-Powered HR Policy & Benefits Assistant
Document Type: Product Requirements Document
Version: 1.0
Status: MVP / Hackathon Ready
Product Category: Enterprise AI / HRTech / RAG
Primary Users: Employees, HR Administrators
Core Technology: RAG, LLM, Vector Search, Document Intelligence
1. Product Overview
PolicyPilot AI is an AI-powered HR assistant that allows employees to ask questions about company policies, leave rules, benefits, employee handbooks, and region-specific HR guidelines.
Instead of employees repeatedly contacting HR for questions that are already answered in company documentation, PolicyPilot AI retrieves the relevant information from approved HR documents and generates a concise, grounded answer with citations.
The system is designed to support organizations where HR policies differ by:
Country
Region
Office
Employee type
Policy version
Employment category
The assistant must prioritize accuracy, source traceability, access control, and prevention of hallucinations.
2. Problem Statement
HR departments receive a large number of repetitive questions such as:
"How many annual leaves do I have?"
"Can I carry forward unused leave?"
"What is the maternity leave policy?"
"Does my insurance cover dependents?"
"How many sick leaves are available?"
"Can I work remotely?"
"What is the notice period?"
"What benefits are available to employees in India?"
Although the answers already exist in company documents, employees often struggle to find the correct information.
This results in:
Repetitive HR workload
Slow response times
Employee frustration
Inconsistent answers
Difficulty finding region-specific policies
Risk of employees relying on outdated documents
3. Product Vision
Create a trusted internal AI assistant that enables employees to get instant, accurate, source-backed answers from company-approved HR policies.
Vision
"Ask HR policies in natural language. Get trusted answers from the right document, for the right region, at the right time."
4. GoalsPrimary Goals
Reduce repetitive HR questions.
Provide instant answers to common policy questions.
Ground every answer in approved company documents.
Support region-specific policies.
Display the source behind every answer.
Prevent the AI from inventing policies.
Allow HR administrators to upload and manage documents.
Support document versioning.
Provide secure employee access.
Escalate questions that cannot be confidently answered.
Secondary Goals
Identify frequently asked HR questions.
Help HR discover documentation gaps.
Provide analytics on employee questions.
Improve employee self-service.
Reduce HR response time.
5. Non-Goals
The MVP will NOT:
Make HR decisions automatically.
Approve leave requests.
Modify employee payroll.
Provide legal advice.
Replace HR personnel.
Make policy changes automatically.
Access confidential employee records unless explicitly integrated later.
Answer questions using general internet knowledge when company policy is unavailable.
6. Target Users6.1 Employee
Employees use the system to find answers about:
Leave
Benefits
Insurance
Working hours
Remote work
Holidays
Parental policies
Payroll-related policies
Employee handbook rules
Employee needs
Fast answers
Simple explanations
Correct regional policy
Source references
Ability to ask follow-up questions
6.2 HR Administrator
HR administrators manage the knowledge base.
HR needs
Upload documents
Replace outdated policies
Manage document versions
Assign regions
Assign policy categories
Activate/deactivate documents
Monitor employee questions
Identify unanswered questions
Review feedback
7. Core User StoriesEmployeeUS-01 — Ask a Policy Question
As an employee, I want to ask a question in natural language so that I can quickly understand company policies.
Example:
"How many paid leaves can I take every year?"
US-02 — Region-Specific Answer
As an employee, I want answers based on my region so that I don't receive policies applicable to another country.
Example:
Employee Region: India
Question:
"What is the maternity leave policy?"
The system should retrieve the India-specific policy rather than a US policy.
US-03 — Source Verification
As an employee, I want to see where the answer came from so that I can verify the information.
US-04 — Follow-Up Questions
As an employee, I want to ask follow-up questions without repeating the context.
Example:
Employee: How many annual leaves do I get?
AI: You receive 24 annual leaves.
Employee: Can I carry them forward?
The system should understand that "them" refers to annual leaves.
US-05 — Unanswered Question
As an employee, I want the assistant to tell me when the available policies do not contain an answer rather than receiving an invented answer.
US-06 — HR Escalation
As an employee, I want to escalate unanswered questions to HR.
8. HR User StoriesUS-07 — Upload Document
HR can upload:
PDF
DOCX
TXT
US-08 — Categorize Document
HR can assign:
Region
Policy category
Effective date
Expiration date
Employee type
US-09 — Version Policy
HR can upload a new version of an existing policy.
Example:
Leave Policy
v1.0 → 2025
v2.0 → 2026
v3.0 → 2027
Only the currently active version should normally be retrieved.
US-10 — Disable Outdated Policy
HR can deactivate outdated documents.
US-11 — View Analytics
HR can see:
Most asked questions
Unanswered questions
Low-confidence questions
Most searched policies
User feedback
9. Functional RequirementsFR-01 Authentication
The system must support secure authentication.
MVP options:
Email/password
Google OAuth
Organization SSO-ready architecture
User roles:
EMPLOYEE
HR_ADMIN
SUPER_ADMIN
10. Employee Profile
Each employee profile should contain:
employee_id
name
email
role
region
country
department
employment_type
Example:
{
  "region": "India",
  "country": "India",
  "employment_type": "Full-Time"
}
The employee's region should automatically influence retrieval.
11. Document Management
HR administrators can upload documents.
Supported formatsPDF
DOCX
TXT
Future:
XLSX
PPTX
HTML
Document metadatadocument_id
title
category
region
employee_type
version
effective_date
expiration_date
status
uploaded_by
created_at
updated_at
Example:
{
  "title": "India Leave Policy",
  "category": "Leave",
  "region": "India",
  "version": "2026.1",
  "effective_date": "2026-01-01",
  "status": "active"
}
12. Document Processing Pipeline
When HR uploads a document:
Upload
   ↓
File Validation
   ↓
Text Extraction
   ↓
Cleaning
   ↓
Chunking
   ↓
Metadata Assignment
   ↓
Embedding Generation
   ↓
Vector Database
   ↓
Index Ready
The system should reject unsupported or corrupted files.
13. Chunking
Documents should be divided into meaningful chunks rather than arbitrary large blocks.
Each chunk should retain metadata:
document_id
document_title
region
category
version
page_number
section
effective_date
Example:
{
  "text": "Employees are entitled to 24 days...",
  "document": "India Leave Policy",
  "region": "India",
  "page": 8,
  "section": "4.2 Annual Leave"
}
14. Retrieval System
The assistant must use Retrieval-Augmented Generation.
Retrieval pipelineUser Question
      ↓
Query Processing
      ↓
Metadata Filtering
      ↓
Semantic Search
      ↓
Top-K Chunks
      ↓
Re-ranking
      ↓
LLM
      ↓
Grounded Answer
The system should prioritize:
Region
Employee type
Active policy version
Policy category
Semantic relevance
15. Vector Database
Recommended MVP:
Qdrant
Alternative:
ChromaDB
Vector records should contain:
embedding
chunk_text
document_id
region
category
version
page
section
status
16. RAG Answer Generation
The LLM must receive:
System Instructions
+
Employee Context
+
User Question
+
Retrieved Policy Chunks
The model must follow strict grounding rules.
Core instruction
Answer only using the provided company policy context. If the available context does not contain enough information to answer the question, explicitly state that the policy information could not be found. Do not invent rules, benefits, dates, eligibility requirements, or numbers.
17. Source Citations
Every answer should provide source information.
Example:
Answer:

Employees in India are eligible for 24 annual paid leaves per
calendar year.

Sources:
India Employee Handbook
Section 4.2 — Annual Leave
Page 8
Policy Version: 2026.1
The source should be clickable where possible.
18. Confidence System
The system should estimate answer confidence based on:
Retrieval similarity
Number of supporting chunks
Source consistency
Policy version validity
Retrieval ranking
Example:
High Confidence
Medium Confidence
Low Confidence
For low-confidence answers:
"I found related information, but I could not confidently
verify the answer from the current HR policies."
19. Hallucination Prevention
The system must NOT:
Invent policy numbers
Invent leave allowances
Guess eligibility
Mix policies from different regions
Use expired policies
Use inactive documents
Present general internet information as company policy
If no reliable information exists:
"I couldn't find this information in the available HR policies.
Please contact HR for clarification."
20. Region-Aware Retrieval
The system must prevent cross-region policy leakage.
Example:
Employee Region: India

Query:
"What is the parental leave policy?"
Retrieval priority:
India + Active + Parental Leave
        ↓
India + Active + Employee Handbook
        ↓
Global Policy
US-only policies should not be returned unless explicitly permitted.
21. Conversation Management
The assistant should maintain conversation context.
Example:
User:
How many sick leaves do I get?

AI:
You receive 12 sick leaves per year.

User:
Can I carry them forward?

AI:
According to the same policy, unused sick leave...
The system should maintain relevant context while preventing unrelated previous conversations from influencing answers.
22. HR Escalation
If the AI cannot answer confidently, the employee can select:
Ask HR
The system creates an HR ticket containing:
employee
question
conversation_context
retrieved_sources
confidence
timestamp
HR can respond through the admin dashboard.
23. Feedback System
After every answer:
Was this answer helpful?

[ Yes ] [ No ]
Optional feedback:
Incorrect information
Outdated policy
Not relevant
Missing information
Other
Feedback should be stored for analytics and future evaluation.
24. Admin Dashboard
The HR dashboard should include:
OverviewTotal Questions
Answered Questions
Escalated Questions
Low Confidence Questions
Documents
Active Policies
AnalyticsMost Asked Questions
Most Viewed Policies
Unanswered Questions
Negative Feedback
Questions by Region
Questions by Category
25. Suggested Dashboard------------------------------------------------
PolicyPilot AI
------------------------------------------------

Total Questions       1,284
Resolved by AI          91%
Escalated               9%
Active Documents         84

------------------------------------------------

Most Asked Topics

Leave                 █████████████
Benefits              █████████
Insurance             ███████
Remote Work           █████
Payroll               ████

------------------------------------------------

Questions Requiring HR Attention

1. Dental insurance eligibility
2. International relocation benefits
3. Carry-forward exception policy
------------------------------------------------
26. Employee Interface
The employee interface should contain:
HeaderPolicyPilot AI                         Profile
Main areaHow can I help you with HR policies?

[ Ask about leave, benefits, insurance... ]

Suggested Questions

- How many annual leaves do I get?
- What is the WFH policy?
- Does insurance cover dependents?
- What is the maternity leave policy?
AnswerYou are entitled to 24 annual paid leaves.

Source
India Leave Policy
Section 4.2
Page 8

Confidence: High

Was this helpful?
[Yes] [No]
27. Technology StackFrontendReact
TypeScript
Vite
Tailwind CSS
Optional:
shadcn/ui
BackendPython
FastAPI
Pydantic
SQLAlchemy / SQLModel
AILLM
Embeddings
RAG
Prompt Engineering
The LLM provider should be configurable so the application is not tightly coupled to a single provider.
Vector DatabaseQdrant
Relational DatabasePostgreSQL
Used for:
Users
Roles
Documents
Document metadata
Conversations
Feedback
HR tickets
Cache / Queue
Optional:
Redis
Celery / Background Tasks
Useful for document processing.
28. High-Level Architecture                     Employee
                         |
                         ▼
                 React Frontend
                         |
                         ▼
                   FastAPI API
                         |
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
      Authentication            Query Service
                                      |
                                      ▼
                              Metadata Filtering
                                      |
                                      ▼
                               Qdrant Search
                                      |
                                      ▼
                                Re-ranking
                                      |
                                      ▼
                                  LLM
                                      |
                                      ▼
                              Answer + Sources
                                      |
                                      ▼
                              React Interface


HR Admin
    |
    ▼
Document Upload
    |
    ▼
Processing Pipeline
    |
    ├── Text Extraction
    ├── Chunking
    ├── Metadata
    └── Embeddings
            |
            ▼
         Qdrant
29. Database Schemausersid
name
email
password_hash
role
region
country
department
employment_type
created_at
documentsid
title
category
region
employee_type
version
effective_date
expiration_date
status
uploaded_by
created_at
updated_at
document_chunksid
document_id
chunk_text
page_number
section
embedding_id
metadata
conversationsid
user_id
created_at
updated_at
messagesid
conversation_id
role
content
confidence
created_at
citationsid
message_id
document_id
chunk_id
page_number
section
similarity_score
feedbackid
message_id
user_id
rating
reason
comment
created_at
hr_ticketsid
user_id
question
conversation_id
status
priority
assigned_to
created_at
resolved_at
30. API RequirementsAuthenticationPOST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET /api/auth/me
ChatPOST /api/chat
GET /api/conversations
GET /api/conversations/{id}
DELETE /api/conversations/{id}
DocumentsPOST /api/admin/documents
GET /api/admin/documents
GET /api/admin/documents/{id}
PUT /api/admin/documents/{id}
DELETE /api/admin/documents/{id}
POST /api/admin/documents/{id}/activate
POST /api/admin/documents/{id}/deactivate
FeedbackPOST /api/feedback
HR TicketsPOST /api/tickets
GET /api/admin/tickets
PUT /api/admin/tickets/{id}
AnalyticsGET /api/admin/analytics/overview
GET /api/admin/analytics/questions
GET /api/admin/analytics/topics
GET /api/admin/analytics/feedback
31. Chat API ExampleRequest{
  "conversation_id": "conv_123",
  "question": "Can I carry forward unused annual leave?"
}
Response{
  "answer": "According to the India Leave Policy, unused annual leave can be carried forward subject to the stated annual limit.",
  "confidence": "high",
  "sources": [
    {
      "document": "India Leave Policy",
      "version": "2026.1",
      "section": "4.3",
      "page": 9
    }
  ],
  "requires_hr": false
}
32. Security Requirements
The system must implement:
Secure authentication
Password hashing
JWT/session security
Role-based access control
API authorization
File upload validation
File size limits
Input validation
Rate limiting
Secure document storage
Audit logging
Critical requirement
Employees must not be able to access documents or policies they are not authorized to view.
33. Privacy Requirements
The system should minimize storage of personal employee information.
Chat data should have configurable retention.
Sensitive information should not be unnecessarily included in LLM prompts.
The application should support:
Data deletion
Conversation deletion
Admin audit logs
Configurable retention
34. Performance Requirements
Target MVP performance:

Metric
Target
API response
< 500 ms excluding LLM
Retrieval
< 500 ms
RAG answer
< 5–8 sec
Document processing
Background
Search top-K
5–10 chunks
Availability
99%+ for production
Concurrent users
100+ MVP target35. Evaluation Metrics
The AI system should be evaluated independently from the UI.
Retrieval MetricsRecall@K
Precision@K
MRR
Answer MetricsFaithfulness
Answer Relevance
Context Relevance
Citation Accuracy
Product MetricsAI Resolution Rate
HR Escalation Rate
User Satisfaction
Average Response Time
Negative Feedback Rate
36. Target MVP Metrics
Initial targets:
≥ 90% citation accuracy
≥ 90% grounded-answer rate
≥ 85% retrieval recall@5
≥ 80% questions resolved without HR
< 10% hallucination rate
< 8 sec average answer generation
These should be measured using a curated evaluation dataset rather than claimed without testing.
37. AI Evaluation Dataset
Create a test dataset containing:
Question
Expected Answer
Expected Document
Expected Section
Region
Difficulty
Example:
{
  "question": "How many annual leaves are available in India?",
  "expected_document": "India Leave Policy",
  "expected_section": "Annual Leave",
  "region": "India"
}
Include difficult questions such as:
Ambiguous questions
Cross-region questions
Outdated policy questions
Questions with no answer
Multi-part questions
Follow-up questions
38. Edge CasesCase 1 — No relevant document
Response:
I couldn't find this information in the current HR policy documents. You can contact HR for clarification.
Case 2 — Conflicting policies
The system should prioritize the active policy version and flag conflicts for HR review.
Case 3 — Expired policy
Expired documents must not normally be retrieved.
Case 4 — Different regional policies
The system must apply employee region filtering.
Case 5 — Question outside HR scope
Example:
"Who will win the World Cup?"
Response:
I'm designed to help with company HR policies and benefits.
39. MVP ScopeMust Have
Authentication
Employee profile
Region selection
Document upload
PDF/DOCX processing
Document chunking
Embeddings
Qdrant
RAG chatbot
Source citations
Conversation history
HR admin dashboard
Document versioning
Feedback
HR escalation
Basic analytics
Should Have
Confidence scoring
Re-ranking
Advanced analytics
Document comparison
Policy expiration warnings
Could Have
Slack/Teams integration
Voice assistant
Multilingual support
SSO
Email escalation
HRIS integration
Won't Have in MVP
Automated leave approval
Payroll modification
Legal decision-making
Automated policy generation
40. Example End-to-End FlowStep 1
HR uploads:
India Leave Policy.pdf
Step 2
System extracts the text.
Step 3
The document is split into chunks.
Step 4
Chunks receive embeddings.
Step 5
Embeddings are stored in Qdrant.
Step 6
Employee asks:
"How many casual leaves do I get?"
Step 7
System identifies:
Region = India
Category = Leave
Step 8
Qdrant retrieves relevant chunks.
Step 9
LLM generates a grounded response.
Step 10
Employee receives:
You are eligible for X casual leaves per year
according to the current India Leave Policy.

Source:
India Leave Policy
Section 3.1
Page 6

Confidence: High
41. Future RoadmapPhase 1 — MVPAuthentication
Document Upload
RAG
Chat
Citations
Region Filtering
Admin Dashboard
Phase 2 — EnterpriseSSO
Slack
Microsoft Teams
Advanced RBAC
HRIS integration
Audit logs
Advanced analytics
Phase 3 — Intelligent HR PlatformPolicy change detection
Automatic policy comparison
Employee-specific policy recommendations
Multilingual HR assistant
Voice interface
Proactive policy notifications
42. Success Criteria
PolicyPilot AI will be considered successful when:
Employees can ask HR policy questions in natural language.
The system retrieves the correct region-specific policy.
Answers are grounded in approved documents.
Answers include verifiable citations.
Outdated policies are not accidentally prioritized.
The system refuses to hallucinate when information is unavailable.
HR can upload and manage policies without developer intervention.
HR can identify frequently asked and unanswered questions.
Employees can escalate unresolved questions.
The system demonstrates measurable improvement on a dedicated RAG evaluation dataset.
43. Product Differentiator
PolicyPilot AI is not simply an HR chatbot.
Its core differentiator is:
        Employee Context
              +
        Region Awareness
              +
        Policy Versioning
              +
        RAG Retrieval
              +
        Source Citations
              +
        Hallucination Guardrails
              +
        HR Escalation
              =
       Trusted HR AI Assistant
The product is designed around trust and traceability, which are more important for HR policy questions than simply generating fluent answers.
44. Final Product Definition
PolicyPilot AI is a secure, region-aware, RAG-powered HR assistant that transforms static HR documentation into an interactive employee self-service system.
Employees get immediate answers.
HR reduces repetitive workload.
Administrators maintain a single source of truth.
Every answer can be traced back to an approved policy.