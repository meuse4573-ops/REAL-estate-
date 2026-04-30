# Creator Sponsorship Agentic System Architecture

## Executive Summary

This document presents a comprehensive architecture for building an intelligent multi-agent backend that automates creator sponsorship deal management. The system replicates the functions of a professional creator finance team by processing incoming sponsor inquiries, evaluating opportunities, conducting brand research, drafting negotiation responses, and managing the entire deal lifecycle while maintaining human oversight at critical decision points. The architecture leverages LangGraph for orchestration, CrewAI for specialized agent roles, Mem0 for persistent memory, and multiple MCP tools for external integrations.

The system is designed to learn and adapt to each creator's preferences over time, building a sophisticated understanding of pricing expectations, brand fit criteria, communication preferences, and negotiation patterns. Every decision is logged for audit purposes, and no external communication is ever sent without explicit human approval. This architecture prioritizes accuracy, adaptability, and creator control while remaining cost-effective for startup deployment.

---

## 1. High-Level System Architecture

### 1.1 Architectural Overview

The system follows a modular, event-driven architecture where specialized agents communicate through a central orchestration layer. Each agent has a narrow, well-defined responsibility and accesses only the tools necessary for its function. This separation of concerns ensures that the system remains maintainable, testable, and adaptable as requirements evolve.

The architecture consists of four primary layers working in concert. The **Ingestion Layer** handles all incoming communications from email and direct messages, normalizing these inputs into a standardized format that downstream agents can process. The **Processing Layer** contains the ten specialized agents that perform classification, research, strategy, drafting, validation, and approval functions. The **Memory Layer** provides persistent storage for creator profiles, brand data, deal history, and learned preferences using a combination of PostgreSQL for structured data and Mem0 for semantic memory. The **Integration Layer** connects the system to external services including email providers, research tools, communication platforms, and monitoring systems.

The orchestration layer sits atop all other layers and manages workflow execution, state management, retry logic, and fallback paths. It uses LangGraph to define the directed acyclic graph of agent interactions, enabling complex branching logic, conditional routing, and loop-back capabilities when agents need to revisit earlier steps.

### 1.2 Design Principles

Several core principles guide the architecture and implementation decisions throughout the system. First, **human-in-the-loop** remains paramount: every external communication requires explicit approval before sending, and the system is designed to escalate uncertain cases rather than make autonomous decisions that could harm the creator's brand or business relationships. Second, **specialization over generalization**: each agent performs a narrow task exceptionally well rather than attempting to handle multiple responsibilities with diminishing effectiveness. Third, **structured memory over chat history**: all data persists in well-defined schemas that support querying, analytics, and machine learning rather than relying on conversational context that degrades over time. Fourth, **adaptive learning**: the system captures every interaction outcome and uses this data to refine future recommendations, recognizing patterns in successful deals and avoiding patterns that lead to rejections. Fifth, **observability**: comprehensive logging tracks every decision, reasoning step, and system action, enabling debugging, compliance auditing, and continuous improvement.

### 1.3 Technology Stack

The technology selections balance capability, cost, and deployment complexity for a startup environment. **LangGraph** serves as the orchestration backbone, providing state management, conditional routing, and retry mechanisms that would be extremely difficult to implement from scratch. **CrewAI** defines the multi-agent structure with role-based agents that can be independently configured, tested, and scaled. **PostgreSQL** through Supabase provides the primary database with vector search capabilities for semantic queries. **Mem0** adds the semantic memory layer that enables natural language queries against stored knowledge. **Tavily** and **Firecrawl** power the research capabilities with web search and content extraction. **Resend** or **Gmail MCP** handles email integration with proper authentication and tracking. **Slack MCP** enables notification workflows. **Puppeteer MCP** supports browser automation for testing and complex research tasks. **Sentry** provides application monitoring and error tracking.

---

## 2. Agent Map and Responsibilities

The system comprises ten specialized agents, each with a clear purpose, defined inputs and outputs, and restricted tool access. This section details each agent's role, decision-making criteria, and interaction patterns.

### 2.1 Message Intake Agent

The Message Intake Agent serves as the entry point for all external communications entering the system. Its sole responsibility is to normalize incoming data from diverse sources into a consistent, structured format that downstream agents can process reliably.

**Responsibilities**: The agent connects to email and DM sources through their respective MCP integrations, pulling new messages at configurable intervals. It identifies the communication source (email, Instagram DM, Twitter DM, LinkedIn message, or other platform), extracts the sender information including email address, social media handle, and any available profile data, and parses the message content to identify the apparent intent. The agent detects urgency indicators such as explicit deadlines, capitalized urgency language, or repeated follow-ups, and determines the current deal stage based on prior context or message indicators.

**Output Contract**: The agent produces a structured message object containing fields for message_id, source, sender_name, sender_email, sender_handle, subject (for email), raw_content, detected_intent, urgency_level, timestamp, thread_id (if available), and deal_stage. This object becomes the canonical representation of the incoming message throughout the system.

**Tool Access**: The agent requires read-only access to email and DM source integrations, with no ability to modify or send messages. It may access the memory system to check if the sender has previous interactions on record.

### 2.2 Opportunity Classification Agent

The Opportunity Classification Agent analyzes the normalized message to determine its nature and routes it appropriately. This agent prevents spam, irrelevant messages, and internal noise from consuming downstream processing resources while ensuring legitimate sponsorship opportunities receive proper attention.

**Responsibilities**: The agent examines message content to classify it into one of several categories. **Sponsorship opportunity** indicates a genuine brand or sponsor seeking collaboration. **Follow-up** indicates continuation of an existing negotiation. **Spam** indicates automated or low-quality mass outreach. **Internal noise** captures system messages, newsletters, or other non-actionable content. **Request for information** captures general inquiries that don't constitute formal opportunities. The agent assigns a confidence score between 0 and 1 reflecting its certainty in the classification and provides a brief rationale explaining its decision.

**Output Contract**: The agent produces a classification object with fields for classification (enum), confidence_score, rationale, routing_destination, and any flags requiring attention (such as potential brand safety concerns or suspicious patterns).

**Tool Access**: The agent operates on the message content and may query the memory system to check sender history and reputation. It does not access research tools or external data sources.

### 2.3 Brand Intelligence Agent

The Brand Intelligence Agent conducts deep research on sponsor brands to provide the factual foundation for negotiation decisions. This agent transforms unknown brands into understood entities with known characteristics, recent activity, and identified risks.

**Responsibilities**: When the classification agent routes a message as a sponsorship opportunity, the Brand Intelligence Agent activates to research the brand. It first identifies the brand name from the sender's company information, email domain, or message content. Using Tavily, it searches for recent news, press releases, and media coverage about the brand. Using Firecrawl, it extracts relevant content from the brand's website, social media profiles, and recent campaign pages. The agent compiles competitive intelligence by identifying the brand's competitors and market positioning. It assesses reputation by searching for customer reviews, controversies, legal issues, or public relations challenges. Finally, it produces a research brief summarizing findings with factual citations and explicit risk flags for any concerning discoveries.

**Output Contract**: The agent produces a research brief containing brand_name, domain, industry, company_size indicators, recent_news (with dates and sources), active_campaigns, competitors, reputation_summary, risk_flags (with severity levels), and research_timestamp. Each fact includes a citation to its source for verification.

**Tool Access**: The agent has access to Tavily search, Firecrawl content extraction, and may query the internal database for any previous research on the same brand. It does not access creator data or negotiation tools.

### 2.4 Creator Context Agent

The Creator Context Agent maintains and retrieves the creator-specific information needed for intelligent decision-making. This agent ensures that every negotiation reflects the creator's actual preferences, capabilities, history, and requirements.

**Responsibilities**: The agent maintains the creator profile including audience demographics, engagement metrics, content categories, pricing tiers, and brand alignment rules. It manages blocked categories listing industries or product types the creator will not engage with. It tracks past deal history including accepted deals, rejected deals, withdrawn opportunities, and the terms of each. It captures communication preferences including tone guidelines, response time expectations, and preferred communication channels. It identifies learned patterns from previous interactions including which types of deals succeed, which brands the creator prefers, and how the creator typically negotiates.

**Output Contract**: The agent produces a context object containing creator_profile with all relevant metrics and preferences, past_deals_summary with success patterns, blocked_categories, tone_guidelines, and any active_negotiations. When updating memory, it produces a memory_update confirmation with the changes made.

**Tool Access**: The agent has full read access to the creator's memory and profile data, with write access to update preferences and deal history based on outcomes. It does not access brand research or external tools.

### 2.5 Negotiation Strategy Agent

The Negotiation Strategy Agent synthesizes brand research and creator context to design an optimal negotiation approach. This agent determines the tactical position for each deal, accounting for market conditions, brand circumstances, and creator preferences.

**Responsibilities**: The agent analyzes the brand research brief to understand the brand's current situation, recent challenges, and likely negotiation flexibility. It examines creator context to identify hard constraints (minimum price, blocked categories), soft preferences (preferred deal types, ideal brand fits), and historical patterns (which negotiation approaches have succeeded). It determines an anchor price using the creator's standard rates adjusted for brand fit, urgency, and market conditions. It identifies counter-offer positions if initial terms are unacceptable. It establishes walk-away boundaries defining the minimum acceptable terms. It selects a negotiation style (aggressive, collaborative, conservative, or experimental) based on the brand's tone and the deal's quality. It anticipates likely brand responses and prepares fallback positions.

**Output Contract**: The agent produces a strategy object containing recommended_anchor_price, counter_offer_range, walk_away_terms, selected_negotiation_style, rationale, anticipated_responses with suggested replies, and confidence_level. This strategy guides the drafting agent's work.

**Tool Access**: The agent reads both brand research and creator context but produces output only. It does not access external tools or memory write capabilities.

### 2.6 Reply Drafting Agent

The Reply Drafting Agent transforms strategy into human communication that sounds natural, confident, and professional. This agent is the voice of the system and must avoid generic AI phrasing while maintaining the creator's authentic tone.

**Responsibilities**: The agent receives the negotiation strategy and brand context as inputs. It writes a response that matches the creator's established tone (formal, casual, professional, friendly) while projecting confidence and value. The response addresses the specific opportunity presented, references relevant brand context to demonstrate research and seriousness, proposes clear terms aligned with the negotiation strategy, includes appropriate next steps and call to action, and maintains flexibility for negotiation while avoiding premature commitment. The agent ensures the response does not include generic AI phrases ("I'm here to help," "I'd be happy to"), does not over-promise or make commitments beyond the strategy, and preserves the creator's control by framing suggestions as proposals requiring approval.

**Output Contract**: The agent produces a draft_response object containing subject_line (for email), body_content, tone_indicators_used, key_points_addressed, proposed_terms, suggested_next_steps, and internal_notes explaining any assumptions or flags for human review.

**Tool Access**: The agent reads brand research, creator context, and negotiation strategy. It has no external communication tools and produces output only.

### 2.7 Validation and Risk Agent

The Validation and Risk Agent acts as a quality control checkpoint, reviewing the drafted response against factual accuracy, brand safety, logical consistency, and quality standards. This agent prevents errors, hallucinations, or inappropriate content from reaching the human approval stage.

**Responsibilities**: The agent verifies that all factual claims in the draft match the brand research, flagging any invented or incorrect information. It confirms the draft respects creator constraints including blocked categories, minimum prices, and communication preferences. It checks for potentially harmful language, excessive commitments, or statements that could create legal exposure. It validates logical consistency between the strategy and the drafted response, ensuring the tone and content align. It assesses overall quality including clarity, professionalism, and likelihood of achieving the negotiation objectives.

**Output Contract**: The agent produces a validation_report object containing validation_passed (boolean), issues_found (array of issues with severity), recommendations, and overall_quality_score. If validation fails, the report includes specific revision_required guidance.

**Tool Access**: The agent reads brand research, creator context, negotiation strategy, and draft response. It does not access external tools or modify memory.

### 2.8 Approval Gate Agent

The Approval Gate Agent enforces the critical requirement that no external communication sends without explicit human approval. This agent manages the workflow between automated drafting and human decision-making.

**Responsibilities**: The agent packages the validated draft with relevant context for human review. It presents the opportunity details, brand research summary, proposed terms, and draft response in a clear format. It provides approval, edit, and rejection options to the human reviewer. It handles modifications if the human edits the draft, re-running validation on the edited version. It tracks approval state and timestamps for audit purposes. It escalates to human review if the validation agent flags high-risk issues or if confidence scores fall below thresholds.

**Output Contract**: The agent produces an approval_decision object containing decision (approved, rejected, needs_revision), approved_content (if approved), revision_notes (if needs_revision), reviewer_identity, timestamp, and any conditions attached to approval.

**Tool Access**: The agent has access to notification tools to alert humans of pending approvals and communication tools to send the approved message. It cannot send messages without explicit approval state.

### 2.9 Memory and CRM Agent

The Memory and CRM Agent maintains all persistent data about brands, deals, and creator preferences. This agent ensures the system remembers everything necessary for intelligent future decisions while maintaining data integrity and privacy.

**Responsibilities**: The agent writes new deal records when opportunities are classified, including all classification data, brand research, negotiation strategy, communications, and outcomes. It updates creator profiles based on deal outcomes, capturing what worked and what did not. It maintains brand profiles accumulating all interactions, research findings, and relationship history. It tracks follow-up schedules and triggers reminders when action is needed. It manages the semantic memory layer enabling natural language queries about past interactions. It enforces data retention policies and privacy requirements.

**Output Contract**: The agent produces memory_operation_results containing record_ids_created, records_updated, memory_search_results (if querying), and operation_status. All operations include audit metadata.

**Tool Access**: The agent has full read and write access to the database and Mem0 memory layer. It is the primary interface for all persistent storage operations.

### 2.10 Orchestrator Agent

The Orchestrator Agent controls the overall workflow, managing agent sequencing, state transitions, error handling, and adaptation. This agent ensures the system operates as a coherent whole rather than disconnected processing steps.

**Responsibilities**: The agent initializes new workflows when intake receives a message. It determines the next agent to execute based on current state and routing rules. It manages conditional branching where different paths apply based on classification, confidence, or other factors. It implements retry logic for failed agent executions with exponential backoff. It handles fallback paths when agents produce unexpected output or confidence is low. It manages loop-backs when additional research is needed or drafts require revision. It tracks complete workflow state including all inputs, outputs, and decisions. It supports workflow resumption if the system restarts mid-process. It triggers follow-up workflows based on scheduled events or external triggers.

**Output Contract**: The agent produces workflow_state updates containing current_agent, next_steps, state_data, and execution_metadata. It logs all decisions to the audit system.

**Tool Access**: The agent has access to workflow execution tools, state management, logging, and can invoke any other agent. It does not directly access external integrations or data.

---

## 3. Tool Map and Integrations

This section details all external tools and integrations required by the system, organized by function and mapped to the agents that utilize each.

### 3.1 Email Integration

The system supports email integration through either Resend MCP or Gmail MCP, providing bidirectional communication capabilities.

**Resend MCP**: Best suited for transactional email sending with high deliverability. The system uses Resend for sending approved sponsorship communications, tracking delivery status, and handling bounces. Integration requires API key configuration and domain setup for authenticated sending.

**Gmail MCP**: Best suited for scenarios requiring full Gmail access including reading incoming messages, managing labels, and sending through the user's Gmail account. The system uses Gmail for both ingestion (reading sponsor emails) and sending (sending replies through authenticated Gmail). Integration requires OAuth2 authentication with appropriate scopes.

**Agents Using Email**: Message Intake Agent reads email through either integration. Approval Gate Agent sends approved replies. Memory and CRM Agent may track email threads for context.

### 3.2 Research Tools

Research capabilities draw from two primary sources providing complementary coverage of web content.

**Tavily MCP Server**: Provides search functionality with relevance scoring and source diversity. The system uses Tavily for discovering recent news, finding brand mentions, identifying competitive landscape, and gathering factual information. Queries return structured results with URLs, titles, and content snippets ranked by relevance.

**Firecrawl MCP Server**: Provides web content extraction including full page content, metadata, and structured data from websites. The system uses Firecrawl for extracting brand website content, pulling campaign details, gathering product information, and retrieving social media profiles. Firecrawl handles JavaScript-rendered content and provides clean output suitable for analysis.

**Agents Using Research**: Brand Intelligence Agent uses both Tavily and Firecrawl for comprehensive research. Negotiation Strategy Agent may use light research for market context. Validation Agent may verify facts against research sources.

### 3.3 Memory and Database

Persistent storage combines structured database capabilities with semantic memory for flexible querying.

**PostgreSQL via Supabase**: Provides the primary structured database for all transactional data. Tables store creator profiles, brand records, deal records, communication logs, approval records, and audit trails. Supabase provides connection pooling, row-level security, and real-time capabilities. Vector similarity search through pgvector enables semantic queries on stored content.

**Mem0**: Provides the semantic memory layer enabling natural language queries against stored knowledge. Mem0 stores creator preferences, brand relationship summaries, interaction patterns, and learned insights. The system queries Mem0 to find "similar past deals" or "brands the creator previously declined" using natural language rather than structured filters.

**Graphiti** (optional alternative): An alternative semantic memory system that builds knowledge graphs from interactions. Graphiti excels at finding relationships between entities and tracking how knowledge evolves over time. Consider Graphiti if complex relationship mapping becomes important.

**Agents Using Memory**: Creator Context Agent reads creator profiles and preferences. Memory and CRM Agent reads and writes all persistent data. Brand Intelligence Agent may query previous brand research. Approval Gate Agent may query relevant past deals for context.

### 3.4 Communication and Notifications

Human stakeholders require notification capabilities for approval requests, escalations, and status updates.

**Slack MCP**: Provides Slack integration for sending notifications, creating channels, and managing workflow approvals. The system uses Slack to notify creators of pending approvals, alert managers of escalations, and provide daily summaries of deal activity.

**Agents Using Notifications**: Approval Gate Agent sends approval requests to creators. Orchestrator Agent sends escalations and alerts. Memory and CRM Agent may send follow-up reminders.

### 3.5 Browser Automation

Complex research and testing scenarios benefit from browser automation capabilities.

**Puppeteer MCP**: Provides headless browser control for web interaction. The system uses Puppeteer for complex research tasks requiring interaction (login-gated content, multi-page navigation), automated testing of the system's own workflows, and screenshot capture for human review of web content.

**Agents Using Browser Automation**: Brand Intelligence Agent uses Puppeteer for complex research requiring interaction. Validation Agent may use Puppeteer to verify links in drafts. Orchestrator may use Puppeteer for testing workflows.

### 3.6 Monitoring and Debugging

Production systems require comprehensive monitoring for reliability and troubleshooting.

**Sentry MCP**: Provides error tracking, performance monitoring, and debugging capabilities. The system uses Sentry to capture exceptions from all agents, track performance metrics for optimization, monitor workflow success rates, and debug failed executions.

**All agents** report errors and performance data through Sentry integration. The Orchestrator maintains detailed workflow traces that can be analyzed in Sentry when issues arise.

### 3.7 Additional MCP Integrations

Several additional integrations enhance specific capabilities.

**GitHub MCP**: Enables integration with GitHub for codebase management, issue tracking, and potentially deploying configuration changes. Useful for managing the system's own deployment and configuration as code.

**Discord MCP**: Alternative notification channel for creators who prefer Discord over Slack.

**Notion MCP**: Potential integration for documentation, content planning, or as an alternative memory store for creator preferences.

---

## 4. Memory Schema Design

The memory system combines relational storage for transactional data with semantic storage for natural language knowledge. This section details the complete schema.

### 4.1 Core Database Tables

The PostgreSQL database through Supabase maintains the following primary tables with comprehensive relationships.

**creators** table stores the core creator entity. Columns include id (UUID primary key), name, email, handle (social media), avatar_url, timezone, created_at, updated_at, and settings (JSONB for flexible configuration). Row-level security ensures each creator sees only their own data.

**creator_profiles** table stores detailed profile information. Columns include id (UUID primary key), creator_id (foreign key), audience_size, audience_demographics (JSONB), engagement_rate, content_categories (array), typical_response_time_hours, preferred_communication_channel, and metadata (JSONB). Each creator has exactly one profile record.

**creator_preferences** table stores learned and configured preferences. Columns include id, creator_id, blocked_categories (array), minimum_rate, preferred_brand_tones (array), negotiation_style_preference, auto_reject_patterns (array), and tone_guidelines (text). Preferences are updated over time based on deal outcomes.

**brands** table stores known brands. Columns include id, name, domain, industry, company_size, logo_url, last_researched_at, risk_score, and metadata (JSONB). Brands are deduplicated across all creators.

**deals** table stores the primary deal record. Columns include id, uuid (for external reference), creator_id, brand_id, source (email, dm, etc.), original_message_id, status (intake, researching, negotiating, approved, rejected, withdrawn, completed), urgency_level, confidence_score, created_at, updated_at, closed_at, and outcome. Status transitions are tracked in deal_status_history.

**deal_communications** table stores all communications related to a deal. Columns include id, deal_id, direction (inbound, outbound), channel, subject, body, approved, approved_by, approved_at, sent_at, and metadata. This table provides complete communication history.

**deal_research** table stores brand research results. Columns include id, deal_id, brand_id, research_data (JSONB), risk_flags (JSONB), sources (array), researched_at, and confidence_score. Enables caching research for future reference.

**deal_strategies** table stores negotiation strategies. Columns include id, deal_id, anchor_price, counter_offer_range, walk_away_terms, negotiation_style, rationale, anticipated_responses (JSONB), created_at, and is_active (boolean).

**deal_drafts** table stores drafted responses. Columns include id, deal_id, draft_content (JSONB), tone_indicators, key_points, validation_status, validation_issues (JSONB), quality_score, created_at, and is_approved.

**approval_records** table stores approval decisions. Columns include id, deal_id, draft_id, decision (approved, rejected, needs_revision), reviewer_type (creator, manager), reviewer_id, approved_content (if different from draft), revision_notes, decided_at, and conditions (JSONB).

**audit_logs** table provides complete decision audit trail. Columns include id, timestamp, agent_name, action_type, deal_id, input_summary (JSONB), output_summary (JSONB), decision_rationale, confidence_score, and metadata (JSONB). This table supports compliance requirements and debugging.

### 4.2 Semantic Memory Structure

Mem0 stores additional knowledge that benefits from natural language representation.

**Creator Knowledge**: Stores preferences in natural language including "Creator prefers to reject cosmetic brands due to past negative experiences," "Creator responds best to professional but friendly tone," "Creator typically accepts deals in the $5000-10000 range for YouTube integrations," and "Creator has declined three offers from gaming brands in the past year."

**Brand Relationship Knowledge**: Stores relationship history including "Brand X has completed two deals with this creator in the past, both successful," "Brand Y was rejected twice due to rate disagreements," "Brand Z had a controversial news story in 2024 that may affect creator reputation," and "Brand A typically negotiates aggressively on rate."

**Pattern Knowledge**: Stores learned patterns including "Deals with under 48-hour response time have 30% higher success rate," "Creator accepts counter-offers 40% of time when under 10% of asking," "Spring months see 50% more sponsorship activity," and "Instagram DMs have lower response rates than email for this creator."

### 4.3 Memory Update Patterns

The system updates memory through specific patterns that maintain data quality.

**On Classification**: The classification result is logged to audit_logs. If the sender is a new brand, a skeleton brand record is created.

**On Research Completion**: Full research is stored in deal_research with sources. Brand record is updated with fresh data. Any risk flags are recorded in brand.risk_score.

**On Deal Outcome**: The creator's preferences are updated based on what worked and did not work. If a pattern is identified (e.g., creator always declines gaming), it's recorded in semantic memory. Deal record status is updated.

**On Approval**: The approved communication is stored. Response time metrics are calculated and stored. Any human modifications to drafts are recorded for learning.

---

## 5. Workflow Diagram and Logic

The workflow represents a sophisticated pipeline with branching, loops, and fallback paths. This section describes the complete flow with state transitions.

### 5.1 Primary Workflow Path

The standard workflow proceeds through ten stages from message intake to follow-up scheduling.

**Stage 1: Intake**: The Orchestrator triggers Message Intake Agent to poll email and DM sources. New messages are normalized into structured format. The workflow advances to classification.

**Stage 2: Classification**: The Orchestrator routes the message to Opportunity Classification Agent. If classified as sponsorship opportunity with confidence above 0.7, the workflow advances to brand research. If confidence between 0.4 and 0.7, the workflow advances to creator context for additional routing guidance. If confidence below 0.4 or classified as spam, the message is archived with rationale and workflow completes.

**Stage 3: Creator Context Load**: The Orchestrator routes to Creator Context Agent to load relevant creator data. If creator profile exists and has sufficient context, proceed to brand research. If creator profile is incomplete, the Orchestrator may prompt for additional setup before continuing. If this is a new creator, initialize basic profile and continue.

**Stage 4: Brand Research**: The Orchestrator routes to Brand Intelligence Agent to research the sponsor. Research results are cached for future deals. The workflow advances to strategy.

**Stage 5: Strategy**: The Orchestrator routes to Negotiation Strategy Agent to design the approach. Strategy is validated for completeness. If strategy is incomplete (missing key data), loop back to brand research for additional information. If strategy is complete, advance to drafting.

**Stage 6: Drafting**: The Orchestrator routes to Reply Drafting Agent to write the response. Draft is produced and advanced to validation.

**Stage 7: Validation**: The Orchestrator routes to Validation and Risk Agent. If validation passes with quality score above threshold, advance to approval. If validation fails or quality score is low, loop back to drafting with specific revision requirements. If validation identifies high-risk issues, route to human review instead of standard approval.

**Stage 8: Approval**: The Orchestrator routes to Approval Gate Agent to present draft to human. Human reviews, edits if desired, and approves, rejects, or requests revision. If approved, advance to send and memory write. If rejected, archive deal and update preferences. If revision requested, loop back to drafting with revision notes.

**Stage 9: Send and Memory Write**: The Orchestrator routes to Approval Gate Agent to send the approved message through email integration. Simultaneously, Memory and CRM Agent writes all records including deal, communications, research, strategy, and audit logs. Update creator preferences based on this interaction. Schedule follow-up if appropriate.

**Stage 10: Follow-up Scheduling**: The Orchestrator calculates follow-up dates based on strategy and deal stage. Creates scheduled tasks for follow-up. If no follow-up needed, workflow completes.

### 5.2 Branching Logic

Several decision points create branching paths in the workflow.

**Classification Confidence Branch**: High confidence (above 0.7) triggers standard flow. Medium confidence (0.4-0.7) triggers enhanced review with additional context loading. Low confidence (below 0.4) triggers archival with human notification option.

**Validation Quality Branch**: High quality (above 0.8) triggers standard approval. Medium quality (0.5-0.8) triggers enhanced approval requiring explicit acceptance. Low quality (below 0.5) triggers draft revision before any approval.

**Risk Flag Branch**: No risk flags triggers standard flow. Minor risk flags trigger notification alongside approval. Major risk flags trigger immediate human escalation before any drafting.

**Brand Known Branch**: Known brand with good history triggers standard negotiation. Known brand with poor history triggers caution flag and potentially revised strategy. Unknown brand triggers full research.

### 5.3 Retry and Fallback Patterns

The system implements sophisticated error handling at multiple levels.

**Agent Retry**: If an agent fails (timeout, error, invalid output), the Orchestrator retries up to three times with exponential backoff. After three failures, the workflow enters error state and alerts humans.

**Research Fallback**: If Tavily search fails, fall back to Firecrawl direct search. If both fail, attempt cached research if available. If no research available, proceed with limited strategy and flag for human review.

**Validation Retry**: If validation fails, provide specific feedback to drafting agent. Allow up to two revision attempts. After two failures, route to human intervention.

**Approval Timeout**: If human does not respond within configured time (default 24 hours), send reminder. After configured number of reminders, escalate to backup contact or archive as abandoned.

### 5.4 Loop-Back Scenarios

The system supports intentional loops back to earlier stages when needed.

**Incomplete Research Loop**: Strategy agent determines research is insufficient. Loop back to brand research with specific questions to answer. Maximum two research iterations per deal.

**Draft Revision Loop**: Validation fails or human requests revision. Loop back to drafting with specific revision requirements. Maximum three drafting iterations.

**Strategy Revision Loop**: Validation or approval indicates strategy mismatch. Loop back to strategy with feedback. Maximum two strategy revisions.

---

## 6. Production Folder Structure

The codebase follows a modular structure that separates concerns while maintaining clear relationships between components.

```
creator-sponsorship-agent/
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore rules
├── README.md                    # Project documentation
├── pyproject.toml               # Python project configuration
├── uv.lock                      # Dependency lock file
├── docker-compose.yml           # Local development services
├── Dockerfile                   # Production container definition
├── .dockerignore                # Docker ignore rules
│
├── src/
│   ├── __init__.py              # Package initialization
│   │
│   ├── main.py                  # Application entry point
│   ├── config.py               # Configuration management
│   ├── constants.py            # Application constants
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── webhooks.py     # Webhook endpoints
│   │   │   ├── approvals.py    # Approval API
│   │   │   ├── deals.py        # Deal management API
│   │   │   └── health.py       # Health check endpoint
│   │   └── deps.py             # API dependencies
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py             # Base agent class
│   │   ├── factory.py          # Agent factory
│   │   ├── registry.py         # Agent registry
│   │   │
│   │   ├── intake/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Message Intake Agent
│   │   │   ├── config.py       # Agent configuration
│   │   │   └── prompts.py      # Agent prompts
│   │   │
│   │   ├── classifier/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Classification Agent
│   │   │   ├── config.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── researcher/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Brand Intelligence Agent
│   │   │   ├── config.py
│   │   │   ├── prompts.py
│   │   │   └── tools/          # Research tools
│   │   │
│   │   ├── context/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Creator Context Agent
│   │   │   ├── config.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── strategy/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Negotiation Strategy Agent
│   │   │   ├── config.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── drafter/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Reply Drafting Agent
│   │   │   ├── config.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── validator/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Validation Agent
│   │   │   ├── config.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── approver/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Approval Gate Agent
│   │   │   ├── config.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py        # Memory and CRM Agent
│   │   │   ├── config.py
│   │   │   └── tools/          # Memory tools
│   │   │
│   │   └── orchestrator/
│   │       ├── __init__.py
│   │       ├── agent.py        # Orchestrator Agent
│   │       ├── config.py
│   │       ├── state.py        # State management
│   │       ├── nodes.py        # Graph nodes
│   │       ├── edges.py        # Graph edges
│   │       └── workflow.py     # Workflow definitions
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py             # Base tool class
│   │   ├── registry.py         # Tool registry
│   │   │
│   │   ├── email/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Email base
│   │   │   ├── resend.py       # Resend integration
│   │   │   └── gmail.py        # Gmail integration
│   │   │
│   │   ├── research/
│   │   │   ├── __init__.py
│   │   │   ├── tavily.py       # Tavily integration
│   │   │   └── firecrawl.py    # Firecrawl integration
│   │   │
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   ├── supabase.py     # Supabase client
│   │   │   └── mem0.py        # Mem0 client
│   │   │
│   │   ├── notifications/
│   │   │   ├── __init__.py
│   │   │   ├── slack.py        # Slack integration
│   │   │   └── discord.py      # Discord integration
│   │   │
│   │   ├── browser/
│   │   │   ├── __init__.py
│   │   │   └── puppeteer.py    # Puppeteer integration
│   │   │
│   │   └── monitoring/
│   │       ├── __init__.py
│   │       └── sentry.py       # Sentry integration
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── schema.py           # Database schemas
│   │   ├── migrations/        # SQL migrations
│   │   │   └── 001_initial.sql
│   │   ├── queries.py         # Query functions
│   │   └── models.py          # Pydantic models
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── message.py         # Message models
│   │   ├── deal.py            # Deal models
│   │   ├── brand.py           # Brand models
│   │   ├── creator.py         # Creator models
│   │   ├── strategy.py         # Strategy models
│   │   └── audit.py            # Audit models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── webhook.py         # Webhook handling
│   │   ├── scheduler.py      # Background scheduling
│   │   └── polling.py        # Message polling
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Logging setup
│       ├── metrics.py         # Metrics collection
│       ├── errors.py          # Custom exceptions
│       └── helpers.py         # Utility functions
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Test configuration
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── test_intake.py
│   │   ├── test_classifier.py
│   │   ├── test_researcher.py
│   │   ├── test_context.py
│   │   ├── test_strategy.py
│   │   ├── test_drafter.py
│   │   ├── test_validator.py
│   │   ├── test_approver.py
│   │   └── test_memory.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── test_email.py
│   │   ├── test_research.py
│   │   └── test_memory.py
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_workflow.py
│   │   └── test_full_flow.py
│   │
│   └── fixtures/
│       ├── messages/          # Sample messages
│       ├── brands/            # Sample brand data
│       └── responses/         # Sample responses
│
├── scripts/
│   ├── __init__.py
│   ├── setup_db.py           # Database setup
│   ├── seed_test_data.py    # Test data seeding
│   ├── migrate.py            # Migration runner
│   └── deploy.py             # Deployment script
│
├── docs/
│   ├── architecture.md       # This document
│   ├── api.md                # API documentation
│   ├── agents.md             # Agent documentation
│   ├── tools.md              # Tool documentation
│   └── deployment.md         # Deployment guide
│
└── configs/
    ├── staging.yaml          # Staging config
    ├── production.yaml       # Production config
    └── development.yaml      # Development config
```

---

## 7. Implementation Order

The implementation follows a phased approach that delivers value incrementally while building toward the complete system. Each phase produces a working system that can be deployed and tested.

### Phase 1: Foundation and Infrastructure (Week 1-2)

The first phase establishes the core infrastructure without which nothing else functions. Tasks include setting up the project structure with all folders and base files, configuring PostgreSQL through Supabase with all schema tables, implementing the database client with connection pooling and row-level security, setting up logging with structured logging to both console and file, configuring Sentry for error tracking from day one, establishing environment configuration management, and creating the base agent class that all specialized agents inherit from.

**Deliverable**: A running API server with health checks, database connectivity, and error tracking. No agent functionality yet.

### Phase 2: Memory and Tools (Week 3-4)

The second phase builds the tools and memory layer that agents depend on. Tasks include implementing the memory agent with full database operations, implementing Mem0 client for semantic memory, implementing email integration with both Resend and Gmail options, implementing research tools with Tavily and Firecrawl wrappers, implementing notification tools with Slack integration, implementing browser automation tools with Puppeteer, and building the tool registry that agents use to access capabilities.

**Deliverable**: All tools are functional and testable independently. The memory system stores and retrieves data correctly.

### Phase 3: Core Agents (Week 5-7)

The third phase implements each specialized agent with its prompts and configuration. Tasks include implementing the Message Intake Agent with source polling, implementing the Opportunity Classification Agent with classification logic, implementing the Creator Context Agent with profile management, implementing the Brand Intelligence Agent with research capabilities, implementing the Negotiation Strategy Agent with strategy generation, implementing the Reply Drafting Agent with tone-aware writing, implementing the Validation Agent with quality checking, implementing the Approval Gate Agent with human review workflow, and implementing the Memory and CRM Agent with full persistence.

**Deliverable**: Each agent produces correct output for its defined contract. Agents can be tested in isolation.

### Phase 4: Orchestration and Workflow (Week 8-9)

The fourth phase builds the orchestration layer that coordinates agents. Tasks include implementing LangGraph workflow definition with all nodes and edges, implementing state management that persists across steps, implementing retry logic with exponential backoff, implementing fallback paths for research failures, implementing loop-back logic for revisions, implementing workflow execution engine with parallel and sequential steps, implementing webhook handlers for external triggers, and implementing the scheduler for automated polling.

**Deliverable**: The complete workflow executes end-to-end for standard cases. All branching and retry logic functions correctly.

### Phase 5: Testing and Refinement (Week 10-11)

The fifth phase focuses on quality assurance and edge cases. Tasks include writing unit tests for all agents, writing integration tests for agent interactions, writing end-to-end tests for complete workflows, conducting user acceptance testing with real scenarios, optimizing performance for agent execution times, implementing caching for research results, implementing rate limiting for external APIs, and conducting security review and penetration testing.

**Deliverable**: A fully tested system with documented test coverage. Production-ready code quality.

### Phase 6: Deployment and Monitoring (Week 12)

The final phase prepares for production deployment. Tasks include configuring production environment variables, setting up containerization with Docker, configuring continuous deployment pipelines, implementing monitoring dashboards, configuring alerting for failures, implementing backup and recovery procedures, documenting operational procedures, and conducting launch readiness review.

**Deliverable**: A production-deployable system with full monitoring and operational documentation.

---

## 8. Key Architectural Decisions

Several significant decisions shape the architecture and warrant explicit justification.

### 8.1 LangGraph over Custom Orchestration

LangGraph was selected over building custom orchestration because it provides state management, conditional routing, retry logic, and persistence as built-in features. Implementing these capabilities from scratch would require substantial development time and introduce bugs. LangGraph's integration with LangChain and CrewAI simplifies the multi-agent architecture while maintaining flexibility.

### 8.2 Mem0 over Pure Vector Storage

Mem0 was selected over pure vector storage because it provides semantic memory with entity tracking and relationship understanding out of the box. While vector databases can store embeddings, Mem0 provides the query interface needed to find "similar deals" or "brands the creator declined" without complex embedding management. For startup cost efficiency, Mem0 can be self-hosted.

### 8.3 PostgreSQL over NoSQL

PostgreSQL was selected for the primary database because sponsorship data is highly structured with clear relationships between creators, brands, deals, and communications. NoSQL databases would require additional complexity to maintain data integrity. Supabase provides PostgreSQL with additional capabilities including real-time subscriptions and vector search.

### 8.4 Human Approval Always Required

The architecture enforces human approval before any external send as a non-negotiable requirement. This design choice prioritizes creator control and brand safety over automation speed. The approval workflow includes editing capabilities so creators can modify drafts before sending.

### 8.5 Agent Specialization

Each agent has a narrow, well-defined responsibility rather than attempting to handle multiple tasks. This specialization enables easier testing, clearer accountability, and the ability to improve individual agents without affecting others. The orchestrator handles coordination rather than attempting to make agents general-purpose.

---

## 9. Future Considerations

As the system evolves, several enhancements may warrant consideration beyond the initial implementation.

Advanced learning capabilities could analyze deal outcomes to automatically adjust strategy recommendations, recognizing patterns in successful negotiations and avoiding unsuccessful approaches. Multi-creator support could extend the system to manage sponsorship for multiple creators with shared brand intelligence. Marketplace integration could enable the system to post available sponsorship slots to marketplaces, actively sourcing opportunities rather than only responding to inbound messages. Analytics dashboards could provide creators with insights into their sponsorship performance, deal flow metrics, and brand relationship health. Contract automation could integrate with e-signature platforms to automate contract execution once terms are agreed. Payment tracking could manage payment schedules, track invoices, and handle payment reminders.

These enhancements build on the foundation established by the core architecture without requiring fundamental changes to the system design.

---

## 10. Summary

This architecture provides a comprehensive blueprint for building an intelligent multi-agent system that automates creator sponsorship deal management. The system replicates the functions of a professional creator finance team through ten specialized agents, persistent memory, comprehensive tooling, and strict human oversight. The architecture prioritizes accuracy, adaptability, and creator control while remaining cost-effective for startup deployment.

The design enables the system to learn from each interaction, improving recommendations and strategies over time. The modular structure ensures maintainability and enables individual components to be upgraded without affecting the whole. The comprehensive logging and audit trails support compliance requirements and enable thorough debugging when issues arise.

This architecture is ready for implementation following the phased approach outlined in the implementation order.
