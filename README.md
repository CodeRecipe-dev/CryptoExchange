# Cryto Exchange with AWS and Web3.js

## Background
**Problem Statement:**

Build a basic crypto exchange, like [Coinbase](https://www.coinbase.com/), for buying and selling cryptocurrencies such as Ethereum.

**Solution:**

A serverless platform that leverages AWS Simple Queue Service (SQS) to handle incoming orders, AWS Lambda function to communicate with and handle blockchain transactions (using [web3.js](https://github.com/ethereum/web3.js/)) and [AWS Aurora Serverless with Data API](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/data-api.html) to store each order info.

**Functional Requirements:**

Be able to perform crypto and fiat transactions between buyers and the exchange.

Buyer:

should be able to place an order

should receive ethereum once the order is completed

Exchange:

should be able to retrieve the most recent 5 orders

**Performance Requirements:**

Allow multiple orders and multiple users to order at the same time.

**Notes:**

For demo purposes, the amount of ether transferred is 0.001 ETH and the app is using the Ropsten test network.

## Prerequisites
npm install
pip install -r requirements.txt

Note:
If deploying from a non linux machine (osx, etc), npm install with docker so that the native extensions required for web3 are installed properly: docker run --rm -v $PWD:/data -w /data node:8.10 npm install scrypt, more info [here](https://stackoverflow.com/questions/47987978/aws-and-web3-deployment-in-lambda-function-error/48487001#48487001) and [here](https://github.com/serverless/serverless/issues/308). 


## Deploy
`serverless deploy --stage <stage_name> --dbUser <db_user> --ROPSTEN_INFURA_KEY <infura_key> --ETH_PRIV_KEY <priv_key> --ETH_FROM_ADDRESS <from_address>`

## Create DB - Must be done before using app
`sls invoke -f TransactionRecorder -d '{"body":{"eventType":"createTable"}}' -l --stage <stage_name> --dbUser <db_user> --ROPSTEN_INFURA_KEY <infura_key> --ETH_PRIV_KEY <priv_key> --ETH_FROM_ADDRESS <from_address>`

## Place Order
`sls invoke -f QueueHandler -d '{"body":{"eventType":"placeOrder", "orderInfo":{"coin_type":"ethereum","price":185.5,"amount":1,"status":"created","toAddress":"ethAddress"}}}' -l --stage <stage_name> --dbUser <db_user> --ROPSTEN_INFURA_KEY <infura_key> --ETH_PRIV_KEY <priv_key> --ETH_FROM_ADDRESS <from_address>`

# Get Orders
`sls invoke -f SellerDashboard -d '{"body":{"eventType":"getOrders"}}' -l --stage <stage_name> --dbUser <db_user> --ROPSTEN_INFURA_KEY <infura_key> --ETH_PRIV_KEY <priv_key> --ETH_FROM_ADDRESS <from_address>`

