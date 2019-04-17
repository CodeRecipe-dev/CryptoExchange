import json
import os
import boto3
from random import *
import pymysql

def handle_order(event, context):
    if "Records" in event:
        request_body = json.loads(event['Records'][0]['body'])
    else:
        request_body = event['body']
    event_type = request_body['eventType']
    order_info = request_body['orderInfo']

    if event_type == "placeOrder":
        lambda_client = boto3.client('lambda')
        order_handler_request = _build_request('saveOrder',order_info)
        order_handler_function_name = "{}-{}".format(os.environ["Stage"], "TransactionRecorder")
        response = lambda_client.invoke(FunctionName=order_handler_function_name,
                             InvocationType='RequestResponse',
                             Payload=json.dumps(order_handler_request))
        order_info = json.loads(response['Payload'].read().decode("utf-8"))
        order_info = order_info['order']
        _init_fiat_transaction(order_info)
        return {"success": True, "order": order_info}

    if event_type == "confirmFiatTransaction":
        _init_crypto_transaction(order_info)
        return {"success": True, "message": "Confirmed fiat transaction"}

    if event_type == "confirmCryptoTransaction":
        lambda_client = boto3.client('lambda')
        order_handler_request = _build_request('updateOrder',order_info)
        order_handler_function_name = "{}-{}".format(os.environ["Stage"], "TransactionRecorder")
        response = lambda_client.invoke(FunctionName=order_handler_function_name,
                             InvocationType='RequestResponse',
                             Payload=json.dumps(order_handler_request))        
        return {"success": True, "message": "Sending to transaction recorder to save data"}

def handle_queue(event, context):
    request_body = event['body']
    event_type = request_body['eventType']
    order_info = request_body['orderInfo']

    if event_type == 'placeOrder':
        _add_to_queue(event_type, order_info)
        return {"success": True, "order": order_info}


def _update_orders_table(order_info):
    database_name = os.environ['DatabaseName']
    client = boto3.client('rds-data')
    response = client.execute_sql(
        awsSecretStoreArn=os.environ['AwsSecretStoreArn'],
        dbClusterOrInstanceArn=os.environ['DbClusterArn'],
        database=database_name,
        sqlStatements='UPDATE Orders SET tx_hash = '+pymysql.escape_string(order_info['tx_hash'])+', wallet_address = '+pymysql.escape_string(order_info['wallet_address'])+' WHERE order_id = '+order_info['order_id']+';'
    )

def handle_transaction_recorder(event, context):
    request_body = event['body']
    event_type = request_body['eventType']

    if event_type == "createTable":
        _create_orders_table()
        return {"success": True, "message": "Created Table"}

    if event_type == "getOrders":
        orders = _get_orders()
        return {"success": True, "orders": orders}

    if event_type == "saveOrder":
        order_info = request_body['orderInfo']
        order_info['order_id'] = randint(1,10000000)
        _save_order_to_db(order_info)
        return {"success": True, "message": "Saved Order", "order": order_info}

    if event_type == "updateOrder":
        order_info = request_body['orderInfo']
        _update_orders_table(order_info)


def handle_seller_dashboard(event, context):
    request_body = event['body']
    event_type = request_body['eventType']

    if event_type == 'getOrders':
        lambda_client = boto3.client('lambda')
        order_handler_request = _build_request('getOrders',{})
        order_handler_function_name = "{}-{}".format(os.environ["Stage"], "TransactionRecorder")
        response = lambda_client.invoke(FunctionName=order_handler_function_name,
                             InvocationType='RequestResponse',
                             Payload=json.dumps(order_handler_request))
        parsed = response['Payload'].read().decode("utf-8")
        return {"success": True, "orders": json.loads(parsed)}

def _get_orders():
    database_name = os.environ['DatabaseName']
    client = boto3.client('rds-data') 
    response = client.execute_sql(
        awsSecretStoreArn=os.environ['AwsSecretStoreArn'],
        dbClusterOrInstanceArn=os.environ['DbClusterArn'],
        database=database_name,
        sqlStatements='select * from Orders limit 5'
    )
    return response['sqlStatementResults'][0]['resultFrame']['records']

def _add_to_queue(event_type, order_info):
    sqs = boto3.resource('sqs')
    sqsClient = boto3.client('sqs')
    response = sqsClient.send_message(
        QueueUrl=os.environ['QueueUrl'],
        MessageBody=json.dumps({"eventType": event_type, "orderInfo": order_info})
    )
    return response

def _create_orders_table():
    database_name = os.environ['DatabaseName']
    client = boto3.client('rds-data') 
    response = client.execute_sql(
        awsSecretStoreArn=os.environ['AwsSecretStoreArn'],
        dbClusterOrInstanceArn=os.environ['DbClusterArn'],
        database=database_name,
        sqlStatements='create table Orders(order_id int NOT NULL, user_id int, coin_type varchar(200), amount float, price float, status varchar(200), wallet_address varchar(255), tx_hash varchar(255), PRIMARY KEY (order_id))'
    )

def _init_fiat_transaction(order_info):
    lambda_client = boto3.client('lambda')
    handler_request = _build_request('transferFiatFromBuyerToSeller',order_info)
    handler_function_name = "{}-{}".format(os.environ["Stage"], "UpdateSellerBankAccount")
    lambda_client.invoke(FunctionName=handler_function_name,
                         InvocationType='Event',
                         Payload=json.dumps(handler_request))

def _init_crypto_transaction(order_info):
    lambda_client = boto3.client('lambda')
    handler_request = _build_request('transferCryptoFromSellerToBuyer',order_info)
    handler_function_name = "{}-{}".format(os.environ["Stage"], "UpdateBuyerWallet")
    lambda_client.invoke(FunctionName=handler_function_name,
                         InvocationType='Event',
                         Payload=json.dumps(handler_request))

def _save_order_to_db(order_info):
    database_name = os.environ['DatabaseName']
    client = boto3.client('rds-data')
    response = client.execute_sql(
        awsSecretStoreArn=os.environ['AwsSecretStoreArn'],
        dbClusterOrInstanceArn=os.environ['DbClusterArn'],
        database=database_name,
        sqlStatements="INSERT INTO Orders(user_id, order_id, coin_type, amount, price, status) VALUES (1,{},'{}',{},{},'{}')".format(order_info['order_id'], pymysql.escape_string(order_info['coin_type']),pymysql.escape_string(order_info['amount']), pymysql.escape_string(order_info['price']), pymysql.escape_string(order_info['status']))
    )

def _build_request(event_type, order_info):
    return {"body": {"eventType": event_type, "orderInfo": order_info}}

def handle_fiat_transaction(event, context):
    order_info = event['body']['orderInfo']
    lambda_client = boto3.client('lambda')
    order_handler_request = _build_request('confirmFiatTransaction',order_info)
    order_handler_function_name = "{}-{}".format(os.environ["Stage"], "OrderHandler")
    lambda_client.invoke(FunctionName=order_handler_function_name,
                         InvocationType='Event',
                         Payload=json.dumps(order_handler_request))


def handle_crypto_transaction(event, context):
    request_body = event['body']
    lambda_client = boto3.client('lambda')
    order_info = event['body']['orderInfo']
    order_handler_request = _build_request('confirmCryptoTransaction',order_info)
    order_handler_function_name = "{}-{}".format(os.environ["Stage"], "OrderHandler")
    lambda_client.invoke(FunctionName=order_handler_function_name,
                         InvocationType='Event',
                         Payload=json.dumps(order_handler_request))
