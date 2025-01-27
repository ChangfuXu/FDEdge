import numpy as np
import collections
from scipy import stats


class OffloadEnvironment:
    def __init__(self, num_tasks, bit_range, num_BSs, time_slots_, es_capacities):
        # INPUT DATA
        self.n_tasks = num_tasks  # The number of mobile devices
        self.n_BSs = num_BSs  # The number of base station or edge server
        self.time_slots = time_slots_  # The number of time slot set
        self.duration = 1  # The length of each time slot t. Unit: seconds
        self.ES_capacities = es_capacities  # GHz or Gigacycles/s
        np.random.seed(5)
        self.tran_rate_BSs = np.random.randint(400, 501, size=[self.n_BSs])  # Mbits/s
        # Set the computing density of each required diffusion step in the range (100, 300) # Cycles/step
        np.random.seed(1)
        self.comp_density = np.random.uniform(0.1024, 0.3072, size=[self.n_tasks])  # Gigacycles/step

        # Initialize the array to storage all the arrival tasks bits in the system
        self.tasks_bit = []
        self.min_bit = bit_range[0]
        self.max_bit = bit_range[1]

        # Initialize the array to storage the queue workload lengths of all ESs
        self.proc_queue_len = np.zeros([self.time_slots + 1, self.n_BSs])  # Gigacycles
        # Initialize an array to storage the queue workload lengths before processing current task in all ESs
        self.proc_queue_bef = np.zeros([self.time_slots + 1, self.n_BSs])  # Gigacycles

    def reset(self, tasks_bit):
        self.tasks_bit = tasks_bit
        # Initialize the array to storage the queue workload lengths of all ESs
        self.proc_queue_len = np.zeros([self.time_slots + 1, self.n_BSs])  # Gigacycles
        # Initialize an array to storage the queue workload lengths before processing current task in all ESs
        self.proc_queue_bef = np.zeros([self.time_slots + 1, self.n_BSs])  # Gigacycles

    # Perform task offloading to achieve:
    # (1) Service delays;
    # (2) The queue workload lengths of arrival tasks in all ES.
    def step(self, t, b, n):
        opt_action = []
        min_service_delay = 1000
        for i in range(self.n_BSs):
            action = i
            wait_delay = (self.proc_queue_len[t][action] + self.proc_queue_bef[t][action]) / self.ES_capacities[action]
            if action == b:  # The transmission delay equals to 0 when task is processed at local BS b
                # Calculate the total transmission and computing delay of task n.
                tran_comp_delays = (self.comp_density[n] * self.tasks_bit[t][b][n] / self.ES_capacities[action])
            else:  # The transmission delay not equals to 0 when task is processed at other BS
                # Calculate the total transmission and computing delay of task n
                tran_comp_delays = (self.tasks_bit[t][b][n] / self.tran_rate_BSs[action] +
                                    self.comp_density[n] * self.tasks_bit[t][b][n] / self.ES_capacities[action])

            service_delay = tran_comp_delays + wait_delay  # Set the delay
            if service_delay < min_service_delay:
                min_service_delay = service_delay
                opt_action = action

        # Update the processing queue workload lengths at the selected ESs before processing next task
        self.proc_queue_bef[t][opt_action] = (self.proc_queue_bef[t][opt_action] +
                                              self.comp_density[n] * self.tasks_bit[t][b][n])

        return min_service_delay

    def step_(self, t, n):
        opt_action = []
        min_service_delay = 1000
        for i in range(self.n_BSs):
            action = i
            wait_delay = (self.proc_queue_len[t][action] + self.proc_queue_bef[t][action]) / self.ES_capacities[action]
            # Calculate the total transmission and computing delay of task n
            tran_comp_delays = (self.tasks_bit[t][n] / self.tran_rate_BSs[action] +
                                self.comp_density[n] * self.tasks_bit[t][n] / self.ES_capacities[action])

            service_delay = tran_comp_delays + wait_delay  # Set the delay
            if service_delay < min_service_delay:
                min_service_delay = service_delay
                opt_action = action

        # Update the processing queue workload lengths at the selected ESs before processing next task
        self.proc_queue_bef[t][opt_action] = (self.proc_queue_bef[t][opt_action] +
                                              self.comp_density[n] * self.tasks_bit[t][n])

        return min_service_delay

    # Update the processing queue length of all ESs at the beginning of next time slot.
    def update_proc_queues(self, t):
        for b in range(self.n_BSs):
            self.proc_queue_len[t + 1][b] = np.max(
                [self.proc_queue_len[t][b] + self.proc_queue_bef[t][b] - self.ES_capacities[b] * self.duration, 0])
