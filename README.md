
Start the server
================
python server.py


GEt all streams
===============

curl --request get http://localhost:5000/streams

Create a stream
================
curl --request post --data-binary '@test.json' http://localhost:5000/streams

Create a stream
================
curl --request put --data-binary '@test.json' http://localhost:5000/streams/<id>

Delete a stream
===============
curl --request delete http://localhost:5000/streams/<id>


MICROSERVICE INSTALLATION
=

Build microservice using ./microservice pack --name media-server

Upload microservice using ./microservice deploy -n media-server -d <tenant url> -u <username> -p <password> -te <tenant id>

To build, upload and subscribe in a single step, use ./microservice pack deploy subscribe -n media-server -d <tenant url> -u <username> -p <password> -te <tenant id>

Microservice upload script requires jq tool https://stedolan.github.io/jq/download/, download and add it to your path
