#!/bin/sh

wine python $HOME/server.py --host $SERVER_HOST -p $SERVER_PORT

# CMD ["wine", "python server.py"]
# --host ${SERVER_HOST} -p ${SERVER_PORT}