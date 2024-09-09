from deprecated import deprecated
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import namedtuple

from trade_flow.agents.deprecated import Agent, ReplayMemory
from datetime import datetime

from trade_flow.environments.generic import TradingEnvironment


TorchDQNTransition = namedtuple(
    "TorchDQNTransition", ["state", "action", "reward", "next_state", "done"]
)


@deprecated(
    version="1.0.4",
    reason="Builtin agents are being deprecated in favor of external implementations (ie: Ray)",
)
class TorchDQNAgent(Agent):
    """

    References:
    ===========
        - https://towardsdatascience.com/deep-reinforcement-learning-build-a-deep-q-network-dqn-to-play-cartpole-with-tensorflow-2-and-gym-8e105744b998
        - https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html#dqn-algorithm
        - https://arxiv.org/abs/1802.00308
    """

    def __init__(self, env: "TradingEnvironment", policy_network: nn.Module = None):
        self.env = env
        self.n_actions = env.action_space.n
        self.observation_shape = env.observation_space.shape

        self.policy_network = policy_network or self._build_policy_network()
        self.target_network = self._build_policy_network()
        self.target_network.load_state_dict(self.policy_network.state_dict())
        self.target_network.eval()

        self.env.agent_id = self.id

    def _build_policy_network(self):
        class PolicyNetwork(nn.Module):
            def __init__(self, input_shape, n_actions):
                super(PolicyNetwork, self).__init__()
                self.conv1 = nn.Conv1d(input_shape[0], 64, kernel_size=6, stride=2)
                self.conv2 = nn.Conv1d(64, 32, kernel_size=3, stride=2)
                self.fc1 = nn.Linear(32 * ((input_shape[1] // 4) // 2), n_actions)
                self.fc2 = nn.Linear(n_actions, n_actions)

            def forward(self, x):
                x = torch.tanh(self.conv1(x))
                x = torch.tanh(self.conv2(x))
                x = x.view(x.size(0), -1)  # flatten the tensor
                x = torch.sigmoid(self.fc1(x))
                return torch.softmax(self.fc2(x), dim=-1)

        return PolicyNetwork(self.observation_shape, self.n_actions)

    def restore(self, path: str, **kwargs):
        self.policy_network.load_state_dict(torch.load(path))
        self.target_network.load_state_dict(self.policy_network.state_dict())

    def save(self, path: str, **kwargs):
        filename = f"policy_network__{self.id[:7]}__{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
        torch.save(self.policy_network.state_dict(), path + filename)

    def get_action(self, state: np.ndarray, **kwargs) -> int:
        threshold: float = kwargs.get("threshold", 0)
        rand = random.random()

        if rand < threshold:
            return np.random.choice(self.n_actions)
        else:
            with torch.no_grad():
                state_tensor = torch.tensor(np.expand_dims(state, 0), dtype=torch.float32)
                return torch.argmax(self.policy_network(state_tensor)).item()

    def _apply_gradient_descent(
        self, memory: ReplayMemory, batch_size: int, learning_rate: float, discount_factor: float
    ):
        # Optimization strategy.
        optimizer = optim.Adam(self.policy_network.parameters(), lr=learning_rate)
        loss_fn = nn.SmoothL1Loss()

        transitions = memory.sample(batch_size)
        batch = TorchDQNTransition(*zip(*transitions))

        state_batch = torch.tensor(batch.state, dtype=torch.float32)
        action_batch = torch.tensor(batch.action, dtype=torch.long).unsqueeze(1)
        reward_batch = torch.tensor(batch.reward, dtype=torch.float32)
        next_state_batch = torch.tensor(batch.next_state, dtype=torch.float32)
        done_batch = torch.tensor(batch.done, dtype=torch.float32)

        # Compute Q values for the current state
        state_action_values = self.policy_network(state_batch).gather(1, action_batch).squeeze()

        # Compute the target Q values
        with torch.no_grad():
            next_state_values = torch.zeros(batch_size)
            next_state_values[~done_batch] = self.target_network(next_state_batch).max(1)[0]
        expected_state_action_values = reward_batch + (discount_factor * next_state_values)

        # Compute loss
        loss_value = loss_fn(state_action_values, expected_state_action_values)

        # Optimize the policy network
        optimizer.zero_grad()
        loss_value.backward()
        optimizer.step()

    def train(
        self,
        n_steps: int = 1000,
        n_episodes: int = 10,
        save_every: int = None,
        save_path: str = "agent/",
        callback: callable = None,
        **kwargs,
    ) -> float:
        batch_size: int = kwargs.get("batch_size", 256)
        memory_capacity: int = kwargs.get("memory_capacity", n_steps * 10)
        discount_factor: float = kwargs.get("discount_factor", 0.95)
        learning_rate: float = kwargs.get("learning_rate", 0.01)
        eps_start: float = kwargs.get("eps_start", 0.9)
        eps_end: float = kwargs.get("eps_end", 0.05)
        eps_decay_steps: int = kwargs.get("eps_decay_steps", n_steps)
        update_target_every: int = kwargs.get("update_target_every", 1000)
        render_interval: int = kwargs.get("render_interval", n_steps // 10)

        memory = ReplayMemory(memory_capacity, transition_type=TorchDQNTransition)
        episode = 0
        total_steps_done = 0
        total_reward = 0
        stop_training = False

        if n_steps and not n_episodes:
            n_episodes = np.iinfo(np.int32).max

        print("====      AGENT ID: {}      ====".format(self.id))

        while episode < n_episodes and not stop_training:
            state = self.env.reset()
            done = False
            steps_done = 0

            while not done:
                threshold = eps_end + (eps_start - eps_end) * np.exp(
                    -total_steps_done / eps_decay_steps
                )
                action = self.get_action(state, threshold=threshold)
                next_state, reward, done, _ , _= self.env.step(action)

                memory.push(state, action, reward, next_state, done)

                state = next_state
                total_reward += reward
                steps_done += 1
                total_steps_done += 1

                if len(memory) < batch_size:
                    continue

                self._apply_gradient_descent(memory, batch_size, learning_rate, discount_factor)

                if n_steps and steps_done >= n_steps:
                    done = True

                if render_interval is not None and steps_done % render_interval == 0:
                    self.env.render(episode=episode, max_episodes=n_episodes, max_steps=n_steps)

                if steps_done % update_target_every == 0:
                    self.target_network.load_state_dict(self.policy_network.state_dict())

            is_checkpoint = save_every and episode % save_every == 0

            if save_path and (is_checkpoint or episode == n_episodes - 1):
                self.save(save_path, episode=episode)

            if not render_interval or steps_done < n_steps:
                self.env.render(episode=episode, max_episodes=n_episodes, max_steps=n_steps)

            self.env.save()

            episode += 1

        mean_reward = total_reward / episode
        return mean_reward
