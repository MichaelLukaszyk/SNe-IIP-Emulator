import astropy.units as u
import numpy as np

def no_exception(f, v):
    success = True
    try:
        f(v)
    except Exception as e:
        success = False
    return success

def find_range(f, guess, fail_range, converge_diff, step_up_size, step_down_size = None, min = None, max = None):
    """
    Finds the minimum and maximum values for which the passed function successfully runs.
    Returns dictionary {"max": value, "min": value} or None if fails within fail_range of guess.
    """
    
    if step_down_size == None:
        step_down_size = step_up_size
    
    # Remove units for Quantity objects
    units = 1
    if type(guess) == u.Quantity:
        units = guess.unit
        fail_range = fail_range.to(units).value
        step_up_size = step_up_size.to(units).value
        step_down_size = step_down_size.to(units).value
        converge_diff = converge_diff.to(units).value
        if min != None:
            min = min.to(units).value
        if max != None:
            max = max.to(units).value
        guess = guess.value

    # First find starting value that works
    start = None
    for dx in (0, fail_range, -fail_range):
        x = guess + dx
        if start == None and no_exception(f, x * units):
            start = x

    if start:
        MAX = None
        MIN = None

        # Find upper bound
        upper = None
        lower = start
        value = start + step_up_size
        while True:
            if no_exception(f, value * units):
                lower = value
                if upper != None:
                    if np.abs(upper - lower) < converge_diff:
                        MAX = lower
                        break
                    else:
                        value = (upper + lower) / 2
                else:
                    value += step_up_size
                if max != None and lower > max:
                    MAX = max
                    break
            else:
                upper = value
                if np.abs(upper - lower) < converge_diff:
                    MAX = lower
                    break
                else:
                    value = (upper + lower) / 2

        # Find lower bound
        upper = start
        lower = None
        value = start - step_down_size
        while True:
            if no_exception(f, value * units):
                upper = value
                if lower != None:
                    if np.abs(upper - lower) < converge_diff:
                        MIN = upper
                        break
                    else:
                        value = (upper + lower) / 2
                else:
                    value -= step_down_size
                if min != None and upper < min:
                    MIN = min
                    break
            else:
                lower = value
                if np.abs(upper - lower) < converge_diff:
                    MIN = upper
                    break
                else:
                    value = (upper + lower) / 2
                
        return {
            "max": MAX * units,
            "min": MIN * units
        }
    else:
        return None

def step_through(f, start, step_size, min, max):
    """
    Runs the passed function over the defined grid until the function no longer returns a value, then
    returns a dictionary of format {value:f(value), ..} or None if no values found around start.
    """

    # Copy value if using Quantity objects
    v = None
    if type(start) == u.Quantity:
        v = start.copy()
    else:
        v = start

    data = {}
    while max == None or v <= max:
        result = f(v)
        if result != None:
            data[v] = result
            v += step_size
        else:
            break

    v = start - step_size
    while min == None or v >= min:
        result = f(v)
        if result != None:
            data[v] = result
            v -= step_size
        else:
            break
    
    if data:
        return data
    else:
        return None
    
from param_space import utilities, config
import json

def step_through_space(f, output_path, data, i = 0):
    """
    Steps through the parameter space of the passed function using the passed data as initial values.
    The parameter space is defined as where the passed function successfully executes.
    All successful runs are logged to the output_path, where the data passed to the function is written.
    """

    data = data.copy()
    key = list(data.keys())[i]
    i += 1

    # Run step_run for each value of the key
    def step_run(v):
        data[key] = v
        if i == len(data):
            success = no_exception(f, data)
            if success:
                # Write to file
                with open(output_path, "a") as out_file:
                    copy = data.copy()
                    json.dump(utilities.convert_quantities(copy), out_file)
                    out_file.write("\n")
            return success or None
        else:
            return step_through_space(f, output_path, data, i)
    
    # Check if initial guess function provided
    start = data[key]
    if callable(start):
        start = start(data)
    return step_through(
        step_run,
        start,
        **config.step_config[key]
    )

def step_through_space_extrema(f, output_path, data, i = 0):
    """
    Similar to step_through_space, except the final data entry is extremized, the min and max values
    are recorded. This is more computationally efficient if you're only interested in finding the
    extrema at which the function fails.
    """

    data = data.copy()
    key = list(data.keys())[i]
    i += 1

    if i < len(data):
        # Run step_run for each value of the key
        def step_run(v):
            data[key] = v
            return step_through_space_extrema(f, output_path, data, i)
        
        # Check if initial guess function provided
        start = data[key]
        if callable(start):
            start = start(data)
        return step_through(
            step_run,
            start,
            **config.step_config[key]
        )
    else:
        # Do range run on final
        def range_run(v):
            data[key] = v
            return f(data)
        
        # Check if initial guess function provided
        start = data[key]
        if callable(start):
            start = start(data)
        entry = find_range(
            range_run,
            start,
            **config.range_config[key]
        )
        if entry != None:
            # Write to file
            copy = data.copy()
            copy[key] = entry
            
            with open(output_path, "a") as out_file:
                json.dump(utilities.convert_quantities(copy), out_file)
                out_file.write("\n")
        return entry