# CCCP API Server

## Requirements
Python 3.5.2+

## Usage
To run the server, please execute the following from the root directory:

```
pip3 install -r requirements.txt
python3 -m ccp_server
```

and open your browser to here:

```
http://localhost:8080/api/v1//ui/
```

Your Swagger definition lives here:

```
http://localhost:8080/api/v1//swagger.json
```

To launch the integration tests, use tox:
```
sudo pip install tox
tox
```

## Running with Docker

To run the server on a Docker container, please execute the following from the root directory:

```bash
# building the image
docker build -t ccp_server .

# starting up a container
docker run -p 8080:8080 ccp_server
```
