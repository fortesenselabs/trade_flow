from deprecated import deprecated
import torch
import torch.nn as nn
import torch.optim as optim
from multiprocessing import Process, Queue
from trade_flow.agents import ReplayMemory, DQNTransition
from trade_flow.agents.deprecated.parallel import ParallelDQNModel


@deprecated(
    version="1.0.4",
    reason="Builtin agents are being deprecated in favor of external implementations (ie: Ray)",
)
class ParallelDQNOptimizer(Process):
    def __init__(
        self,
        model: "ParallelDQNModel",
        n_envs: int,
        memory_queue: Queue,
        model_update_queue: Queue,
        done_queue: Queue,
        discount_factor: float = 0.9999,
        batch_size: int = 128,
        learning_rate: float = 0.001,
        memory_capacity: int = 10000,
    ):
        super().__init__()

        self.model = model
        self.n_envs = n_envs
        self.memory_queue = memory_queue
        self.model_update_queue = model_update_queue
        self.done_queue = done_queue
        self.discount_factor = discount_factor
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.memory_capacity = memory_capacity

    def run(self):
        memory = ReplayMemory(self.memory_capacity, transition_type=DQNTransition)

        # Optimization strategy.
        optimizer = optim.Adam(self.model.policy_network.parameters(), lr=self.learning_rate)

        loss_fn = nn.SmoothL1Loss()  # Equivalent to Huber loss

        while self.done_queue.qsize() < self.n_envs:
            while self.memory_queue.qsize() > 0:
                sample = self.memory_queue.get()
                memory.push(*sample)

            if len(memory) < self.batch_size:
                continue

            transitions = memory.sample(self.batch_size)
            batch = DQNTransition(*zip(*transitions))

            state_batch = torch.tensor(batch.state, dtype=torch.float32)
            action_batch = torch.tensor(batch.action, dtype=torch.int64)
            reward_batch = torch.tensor(batch.reward, dtype=torch.float32)
            next_state_batch = torch.tensor(batch.next_state, dtype=torch.float32)
            done_batch = torch.tensor(batch.done, dtype=torch.bool)

            # Set the model to training mode
            self.model.policy_network.train()

            # Compute Q-values for the current states
            state_action_values = (
                self.model.policy_network(state_batch)
                .gather(1, action_batch.unsqueeze(-1))
                .squeeze(-1)
            )

            # Compute Q-values for the next states
            next_state_values = torch.zeros(self.batch_size)
            next_state_values[~done_batch] = (
                self.model.target_network(next_state_batch[~done_batch]).max(1)[0].detach()
            )

            # Calculate expected Q-values
            expected_state_action_values = reward_batch + (self.discount_factor * next_state_values)

            # Compute loss
            loss_value = loss_fn(state_action_values, expected_state_action_values)

            # Backpropagate the loss
            optimizer.zero_grad()
            loss_value.backward()
            optimizer.step()

            # Send the updated model to the queue
            self.model_update_queue.put(self.model)
