from fuel_health.common.ssh import Client as SSHClient


class RabbitClient(object):
    def __init__(self, host, username, password, key, timeout, rabbit_username, rabbit_password):
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key
        self.timeout = timeout
        self.rabbit_user = rabbit_username
        self.rabbit_password = rabbit_password
        self.ssh = SSHClient(host=self.host,
                             username=self.username,
                             password=self.password,
                             key_filename=self.key_file,
                             timeout=self.timeout)

    def _query(self, query, type='-XGET', arguments=''):
        return 'curl -i -u {ruser}:{rpass} -H "content-type:application/json"'\
                ' {type} {args} http://localhost:55672/api/{query}'.format(
            ruser=self.rabbit_user,
            rpass=self.rabbit_password,
            type=type, query=query,
            args=arguments)

    def list_queues(self):
        query = self._query('/queues/')
        return self.ssh.exec_command(query)

    def create_queue(self, queue_name):
        query = self._query(
            query='/queues/%2f/{queue_name}'.format(queue_name=queue_name),
            type='-XPUT',
            arguments='-d \{\}')
        return self.ssh.exec_command(query)

        # def send_message(self, queue_name, message):
        #     connection = pika.BlockingConnection(
        #         pika.ConnectionParameters(host=self.host,
        #                                   credentials=self.credentials))
        #     channel = connection.channel()
        #     channel.queue_declare(queue=queue_name, passive=True)
        #     channel.basic_publish(exchange='',
        #                           routing_key=queue_name,
        #                           body=message)
        #     connection.close()
        #
        # def receive_message(self, queue_name):
        #     connection = pika.BlockingConnection(
        #         pika.ConnectionParameters(host=self.host,
        #                                   credentials=self.credentials))
        #     channel = connection.channel()
        #     channel.queue_declare(queue=queue_name, passive=True)
        #     method_frame, _, message = channel.basic_get(queue=queue_name)
        #     if method_frame is None:
        #         connection.close()
        #         return None
        #     else:
        #         channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        #         connection.close()
        #         return message
        #
        # def empty_queue(self, queue_name):
        #     message = 'Something'
        #     while message:
        #         message = self.receive_message(queue_name)
        #
        # def close(self, queue_name):
        #     connection = pika.BlockingConnection(
        #         pika.ConnectionParameters(host=self.host,
        #                                   credentials=self.credentials))
        #     channel = connection.channel()
        #     try:
        #         channel.queue_delete(queue=queue_name)
        #     except pika.exceptions.AMQPChannelError:
        #         pass
