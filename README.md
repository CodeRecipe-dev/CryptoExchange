# How I Build a Scalable Crypto Exchange with AWS and web3.js

More info here: https://coderecipe.ai/architectures/95580531

**Problem Statment**
Build a basic crypto exchange, like  [Coinbase](https://www.coinbase.com/), for buying and selling cryptocurrencies such as Ethereum.

**Solution**
A serverless platform that leverages AWS Simple Queue Service (SQS) to handle incoming orders, AWS Lambda function to communicate with and handle blockchain transactions (using [web3.js](https://github.com/ethereum/web3.js/)) and [AWS Aurora Serverless with Data API](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/data-api.html) to store each order info.

**Functional Requirements**
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

**Prerequisites**
```
npm install serverless

export AWS_ACCESS_KEY_ID=<your-key-here>

export AWS_SECRET_ACCESS_KEY=<your-secret-key-here>
```
**Deploy**

```
serverless create --template-url https://github.com/CodeRecipe-dev/CryptoExchange --path crypto-exchange

cd crypto-exchange

npm install

serverless deploy --stage <stage_name> --dbUser <db_user> --ROPSTEN_INFURA_KEY <infura_key> --ETH_PRIV_KEY <priv_key> --ETH_FROM_ADDRESS <from_address>
```

**Create DB - Must be done before using app**

```
sls invoke -f TransactionRecorder -d '{"body":{"eventType":"createTable"}}' -l --stage <stage_name> --dbUser <db_user> --ROPSTEN_INFURA_KEY <infura_key> --ETH_PRIV_KEY <priv_key> --ETH_FROM_ADDRESS <from_address>
```

**Place Order**

```
sls invoke -f QueueHandler -d '{"body":{"eventType":"placeOrder", "orderInfo":{"coin_type":"ethereum","price":185.5,"amount":1,"status":"created","toAddress":"ethAddress"}}}' -l --stage <stage_name> --dbUser <db_user> --ROPSTEN_INFURA_KEY <infura_key> --ETH_PRIV_KEY <priv_key> --ETH_FROM_ADDRESS <from_address>
```

**Get Orders**

```
sls invoke -f SellerDashboard -d '{"body":{"eventType":"getOrders"}}' -l --stage <stage_name> --dbUser <db_user> --ROPSTEN_INFURA_KEY <infura_key> --ETH_PRIV_KEY <priv_key> --ETH_FROM_ADDRESS <from_address>
```

