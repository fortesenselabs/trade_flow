# Resources

This section provides a curated list of resources for building a trading platform leveraging machine learning and quantitative analysis techniques.

**Algorithmic Trading**

- https://youtu.be/BRUlSm4gdQ4?si=gI9e4PcNiPkDbtcJ
- https://youtu.be/pRurbL9-Lus?si=f4LPI17CbRLuQENO
- [Books](./books/): Contains books about algorithmic trading.

**Open-Source Frameworks and Libraries**

- **Trading Strategies:**
  - **tensortrade:** A flexible backtesting framework for machine learning-based trading strategies (GitHub: [https://github.com/tensortrade-org/tensortrade](https://github.com/tensortrade-org/tensortrade)).
  - **freqtrade:** A modular crypto trading bot with a focus on backtesting and hyperparameter optimization (GitHub: [https://github.com/freqtrade](https://github.com/freqtrade)).
  - **OctoBot:** A customizable algorithmic trading framework with support for various exchanges and strategies (GitHub: [https://github.com/topics/algorithmic-trading-python](https://github.com/topics/algorithmic-trading-python)).
  - **intelligent-trading-bot:** A research project exploring reinforcement learning for stock trading (GitHub: [https://github.com/aruancaf/stock-trading-bot](https://github.com/aruancaf/stock-trading-bot)).
  - **releat:** A Python library for backtesting trading strategies (GitHub: [https://github.com/repeats/Repeat/releases](https://github.com/repeats/Repeat/releases)).
- **Machine Learning Libraries:**
  - **tensorflow-rl:** A collection of libraries built on TensorFlow for implementing various reinforcement learning algorithms (GitHub: [https://github.com/marload/DeepRL-TensorFlow2](https://github.com/marload/DeepRL-TensorFlow2)).
  - **RL_StockTrader-TFAgents:** An example project using TensorFlow Agents for building a stock trading bot (GitHub: [https://github.com/tensorflow/agents](https://github.com/tensorflow/agents)).
- **Additional Resources:**
  - **CodeFromVideo:** A collection of code examples from algorithmic trading video tutorials (GitHub: [https://github.com/chrisconlan/algorithmic-trading-with-python](https://github.com/chrisconlan/algorithmic-trading-with-python)).
  - **machine-learning-for-trading:** A comprehensive GitHub repository exploring various machine-learning techniques for trading (GitHub: [https://github.com/stefan-jansen/machine-learning-for-trading](https://github.com/stefan-jansen/machine-learning-for-trading)).
  - https://github.com/jiewwantan/StarTrader/
  - https://github.com/releat215/releat/tree/dev
  - https://github.com/emoen/Machine-Learning-for-Asset-Managers

**Hardware and Infrastructure**

- **epochfin:** A cloud-based platform for financial data, analytics, and machine learning (Epoch: [https://www.epochfin.com/](https://www.epochfin.com/)).

**Deep Learning Frameworks**

- **PyTorch:** A powerful open-source framework for deep learning research and development (Pytorch Ecosystem: [https://pytorch.org/ecosystem/](https://pytorch.org/ecosystem/)).
- **libtorch:** The C++ API for PyTorch, enabling interoperability with C++ code for potential performance benefits (Pytorch C++ API docs: [https://pytorch.org/cppdocs/](https://pytorch.org/cppdocs/)).

## Recommendations

- **Prioritize Low-Level Languages:** While Python serves as a good starting point, consider exploring lower-level languages like C++ or Rust for performance-critical components where necessary.
- **Favor PyTorch:** While TensorFlow remains a prominent option, PyTorch might offer a more streamlined and efficient approach for deep learning tasks in this context.
- **Leverage Scalable Computing:** Explore platforms like Ray (potentially coupled with Kubernetes in the future) for distributed computing and efficient training on large datasets.
- **Gradual Language Transition:** Rewriting the entire platform with Rust might be ideal long-term, but consider a phased approach, leveraging existing Python libraries with Rust or C++ backends.
- **Initial User Scale:** For the initial phase, the platform should be capable of comfortably handling a million users. However, scaling for significantly larger user bases can be addressed in later development stages.

**Note:** This documentation assumes some familiarity with machine learning concepts and tools.

## Dump

Configuration:
Edit the `config.json` OR `config.yaml` OR `config.jsonc` file to define your API keys, trading strategies, and risk parameters.
