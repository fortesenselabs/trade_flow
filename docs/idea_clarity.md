# README

Idea clarification: https://www.epochfin.com/

Tradeflow: Use reinforcement learning to adapt to the markets. DQN Agents.
AutoML + RL

Infracstructure: TradeFlow
-- DataClients: Based on Nautilus Trader's DataClients (only needed for now).
-- ExecutionClients: Based on Nautilus Trader's ExecutionClients (same thing with the data client).
-- Environments: Nautilus Trader(for Backward and forward [paper trading] testing), openAI's gym(for training in a simulated environment).
-- Trader: Take a cue from pipsProphet, goal here is a DQN agent capable of adapting to the market.
---- The Models: We can still reuse the previous supervised learning models here.
---- AutoML(optional): We use this to determine if the agent needs to be retrained and train it.

Trade Node: Nautilus Trader
Cloud Platform: Orchestrate the bot, we an make this better since the trading node just needs separates execution processes not runtimes or machines to work.
