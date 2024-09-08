## Environment 1
Environment - 1:
Data: Stock NFLX Sinewave
* Training: 5 years (1260 days)
* Evaluation: 3 years (756 days)
* Testing: 2 years

Observation Space: 
* price values,
* price -> rolling mean (10 data points),
* price -> rolling mean (20 data points),
* price -> rolliong mean (30 data points),
* price -> log difference

Action Space: 
* buy-sell-hold

Reward Strategy: 
* proportion-net-worth-change

## Algorithm Proximal Policy Proximation
More to write on here...

### Model
* batch size: The number of samples in our training set
* mini batch size: The number of samples we use to update the NN at one time
* num_sgd_iter the number of times we run a mini batch through the NN.

## Strategies
### Strategy 1
This strategy uses applies a custom PPO algorithm to environment 1 with the following configurations:
* An MLP with [128, 128] hidden layers and a tanh activation function. 
* A batch size of 1260
* A mini-batch size of 128
* num_sgd_iter = 10

<b>Strategy Notes</b>:
* When considering the constraints of the environment, this performs pretty well and develops a buy and hold trading strategy. Things to note are that the environment is a 100% buy or 100% sell.
* The agent agent takes advantage of the macro upward trend, but does not take advantage of micro downward trends.
* Many different directions to go from here, first steps are to see if adding more hidden layers or hidden nodes increases performance.

### Strategy 2
This strategy uses applies a custom PPO algorithm to environment 1 with the following configurations:
* An MLP with [128, 128, 128] hidden layers and a tanh activation function. 
* A batch size of 1260
* A mini-batch size of 128
* num_sgd_iter = 10

<b>Strategy Notes</b>:
* This model behaves effectively the same as the one from strategy1

### Strategy 3
This strategy uses applies a custom PPO algorithm to environment 1 with the following configurations:
* An MLP with [256, 256] hidden layers and a tanh activation function. 
* A batch size of 1260
* A mini-batch size of 128
* num_sgd_iter = 10

<b>Strategy Notes</b>:
* Next steps are to test an environmet which is not 100% buy or 100% sell.
* We could also test a 100% short or hold environment, but I expect it will suffer from a similar pitfall and not pick up the micro trends.
