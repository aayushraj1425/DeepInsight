from agents.state import AgentState
from events import AgentEvent
from runtime import emit
from tools.datasets import discover_datasets, load_dataset_tables
from tools.trusted_data import load_trusted_time_series


async def datafinder_node(state: AgentState) -> dict:
    sid = state["session_id"]
    await emit(sid, AgentEvent(
        type="node_start",
        agent="datafinder",
        payload={"message": "Searching trusted data sources, public catalogs, and loadable time series..."},
    ))

    trusted_sources, trusted_profiles, trusted_findings = await load_trusted_time_series(
        state["query"],
        state.get("research_plan", {}),
    )
    datasets = await discover_datasets(state["query"], state.get("subqueries", []))
    table_profiles, dataset_findings = await load_dataset_tables(datasets)
    trusted_datasets = [
        {
            "source_id": profile["dataset_id"],
            "provider": profile.get("provider"),
            "title": profile.get("title"),
            "description": f"Trusted {profile.get('source_class', 'time series')} with {profile.get('rows', 0)} observations.",
            "url": profile.get("url"),
            "resources": [],
            "score": 10,
            "credibility": profile.get("credibility"),
            "latest_year": (profile.get("summary", {}).get("value") or {}).get("latest_year"),
        }
        for profile in trusted_profiles
    ]
    all_datasets = trusted_datasets + datasets
    all_profiles = trusted_profiles + table_profiles
    all_findings = trusted_findings + dataset_findings

    source_index = dict(state.get("source_index", {}))
    for dataset in all_datasets:
        source_index[dataset["source_id"]] = {
            "source_id": dataset["source_id"],
            "source_type": "dataset",
            "provider": dataset.get("provider"),
            "title": dataset.get("title"),
            "url": dataset.get("url"),
            "description": dataset.get("description"),
        }

    await emit(sid, AgentEvent(
        type="datasets_ready",
        agent="datafinder",
        payload={
            "count": len(all_datasets),
            "trusted_sources": trusted_sources,
            "loaded_tables": len(all_profiles),
            "datasets": [
                {
                    "source_id": dataset["source_id"],
                    "provider": dataset.get("provider"),
                    "title": dataset.get("title"),
                    "description": dataset.get("description"),
                    "url": dataset.get("url"),
                    "resource_count": len(dataset.get("resources", [])),
                    "credibility": dataset.get("credibility"),
                    "latest_year": dataset.get("latest_year"),
                }
                for dataset in all_datasets
            ],
            "table_profiles": all_profiles,
            "message": f"Found {len(all_datasets)} dataset candidates and loaded {len(all_profiles)} trusted/analyzable table(s)",
        },
    ))

    await emit(sid, AgentEvent(
        type="node_end",
        agent="datafinder",
        payload={"dataset_count": len(all_datasets), "loaded_tables": len(all_profiles)},
    ))

    return {
        "datasets": all_datasets,
        "dataset_findings": all_findings,
        "dataset_analysis": {"tables": all_profiles, "trusted_sources": trusted_sources},
        "source_index": source_index,
    }
