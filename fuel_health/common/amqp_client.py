import pika
import pika.exceptions as AmqpEx


class AmqpClient(object):
    def __init__(self, host, rabbit_username, rabbit_password):
        self.host = host
        self.username = rabbit_username
        self.password = rabbit_password
        self.credentials = pika.credentials.PlainCredentials(
            username=self.username,
            password=self.password)

    def create_queue(self, queue_name):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host,
                                      credentials=self.credentials))
        channel = connection.channel()
        channel.queue_declare(queue=queue_name,
                              durable=True,
                              arguments={'x-ha-policy': 'all'})
        connection.close()

    def send_message(self, queue_name, message):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host,
                                      credentials=self.credentials))
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, passive=True)
        channel.basic_publish(exchange='',
                              routing_key=queue_name,
                              body=message)
        connection.close()

    def receive_message(self, queue_name):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host,
                                      credentials=self.credentials))
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, passive=True)
        method_frame, _, message = channel.basic_get(queue=queue_name)
        if method_frame is None:
            connection.close()
            return None
        else:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            connection.close()
            return message

    def empty_queue(self, queue_name):
        message = 'Something'
        while message:
            message = self.receive_message(queue_name)

    def close(self, queue_name):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host,
                                      credentials=self.credentials))
        channel = connection.channel()
        try:
            channel.queue_delete(queue=queue_name)
        except pika.exceptions.AMQPChannelError:
            pass
