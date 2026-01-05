import click
from syn_file_GG import run_experiment_gg
from syn_file_NG import run_experiment_ng
from syn_file_GN import run_experiment_gn
from syn_file_NN import run_experiment_nn

# Add the choice type to everything.
@click.command()
@click.option(
    "--num-r-units",
    prompt="Number of red units in underlying map",
    help="",
    type=click.Choice([72, 86, 58]),
)
@click.option("--map-number",
    prompt="Which map to use? (1, 2, or 3)",
    help="",
    type=click.Choice([1, 2, 3])
)
@click.option("--block-size",
    prompt="Which block size? (2, 3, 4, or 6)",
    help="",
    type=click.Choice([2, 3, 4, 6])
)
@click.option("--experiment-type",
    prompt="Experiment type? (GG, NG, GN, or NN)",
    help="",
    type=click.Choice(["GG", "GN", "NG", "NN"])
)
@click.option(
    "--random-seed",
    prompt="Random seed",
    help="Integer to set random seed",
    type=int
)
@click.option(
    "--total-steps",
    prompt="Step count (must be divisible by 20)",
    type=int,
    help="Number of districting plans per building block graph",
)
def main(
    num_r_units, map_number, block_size, experiment_type, random_seed, total_steps
):
    if experiment_type == "GG":
        run_experiment_gg(num_r_units, map_number, block_size, random_seed, total_steps)
    elif experiment_type == "NG":
        run_experiment_ng(num_r_units, map_number, block_size, random_seed, total_steps)
    elif experiment_type == "GN":
        run_experiment_gn(num_r_units, map_number, block_size, random_seed, total_steps)
    elif experiment_type == "NN":
        run_experiment_nn(num_r_units, map_number, block_size, random_seed, total_steps)

if __name__ == "__main__":
    main()