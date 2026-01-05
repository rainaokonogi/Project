from networkx.algorithms.minors import quotient_graph
from gerrychain import (Partition, Graph, MarkovChain, updaters, accept, Election)
from gerrychain.proposals import recom
from gerrychain.tree import recursive_tree_part, bipartition_tree
from gerrychain.constraints import contiguous, within_percent_of_ideal_population
from gerrychain.optimization import SingleMetricOptimizer, Gingleator
import jsonlines as jl
from functools import partial
import random
import json
from datetime import datetime
import ast
import os
from pyben import PyBenEncoder

# Gingleator score function that won't throw an error if no districts are below threshold
# If no such district exists, returns number of opportunity districts
def safe_reward_partial_dist(part, minority_perc_col, threshold):
    try:
        return Gingleator.reward_partial_dist(
            part=part, minority_perc_col=minority_perc_col, threshold=threshold
        )
    except ValueError:
        return Gingleator.num_opportunity_dists(
            part=part, minority_perc_col=minority_perc_col, threshold=threshold
        )

# R_seat_number indicates number of Republicans in underlying map; three options based on 50-50, 40-60, 60-40 splits
# Map number indicates which underlying map to use (9 options total, 3 for each partisan split)
# Total steps is number of steps for each chain; number of plans in final ensemble will be 100 * total_steps
def run_experiment_gg(num_r_units, map_number, block_size, random_seed, total_steps):

    # Make save files
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_assignment_results_to = f"/share/duchin/raina/final exp results/syn exp results/GG/r_votes_{num_r_units}_map_{map_number}/{block_size}/{total_steps}_{current_time}_assignment.jsonl.ben"
    save_updaters_results_to = f"/share/duchin/raina/final exp results/syn exp results/GG/r_votes_{num_r_units}_map_{map_number}/{block_size}/{total_steps}_{current_time}_updaters.jsonl"
    os.makedirs(os.path.dirname(save_assignment_results_to), exist_ok=True)
    os.makedirs(os.path.dirname(save_updaters_results_to), exist_ok=True)

    # Set pop data, random seed
    random.seed(random_seed)
    pop_col = 'group_pop'

    # Iterate over building block files
    for sample in range(1,101):

        # Load building block graph — originally I was building a quotient graph
        # But I think these files have all the info we need, including adjacency
        block_data = f"/share/duchin/raina/final_exp_files/building block graphs with init parts and votes/gerry/R {num_r_units} map {map_number}/block size {block_size}/sample_{sample}.json"
        with open(block_data, 'r') as file:

            block_graph = Graph.from_json(block_data)

            # For use later when saving results
            graph_node_order = list(block_graph.nodes)
        
            # Updaters
            my_updaters = {
                "population": updaters.Tally("group_pop",alias="population"),
                "election": Election("election", {"D": "D", "R": "R"}),
                "R_tally": updaters.Tally("R",alias="R_tally"),
                "D_tally": updaters.Tally("D",alias="D_tally"),
                }

            # Pull initial partition for block graph
            part = Partition(
                block_graph,
                assignment="init_part_assignment",
                updaters=my_updaters
            )

            # 144 nodes and 12 districts, so pop_target is 12
            proposal = partial(
                recom,
                pop_col=pop_col,
                pop_target=12,
                epsilon=0,
                node_repeats=2
            )

            # Define recom chain
            # Gingleator score function should return number of districts where over 50% of the votes go to gerrymandered party
            # + percentage of that party in district where it gets the highest vote share under 50%
            recom_chain = Gingleator(
                proposal=proposal,
                constraints=[contiguous],
                threshold=0.5,
                initial_state=part,
                total_pop_col="population",
                minority_pop_col='D_tally',
                score_function=safe_reward_partial_dist
            )

            # Save data
            with (
                    PyBenEncoder(save_assignment_results_to, overwrite=True) as encoder,
                    jl.open(save_updaters_results_to, "w") as updater_output_file,
                ):
           
                for i, plan in enumerate(recom_chain.short_bursts(5,round(total_steps/5))):

                    assert (
                        plan is not None
                    ), "Something went terribly wrong. There is no output partition."

                    assignment_series = plan.assignment.to_series()
                    ordered_assignment = (
                        assignment_series.loc[graph_node_order].astype(int).tolist()
                    )
                    encoder.write(ordered_assignment)

                    election = plan["election"]
                    
                    seats_won = {
                        "D": election.seats("D"),
                        "R": election.seats("R")
                    }

                    regions = election.regions 

                    d_counts = election.counts("D")
                    r_counts = election.counts("R")
                    d_votes_by_district = dict(zip(regions, d_counts))
                    r_votes_by_district = dict(zip(regions, r_counts))

                    district_winners = {region: ("D" if d > r else "R") for region, d, r in zip(regions, d_counts, r_counts)}

                    record = {
                        "step": i,
                        "population": dict(plan["population"]),
                        "Seats won": seats_won,
                        "D votes": d_votes_by_district,
                        "R votes": r_votes_by_district,
                        "District winners": district_winners
                    }

                    updater_output_file.write(record)