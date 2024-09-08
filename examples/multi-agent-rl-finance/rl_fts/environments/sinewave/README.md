## Sine wave Environments
This folder contains all environments where the observation state (price history) follows a sinewave. 

## Data
We use a sinewave generator for creating the training, evaluation and training. The sinewave generator has the following inputs:
- x_sample: number of samples to generate,
- period: the number of periods (peaks) in the sinewave,
- amplitude: the amplitude of the sine wave,
- y_adjustment: how much to shift the sinewave by, (this helps with removing negative price values)
- d_ratio: the ratio to use for training, validating and testing

## Environments
Different environments have been created to use the mock price / sinewave data. These environments differ in either there observation space, action space, rewards space or all, or a combindation of them. More information on the the actions and reward schemes can be found in `rl_fts/tensortradeExtension/actions` and `rl_fts/tensortradeExtension/rewards` respectfully. The observation space is defined in the environment file itself. More about the environments can be found below.

---
## Environment 1
<b>Data</b>: Generated Sinewave
- Training: 5 peaks
- Evaluation: 2 peaks
- Testing: 3 peaks

<b>Observation Space</b>: 
- price values,
- price -> rolling mean (10 data points),
- price -> rolling mean (20 data points),
- price -> rolliong mean (30 data points),
- price -> log difference

<b>Action Space</b>: 
 - buy-sell-hold

<b>Reward Strategy</b>:
 - position-based-return

---

## Environment 2
<b>Data</b>: Generated Sinewave
- Training: 5 peaks
- Evaluation: 2 peaks
- Testing: 3 peaks

<b>Observation Space</b>: 
- price values,
- price -> rolling mean (10 data points),
- price -> rolling mean (20 data points),
- price -> rolliong mean (30 data points),
- price -> log difference

<b>Action Space</b>: 
- short-hold

<b>Reward Strategy</b>: 
- short-networth-change
---

## Environment 3
<b>Data</b>: Generated Sinewave
* Training: 5 peaks
* Evaluation: 2 peaks
* Testing: 3 peaks

<b>Observation Space</b>: 
* price values,
* price -> rolling mean (10 data points),
* price -> rolling mean (20 data points),
* price -> rolliong mean (30 data points),
* price -> log difference\

<b>Action Space</b>: 
* buy-sell-short-hold

<b>Reward Strategy</b>: 
* short-networth-change

---

## Environment 4
<b>Data</b>: Generated Sinewave
* Training: 5 peaks
* Evaluation: 2 peaks
* Testing: 3 peaks

<b>Observation Space</b>: 
* price values,
* price -> rolling mean (10 data points),
* price -> rolling mean (20 data points),
* price -> rolliong mean (30 data points),
* price -> log difference

<b>Action Space</b>: 
* proportion-buy-hold-sell

<b>Reward Strategy<b>: 
* net-worth-change
---

## Environment 5
<b>Data</b>: Generated Sinewave
* Training: 5 peaks
* Evaluation: 2 peaks
* Testing: 3 peaks

<b>Observation Space</b>: 
* price values,
* price -> rolling mean (10 data points),
* price -> rolling mean (20 data points),
* price -> rolliong mean (30 data points),
* price -> log difference

<b>Action Space</b>: 
* proportion-short-hold

<b>Reward Strategy</b>: 
* short-networth-change
---

## Environment 6
<b>Data</b>: Generated Sinewave
- Training: 5 peaks
- Evaluation: 2 peaks
- Testing: 3 peaks

<b>Observation Space</b>: 
- price values,
- price -> rolling mean (10 data points),
- price -> rolling mean (20 data points),
- price -> rolliong mean (30 data points),
- price -> log difference

<b>Action Space</b>: 
- proportion-buy-sell-short-hold

<b>Reward Strategy</b>: 
- short-networth-change
---

## Environment 7
<b>Data</b>: Generated Sinewave
- Training: 5 peaks
- Evaluation: 2 peaks
- Testing: 3 peaks

<b>Observation Space</b>: 
- price values

<b>Action Space</b>: 
- buy-sell-hold

<b>Reward Strategy</b>: 
- net-worth-change
---

## Environment 8
<b>Data</b>: Generated Sinewave
* Training: 5 peaks
* Evaluation: 2 peaks
* Testing: 3 peaks

<b>Observation Space</b>: 
- price values

<b>Action Space</b>: 
- buy-sell-hold

<b>Reward Strategy</b>: 
- net-worth-change
---