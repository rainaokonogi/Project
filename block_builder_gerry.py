import networkx as nx
import numpy as np
from gerrychain import (Partition, Graph, MarkovChain, updaters, accept, Election)
from gerrychain.proposals import recom
from gerrychain.tree import recursive_tree_part, bipartition_tree
from gerrychain.constraints import contiguous, within_percent_of_ideal_population
from gerrychain.optimization import SingleMetricOptimizer, Gingleator
from functools import partial
import pandas as pd
import matplotlib.pyplot as plt
import random
import operator
from matplotlib.lines import Line2D
import json
import datetime
import os

def safe_reward_partial_dist(part, minority_perc_col, threshold):
    try:
        return Gingleator.reward_partial_dist(
            part=part, minority_perc_col=minority_perc_col, threshold=threshold
        )
    except ValueError:
        return Gingleator.num_opportunity_dists(
            part=part, minority_perc_col=minority_perc_col, threshold=threshold
        )

block_sizes = [2,3,4,6]
r_seats = [58,72,86]
map_numbers = [1,2,3]

for a in r_seats:
    for b in map_numbers:
        for c in block_sizes:

            file_to_read = f"/share/duchin/raina/summer_2025_project/underlying maps/map .jsons/R_{a}_map_{b}.json"
            pop_col = 'population'
            random_seed_num = 5683
            r_seats = a
            map_number = b
            block_size = c
            num_blocks = 144/block_size
            random.seed(random_seed_num)

            graph = Graph.from_json(file_to_read)

            my_updaters = {
            "population": updaters.Tally("population"),
            "election": Election("election", {"D": "D", "R": "R"}),
            "R_tally": updaters.Tally("R",alias="R_tally"),
            "D_tally": updaters.Tally("D",alias="D_tally")
            }

            partition_4_lst = []
            n_found = 0
            while n_found < 1:
                try:
                    part = Partition.from_random_assignment(
                        graph=graph,
                        n_parts=144//block_size,
                        pop_col='population',
                        updaters = my_updaters,
                        epsilon = 0.00001,
                        method = recursive_tree_part
                    )
                    assert all(part.assignment.to_series().value_counts() == block_size)
                    partition_4_lst.append(part.assignment.to_dict())
                    n_found += 1
                except Exception:
                    pass

            num_dem_seats = lambda p: p["election"].seats("D")

            proposal = partial(
                recom,
                pop_col=pop_col,
                pop_target=block_size,
                epsilon=0,
                node_repeats=2
            )

            recom_chain = Gingleator(
                proposal=proposal,
                constraints=[contiguous],
                threshold=0.5,
                initial_state=part,
                total_pop_col='population',
                minority_pop_col='D_tally',
                score_function=safe_reward_partial_dist
            )

            samples = []
            for i, partition in enumerate(recom_chain.short_bursts(20, round(1000000/20))):
                if (i+1) % 10000 == 0:
                    partition_info = partition.assignment.to_dict()
                    samples.append(partition_info)
                    print(f"collected sample! (i = {i})")
                else:
                    continue
                
            print(f"Collected {len(samples)} samples.")

            for i in range(len(samples)):
                partition_dict = {}
                for node, assign in samples[i].items():
                    if assign not in partition_dict:
                        partition_dict[assign] = set()
                    partition_dict[assign].add(int(node))

                subgraph = nx.quotient_graph(graph, list(partition_dict.values()))
                subgraph = nx.convert_node_labels_to_integers(subgraph)
                gerry_subgraph = Graph.from_networkx(subgraph)
                gerry_subgraph.nodes(data=True)
                for node, data in gerry_subgraph.nodes(data=True):
                    atomics = data['graph'].nodes
                    gerry_subgraph.nodes[node]['atomics'] = str(atomics)
                    gerry_subgraph.nodes[node]['group_pop'] = block_size
                    gerry_subgraph.nodes[node]['id'] = "\"" + str(node) + "\""

                file_name = f"/share/duchin/raina/final_exp_files/final building block graphs/gerry/R {r_seats} map {map_number}/block size {block_size}/sample_{i+1}.json"
                os.makedirs(os.path.dirname(file_name), exist_ok=True)
                gerry_subgraph.to_json(file_name)