from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from core import normalized_path_key, output_path_from_tags, read_audio_tags


@dataclass
class OutputPlan:
    destinations: Dict[Path, Path]
    failures: Dict[Path, str]
    failure_destinations: Dict[Path, Path]


def prepare_source_plan(sources: list[Path]) -> OutputPlan:
    destinations = {}
    groups = {}
    for source in sources:
        destination = source.with_suffix(".mp3")
        groups.setdefault(normalized_path_key(destination), []).append((source, destination))

    failures = {}
    for group in groups.values():
        if len(group) > 1:
            for source, destination in group:
                failures[source] = f"collision de destination : {destination}"
        else:
            source, destination = group[0]
            destinations[source] = destination

    return OutputPlan(
        destinations,
        failures,
        {source: source.with_suffix(".mp3") for source in failures},
    )


def prepare_output_plan(sources: list[Path], output_root: Path) -> OutputPlan:
    prepared = {}
    failures = {}
    failure_destinations = {}

    for source in sources:
        try:
            artist, album = read_audio_tags(source)
            prepared[source] = output_path_from_tags(source, output_root, artist, album)
        except Exception as exc:
            failures[source] = str(exc)

    groups = {}
    for source, destination in prepared.items():
        groups.setdefault(normalized_path_key(destination), []).append((source, destination))

    destinations = {}
    for group in groups.values():
        if len(group) > 1:
            for source, destination in group:
                failures[source] = f"collision de destination : {destination}"
                failure_destinations[source] = destination
        else:
            source, destination = group[0]
            destinations[source] = destination

    return OutputPlan(destinations, failures, failure_destinations)
