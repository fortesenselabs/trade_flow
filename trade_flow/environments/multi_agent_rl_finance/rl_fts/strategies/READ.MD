# Strategies
This is a Work In Progress, as there will be allot more to add here...

A strategy is framed a solution to solving an environment. Each environment has one or more strategies for solving it. A strategy is the application of a Deep Reinforcement learning algorithm, applied to an environment. The Deep Reinforcement learning algorithm may (and should) take advantage of a custom Neural Network Model. These models are defined in a subdirectory per strategy/environment combination (e.g., `/rl_fts/strategies/sinewave/environment1/models/model1.py`).

Something to note is that a strategy may influence an environment through environment settings, i.e, setting the horizon value and whether it is hard or soft. This logic should technically be moved out to be specified for an environment, however I am technically viewing it as a parameter which the strategy can choose for solving the environment (which is probably bad). 

## Deep Reinforcement Learning
For rapidly developing and evaluating strategies, we take advantage of a production ready Deep Reinforcement Learning framework called ray. Ray implements efficient and customisable deep reinforcement learning algorithims that can be trained locally, on a cluster or in the cloud. For the purpose of my masters, I am training locally and almost exclusivley using ray's implementation of PPO (Proximal Policy Opitmisation). The goal is to have a custom model defined per `/strategy/environment` combination. This model may abstracted to have all parameters defined on the strategy level.

## Training a Strategy
Each strategy loads an environment and a deep reinfocement learning algirithm, both with some evironment specific configurations. Ray then applies the ray.tune() execution to the current run configuration and starts training an agent to solve the environment. The training progress will be shown in the terminal and a plot of an evalution will stored in the logs directory, for every epoch/iteration. The training logs can be accessed with `tensorboard` by running `tensorboard --logdir logs/` from the root directory. There is the potential for strategies to implement hyperparameter tuning and this may be explored at a later stage. 

## Training Evaluation
Policies are evaluated throughout the training run. The evaluation occurs at intervals of 10% * max epoch. These evalutions can be viewed in tensorboard. More specifically, plots of the evaluation runs can be found on the images tab in tensorboard.
## Evaluating a Strategy
More to write here...