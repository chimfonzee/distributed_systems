import pika
import base64, json, os

credentials = pika.PlainCredentials('rabbituser', 'rabbit1234')

connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials))
channel = connection.channel()

channel.queue_declare(queue='uqueue', auto_delete=True)

if __name__ == "__main__":
    input_folder_path = input('Enter folder location of images (e.g., path/input_folder): ')
    output_folder_path = input('Enter folder location of enhanced images (e.g., path/output_folder): ')

    brightness_factor = float(input('Enter brightness enhancement factor: '))
    sharpness_factor = float(input('Enter sharpness enhancement factor: '))
    contrast_factor = float(input('Enter contrast enhancement factor: '))
    
    num_workers = int(input('Number of Enhancers deployed: '))

    enhancing_time = float(input('Enter enhancing time in minutes : '))
    enhancing_time_seconds = enhancing_time * 60

    for img in os.listdir(input_folder_path):
        image_name = os.path.join(input_folder_path, img)

        with open(image_name, 'rb') as image_file:
            data = base64.b64encode(image_file.read())
    
            msg_dict = {
                "name": img,
                "enhancements": {
                    "brightness": brightness_factor,
                    "sharpness": sharpness_factor,
                    "contrast": contrast_factor
                },
                "output_folder": output_folder_path,
                "img": data.decode()
            }

            msg_json = json.dumps(msg_dict)
            channel.basic_publish(exchange='upload', routing_key='', body=msg_json)

    print('Reached end of image lists; sending end of list message')
    print('Interrupt application if uploader needs to quit')

    for _ in range(num_workers):
        channel.basic_publish(exchange='upload', routing_key='', body=json.dumps({"msg": "end"}))
