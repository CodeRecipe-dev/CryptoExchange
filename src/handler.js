var AWS = require('aws-sdk');
var lambda = new AWS.Lambda();
var web3 = require('web3');
var Tx = require('ethereumjs-tx');

exports.handler = function(event, context) {
	var eventType = event['body']['eventType']
	if (eventType === 'transferCryptoFromSellerToBuyer') {
		var orderInfo = event['body']['orderInfo']
		var ethAmount = '0.001' //Using 0.001 for demo purposes, change accordingly.
		var web3js = new web3(new web3.providers.HttpProvider("https://ropsten.infura.io/v3/"+process.env.ROPSTEN_INFURA_KEY));
		var txData = web3js.utils.asciiToHex('sample exchange demo');

		web3js.eth.getTransactionCount(process.env.ETH_FROM_ADDRESS, function(err, nonce){
			var rawTransaction = {
				"from": process.env.ETH_FROM_ADDRESS,
				"nonce": nonce,
				"gasPrice": web3js.utils.toHex(30 * 1e9),
				"gasLimit": web3js.utils.toHex(210000),
				"to": orderInfo['toAddress'],
				"value": web3js.utils.numberToHex(web3js.utils.toWei(ethAmount, 'ether')),
				"data": txData
			};

			var privateKey = new Buffer(process.env.ETH_PRIV_KEY, 'hex');
			var tx = new Tx(rawTransaction);
			tx.sign(privateKey);
			var serializedTx = tx.serialize();

			web3js.eth.sendSignedTransaction('0x' + serializedTx.toString('hex'), function(err, hash) {
				if (!err)
				{
					orderInfo['tx_hash'] = hash;
					walletAddress = orderInfo['toAddress'];
					var params = {
						FunctionName: process.env.Stage+'-OrderHandler',
						InvocationType: 'Event',
						LogType: 'Tail',
						Payload: '{ "body" : { "eventType": "confirmCryptoTransaction", "orderInfo": { "tx_hash": "'+hash+'", "order_id": "'+orderInfo['order_id']+'", "wallet_address": "'+walletAddress+'"} } }'
					};
					lambda.invoke(params, function(err, data) {
						if (err) {
							context.fail(err);
						} else {
							context.succeed(data);
						}
					})
				}
				else
				{
					console.error(err);
				}
			});
		})
	}
};