from google.adk import Agent
from google.adk.agents import SequentialAgent

import janitor.schemas as schemas
import janitor.settings as settings
import janitor.tools as tools


resource_scanner_agent = Agent(
    name="resource_scanner_agent",
    model=settings.GEMINI_MODEL,
    instruction="""
    You are a Cloud Resource Scanner.
    Return *all* resources.
    """,
    tools=[tools.get_compute_instances_list],
    output_schema=schemas.VMInstanceList,
    output_key="resources",
)

resource_monitor_agent = Agent(
    name="resource_monitor_agent",
    model=settings.GEMINI_MODEL,
    instruction="""
    You are a Cloud Resource Monitor. Your job is to identify idle VM instances.

    The VMs to analyze are: {resources}

    For each VM, call get_compute_instance_stats using the format project_id/zone/instance_name.
    A VM is considered idle if its average CPU utilization is below 0.10 (10%) and network traffic is minimal.

    Return only the idle VMs.
    """,
    tools=[tools.get_compute_instance_stats],
    output_schema=schemas.VMStatsList,
    output_key="idle_resources",
)

orchestrator_agent = SequentialAgent(
    name="orchestrator_agent",
    sub_agents=[resource_scanner_agent, resource_monitor_agent],
)

# The root_agent is the entry point for the user query.
root_agent = orchestrator_agent
