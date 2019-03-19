Inspired by [Daniel van Flymen](https://hackernoon.com/learn-blockchains-by-building-one-117428612f46) and written to run on [Debian on Termux](https://github.com/sp4rkie/debian-on-termux)


## First time setup/running process
1. Clone this repo
2. Install pipenv if you don't already use it.  It's great.
3. cd nanobitcoin
4. pipenv install
5. pipenv shell
6. python blockchain.py
7. Use a method of your choice to make HTTP get/post requests to the node

## Features
* Allows basic mining
* Very basic transaction validation that uses concept of accounts to ensure the sender of a transaction already has the necessary amount of nanobitcoin to make the transaction.

## Usage - hit these endpoints to access various node features
GET Requests
* /chain - Node will respond with the entire chain
* /mine  - Node will mine a new block 
* /nodes/resolve - Consensus protocol to determine which chain is valid
POST Requests - look at code for required fields
* /transactions/new - Adds a new transaction to the next block
* /nodes/register - Register an additional nanobitcoin node and increase the security of the network!


Will hopefully grow beyond this as I experiment and learn about blockchain.

