from langgraph.graph import StateGraph, END
from agents import (planner_agent,researcher_agent,subject_line_writer_agent,preheader_writer_agent,
                    body_writer_agent,email_variant_aggregator,quality_assurance_agent,html_agent,add_approved_variant)
from langgraph.checkpoint import MemorySaver
from models import EmailCampaignState
from config import TONES

def create_email_campaign_graph():
    email_campaign_graph = StateGraph(EmailCampaignState)

    email_campaign_graph.add_node("planner", planner_agent)
    email_campaign_graph.add_node("researcher", researcher_agent)
    email_campaign_graph.add_node("subject line writer", subject_line_writer_agent)
    email_campaign_graph.add_node("preheader writer", preheader_writer_agent)
    email_campaign_graph.add_node("body writer", body_writer_agent)
    email_campaign_graph.add_node("email variant aggregator", email_variant_aggregator)
    email_campaign_graph.add_node("quality assurance agent", quality_assurance_agent)
    email_campaign_graph.add_node("html agent", html_agent)
    email_campaign_graph.add_node("add approved variant", add_approved_variant)

    email_campaign_graph.add_edge("planner", "researcher")
    email_campaign_graph.add_edge("researcher", "subject line writer")
    email_campaign_graph.add_edge("subject line writer", "preheader writer")
    email_campaign_graph.add_edge("preheader writer", "body writer")
    email_campaign_graph.add_edge("body writer", "email variant aggregator")
    email_campaign_graph.add_edge("email variant aggregator", "quality assurance agent")
    email_campaign_graph.add_edge("html agent", "add approved variant")

    email_campaign_graph.add_conditional_edges(
    "quality assurance agent",
    should_approve_or_revise,
    {
        "subject line writer": "subject line writer",
        "html agent": "html agent"
    }
    )

    email_campaign_graph.add_conditional_edges(
    "add approved variant",
    should_continue_or_finish,
    {
        "subject line writer": "subject line writer",
        "END": END
    }
    )

    email_campaign_graph.set_entry_point("planner")
    memory = MemorySaver()

    return email_campaign_graph.compile(checkpointer=memory)

def should_continue_or_finish(state: EmailCampaignState):
    if len(state.get('variants', [])) < state['campaignInfo'].num_variants * len(TONES):
        return "subject line writer"
    else:
        return "END"

def should_approve_or_revise(state: EmailCampaignState):
    if state.get('qa_feedback') and isinstance(state['qa_feedback'], dict):
        feedback = state['qa_feedback']
        if feedback.get('needs_revision'):
            return "subject line writer"
        else:
            return "html agent"
    return "subject line writer"


email_campaign_graph = create_email_campaign_graph()