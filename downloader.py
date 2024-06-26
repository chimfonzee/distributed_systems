from PIL import Image

import pika
import base64, io, json, os

credentials = pika.PlainCredentials('rabbituser', 'rabbit1234')

connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials))
receive = connection.channel()

receive.exchange_declare(exchange='download', exchange_type='fanout')
result = receive.queue_declare(queue='dqueue', exclusive=True)
queue_name = result.method.queue

receive.queue_bind(exchange='download', queue=queue_name)

def callback(ch, method, properties, body):
    json_data = json.loads(body.decode())

    if json_data.get("msg"):
        print('Downloader Module received end of list; closing connection')
        receive.close()
    else:
        print(json_data["name"])
        image = Image.open(io.BytesIO(base64.b64decode(json_data["img"])))
        image.save(os.path.join('./output/', json_data["name"]))

receive.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
print('Receiver Module now consuming from RabbitMQ')
receive.start_consuming()
