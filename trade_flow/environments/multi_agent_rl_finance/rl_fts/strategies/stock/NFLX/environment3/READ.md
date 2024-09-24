## Environment 3
Environment - 3:
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
* proportional-sell-hold

Reward Strategy: 
* proportion-net-worth-change

### Model
* batch size: The number of samples in our training set
* mini batch size: The number of samples we use to update the NN at one time
* num_sgd_iter the number of times we run a mini batch through the NN.

## Strategies
### Strategy 1
This strategy uses applies a custom PPO algorithm to environment 1 with the following configurations:
* An MLP with [128, 128] hidden layers and a relu activation functions. 
* A batch size of 1260
* A mini-batch size of 128
* num_sgd_iter = 100
