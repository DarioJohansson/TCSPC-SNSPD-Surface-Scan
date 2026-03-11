

def raster_sequence(step_counter: dict, resolution: dict):
            # Motion algorithm
            for axis, value in step_counter.items():       ## Raster algorithm iterations: 4 works correctly now, finally
                if value < resolution[axis] - 1:
                    step_counter[axis] += 1
                    break
                else:
                    step_counter[axis] = 0
        
def snake_sequence(step_counter: dict, resolution: dict, direction: dict):

    for axis, value in step_counter.items():               ## snake algorithm iteration: 1. seems logic, probably isn't. also, probably some strange bugs with 3+ axes.
        # Normal operating condition
        if  value + direction[axis] >= 0 and  value + direction[axis] < resolution[axis]:
            step_counter[axis] += direction[axis]       # add +1 or -1 to the counter normally.
            break
        # Turning condition:
        # Predictive check if the next step will be in the resolution interval
        elif value + direction[axis] >= resolution [axis] or value + direction[axis] < 0:
            direction[axis] *= -1                       # invert sign of the direction for the axis.

