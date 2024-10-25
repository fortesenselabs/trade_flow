## Environment 1
Environment - 1:
Data: Generated Sinewave
* Training: 5 peaks
* Evaluation: 2 peaks
* Testing: 3 peaks

Observation Space: 
* price values,
* price -> rolling mean (10 data points),
* price -> rolling mean (20 data points),
* price -> rolliong mean (30 data points),
* price -> log difference

Action Space: 
* buy-sell-hold

Reward Strategy: 
* position-based-return

## Algorithm Proximal Policy Proximation
More to write on here...

### Model
* batch size: The number of samples in our training set
* mini batch size: The number of samples we use to update the NN at one time
* num_sgd_iter the number of times we run a mini batch through the NN.
    * How much we train the NN to recognise this batch (observation, action and reward for action from observation)

## Strategies
### Strategy 1
This strategy uses the default `RLLIB` configurations for the PPO algorithm. These configurations includes the following:
* A simple MLP Neural Network model with [256, 256] hidden layers and a tanh activation function. 
* A batch size of 4000
* A mini-batch size of 128
* The number of times we sample a mini-batch from the batch and train it on the model (num_sgd_iter) is set to 30. 
    * Every epoch, we are training the NN with 30 minibatches of size 128 (30 * 128 = 4020). This effectively trains the NN on a number of samples equal to the entire batch size.

<b>Strategy Notes</b>:
* This model does not normalise the input data with a preprocessing layer, nor does it have any regularization methods (such as batch norm).
* This model flattens the inputs / observation space and forces each observation into the range [-1, 1]
* This model should perform poorly.

### Strategy 2
This strategy uses custom PPO configurations with the default model. The custom PPO configurations are:
* A batch size of 30
* A mini-batch size of 30 (I could try this with 10)
* The number of times we sample a mini-batch from the batch and train it on the model (num_sgd_iter) 1.

<b>Strategy Notes</b>:
* This model should suffer from the same pitfalls as the previous mode, but should train faster non-the less as all batch size related configurations are set more appropriately for the environment. 

### Strategy 3
This strategy implements the same custom PPO configurations as Strategy2, but it also implements a custom Neural Network with the following configurations:
* Number of Hidden layers [128, 128]
* A z-score normalisation prepocessing layer, which uses the mean and variance of the training data
* Batch normalization for regularization during training. 

<b>Strategy Notes</b>:
* This strategy must be run with Tensorflow V1, as V2 breaks the with they way that Is_training is passed into the batch norm layer. More on this can be found in the model file.

### Strategy 4
This strategy is exactly the same as Strategy 3, however, it uses a tensorflow methodoly, instead of a keras methadology and therefore can be trained with Tensorflow V2, but cannot be executed with eager graph tracing enabled. 

### Strategy 5
This is the same as strategy is 1, with a change made to the number of times we use a batch to train the model. (num_sgd_iter)
* num_sgd_iter = 1