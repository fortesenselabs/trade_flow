"""
References:
    - http://inoryy.com/post/tensorflow2-deep-reinforcement-learning/#agent-interface
"""

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

TorchA2CTransition = namedtuple(
    "TorchA2CTransition", ["state", "action", "reward", "done", "value"]
)


@deprecated(
    version="1.0.4",
    reason="Builtin agents are being deprecated in favor of external implementations (ie: Ray)",
)
class TorchA2CAgent(Agent):
    def __init__(
        self,
        env: "TradingEnvironment",
        shared_network: nn.Module = None,
        actor_network: nn.Module = None,
        critic_network: nn.Module = None,
    ):
        self.env = env
        self.n_actions = env.action_space.n
        self.observation_shape = env.observation_space.shape

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.shared_network = shared_network or self._build_shared_network()
        self.actor_network = actor_network or self._build_actor_network()
        self.critic_network = critic_network or self._build_critic_network()

        self.shared_network.to(self.device)
        self.actor_network.to(self.device)
        self.critic_network.to(self.device)

        self.env.agent_id = self.id

    def _build_shared_network(self):
        network = nn.Sequential(
            nn.Conv1d(
                in_channels=self.observation_shape[0], out_channels=64, kernel_size=6, padding=2
            ),
            nn.Tanh(),
            nn.MaxPool1d(kernel_size=2),
            nn.Conv1d(in_channels=64, out_channels=32, kernel_size=3, padding=1),
            nn.Tanh(),
            nn.MaxPool1d(kernel_size=2),
            nn.Flatten(),
        )
        return network

    def _build_actor_network(self):
        actor_head = nn.Sequential(
            nn.Linear(self._get_shared_output_size(), 50),
            nn.ReLU(),
            nn.Linear(50, self.n_actions),
            nn.ReLU(),
        )
        return nn.Sequential(self.shared_network, actor_head)

    def _build_critic_network(self):
        critic_head = nn.Sequential(
            nn.Linear(self._get_shared_output_size(), 50),
            nn.ReLU(),
            nn.Linear(50, 25),
            nn.ReLU(),
            nn.Linear(25, 1),
            nn.ReLU(),
        )
        return nn.Sequential(self.shared_network, critic_head)

    def _get_shared_output_size(self):
        dummy_input = torch.zeros((1,) + self.observation_shape).to(self.device)
        return self.shared_network(dummy_input).shape[1]

    def restore(self, path: str, **kwargs):
        actor_filename: str = kwargs.get("actor_filename", None)
        critic_filename: str = kwargs.get("critic_filename", None)

        if not actor_filename or not critic_filename:
            raise ValueError(
                "The `restore` method requires a directory `path`, a `critic_filename`, and an `actor_filename`."
            )

        self.actor_network.load_state_dict(torch.load(path + actor_filename))
        self.critic_network.load_state_dict(torch.load(path + critic_filename))

    def save(self, path: str, **kwargs):
        episode: int = kwargs.get("episode", None)

        suffix = self.id[:7] + "__" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pth"
        actor_filename = "actor_network__" + suffix
        critic_filename = "critic_network__" + suffix

        torch.save(self.actor_network.state_dict(), path + actor_filename)
        torch.save(self.critic_network.state_dict(), path + critic_filename)

    def get_action(self, state: np.ndarray, **kwargs) -> int:
        threshold: float = kwargs.get("threshold", 0)
        rand = random.random()

        if rand < threshold:
            return np.random.choice(self.n_actions)
        else:
            state_tensor = torch.tensor(state[None, :], dtype=torch.float32).to(self.device)
            with torch.no_grad():
                logits = self.actor_network(state_tensor)
            return torch.argmax(logits, dim=-1).item()

    def _apply_gradient_descent(
        self,
        memory: ReplayMemory,
        batch_size: int,
        learning_rate: float,
        discount_factor: float,
        entropy_c: float,
    ):
        huber_loss = nn.SmoothL1Loss()
        wsce_loss = nn.CrossEntropyLoss()

        optimizer = optim.Adam(
            list(self.actor_network.parameters()) + list(self.critic_network.parameters()),
            lr=learning_rate,
        )

        transitions = memory.tail(batch_size)
        batch = TorchA2CTransition(*zip(*transitions))

        states = torch.tensor(batch.state, dtype=torch.float32).to(self.device)
        actions = torch.tensor(batch.action).to(self.device)
        rewards = torch.tensor(batch.reward, dtype=torch.float32).to(self.device)
        dones = torch.tensor(batch.done).to(self.device)
        values = torch.tensor(batch.value, dtype=torch.float32).to(self.device)

        returns = []
        exp_weighted_return = 0

        for reward, done in zip(rewards[::-1], dones[::-1]):
            exp_weighted_return = reward + discount_factor * exp_weighted_return * (1 - int(done))
            returns += [exp_weighted_return]

        returns = torch.tensor(returns[::-1], dtype=torch.float32).to(self.device)

        optimizer.zero_grad()

        state_values = self.critic_network(states).squeeze(-1)
        critic_loss_value = huber_loss(state_values, returns)

        critic_loss_value.backward()
        optimizer.step()

        optimizer.zero_grad()

        advantages = returns - values
        logits = self.actor_network(states)
        policy_loss_value = wsce_loss(logits, actions, weight=advantages)

        probs = torch.softmax(logits, dim=-1)
        entropy_loss_value = -(probs * torch.log(probs)).sum(dim=-1).mean()
        policy_total_loss_value = policy_loss_value - entropy_c * entropy_loss_value

        policy_total_loss_value.backward()
        optimizer.step()

    def train(
        self,
        n_steps: int = None,
        n_episodes: int = None,
        save_every: int = None,
        save_path: str = None,
        callback: callable = None,
        **kwargs,
    ) -> float:
        batch_size: int = kwargs.get("batch_size", 128)
        discount_factor: float = kwargs.get("discount_factor", 0.9999)
        learning_rate: float = kwargs.get("learning_rate", 0.0001)
        eps_start: float = kwargs.get("eps_start", 0.9)
        eps_end: float = kwargs.get("eps_end", 0.05)
        eps_decay_steps: int = kwargs.get("eps_decay_steps", 200)
        entropy_c: int = kwargs.get("entropy_c", 0.0001)
        memory_capacity: int = kwargs.get("memory_capacity", 1000)

        memory = ReplayMemory(memory_capacity, transition_type=TorchA2CTransition)
        episode = 0
        steps_done = 0
        total_reward = 0
        stop_training = False

        if n_steps and not n_episodes:
            n_episodes = np.iinfo(np.int32).max

        print("====      AGENT ID: {}      ====".format(self.id))

        while episode < n_episodes and not stop_training:
            state = self.env.reset()
            done = False

            print(
                "====      EPISODE ID ({}/{}): {}      ====".format(
                    episode + 1, n_episodes, self.env.episode_id
                )
            )

            while not done:
                threshold = eps_end + (eps_start - eps_end) * np.exp(-steps_done / eps_decay_steps)
                action = self.get_action(state, threshold=threshold)
                next_state, reward, done, _, _ = self.env.step(action)

                value = self.critic_network(
                    torch.tensor(state[None, :], dtype=torch.float32).to(self.device)
                ).squeeze(-1)

                memory.push(state, action, reward, done, value.item())

                state = next_state
                total_reward += reward
                steps_done += 1

                if len(memory) < batch_size:
                    continue

                self._apply_gradient_descent(
                    memory, batch_size, learning_rate, discount_factor, entropy_c
                )

                if n_steps and steps_done >= n_steps:
                    done = True
                    stop_training = True

            is_checkpoint = save_every and episode % save_every == 0

            if save_path and (is_checkpoint or episode == n_episodes):
                self.save(save_path, episode=episode)

            episode += 1

        mean_reward = total_reward / steps_done

        return mean_reward
