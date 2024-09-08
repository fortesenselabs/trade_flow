## Getting Started

You can get started testing on Google Colab or your local machine, by viewing our [many examples](https://github.com/fortesenselabs/trade_flow/tree/master/examples)

---

## Installation

TradeFlow requires Python >= 3.11.9 for all functionality to work as expected.

You can install the package from PyPi via pip or from the Github repo.

```bash
pip install trade_flow
```

OR

```bash
pip install git+https://github.com/fortesenselabs/trade_flow.git
```

## Docker

To run the commands below ensure Docker is installed. Visit https://docs.docker.com/install/ for more information

### Run Jupyter Notebooks

To run a jupyter notebook execute the following

```bash
make run-notebook
```

which will generate a link of the form 127.0.0.1:8888/?token=... Paste this link into your browsers and select the notebook you'd like to explore

### Build Documentation

To build documentation execute the following

```bash
make run-docs
```

### Run Test Suite

To run the test suite execute the following

```bash
make run-tests
```
