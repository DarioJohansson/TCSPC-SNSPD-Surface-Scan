   def next_step_in_sequence(self) -> tuple[dict, list[dict]]|None:
        
        def diff_positions(old: dict, new: dict) -> list:
            changes = []
            for key, new_value in new.items():
                old_value = old.get(key)
                if old_value != new_value:
                    changes.append({"axis": key, "position": new_value})
            return changes
        
        old_position_vector = self.position

        # Next Step Index calculation        
        if self.step_counter != {axis: self.resolution[axis] - 1 for axis in self.active_axes}:
            
            axis_idx_map = {key: i for i, key in enumerate(self.step_counter)}
            asse_riferimento = axis_idx_map.get(1)
            
            for index, axis in enumerate(self.step_counter):       ## Algorithm iterations: 4 works correctly now, finally
                value = self.step_counter[axis]

                '''
                if value < self.resolution[axis] - 1:
                    self.step_counter[axis] += 1
                    break
                else:
                    self.step_counter[axis] = 0
                '''
            # Now convert indexes to positions via the step size matrix 
            new_position_vector = {axis: round(self.step_counter[axis] * self.step_size[axis], 9) for axis in self.active_axes}
            self.position = new_position_vector
            index_vector = self.step_counter
            motion_instructions = diff_positions(old_position_vector, new_position_vector)

            # Finally return the index vector and the instructions for motion.
            return index_vector, motion_instructions                # return signature iterations: at least 10 now.. my god. this should work, since the 
                                                                    # index vector is used by data input functions to put data in the right matrix slots
                                                                    # and instructions are interpreted by the positioner motion function.
        
        
        else:           # once scan is over, the sequences flips it's flag and outside functions can tell the sequence is over, to stop looping.
            self.step_counter = {axis: 0 for axis in self.active_axes}
            self.position = self.step_counter
            return None