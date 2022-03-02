from typing import *
import itertools
from datetime import datetime

import networkx as nx
from dateutil.relativedelta import relativedelta


def iterate_windows_over_month(month_start_date: datetime, window_size: int=31) -> Iterator[Tuple[datetime, datetime]]:
    month_end_date = month_start_date + relativedelta(day=31)
    while month_start_date < month_end_date:
        curr = min(month_start_date + relativedelta(days=window_size), month_end_date)
        yield (month_start_date, curr)
        month_start_date = curr + relativedelta(days=1)


def iterate_windows_over_year(year_start_date: datetime) -> Iterator[Tuple[datetime, datetime]]:
    for i in range(0, 12):
        month_windows = iterate_windows_over_month(year_start_date + relativedelta(months=i))
        for w in month_windows:
            yield w


def iterate_windows_over_range(starting_year: int, ending_year: int) -> Iterator[Tuple[datetime, datetime]]:
    start = datetime(year=starting_year, month=1, day=1)
    end = datetime(year=ending_year, month=1, day=1)
    curr = start
    while curr < end:
        windows = iterate_windows_over_year(curr)
        chunks = list(itertools.islice(windows, 12))
        s, e = chunks[0][0], chunks[-1][-1]
        yield (s, e)
        # for w in iterate_windows_over_year(curr): yield w

        curr = curr + relativedelta(years=1)

def normalize_node_attributes(graph, attribute: str):
    max_points = max(graph.nodes[n][attribute] for n in graph.nodes)
    min_points = min(graph.nodes[n][attribute] for n in graph.nodes)

    for n in graph.nodes:
        graph.nodes[n][attribute] = (graph.nodes[n][attribute] - min_points) / (max_points - min_points)

    return graph

def normalize_edge_attribute(graph, attribute: str):
    max_points = max(graph.edges[p, q][attribute] for p,q in graph.edges)
    min_points = min(graph.edges[p, q][attribute] for p,q in graph.edges)

    for p,q in graph.edges:
        graph.edges[p,q][attribute] = (graph.edges[p,q][attribute] - min_points) / (max_points - min_points)

    return graph
    

def normalize_pagerank_scores(pagerank_scores: Dict[str, float]) -> Dict[str, float]:
    min_score = min(v for k,v in pagerank_scores.items())
    max_score = max(v for k,v in pagerank_scores.items())
    for k in pagerank_scores:
        pagerank_scores[k] = (pagerank_scores[k] - min_score) / (max_score - min_score)

    return pagerank_scores
