# What is this?

This is an implementation of my masters thesis. It relies on the `tensortrade` for setting up financial RL environments and `Rlib` for RL agent implementations. My masters thesis has the goal of combining multiple trading RL algorithms, each trainined on different data types, to create a more sofisticated and greater performing algorithm. To achieve this goal, I will be creating trading strategies. Each trading strategy will produce an RL algorithm. Strategies may encorporate previous strategies.

# Repository Structure

- **.vscode** contains opinionated vscode settings for debugging and formatting.
- **environments** financial trading rl environements.
- **strategies** strategies implemented to train DRL agents on a specified environment.
- **logs** training logs for strategies.
- **rayExtensions** classes which extend the behaviour of the ray framework.
- **tensortrade** extensions made to plug into the tensortrade framework.

## Strategies

If an environment represents a problem, a strategy represents a solution for solving the environment. Strageies apply deep reinforcement learning algorithms to environments. Strategies are separated into the domains of environments that they are solving. Each environment domain has one or more strategies for solving it. Strategies may make use of custom models for their deep reinforcement learning algorithms.

# Install Instructions

1. Install Anaconda and create a new environment for this projects dependencies
2. Attemp to install from the environment.yml for conda. If it works great, if it doesn't, follow the next steps.
3. Install Ray RLlib from the official installation instructions
4. Install tensortrade

# Apple silicon (m1), Install Instructions

1. Install Anaconda and create a new environment for this projects dependancies
2. Attemp to install from the environment.yml for conda. If it works great, if it doesn't,
3. Install Ray Rlib, follow the apple silicon instructions from the official website
4. Install tensortrade for apple silicon
5. Download the tensortrade repository, comment out tensotrade from the requirements.txt and install all depedencies.
6. You're good to go.

# Viewing Experiments

Experiments can be viewed in tensorboard. This can be viewed buy running the following:
`tensorboard --logdir logs/`

# Algorithm Information

## RL Algorithm

Model is PPO

## Policy Model

# Notes:

- Update the batch size to something reasonable
- update the number of workers
- find out what a env spec should look like (specifically the ID)

# TODO:

## Other TODO

- update reward scheme from simple net worth change to something which includes risk, position-time and other useful evaluators identified in my research.
- update network architecture to use LSTM
- update network architecture to use Attention
- implement a strategy on stock data
  - Setup preprocessing:
    - generate technical indicators
    - identify corelation & remove duplicates
    - normalise the data set
    - implement a function to un-normalise the dataset for rendering
- implement a strategy on fundamental data
- implement a strategy which utilises multi-agent rl
- implement a strategy which utilises hierarchical rl for quantity selection and stock action
  - implement a new strategy as an action selection strategy which specifies an amount of stock to buy / sell / short

**future additions**

- Add a stock picking rl agent who's trained to select the best stock at a specified period
  - Add this rl agent as a new level to the hierarchical rl agent.
