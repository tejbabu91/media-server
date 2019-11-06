
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
Microservice upload script requires jq tool https://stedolan.github.io/jq/download/, download and add it to your path
