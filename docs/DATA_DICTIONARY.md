# LeaveHRAlone Data Dictionary & Metadata Schema

This document provides a comprehensive reference of all data models, metadata schemas, vector payload structures, and API data types utilized within **LeaveHRAlone (PolicyPilot AI)**.

---

## 1. User & Profile Data Schema (`users`)

| Field Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUID` | Primary Key | Unique user identifier |
| `name` | `String` | Required | Full user name |
| `email` | `String` | Unique, Required | Organizational email address |
| `password_hash` | `String` | Required | Argon2 / bcrypt hashed password |
| `role` | `Enum` | `EMPLOYEE`, `HR_ADMIN`, `SUPER_ADMIN` | User access control role |
| `region` | `String` | Required | Country/office region (e.g., `India`, `US`, `UK`) |
| `country` | `String` | Required | Country code/name for policy matching |
| `department` | `String` | Optional | Organizational department (e.g., `Engineering`, `Sales`) |
| `employment_type` | `String` | Required | Employment category (e.g., `Full-Time`, `Contractor`) |
| `created_at` | `Timestamp` | Default `NOW()` | Record creation timestamp |

---

## 2. Document Metadata Schema (`documents`)

| Field Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUID` | Primary Key | Unique document identifier |
| `title` | `String` | Required | Display title of the HR document |
| `category` | `String` | Required | Policy category (e.g., `Leave`, `Benefits`, `Insurance`, `Remote Work`) |
| `region` | `String` | Required | Target region tag for policy isolation (e.g., `India`, `Global`) |
| `employee_type` | `String` | Default `All` | Applicable employee type constraint |
| `version` | `String` | Required | Version tag (e.g., `2026.1`, `v2.0`) |
| `effective_date` | `Date` | Required | Policy start date |
| `expiration_date` | `Date` | Optional | Policy expiration date |
| `status` | `Enum` | `active`, `inactive`, `archived` | Operational status of the document |
| `uploaded_by` | `UUID` | Foreign Key (`users.id`) | HR administrator who uploaded the file |
| `created_at` | `Timestamp` | Default `NOW()` | Upload timestamp |
| `updated_at` | `Timestamp` | Auto-update | Last modification timestamp |

---

## 3. Vector Payload & Document Chunks Schema (`document_chunks`)

| Payload Key | Type | Description |
| --- | --- | --- |
| `chunk_id` | `UUID` | Unique identifier for vector record |
| `document_id` | `UUID` | Parent document reference ID |
| `document_title` | `String` | Title of parent document for instant citation |
| `chunk_text` | `Text` | Extracted textual content slice |
| `region` | `String` | Region tag for vector filtering |
| `category` | `String` | Category tag for metadata filtering |
| `version` | `String` | Version tag of active document |
| `page_number` | `Integer` | Page number in original document |
| `section` | `String` | Section header or heading hierarchy |
| `effective_date` | `String` | ISO date string for temporal filtering |

---

## 4. Conversation & Message Schema (`conversations` & `messages`)

### `conversations`
| Field Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUID` | Primary Key | Conversation session ID |
| `user_id` | `UUID` | Foreign Key (`users.id`) | Owner employee ID |
| `created_at` | `Timestamp` | Default `NOW()` | Conversation start time |
| `updated_at` | `Timestamp` | Auto-update | Last activity timestamp |

### `messages`
| Field Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUID` | Primary Key | Message ID |
| `conversation_id` | `UUID` | Foreign Key | Parent conversation ID |
| `role` | `Enum` | `user`, `assistant`, `system` | Speaker role |
| `content` | `Text` | Required | Text payload |
| `confidence` | `Enum` | `high`, `medium`, `low`, `none` | AI confidence rating |
| `created_at` | `Timestamp` | Default `NOW()` | Message creation time |

---

## 5. HR Ticket Schema (`hr_tickets`)

| Field Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | `UUID` | Primary Key | Ticket reference ID |
| `user_id` | `UUID` | Foreign Key (`users.id`) | Employee submitting the ticket |
| `question` | `Text` | Required | Original employee query |
| `conversation_id` | `UUID` | Foreign Key | Context conversation thread |
| `status` | `Enum` | `open`, `in_progress`, `resolved`, `closed` | Ticket workflow state |
| `priority` | `Enum` | `low`, `medium`, `high` | Resolution priority |
| `assigned_to` | `UUID` | Foreign Key (`users.id`) | HR admin assigned to ticket |
| `created_at` | `Timestamp` | Default `NOW()` | Ticket creation timestamp |
| `resolved_at` | `Timestamp` | Optional | Ticket resolution timestamp |
