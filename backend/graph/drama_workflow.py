from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.director_agent import optimize_prompt
from agents.prompt_agent import generate_all_prompts
from agents.storyboard_agent import create_storyboard
from agents.writer_agent import parse_story


class DramaState(TypedDict, total=False):
    story: str
    style: str
    shot_count: int
    scenes: list
    characters_profile: list
    shots: list
    prompts: list
    errors: list


async def node_parse_story(state: DramaState) -> DramaState:
    parsed = await parse_story(state["story"])
    return {
        **state,
        "scenes": parsed.get("scenes", []),
        "characters_profile": parsed.get("characters_profile", []),
    }


async def node_storyboard(state: DramaState) -> DramaState:
    shots = await create_storyboard(state.get("scenes", []), state.get("shot_count", 3))
    return {**state, "shots": shots}


async def node_prompts(state: DramaState) -> DramaState:
    prompts = await generate_all_prompts(state.get("shots", []), state.get("style", "cinematic"))
    return {**state, "prompts": prompts}


async def node_director(state: DramaState) -> DramaState:
    optimized = []
    for p in state.get("prompts", []):
        optimized.append(await optimize_prompt(p))
    return {**state, "prompts": optimized}


def build_drama_graph():
    graph = StateGraph(DramaState)
    graph.add_node("parse_story", node_parse_story)
    graph.add_node("storyboard", node_storyboard)
    graph.add_node("prompts", node_prompts)
    graph.add_node("director", node_director)
    graph.set_entry_point("parse_story")
    graph.add_edge("parse_story", "storyboard")
    graph.add_edge("storyboard", "prompts")
    graph.add_edge("prompts", "director")
    graph.add_edge("director", END)
    return graph.compile()


drama_graph = build_drama_graph()
