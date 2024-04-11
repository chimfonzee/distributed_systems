# v6 added timer

import multiprocessing, os, time, random
from PIL import Image, ImageEnhance

class Producer(multiprocessing.Process):
    def __init__(self, queue, input_folder, output_folder):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.list = []

    def run(self):
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        input_files = os.listdir(self.input_folder)  # get input files

        for input_file in input_files:
            if input_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):  # check if file is image
                input_path = os.path.join(self.input_folder, input_file)  # input image path
                self.queue.put(input_path)
                self.list.append(input_path)
                print(f'Producer produce {input_path}')
                
        print(f'\nProducer produce count {len(self.list)}')
        print(f'\nProducer list produced: {self.list}\n')
        self.queue.put(None)

class Consumer(multiprocessing.Process):
    def __init__(self, queue, consumer_no, output_folder, brightness_factor, sharpness_factor, contrast_factor, counter, semaphore):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.consumer_no = consumer_no
        self.output_folder = output_folder
        self.brightness_factor = brightness_factor
        self.sharpness_factor = sharpness_factor
        self.contrast_factor = contrast_factor
        self.list = []
        self.counter = counter
        self.semaphore = semaphore

    def run(self):
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        not_terminated = True

        while not_terminated:
            input_path = self.queue.get()
            self.list.append(input_path)

            if input_path != None:
                print(f'Consumer {self.consumer_no}: consume {input_path}')
                _, input_file = os.path.split(input_path)
                output_path = os.path.join(self.output_folder, input_file)
                img = Image.open(input_path)  # open image

                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(self.brightness_factor)  # enhance brightness

                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(self.sharpness_factor)  # enhance sharpness

                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(self.contrast_factor)  # enhance contrast

                img.save(output_path) # save enhanced image

                self.semaphore.acquire()
                self.counter.value +=1  # count number of enhanced images
                self.semaphore.release()

                time.sleep(random.randint(0,1))
            else:
                self.queue.put(None) # notify other consumers that process is done
                not_terminated = False

        print(f'\nConsumer {self.consumer_no} list consumed {self.list}')


if __name__ == "__main__":
    # folder locations
    input_folder_path = input('Enter folder location of images (e.g., path/input_folder): ')
    output_folder_path = input('Enter folder location of enhanced images (e.g., path/output_folder): ')

    # enhancement factors
    brightness_factor = float(input('Enter brightness enhancement factor: '))
    sharpness_factor = float(input('Enter sharpness enhancement factor: '))
    contrast_factor = float(input('Enter contrast enhancement factor: '))

    # enhancing time in minutes 
    enhancing_time = float(input('Enter enhancing time in minutes : '))
    enhancing_time_seconds = enhancing_time * 60

    # multiprocessing stuff
    consumer_threads = int(input('Enter number of threads to use: '))
    queue = multiprocessing.Queue()
    threads = []

    manager = multiprocessing.Manager()
    counter = manager.Value('i',0) # shared_counter_with_lock
    semaphore = multiprocessing.Semaphore(1) # shared_resource_lock

    start_time = time.time()  # start time

    producer = Producer(queue, input_folder_path, output_folder_path)
    producer.start()
    threads.append(producer)

    for i in range(consumer_threads):
        consumer = Consumer(queue, i+1, output_folder_path, brightness_factor, sharpness_factor, contrast_factor, counter, semaphore)
        consumer.start()
        threads.append(consumer)

    for thread in threads:
        thread.join()

    print(f'\nDone.\n')

    file_path = 'output.txt'
    elapsed_time = time.time() - start_time
    stats = 'number of images enhanced: ' + str(counter.value) + '\n' + \
            'number of threads used: ' + str(consumer_threads) + '\n' + \
            'output folder location: ' + output_folder_path + '\n' + \
            'enhancing time input in minutes: ' + str(enhancing_time) + '\n' + \
            'time taken by the program in seconds: ' + str(elapsed_time) + '\n' + \
            'time taken by the program in minutes: ' + str(elapsed_time/60) + '\n'

    with open(file_path, 'w') as f:
        f.write(stats)
