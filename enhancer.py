from PIL import Image, ImageEnhance

import pika
import base64, io, json, os

credentials = pika.PlainCredentials('rabbituser', 'rabbit1234')

receive_conn = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials))
send_conn = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials))

receive = receive_conn.channel()
send = send_conn.channel()

receive.exchange_declare(exchange='upload', exchange_type='fanout')
send.queue_declare(queue='accept')
result = receive.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

receive.queue_bind(exchange='upload', queue=queue_name)

def callback(ch, method, properties, body):
    json_data = json.loads(body.decode())
    enhancements = json_data["enhancements"]
    image = Image.open(io.BytesIO(base64.b64decode(json_data["img"])))

    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(enhancements["brightness"])

    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(enhancements["sharpness"])

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(enhancements["contrast"])

    temp_file = f'./temp.{json_data["name"].split(".")[1]}'
    image.save(temp_file)

    with open(temp_file, 'rb') as image_file:
        data = base64.b64encode(image_file.read())

        msg_dict = {
            "name": json_data["name"],
            "output_folder": json_data["output_folder"],
            "img": data.decode()
        }

        msg_json = json.dumps(msg_dict)
        send.basic_publish(exchange='download', routing_key='', body=msg_json)
    
    os.remove(temp_file)

receive.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
receive.start_consuming()
