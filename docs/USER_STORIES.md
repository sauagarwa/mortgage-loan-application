# MortgageAI: User Stories & Workflows

**Version:** 1.0
**Date:** 2026-02-13

---

## 1. Personas

### 1.1 Maria - First-Time Homebuyer (Applicant)
- **Age:** 28, Software Engineer
- **Credit:** 720 (limited history, 3 years)
- **Situation:** Stable job for 3 years, good savings, first mortgage
- **Needs:** Simple application process, clear guidance on requirements

### 1.2 Raj - Non-Citizen Applicant
- **Age:** 34, Data Scientist on H-1B visa
- **Credit:** No US credit history (arrived 2 years ago)
- **Situation:** High income ($140K), has ITIN, strong savings, employer-sponsored
- **Needs:** Fair evaluation beyond credit score, clear eligibility guidance

### 1.3 Sarah - Credit Rebuilder (Applicant)
- **Age:** 42, Nurse
- **Credit:** 620 (was 480 after medical debt, improving steadily)
- **Situation:** Had medical emergency 4 years ago, now fully recovered, 2 years of perfect payments
- **Needs:** Recognition of her credit trajectory, not just current score

### 1.4 David - Loan Servicer (Underwriter)
- **Age:** 35, 8 years experience in mortgage underwriting
- **Situation:** Reviews 15-20 applications daily, needs efficiency tools
- **Needs:** Quick risk summaries, detailed drill-down capability, override workflow

### 1.5 Admin - System Administrator
- **Role:** Manages system configuration, LLM providers, user accounts
- **Needs:** Health monitoring, audit logs, configuration management

---

## 2. Applicant User Stories

### Epic: Account Management

#### US-101: User Registration
**As** a prospective borrower,
**I want to** create an account on the platform,
**So that** I can start a mortgage application.

**Acceptance Criteria:**
- [ ] User can register via Keycloak (email/password)
- [ ] User can register via social login (Google, Microsoft)
- [ ] Upon first login, user is prompted to complete their profile (name, phone)
- [ ] User is assigned the `applicant` role by default
- [ ] Email verification is required before submitting applications

#### US-102: User Login
**As** a registered user,
**I want to** log in to my account,
**So that** I can access my applications and dashboard.

**Acceptance Criteria:**
- [ ] Login redirects to Keycloak login page
- [ ] After successful login, user is redirected back to the dashboard
- [ ] Session persists across browser tabs
- [ ] Token refresh happens transparently
- [ ] User can log out, which clears session and tokens

#### US-103: View Profile
**As** a logged-in user,
**I want to** view and update my profile information,
**So that** my contact details are current.

**Acceptance Criteria:**
- [ ] Profile page shows name, email, phone
- [ ] User can update first name, last name, phone
- [ ] Email changes require re-verification
- [ ] Changes are saved and confirmed

---

### Epic: Loan Discovery

#### US-201: Browse Loan Products
**As** an applicant,
**I want to** browse available mortgage loan products,
**So that** I can understand my options before applying.

**Acceptance Criteria:**
- [ ] Loan products page shows all active products in card format
- [ ] Each card shows: name, type, term, rate type, min down payment, key features
- [ ] Cards are filterable by type (Conventional, FHA, VA, USDA, Jumbo)
- [ ] Cards are sortable by term length or minimum down payment
- [ ] Clicking a card shows full product details

#### US-202: Eligibility Pre-Check
**As** an applicant,
**I want to** check my basic eligibility before starting a full application,
**So that** I don't waste time on a loan I won't qualify for.

**Acceptance Criteria:**
- [ ] Pre-check form asks: annual income, monthly debts, credit score range, down payment, property value, citizenship status
- [ ] Submit returns: eligible (yes/no), estimated rate range, estimated monthly payment, max loan amount
- [ ] Warnings are shown for borderline criteria
- [ ] Suggestions for improvement are provided
- [ ] Pre-check data can optionally pre-fill the full application
- [ ] Pre-check does NOT create an application record

---

### Epic: Application Process

#### US-301: Start Application
**As** an applicant,
**I want to** start a new mortgage application for a selected loan product,
**So that** I can begin the approval process.

**Acceptance Criteria:**
- [ ] From loan product page, "Apply Now" button creates a new draft application
- [ ] Application is linked to the selected loan product
- [ ] Application number is generated (format: MA-YYYY-NNNNN)
- [ ] User is redirected to the multi-step application form
- [ ] Draft applications are saved automatically

#### US-302: Fill Personal Information
**As** an applicant,
**I want to** enter my personal information,
**So that** the lender can identify me.

**Acceptance Criteria:**
- [ ] Step 1 of the application form
- [ ] Fields: full name, date of birth, SSN (last 4), email, phone, current address
- [ ] Citizenship status selection (citizen, permanent resident, visa holder, other)
- [ ] If visa holder: visa type selector, years in country
- [ ] All fields validate on blur and on submit
- [ ] Progress is auto-saved every 30 seconds and on step navigation

#### US-303: Fill Employment Information
**As** an applicant,
**I want to** enter my employment details,
**So that** my income can be assessed.

**Acceptance Criteria:**
- [ ] Step 2 of the application form
- [ ] Employment status: employed, self-employed, retired, unemployed
- [ ] If employed: employer name, job title, years at job, years in field, annual income
- [ ] Additional income fields (freelance, rental, investments)
- [ ] Self-employed section: business type, years in business
- [ ] Income fields accept currency format with validation

#### US-304: Fill Financial Information
**As** an applicant,
**I want to** enter my financial details,
**So that** my financial health can be assessed.

**Acceptance Criteria:**
- [ ] Step 3 of the application form
- [ ] Self-reported credit score (or "I don't know" option)
- [ ] Has credit history (yes/no) - if no, alternative data section appears
- [ ] Monthly debts breakdown: car loan, student loans, credit cards, other
- [ ] Assets: checking, savings, retirement, investments
- [ ] History questions: bankruptcy (yes/no/when), foreclosure (yes/no/when)
- [ ] Alternative data section: rent payment history, utility payments

#### US-305: Fill Property Information
**As** an applicant,
**I want to** enter the property details,
**So that** the property can be assessed as collateral.

**Acceptance Criteria:**
- [ ] Step 4 of the application form
- [ ] Property type: single family, condo, townhouse, multi-family
- [ ] Property use: primary residence, second home, investment
- [ ] Purchase price and down payment amount
- [ ] Property address
- [ ] Computed fields shown: loan amount, LTV ratio, estimated DTI

#### US-306: Declarations
**As** an applicant,
**I want to** complete required declarations,
**So that** I provide legally required disclosures.

**Acceptance Criteria:**
- [ ] Step 5 of the application form
- [ ] Yes/no questions: outstanding judgments, lawsuits, federal debt, alimony, co-signer obligations
- [ ] Primary residence confirmation
- [ ] US citizen confirmation
- [ ] Each declaration has a brief explanation of what it means

#### US-307: Review and Submit
**As** an applicant,
**I want to** review my complete application before submitting,
**So that** I can verify all information is correct.

**Acceptance Criteria:**
- [ ] Step 6 (final step) shows all entered information in read-only summary
- [ ] Each section has an "Edit" link back to that step
- [ ] Required documents checklist shows which docs are uploaded and which are missing
- [ ] Consent checkbox for credit check authorization
- [ ] Submit button is disabled until all required fields and documents are present
- [ ] Confirmation dialog before final submission
- [ ] After submission, status changes to "submitted" and AI processing begins

---

### Epic: Document Upload

#### US-401: Upload Documents
**As** an applicant,
**I want to** upload my supporting documents,
**So that** my application can be verified.

**Acceptance Criteria:**
- [ ] Document upload section accessible from application form (step between financial and review)
- [ ] Shows required document types with status (not uploaded, uploaded, processing, processed)
- [ ] Drag-and-drop file upload or click to browse
- [ ] Accepts PDF, PNG, JPG (max 10MB per file)
- [ ] Multiple files per document type allowed
- [ ] Upload progress bar shown during upload
- [ ] File preview (thumbnail for images, icon for PDFs)
- [ ] Delete button for each uploaded document (only in draft status)

#### US-402: View Extracted Data
**As** an applicant,
**I want to** see what data was extracted from my documents,
**So that** I can verify the extraction is accurate.

**Acceptance Criteria:**
- [ ] After document processing completes, show extracted data summary
- [ ] Highlight any fields that had low extraction confidence
- [ ] Allow applicant to flag "incorrect" on any extracted field
- [ ] Show processing status: uploaded, processing, processed, failed

---

### Epic: Application Tracking

#### US-501: View My Applications
**As** an applicant,
**I want to** see all my mortgage applications,
**So that** I can track their status.

**Acceptance Criteria:**
- [ ] Dashboard shows list of all my applications
- [ ] Each application shows: number, loan type, amount, status, date
- [ ] Status badge with color coding (draft=gray, submitted=blue, under review=yellow, approved=green, denied=red)
- [ ] Click to view application details
- [ ] Draft applications show "Continue" button

#### US-502: View Application Status
**As** an applicant,
**I want to** see detailed status of my submitted application,
**So that** I know where it is in the process.

**Acceptance Criteria:**
- [ ] Progress tracker showing pipeline steps: Submitted → Documents Processing → AI Analysis → Under Review → Decision
- [ ] Current step is highlighted
- [ ] Real-time updates via WebSocket (agent progress messages)
- [ ] When AI analysis is running, show which agents are complete and which are in progress
- [ ] Estimated completion shown as agent count (e.g., "4 of 6 assessments complete")

#### US-503: View AI Decision
**As** an applicant,
**I want to** see the AI assessment of my application,
**So that** I understand how my application was evaluated.

**Acceptance Criteria:**
- [ ] Shows overall risk score with visual gauge (0-100)
- [ ] Risk band label (Low, Medium, High) with color
- [ ] AI recommendation text (approve, conditional, deny)
- [ ] Natural language summary written for non-experts
- [ ] List of positive highlights (strengths)
- [ ] List of areas of concern (with context)
- [ ] Note that final decision is pending loan servicer review

#### US-504: View Final Decision
**As** an applicant,
**I want to** see the final decision on my application,
**So that** I know whether my loan is approved.

**Acceptance Criteria:**
- [ ] Clear approved/denied/conditional status
- [ ] If approved: interest rate, loan amount, term, monthly payment
- [ ] If conditional: list of conditions to satisfy
- [ ] If denied: specific reasons (adverse action notice) and improvement suggestions
- [ ] Decision explanation in plain language
- [ ] Next steps guidance

#### US-505: Respond to Information Request
**As** an applicant,
**I want to** respond to requests for additional information,
**So that** my application can continue processing.

**Acceptance Criteria:**
- [ ] Notification when servicer requests additional info
- [ ] View requested items (documents, clarifications)
- [ ] Upload additional documents or provide text responses
- [ ] See due date for response
- [ ] Submit response, which notifies the servicer

---

## 3. Loan Servicer User Stories

### Epic: Application Review

#### US-601: View Application Queue
**As** a loan servicer,
**I want to** see all pending applications,
**So that** I can prioritize my review work.

**Acceptance Criteria:**
- [ ] Dashboard table showing all applications in "under_review" status
- [ ] Columns: app number, applicant name, loan type, amount, risk score, risk band, submitted date, assigned to
- [ ] Sortable by any column
- [ ] Filterable by: risk band, loan type, assigned servicer, date range
- [ ] Risk score shown with color-coded badge
- [ ] Unassigned applications highlighted
- [ ] Click row to open application review

#### US-602: View Dashboard Statistics
**As** a loan servicer,
**I want to** see summary statistics of my workload,
**So that** I can manage my time effectively.

**Acceptance Criteria:**
- [ ] Card showing: pending review count, in-progress count, decided today count
- [ ] Approval rate for current month
- [ ] Risk distribution chart (pie/donut) of pending applications
- [ ] Average processing time
- [ ] My assigned applications vs. unassigned pool

#### US-603: Review Application Details
**As** a loan servicer,
**I want to** review a complete application with AI assessment,
**So that** I can make an informed lending decision.

**Acceptance Criteria:**
- [ ] Full application data in organized sections (personal, employment, financial, property)
- [ ] Side-by-side view: application data on left, AI assessment on right
- [ ] AI risk score prominently displayed with recommendation
- [ ] Tab or accordion view for each risk dimension
- [ ] Each dimension shows: score, positive factors, risk factors, mitigating factors, explanation
- [ ] Document list with view/download links
- [ ] Extracted document data shown alongside stated application data (for comparison)

#### US-604: View Risk Dimension Detail
**As** a loan servicer,
**I want to** drill into any risk dimension,
**So that** I can understand the AI's reasoning.

**Acceptance Criteria:**
- [ ] Expandable section for each risk dimension
- [ ] Shows dimension score, weight, weighted contribution
- [ ] Lists all positive factors with supporting data
- [ ] Lists all risk factors with severity indicators
- [ ] Lists mitigating factors that offset risks
- [ ] Full natural language explanation from the agent
- [ ] Agent name and model used shown for transparency
- [ ] Radar chart showing all dimension scores at a glance

#### US-605: View Documents
**As** a loan servicer,
**I want to** review uploaded documents,
**So that** I can verify the applicant's claims.

**Acceptance Criteria:**
- [ ] Document list organized by type
- [ ] Click to open document in viewer (PDF viewer or image viewer)
- [ ] Extracted data panel alongside document viewer
- [ ] Extraction confidence indicator for each field
- [ ] Compare extracted data with stated application data (highlight discrepancies)

---

### Epic: Decision Making

#### US-701: Approve Application
**As** a loan servicer,
**I want to** approve a mortgage application,
**So that** the applicant can proceed with their loan.

**Acceptance Criteria:**
- [ ] "Approve" button on application review page
- [ ] Approval form with: interest rate, conditions (optional), notes
- [ ] If AI recommended approve: simple confirmation workflow
- [ ] If overriding AI (AI said deny): require justification text
- [ ] Confirmation dialog showing decision summary
- [ ] After approval: application status → approved, applicant notified

#### US-702: Deny Application
**As** a loan servicer,
**I want to** deny a mortgage application,
**So that** the applicant receives a proper adverse action notice.

**Acceptance Criteria:**
- [ ] "Deny" button on application review page
- [ ] Denial form with: adverse action reasons (required, select from list + custom), notes
- [ ] If overriding AI (AI said approve): require justification text
- [ ] System generates adverse action notice preview for review
- [ ] Confirmation dialog with regulatory compliance check
- [ ] After denial: application status → denied, applicant notified with reasons

#### US-703: Conditionally Approve Application
**As** a loan servicer,
**I want to** conditionally approve an application,
**So that** the applicant can satisfy remaining requirements.

**Acceptance Criteria:**
- [ ] "Approve with Conditions" button
- [ ] Form to specify conditions (add/remove condition items)
- [ ] Common conditions available as templates
- [ ] Notes field for additional context
- [ ] After conditional approval: applicant notified with condition list and timeline

#### US-704: Request Additional Information
**As** a loan servicer,
**I want to** request additional information from the applicant,
**So that** I can make a more informed decision.

**Acceptance Criteria:**
- [ ] "Request Info" button on application review page
- [ ] Form to specify: requested documents (type + description), clarification questions
- [ ] Set due date for response
- [ ] Application status → additional_info_requested
- [ ] Applicant notified with specific requests
- [ ] When applicant responds, servicer notified and status returns to under_review

#### US-705: Override AI Recommendation
**As** a loan servicer,
**I want to** override the AI recommendation with documented justification,
**So that** I can exercise professional judgment while maintaining an audit trail.

**Acceptance Criteria:**
- [ ] When making a decision that differs from AI recommendation, system flags the override
- [ ] Justification text is required (minimum 50 characters)
- [ ] Override is recorded in audit log with full context
- [ ] Override statistics tracked in analytics dashboard

---

## 4. Admin User Stories

### Epic: System Configuration

#### US-801: Configure LLM Providers
**As** an admin,
**I want to** configure LLM providers,
**So that** the AI agents can use the appropriate models.

**Acceptance Criteria:**
- [ ] Settings page showing all LLM providers (OpenAI, Anthropic, Local)
- [ ] For each provider: enable/disable toggle, base URL, API key (masked), default model, temperature, max tokens, rate limit
- [ ] Set one provider as default
- [ ] "Test Connection" button to verify provider is accessible
- [ ] Changes require confirmation
- [ ] Audit log entry for any configuration change

#### US-802: Manage Users
**As** an admin,
**I want to** manage user accounts and roles,
**So that** I can control access to the system.

**Acceptance Criteria:**
- [ ] User list with search and filter
- [ ] View user details (profile, role, last login, application count)
- [ ] Change user role (applicant, loan_servicer, admin)
- [ ] Deactivate/reactivate user accounts
- [ ] All changes logged in audit trail

#### US-803: View Audit Log
**As** an admin,
**I want to** view the system audit log,
**So that** I can monitor activity and investigate issues.

**Acceptance Criteria:**
- [ ] Searchable, filterable audit log table
- [ ] Filters: date range, user, action type, resource type
- [ ] Each entry shows: timestamp, user, action, resource, details, IP address
- [ ] Export to CSV functionality
- [ ] Audit log entries are immutable (no delete option)

#### US-804: View System Health
**As** an admin,
**I want to** monitor system health,
**So that** I can identify and resolve issues.

**Acceptance Criteria:**
- [ ] Dashboard showing health status of all components
- [ ] Components: API, Database, Redis, MinIO, Celery Workers, Keycloak, LLM Providers
- [ ] Each component: status (healthy/degraded/down), key metrics
- [ ] LLM provider metrics: latency, token usage, error rate
- [ ] Auto-refresh every 30 seconds

---

## 5. Workflow Diagrams

### 5.1 Complete Application Workflow

```
                    APPLICANT                         SYSTEM                          SERVICER
                        │                                │                                │
                   ┌────┴────┐                           │                                │
                   │Register │                           │                                │
                   │ & Login │                           │                                │
                   └────┬────┘                           │                                │
                        │                                │                                │
                   ┌────┴────┐                           │                                │
                   │ Browse  │                           │                                │
                   │  Loans  │                           │                                │
                   └────┬────┘                           │                                │
                        │                                │                                │
                   ┌────┴────┐                           │                                │
                   │  Pre-   │                           │                                │
                   │ Check   │                           │                                │
                   └────┬────┘                           │                                │
                        │                                │                                │
                   ┌────┴────┐                           │                                │
                   │  Fill   │                           │                                │
                   │  Form   │ (5 steps, auto-saved)     │                                │
                   └────┬────┘                           │                                │
                        │                                │                                │
                   ┌────┴────┐                           │                                │
                   │ Upload  │                           │                                │
                   │  Docs   │                           │                                │
                   └────┬────┘                           │                                │
                        │                                │                                │
                   ┌────┴────┐                      ┌────┴─────┐                          │
                   │ Review  │─────────────────────>│ Validate │                          │
                   │& Submit │                      │ & Queue  │                          │
                   └────┬────┘                      └────┬─────┘                          │
                        │                                │                                │
                        │                           ┌────┴─────┐                          │
                        │  ◄──── WebSocket ────────│  OCR &   │                          │
                        │       progress            │  Extract │                          │
                        │                           └────┬─────┘                          │
                        │                                │                                │
                        │                           ┌────┴─────┐                          │
                        │  ◄──── WebSocket ────────│ AI Agent │                          │
                        │       agent updates       │ Pipeline │                          │
                        │                           └────┬─────┘                          │
                        │                                │                                │
                        │                           ┌────┴─────┐                     ┌────┴────┐
                        │                           │ Results  │────────────────────>│ Review  │
                        │                           │ Ready    │                     │  Queue  │
                        │                           └──────────┘                     └────┬────┘
                        │                                                                 │
                        │                                                            ┌────┴────┐
                        │                                                            │ Review  │
                        │                                                            │ App +   │
                        │                                                            │ AI Risk │
                        │                                                            └────┬────┘
                        │                                                                 │
                        │                                                          ┌──────┴──────┐
                        │                                                          │             │
                        │                                                     ┌────┴────┐  ┌────┴────┐
                   ┌────┴────┐                                                │ Approve │  │  Deny  │
                   │ View    │◄───────────────────────────────────────────────│ / Cond  │  │        │
                   │Decision │                                                └─────────┘  └─────────┘
                   └─────────┘
```

### 5.2 Information Request Flow

```
     SERVICER                          SYSTEM                           APPLICANT
         │                                │                                │
    ┌────┴────┐                           │                                │
    │ Request │──────────────────────────>│                                │
    │  Info   │                      ┌────┴─────┐                          │
    └─────────┘                      │  Update  │                          │
                                     │  Status  │                          │
                                     └────┬─────┘                          │
                                          │                                │
                                     ┌────┴─────┐                     ┌────┴────┐
                                     │  Notify  │────────────────────>│  View   │
                                     │ Applicant│                     │ Request │
                                     └──────────┘                     └────┬────┘
                                                                           │
                                                                      ┌────┴────┐
                                                                      │ Upload  │
                                                                      │ Respond │
                                                                      └────┬────┘
         │                                │                                │
    ┌────┴────┐                      ┌────┴─────┐                          │
    │  View   │◄─────────────────────│  Notify  │◄─────────────────────────┘
    │Response │                      │ Servicer │
    └────┬────┘                      └──────────┘
         │
    ┌────┴────┐
    │ Continue│
    │ Review  │
    └─────────┘
```

---

## 6. Non-Functional Requirements

### 6.1 Performance
- Application form saves draft within 1 second
- Document upload starts immediately, progress visible
- AI risk assessment completes within 5 minutes
- Dashboard loads within 2 seconds
- Real-time WebSocket updates with < 500ms latency

### 6.2 Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation for all workflows
- Screen reader support for all interactive elements
- Sufficient color contrast (not relying on color alone)
- Focus management during multi-step forms

### 6.3 Responsiveness
- Desktop-first design (primary use case is desktop for servicers)
- Responsive layout for applicant flows (tablet and mobile)
- Minimum supported width: 320px (mobile)
- Touch-friendly targets on mobile

### 6.4 Data Validation
- Client-side validation on blur and submit (Zod schemas)
- Server-side validation on all API endpoints (Pydantic models)
- SSN last 4 digits: exactly 4 numeric digits
- Phone: valid US format
- Income/amounts: positive numbers, max 2 decimal places
- Date of birth: must be 18+ years old
- File uploads: type and size validation before upload
