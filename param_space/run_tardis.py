from tardis.io.configuration.config_reader import Configuration
from tardis.simulation import Simulation
from tardis.io.atom_data.base import AtomData
from param_space import utilities
import os

os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"
os.environ["NUMEXPR_NUM_THREADS"] = "4"

def run_tardis(params):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    atomic = AtomData.from_hdf(os.path.join(current_dir, "tardis_data/atom_data.h5"))
    config = Configuration.from_yaml(os.path.join(current_dir, "tardis_data/base_config.yml"))
    
    for name, value in params.items():
        if name == "lum":
            config.supernova.luminosity_requested = value
        elif name == "log_lsun":
            config.supernova.luminosity_requested = utilities.from_loglsun(value)
        elif name == "t_exp":
            config.supernova.time_explosion = value
        elif name == "v_start":
            config.model.structure.velocity.start = value
        elif name == "t_inner":
            config.plasma.initial_t_inner = value

    config.model.structure.velocity.stop = config.model.structure.velocity.start * 3

    sim = Simulation.from_config(
        config,
        atom_data = atomic,
        log_level="CRITICAL"
    )
    sim.run_convergence()
    sim.run_final()

import astropy.units as u

def run_tardis_test(params):
    for name, value in params.items():
        if name == "lum":
            v = utilities.to_loglsun(value)
            if v > 10.21 or v < 8.745:
                raise ValueError
        elif name == "log_lsun":
            if value > 10.21 or value < 8.745:
                raise ValueError
        elif name == "t_exp":
            if value > 21 * u.day or value < 4 * u.day:
                raise ValueError
        elif name == "v_start":
            if value > 22500 * u.km/u.s or value < 4000 * u.km/u.s:
                raise ValueError
        elif name == "t_inner":
            if value > 35000 * u.K or value < 12000 * u.K:
                raise ValueError