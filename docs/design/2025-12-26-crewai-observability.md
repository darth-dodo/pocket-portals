# CrewAI Observability Guide

> Comprehensive documentation of all observability options for CrewAI systems

**Created**: 2025-12-26
**Status**: Reference Documentation
**Applies to**: Pocket Portals CrewAI Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Built-in Options](#built-in-options)
   - [Event Listener System](#1-event-listener-system)
   - [Execution Hooks](#2-execution-hooks)
   - [Crew-Level Callbacks](#3-crew-level-callbacks)
   - [Verbose Mode & Logging](#4-verbose-mode--logging)
3. [External Integrations](#external-integrations)
   - [OpenTelemetry / OpenLIT](#5-opentelemetry--openlit)
   - [Langfuse](#6-langfuse)
   - [Arize Phoenix](#7-arize-phoenix)
   - [MLflow](#8-mlflow)
   - [Maxim](#9-maxim)
   - [Datadog](#10-datadog)
   - [Braintrust](#11-braintrust)
4. [Available Events Reference](#available-events-reference)
5. [Implementation Recommendations](#implementation-recommendations)

---

## Overview

CrewAI provides multiple layers of observability, from simple logging to enterprise-grade distributed tracing. Choose based on your needs:

| Need | Recommended Approach |
|------|---------------------|
| Quick debugging | Verbose mode + Crew logging |
| Development monitoring | Event Listeners + Execution Hooks |
| Production tracing | OpenTelemetry (OpenLIT/Langfuse) |
| ML experiment tracking | MLflow |
| Enterprise observability | Datadog / Arize Phoenix |

---

## Built-in Options

### 1. Event Listener System

**Best for**: Custom monitoring, debugging, analytics integration

The Event Listener system is CrewAI's primary observability mechanism. It uses an event bus pattern where you subscribe to specific events.

#### Basic Implementation

```python
# src/observability/listeners.py
from crewai.events import (
    BaseEventListener,
    CrewKickoffStartedEvent,
    CrewKickoffCompletedEvent,
    AgentExecutionCompletedEvent,
    TaskStartedEvent,
    TaskCompletedEvent,
    LLMCallStartedEvent,
    LLMCallCompletedEvent,
)
import logging
import time

logger = logging.getLogger("crewai.observability")

class CrewObservabilityListener(BaseEventListener):
    """Comprehensive crew execution monitoring."""

    def __init__(self):
        super().__init__()
        self.execution_times: dict[str, float] = {}
        self.agent_stats: dict[str, dict] = {}

    def setup_listeners(self, crewai_event_bus):
        # Crew lifecycle events
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_started(source, event):
            self.execution_times[event.crew_name] = time.time()
            logger.info(f"🚀 Crew '{event.crew_name}' started execution")

        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_crew_completed(source, event):
            start = self.execution_times.get(event.crew_name, time.time())
            duration = time.time() - start
            logger.info(f"✅ Crew '{event.crew_name}' completed in {duration:.2f}s")
            logger.debug(f"Output: {str(event.output)[:200]}...")

        # Agent execution events
        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_completed(source, event):
            role = event.agent.role
            if role not in self.agent_stats:
                self.agent_stats[role] = {'executions': 0, 'total_time': 0}
            self.agent_stats[role]['executions'] += 1
            logger.info(f"🤖 Agent '{role}' completed task")

        # Task events
        @crewai_event_bus.on(TaskStartedEvent)
        def on_task_started(source, event):
            logger.info(f"📋 Task started: {event.task.description[:50]}...")

        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event):
            logger.info(f"✅ Task completed: {event.task.description[:50]}...")

        # LLM call events
        @crewai_event_bus.on(LLMCallStartedEvent)
        def on_llm_started(source, event):
            logger.debug(f"🧠 LLM call initiated")

        @crewai_event_bus.on(LLMCallCompletedEvent)
        def on_llm_completed(source, event):
            logger.debug(f"🧠 LLM call completed")

    def get_stats(self) -> dict:
        """Return collected statistics."""
        return {
            'agent_stats': self.agent_stats,
            'execution_times': self.execution_times
        }

# IMPORTANT: Instantiate at module level for auto-registration
crew_listener = CrewObservabilityListener()
```

#### Memory Events Listener

```python
from crewai.events import (
    BaseEventListener,
    MemorySaveStartedEvent,
    MemorySaveCompletedEvent,
    MemoryQueryStartedEvent,
    MemoryQueryCompletedEvent,
    MemoryRetrievalCompletedEvent,
    MemorySaveFailedEvent,
    MemoryQueryFailedEvent,
)
import logging

logger = logging.getLogger("crewai.memory")

class MemoryObservabilityListener(BaseEventListener):
    """Monitor memory operations for performance and debugging."""

    def __init__(self):
        super().__init__()
        self.query_times: list[float] = []
        self.save_times: list[float] = []
        self.error_count: int = 0

    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(MemorySaveStartedEvent)
        def on_save_started(source, event):
            agent = event.agent_role or "Unknown"
            logger.debug(f"💾 Memory save started by '{agent}'")

        @crewai_event_bus.on(MemorySaveCompletedEvent)
        def on_save_completed(source, event):
            self.save_times.append(event.save_time_ms)
            avg = sum(self.save_times) / len(self.save_times)
            logger.info(f"💾 Memory saved in {event.save_time_ms:.2f}ms (avg: {avg:.2f}ms)")

        @crewai_event_bus.on(MemoryQueryStartedEvent)
        def on_query_started(source, event):
            logger.debug(f"🔍 Memory query: '{event.query}' (limit: {event.limit})")

        @crewai_event_bus.on(MemoryQueryCompletedEvent)
        def on_query_completed(source, event):
            self.query_times.append(event.query_time_ms)
            avg = sum(self.query_times) / len(self.query_times)
            logger.info(f"🔍 Memory query completed in {event.query_time_ms:.2f}ms (avg: {avg:.2f}ms)")

        @crewai_event_bus.on(MemoryRetrievalCompletedEvent)
        def on_retrieval_completed(source, event):
            task = event.task_id or "Unknown"
            logger.debug(f"📥 Memory retrieved for task {task} in {event.retrieval_time_ms:.2f}ms")

        @crewai_event_bus.on(MemorySaveFailedEvent)
        def on_save_failed(source, event):
            self.error_count += 1
            logger.error(f"❌ Memory save failed: {event.error}")

        @crewai_event_bus.on(MemoryQueryFailedEvent)
        def on_query_failed(source, event):
            self.error_count += 1
            logger.error(f"❌ Memory query failed: {event.error}")

    def get_performance_stats(self) -> dict:
        return {
            'avg_query_time_ms': sum(self.query_times) / max(len(self.query_times), 1),
            'avg_save_time_ms': sum(self.save_times) / max(len(self.save_times), 1),
            'total_queries': len(self.query_times),
            'total_saves': len(self.save_times),
            'error_count': self.error_count
        }

memory_listener = MemoryObservabilityListener()
```

#### Knowledge Events Listener

```python
from crewai.events import (
    BaseEventListener,
    KnowledgeRetrievalStartedEvent,
    KnowledgeRetrievalCompletedEvent,
)

class KnowledgeObservabilityListener(BaseEventListener):
    """Monitor knowledge retrieval operations."""

    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(KnowledgeRetrievalStartedEvent)
        def on_retrieval_started(source, event):
            print(f"📚 Agent '{event.agent.role}' started knowledge retrieval")

        @crewai_event_bus.on(KnowledgeRetrievalCompletedEvent)
        def on_retrieval_completed(source, event):
            print(f"📚 Agent '{event.agent.role}' completed knowledge retrieval")
            print(f"   Query: {event.query}")
            print(f"   Retrieved {len(event.retrieved_knowledge)} chunks")

knowledge_listener = KnowledgeObservabilityListener()
```

#### LLM Streaming Listener

```python
from crewai.events import BaseEventListener, LLMStreamChunkEvent

class StreamingListener(BaseEventListener):
    """Monitor LLM streaming responses in real-time."""

    def __init__(self, target_agent_id: str = None):
        super().__init__()
        self.target_agent_id = target_agent_id

    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(LLMStreamChunkEvent)
        def on_stream_chunk(source, event):
            # Optionally filter by agent
            if self.target_agent_id and event.agent_id != self.target_agent_id:
                return
            print(f"📝 Stream chunk: {event.chunk}", end="", flush=True)

streaming_listener = StreamingListener()
```

#### Scoped Event Handlers (Testing/Debugging)

```python
from crewai.events import crewai_event_bus, CrewKickoffStartedEvent

# Temporary handlers that auto-cleanup
with crewai_event_bus.scoped_handlers():
    @crewai_event_bus.on(CrewKickoffStartedEvent)
    def temp_debug_handler(source, event):
        print(f"[DEBUG] Crew started: {event.crew_name}")

    # Execute crew here - handler only active in this block
    crew.kickoff()

# Handler automatically removed outside the context
```

#### Registering Listeners

```python
# Option 1: Import in your flow/crew file
# In src/engine/flow.py
from src.observability.listeners import crew_listener, memory_listener

# Option 2: Import the package
import src.observability.listeners  # Auto-registers all listeners

# Option 3: Create instance in crew file
from src.observability.listeners import CrewObservabilityListener
my_listener = CrewObservabilityListener()
```

---

### 2. Execution Hooks

**Best for**: Tool/LLM call metrics, debugging, request modification

Hooks intercept execution at specific points and can modify behavior.

#### Tool Hooks

```python
from crewai import before_tool_call, after_tool_call
from crewai.tools import ToolCallHookContext
from collections import defaultdict
import time
import logging

logger = logging.getLogger("crewai.tools")
tool_metrics = defaultdict(lambda: {'count': 0, 'total_time': 0, 'errors': 0})
tool_call_chain = []

@before_tool_call
def log_tool_invocation(context: ToolCallHookContext) -> None:
    """Log and prepare tool call metrics."""
    agent = context.agent.role if context.agent else 'Unknown'
    task = context.task.description[:50] if context.task else 'Unknown'

    logger.info(f"""
    🔧 Tool Call:
    - Tool: {context.tool_name}
    - Agent: {agent}
    - Task: {task}...
    - Input: {context.tool_input}
    """)

    # Store start time for duration tracking
    context.tool_input['_start_time'] = time.time()
    return None

@after_tool_call
def track_tool_metrics(context: ToolCallHookContext) -> None:
    """Collect tool execution metrics."""
    start = context.tool_input.pop('_start_time', time.time())
    duration = time.time() - start

    tool_metrics[context.tool_name]['count'] += 1
    tool_metrics[context.tool_name]['total_time'] += duration

    if context.tool_result:
        result_preview = str(context.tool_result)[:200]
        logger.debug(f"✅ Tool result preview: {result_preview}...")
    else:
        logger.warning(f"⚠️ Tool '{context.tool_name}' returned no result")

    return None

@before_tool_call
def detect_tool_loops(context: ToolCallHookContext) -> None:
    """Detect potential infinite loops in tool chains."""
    tool_call_chain.append({
        'tool': context.tool_name,
        'timestamp': time.time(),
        'agent': context.agent.role if context.agent else 'Unknown'
    })

    # Check for repeated calls
    recent = tool_call_chain[-5:]
    if len(recent) == 5 and all(c['tool'] == context.tool_name for c in recent):
        logger.warning(f"⚠️ Potential loop: '{context.tool_name}' called 5 times consecutively")

    return None

def get_tool_metrics() -> dict:
    """Get summary of tool usage metrics."""
    return {
        tool: {
            'calls': data['count'],
            'avg_time': data['total_time'] / max(data['count'], 1),
            'total_time': data['total_time']
        }
        for tool, data in tool_metrics.items()
    }
```

#### LLM Hooks

```python
from crewai import before_llm_call, after_llm_call
import logging
import time

logger = logging.getLogger("crewai.llm")
llm_metrics = {'calls': 0, 'total_time': 0, 'tokens': 0}

@before_llm_call
def log_llm_call(context) -> None:
    """Log LLM call initiation."""
    agent = context.agent.role if context.agent else 'Unknown'
    iteration = context.iterations

    logger.debug(f"🧠 LLM call: agent='{agent}', iteration={iteration}")
    context.tool_input['_llm_start'] = time.time()
    return None

@after_llm_call
def track_llm_metrics(context) -> None:
    """Track LLM call performance."""
    start = context.tool_input.pop('_llm_start', time.time())
    duration = time.time() - start

    llm_metrics['calls'] += 1
    llm_metrics['total_time'] += duration

    logger.debug(f"🧠 LLM response in {duration:.2f}s")
    return None

def get_llm_metrics() -> dict:
    """Get LLM usage summary."""
    return {
        'total_calls': llm_metrics['calls'],
        'avg_time': llm_metrics['total_time'] / max(llm_metrics['calls'], 1),
        'total_time': llm_metrics['total_time']
    }
```

---

### 3. Crew-Level Callbacks

**Best for**: Simple step logging, collaboration tracking

#### Step Callback

```python
from crewai import Crew

def step_callback(output):
    """Monitor each step of crew execution."""
    raw = output.raw if hasattr(output, 'raw') else str(output)

    # Track collaboration patterns
    if "Delegate work to coworker" in raw:
        print("🤝 Agent delegation occurred")
    if "Ask question to coworker" in raw:
        print("❓ Agent asked question to coworker")

    # Log step output
    print(f"📝 Step output: {raw[:100]}...")

crew = Crew(
    agents=[...],
    tasks=[...],
    step_callback=step_callback,
    verbose=True
)
```

#### Task Callback

```python
from crewai import Task
from crewai.tasks import TaskOutput

def task_completed_callback(output: TaskOutput):
    """Execute after task completion."""
    print(f"""
    ✅ Task completed!
    Task: {output.description}
    Output: {output.raw[:200]}...
    """)
    # Send notification, log to external system, etc.

research_task = Task(
    description='Find and summarize the latest AI news',
    expected_output='A bullet list summary',
    agent=research_agent,
    callback=task_completed_callback  # Attach callback
)
```

---

### 4. Verbose Mode & Logging

**Best for**: Quick debugging, development

#### Verbose Mode

```python
from crewai import Agent, Crew

# Enable verbose on agents
agent = Agent(
    role="Researcher",
    goal="Research topics",
    backstory="...",
    verbose=True  # Detailed agent logging
)

# Enable verbose on crew
crew = Crew(
    agents=[agent],
    tasks=[...],
    verbose=True  # Crew-level logging
)
```

#### Output Log File

```python
from crewai import Crew

# Automatic logging to file
crew = Crew(
    agents=[...],
    tasks=[...],
    output_log_file=True,  # Saves as logs.txt
    # OR
    output_log_file="crew_execution.json",  # Custom JSON filename
    # OR
    output_log_file="crew_execution.txt",   # Custom text filename
)
```

#### Python Logging Configuration

```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crewai_debug.log')
    ]
)

# Set specific loggers
logging.getLogger('crewai').setLevel(logging.DEBUG)
logging.getLogger('crewai.tools').setLevel(logging.INFO)
logging.getLogger('crewai.memory').setLevel(logging.DEBUG)
```

---

## External Integrations

### 5. OpenTelemetry / OpenLIT

**Best for**: Production tracing, standardized observability

#### Installation

```bash
pip install openlit
```

#### Basic Setup

```python
import openlit

# Simple initialization
openlit.init()

# With custom endpoint
openlit.init(otlp_endpoint="http://127.0.0.1:4318")

# Disable metrics (traces only)
openlit.init(disable_metrics=True)
```

#### Environment Variables

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://127.0.0.1:4318"
```

#### Full Example

```python
from crewai import Crew, Agent, Task
import openlit

# Initialize OpenLIT
openlit.init(otlp_endpoint="http://127.0.0.1:4318")

# Your crew definition
agent = Agent(
    role="Researcher",
    goal="Research topics",
    backstory="Expert researcher",
    verbose=True
)

task = Task(
    description="Research AI trends",
    expected_output="Summary report",
    agent=agent
)

crew = Crew(agents=[agent], tasks=[task])

# All execution is automatically traced
result = crew.kickoff()
```

---

### 6. Langfuse

**Best for**: LLM-specific observability, prompt tracking

#### Installation

```bash
pip install langfuse openlit
```

#### Setup

```python
import os
import openlit

# Configure Langfuse
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-..."
os.environ["LANGFUSE_SECRET_KEY"] = "sk-..."
os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"

# Initialize OpenLIT (bridges to Langfuse)
openlit.init()
```

---

### 7. Arize Phoenix

**Best for**: ML observability, debugging, local development

#### Installation

```bash
pip install arize-phoenix openinference-instrumentation-crewai
```

#### Setup

```python
from phoenix.otel import register
from openinference.instrumentation.crewai import CrewAIInstrumentor

# Register tracer provider
tracer_provider = register(
    project_name="pocket-portals",
    auto_instrument=True,
)

# OR with custom endpoint
tracer_provider = register(
    endpoint="http://localhost:6006/v1/traces"
)

# Instrument CrewAI
CrewAIInstrumentor().instrument(
    skip_dep_check=True,
    tracer_provider=tracer_provider
)
```

#### Environment Variables (Phoenix Cloud)

```python
import os
os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com"
```

---

### 8. MLflow

**Best for**: ML experiment tracking, model versioning

#### Installation

```bash
pip install mlflow  # >= 2.19.0
```

#### Setup

```python
import mlflow

# Enable autologging for CrewAI
mlflow.crewai.autolog()

# Optional: Configure tracking server
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("PocketPortals")
```

---

### 9. Maxim

**Best for**: Agent-specific observability dashboard

#### Installation

```bash
pip install maxim-py
```

#### Setup

```python
from crewai import Agent, Task, Crew
from maxim import Maxim
from maxim.logger.crewai import instrument_crewai

# Initialize Maxim
maxim = Maxim()

# Instrument CrewAI with one line
instrument_crewai(maxim.logger())

# Your crew code...
agent = Agent(role="...", goal="...", backstory="...", verbose=True)

try:
    result = crew.kickoff()
finally:
    maxim.cleanup()  # Always cleanup
```

---

### 10. Datadog

**Best for**: Enterprise APM, infrastructure monitoring

#### Environment Variables

```bash
export DD_API_KEY=<YOUR_DD_API_KEY>
export DD_SITE=<YOUR_DD_SITE>
export DD_LLMOBS_ENABLED=true
export DD_LLMOBS_ML_APP=pocket-portals
export DD_LLMOBS_AGENTLESS_ENABLED=true
export DD_APM_TRACING_ENABLED=false
```

---

### 11. Braintrust

**Best for**: LLM evaluation, A/B testing

#### Installation

```bash
pip install braintrust opentelemetry-instrumentation-crewai opentelemetry-instrumentation-openai
```

#### Setup

```python
from braintrust.otel import BraintrustSpanProcessor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.crewai import CrewAIInstrumentor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

def setup_tracing():
    """Setup OpenTelemetry tracing with Braintrust."""
    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, TracerProvider):
        provider = current_provider
    else:
        provider = TracerProvider()
        trace.set_tracer_provider(provider)

    provider.add_span_processor(BraintrustSpanProcessor())
    CrewAIInstrumentor().instrument(tracer_provider=provider)
    OpenAIInstrumentor().instrument(tracer_provider=provider)

setup_tracing()
```

---

## Available Events Reference

### Crew Events
| Event | Description |
|-------|-------------|
| `CrewKickoffStartedEvent` | Crew execution started |
| `CrewKickoffCompletedEvent` | Crew execution completed successfully |
| `CrewKickoffFailedEvent` | Crew execution failed |
| `CrewTrainStartedEvent` | Crew training started |
| `CrewTrainCompletedEvent` | Crew training completed |
| `CrewTestStartedEvent` | Crew testing started |
| `CrewTestCompletedEvent` | Crew testing completed |

### Agent Events
| Event | Description |
|-------|-------------|
| `AgentExecutionStartedEvent` | Agent execution began |
| `AgentExecutionCompletedEvent` | Agent execution completed |
| `AgentExecutionErrorEvent` | Agent execution error |
| `AgentReasoningStartedEvent` | Agent reasoning process started |
| `AgentReasoningCompletedEvent` | Agent reasoning completed |
| `AgentEvaluationStartedEvent` | Agent evaluation began |
| `AgentEvaluationCompletedEvent` | Agent evaluation completed |

### Task Events
| Event | Description |
|-------|-------------|
| `TaskStartedEvent` | Task execution started |
| `TaskCompletedEvent` | Task execution completed |
| `TaskFailedEvent` | Task execution failed |
| `TaskEvaluationEvent` | Task evaluation result |

### LLM Events
| Event | Description |
|-------|-------------|
| `LLMCallStartedEvent` | LLM API call initiated |
| `LLMCallCompletedEvent` | LLM API call completed |
| `LLMCallFailedEvent` | LLM API call failed |
| `LLMStreamChunkEvent` | LLM streaming chunk received |
| `LLMGuardrailStartedEvent` | LLM guardrail check started |
| `LLMGuardrailCompletedEvent` | LLM guardrail check completed |

### Tool Events
| Event | Description |
|-------|-------------|
| `ToolUsageStartedEvent` | Tool execution started |
| `ToolUsageFinishedEvent` | Tool execution completed |
| `ToolUsageErrorEvent` | Tool execution error |
| `ToolValidateInputErrorEvent` | Tool input validation failed |
| `ToolSelectionErrorEvent` | Tool selection error |

### Memory Events
| Event | Description |
|-------|-------------|
| `MemoryQueryStartedEvent` | Memory query started |
| `MemoryQueryCompletedEvent` | Memory query completed |
| `MemoryQueryFailedEvent` | Memory query failed |
| `MemorySaveStartedEvent` | Memory save started |
| `MemorySaveCompletedEvent` | Memory save completed |
| `MemorySaveFailedEvent` | Memory save failed |
| `MemoryRetrievalStartedEvent` | Memory retrieval started |
| `MemoryRetrievalCompletedEvent` | Memory retrieval completed |

### Knowledge Events
| Event | Description |
|-------|-------------|
| `KnowledgeRetrievalStartedEvent` | Knowledge search started |
| `KnowledgeRetrievalCompletedEvent` | Knowledge search completed |
| `KnowledgeSearchQueryStartedEvent` | Knowledge query started |
| `KnowledgeSearchQueryCompletedEvent` | Knowledge query completed |
| `KnowledgeSearchQueryFailedEvent` | Knowledge query failed |

### Flow Events
| Event | Description |
|-------|-------------|
| `FlowCreatedEvent` | Flow instance created |
| `FlowStartedEvent` | Flow execution started |
| `FlowFinishedEvent` | Flow execution completed |
| `MethodExecutionStartedEvent` | Flow method execution began |
| `MethodExecutionFinishedEvent` | Flow method execution completed |
| `MethodExecutionFailedEvent` | Flow method execution failed |

---

## Implementation Recommendations

### For Pocket Portals

#### Phase 1: Development (Immediate)
```python
# src/observability/__init__.py
from .listeners import crew_listener, memory_listener
from .hooks import get_tool_metrics, get_llm_metrics

def setup_dev_observability():
    """Development observability setup."""
    import logging
    logging.basicConfig(level=logging.INFO)
    # Listeners auto-register on import
    return True
```

#### Phase 2: Production
```python
# src/observability/production.py
import os
import openlit

def setup_production_observability():
    """Production observability with OpenTelemetry."""
    endpoint = os.getenv("OTEL_ENDPOINT", "http://localhost:4318")
    openlit.init(otlp_endpoint=endpoint)

    # Import listeners for additional custom events
    from . import listeners
    return True
```

#### Integration with Flow

```python
# src/engine/flow.py
import src.observability  # Auto-registers listeners

class ConversationFlow(Flow[ConversationFlowState]):
    # ... existing code ...
```

### Disabling Telemetry

If you need to disable CrewAI's built-in telemetry:

```python
import os

# Disable CrewAI telemetry only
os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'

# Disable all OpenTelemetry
os.environ['OTEL_SDK_DISABLED'] = 'true'
```

---

## Summary

| Method | Complexity | Use Case | Production Ready |
|--------|------------|----------|------------------|
| Event Listeners | Low | Custom monitoring | ✅ |
| Execution Hooks | Low | Tool/LLM metrics | ✅ |
| Verbose Mode | Minimal | Quick debugging | ❌ |
| Crew Callbacks | Minimal | Step logging | ✅ |
| OpenTelemetry | Medium | Distributed tracing | ✅ |
| Langfuse | Medium | LLM observability | ✅ |
| Arize Phoenix | Medium | ML debugging | ✅ |
| MLflow | Medium | Experiment tracking | ✅ |
| Maxim | Low | Agent dashboard | ✅ |
| Datadog | High | Enterprise APM | ✅ |
| Braintrust | Medium | LLM evaluation | ✅ |
