"""LangGraph orchestration with durable graph checkpoints and HTTP write-ahead journal."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from .engine import choose, initialize, interpret
from .gateway import Gateway
from .models import Experiment, Knowledge
from .persistence import JournaledGateway, Store
from .security import PolicyError, TargetPolicy
from .telemetry import stage


class GraphState(TypedDict):
    knowledge: dict[str, Any]
    selected: dict[str, Any] | None
    observation: dict[str, Any] | None


def run_graph(
    session_id: str,
    policy: TargetPolicy,
    directory: Path,
    strategy: str = "gain",
    random_seed: int = 42,
) -> Knowledge:
    from dataclasses import asdict

    from langchain_core.runnables import RunnableConfig, RunnableLambda
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.graph import END, START, StateGraph

    from .models import Observation

    model_config = None
    if strategy == "llm":
        from .model_config import ModelConfig

        model_config = ModelConfig.from_environment()

    store = Store(directory / "evidence.sqlite")
    current = store.load(session_id) or initialize(session_id, strategy=strategy)
    current.random_seed = random_seed if store.load(session_id) is None else current.random_seed
    store.save(current)
    used, started = store.budget(session_id)
    gateway = JournaledGateway(
        Gateway(policy, used=used, started=started, session_id=session_id), store, session_id
    )

    def select(value: GraphState) -> dict[str, Any]:
        state = Knowledge.from_dict(value["knowledge"])
        if store.cancelled(session_id):
            state.status = "cancelled"
        if not state.pending and state.status == "running":
            state.status = "complete"
        if state.status != "running":
            return {"knowledge": state.to_dict(), "selected": None}
        persisted = store.load(session_id)
        if persisted and persisted.model_usage["calls"] > state.model_usage["calls"]:
            state.model_usage = persisted.model_usage
        index = None
        if model_config is not None:
            from openai import OpenAI

            from .model import rank

            state.model_usage.update(provider=model_config.provider, model=model_config.model)
            with OpenAI(**model_config.client_options()) as client:
                index = rank(
                    state,
                    model_config.model,
                    client,
                    checkpoint=lambda: store.save(state),
                    api=model_config.api,
                )
        experiment = state.pending.pop(index) if index is not None else choose(state)
        state.seen.add(experiment.key)
        return {"knowledge": state.to_dict(), "selected": asdict(experiment)}

    def execute(value: GraphState) -> dict[str, Any]:
        state = Knowledge.from_dict(value["knowledge"])
        assert value["selected"] is not None
        try:
            with stage("http_experiment", session_id):
                observation = gateway.execute(Experiment(**value["selected"]))
            return {"observation": observation.to_dict()}
        except PolicyError as error:
            state.rejected.append({"category": "policy", "reason": str(error)})
            if store.cancelled(session_id):
                state.status = "cancelled"
            elif "budget" in str(error).lower():
                state.status = "budget_exhausted"
            elif "Uncertain" in str(error):
                state.status = "interrupted"
            else:
                state.status = "running"
            return {"knowledge": state.to_dict(), "observation": None}

    def update(value: GraphState) -> dict[str, Any]:
        state = Knowledge.from_dict(value["knowledge"])
        if value["observation"]:
            record = dict(value["observation"])
            record["experiment"] = Experiment(**record["experiment"])
            with stage("schema_and_state_inference", session_id):
                interpret(state, Observation(**record))
        store.save(state)
        return {"knowledge": state.to_dict()}

    graph = StateGraph(GraphState)
    graph.add_node("rank", RunnableLambda(select))
    graph.add_node("execute_gateway", RunnableLambda(execute))
    graph.add_node("update_evidence", RunnableLambda(update))
    graph.add_edge(START, "rank")
    graph.add_conditional_edges(
        "rank", lambda value: "execute_gateway" if value["selected"] else END
    )
    graph.add_edge("execute_gateway", "update_evidence")
    graph.add_edge("update_evidence", "rank")
    try:
        with SqliteSaver.from_conn_string(str(directory / "graph.sqlite")) as saver:
            compiled = graph.compile(checkpointer=saver)
            config: RunnableConfig = {
                "configurable": {"thread_id": session_id},
                "recursion_limit": policy.max_requests * 4 + 20,
            }
            snapshot = compiled.get_state(config)
            initial: GraphState | None = (
                None
                if snapshot.next
                else {"knowledge": current.to_dict(), "selected": None, "observation": None}
            )
            result = compiled.invoke(initial, config)
            state = Knowledge.from_dict(result["knowledge"])
            store.save(state)
            return state
    finally:
        store.close()
