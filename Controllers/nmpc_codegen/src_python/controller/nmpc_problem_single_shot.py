import casadi as cd
from .casadi_code_generator import Casadi_code_generator as ccg

class Single_shot_definition:
    """ single shot nmpc defintion """
    def __init__(self,controller):
        self._controller=controller
        self._dimension=controller.model.number_of_inputs*controller.horizon
        self._period_steps = controller.model.step_number // (controller.model.number_of_inputs + 1)
        self._period = controller.model.period
        
    def generate_cost_function(self):
        initial_state = cd.SX.sym('initial_state', self._controller.model.number_of_states, 1)
        state_reference = cd.SX.sym('state_reference', self._controller.model.number_of_states, 1)
        input_reference = cd.SX.sym('input_reference', self._controller.model.number_of_inputs, 1)
        static_casadi_parameters = cd.vertcat(initial_state, state_reference, input_reference)

        constraint_weights = cd.SX.sym('constraint_weights', self._controller.number_of_constraints, 1)
        
        input_all_steps = cd.SX.sym('input_all_steps', self._controller.model.number_of_inputs*self._controller.horizon, 1)
        cost=cd.SX.sym('cost',1,1)
        cost=0

        current_state = initial_state
        number_inputs = self._controller.model.number_of_inputs
        for i in range(1,self._controller.horizon+1):
            input = input_all_steps[(i-1)*self._controller.model.number_of_inputs:i*self._controller.model.number_of_inputs]
            
            sum_of_input = 0
            for size in range(number_inputs):
                interval = input[size] * self._period / self._period_steps
                sum_of_input += input[size]
                for j in range(self._period_steps):
#                    current_state = self._controller.model.get_next_state(interval, current_state, input, size)

                    cost = cost + self._controller.generate_cost_constraints(current_state, input[size], size, constraint_weights)
            
            interval = (1 - sum_of_input) * self._period / self._period_steps
            for j in range(self._period_steps):
#                current_state = self._controller.model.get_next_state(interval, current_state, input, number_inputs)

                cost = cost + self._controller.generate_cost_constraints(current_state, 1 - sum_of_input, size + 1, constraint_weights)
            
            current_state = self._controller.model.period_solution(current_state, input)
            cost = cost + self._controller.stage_cost(current_state, input, i, state_reference, input_reference)

        (cost_function, cost_function_derivative_combined) = \
            ccg.setup_casadi_functions_and_generate_c(static_casadi_parameters, input_all_steps, constraint_weights, cost,\
                                                      self._controller.location)

        return (cost_function,cost_function_derivative_combined)

    @property
    def dimension(self):
        return self._dimension