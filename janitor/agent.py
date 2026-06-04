from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams

import janitor.schemas as schemas
import janitor.settings as settings
import janitor.tools as tools

mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url="https://mcp-server-pszgpylysa-uc.a.run.app")
)

resource_scanner_agent = Agent(
    name="resource_scanner_agent",
    model=settings.GEMINI_MODEL,
    instruction="""
    You are a Cloud Resource Scanner.
    Call the get_compute_instances_list tool and populate the vm_instances field
    with EVERY VM the tool returns. Do not leave vm_instances empty.
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

resource_labeler_agent = Agent(
    name="resource_labeler_agent",
    model=settings.GEMINI_MODEL,
    instruction="""
    You are a Cloud Resource Labeler. Apply lifecycle labels to idle VM instances.

    The idle VMs to process are: {idle_resources}

    For each VM:
    1. Call get_current_date to get today's date.
    2. Call add_days_to_date with that date and 7 to compute the scheduled date.
    3. Use the MCP tools to check if the VM already has a 'janitor-scheduled' label.
    4. If the VM does NOT have a 'janitor-scheduled' label, apply it using the scheduled date as the value.
    5. If the VM already has a 'janitor-scheduled' label, leave it completely unchanged.
    """,
    tools=[
        tools.get_current_date,
        tools.add_days_to_date,
        mcp_toolset
    ],
)

orchestrator_agent = SequentialAgent(
    name="orchestrator_agent",
    sub_agents=[resource_scanner_agent, resource_monitor_agent, resource_labeler_agent],
)

# The root_agent is the entry point for the user query.
root_agent = orchestrator_agent
