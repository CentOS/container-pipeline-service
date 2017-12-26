import container_pipeline.api.v1 as api_v1

API_ENDPOINT = r'^api'


def get_urls():
    urls = []
    urls += api_v1.get_urls()
    return urls