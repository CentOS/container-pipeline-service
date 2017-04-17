import socket
hostname = socket.gethostname().split('.')[0]
config = dict(
    # endpoints={
    #     "container_pipeline.%s" % hostname: [
    #         "tcp://127.0.0.1:13005",
    #     ],
    #     "__main__.%s" % hostname: [
    #         "tcp://127.0.0.1:13006",
    #     ]
    # },
    active=True
)
