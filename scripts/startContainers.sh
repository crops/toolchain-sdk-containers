#!/bin/bash

docker run -d -p $CODI_PORT:$CODI_PORT --name crops-codi crops/codi
#wait for the crops container to come up
while ! wget -q http://localhost:$CODI_PORT/codi/; do
    echo "waiting for codi to come up"
    sleep 1
done
IFS=' '; for t in $TARGETS; do
    echo "Starting toolchain  $DOCKERHUB_REPO/toolchain-$t:$YP_RELEASE"
    docker run -d --link crops-codi --name=tc-$t $DOCKERHUB_REPO/toolchain-$t:$YP_RELEASE
done
