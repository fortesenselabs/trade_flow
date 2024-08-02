from trade_flow.agents.dqn import DqnAgent
import ray


if __name__ == "__main__":
    # Initialize Ray
    ray.init(ignore_reinit_error=True)

    # Define environment and configuration
    env_name = "CartPole-v1"
    config = {
        "num_workers": 1,
        "lr": 1e-3,
        "train_batch_size": 64,
        "learning_starts": 1000,
        "target_network_update_freq": 500,
        "exploration_final_eps": 0.02,
        "exploration_fraction": 0.1,
    }

    # Create and train the agent
    agent = DqnAgent(env_name=env_name, config=config)
    for _ in range(10):  # Train for 10 iterations
        agent.train()

    # Evaluate the agent
    results = agent.evaluate()
    print(results)

    # Save the agent
    agent.save("dqn_checkpoint")

    # Load the agent
    agent.load("dqn_checkpoint")

    # Shutdown Ray
    ray.shutdown()
