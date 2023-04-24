import pathlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as pltpatch
import tqdm
import pandas


def generate_positions(
    n_circles: int,
    radius: float = 0,
    seed: int = 42,
    with_overlap=True,
    n_tries_per_addition: int = 50000,
    box_l=1.0,
):
    rng = np.random.default_rng(seed)
    box = np.array([box_l, box_l])[None, :]
    if with_overlap:
        return box * rng.random((n_circles, 2))
    else:
        # first one always fits
        circle_positions = rng.random((1, 2))
        for _ in range(1, n_circles):
            for _ in range(n_tries_per_addition):
                proposed_new = rng.random((1, 2)) * box
                dists = circle_positions - proposed_new
                dists_folded = dists - np.rint(dists / box) * box
                if np.all(np.linalg.norm(dists_folded, axis=1) > 2 * radius):
                    circle_positions = np.append(circle_positions, proposed_new, axis=0)
                    break
            else:
                break
        return circle_positions


def plot_positions(positions, radius, box_l=1.0):
    fig = plt.figure()
    ax = plt.gca()
    plt.xlim((0, box_l))
    plt.ylim((0, box_l))
    ax.set_aspect("equal")
    for pos in positions:
        circ = pltpatch.Circle(pos, radius)
        ax.add_patch(circ)
    return fig


def calc_exclusion_probability(
    positions, radius, box_l=1.0, n_test_partcls=1000, seed: int = 42
):
    rng = np.random.default_rng(seed)
    box = np.array([box_l, box_l])[None, :]
    test_positions = rng.random((n_test_partcls, 2)) * box

    n_fit_in = 0

    for test_pos in test_positions:
        dists = positions - test_pos[None, :]
        dists -= np.rint(dists / box) * box
        if np.all(np.linalg.norm(dists, axis=1) > 2 * radius):
            n_fit_in += 1

    return 1 - n_fit_in / n_test_partcls


def produce_data():

    results_dicts = []

    modes = ["rsa", "overlapping"]
    pack_fracs = [0.2, 0.5]
    particle_radius = 1
    test_radii = np.linspace(0.01, 3, num=100)
    n_partcls = 1000
    n_test_partcls = 1000

    n_configurations = 5
    n_configuration_tries = 100

    for mode in modes:
        for pack_frac in pack_fracs:
            phi_1 = 1 - pack_frac
            if mode == "overlapping":
                box_l = np.sqrt(
                    -n_partcls / np.log(phi_1) * np.pi * particle_radius**2
                )
            elif mode == "rsa":
                box_l = np.sqrt(np.pi * n_partcls * particle_radius**2 / (1 - phi_1))
            else:
                raise ValueError("unknown mode")

            config_seed = 0
            n_good_configs = 0
            progress_bar = tqdm.tqdm(
                total=n_configurations, desc=f"mode={mode}, pack frack={pack_frac}"
            )
            for _ in range(n_configuration_tries):
                config_seed += 1
                circle_poss = generate_positions(
                    n_partcls,
                    radius=particle_radius,
                    with_overlap=mode == "overlapping",
                    box_l=box_l,
                    seed=config_seed,
                )
                if len(circle_poss) < n_partcls:
                    # bad configuration, do not do analysis
                    continue

                # we have found a good config, do test particle analysis
                n_good_configs += 1
                progress_bar.update(1)
                for test_radius in test_radii:

                    exclusion_prob = calc_exclusion_probability(
                        circle_poss,
                        test_radius,
                        box_l=box_l,
                        n_test_partcls=n_test_partcls,
                        seed=1000000 + n_good_configs,
                    )
                    results_dicts.append(
                        {
                            "mode": mode,
                            "pack_frac": pack_frac,
                            "test_radius": test_radius,
                            "exclusion_prob": exclusion_prob,
                            "config_seed": config_seed,
                        }
                    )

                if n_good_configs >= n_configurations:
                    break

            else:
                raise RuntimeError(
                    f"could not find a legal configuration in {n_configuration_tries} tries"
                )
            progress_bar.close()

    return pandas.DataFrame(results_dicts)


def calc_forward_derivative(y, x):
    return np.diff(y) / np.diff(x)


def plot_results(results):
    fig, [ax_E, ax_H] = plt.subplots(nrows=2, ncols=1, sharex=True)

    for mode, df_by_mode in results.groupby("mode"):
        for pack_frac, df_by_pack_frac in df_by_mode.groupby("pack_frac"):
            n_seeds = len(np.unique(df_by_pack_frac["config_seed"]))
            # mean/std over configurations to get an error estimate
            df_mean = df_by_pack_frac.groupby("test_radius").mean().reset_index()
            df_std = df_by_pack_frac.groupby("test_radius").std().reset_index()

            df_mean.sort_values(by="test_radius")

            radii = df_mean["test_radius"].to_numpy()
            exclusion_probs = df_mean["exclusion_prob"].to_numpy()
            exclusion_probs_SEM = df_std["exclusion_prob"].to_numpy() / np.sqrt(n_seeds)

            exprob_deriv = calc_forward_derivative(exclusion_probs, radii)

            ls = "--" if mode == "overlapping" else "-"
            color = "C0" if pack_frac > 0.3 else "C1"
            ax_E.errorbar(
                radii,
                exclusion_probs,
                yerr=exclusion_probs_SEM,
                ls=ls,
                color=color,
                label=f"{mode}, packing fraction = {pack_frac}",
            )
            ax_H.plot(
                radii[:-1],
                exprob_deriv,
                ls=ls,
                color=color,
                label=f"{mode}, packing fraction = {pack_frac}",
            )
    ax_E.legend()
    ax_H.set_xlabel("r / R")
    ax_E.set_ylabel("$E(r)$")
    ax_H.set_ylabel("$H(r)$")
    plt.tight_layout()

    return fig


def main():

    outfolder = pathlib.Path("/home/clohrmann/data/circle_packings").resolve() / "prod"
    outfolder.mkdir(parents=True, exist_ok=True)

    results = produce_data()
    results.to_json(outfolder/"raw_results.json")

    results = pandas.read_json(outfolder / "raw_results.json")
    fig = plot_results(results)
    fig.savefig(outfolder / "exclusion_prob.pdf")

    plt.show()


if __name__ == "__main__":
    main()
