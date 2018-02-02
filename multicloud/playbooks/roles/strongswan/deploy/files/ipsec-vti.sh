#!/bin/bash

set -o nounset
set -o errexit

VTI_IF="vti${PLUTO_UNIQUEID}"

export >/tmp/vti.txt

my_ip=`printf "%q" $PLUTO_MY_ID| tr -cd [[:digit:][.]]`
peer_ip=`printf "%q" $PLUTO_PEER_ID| tr -cd [[:digit:][.]]`

case "${PLUTO_VERB}" in
    up-client|up-host)
        #this is workaround for https://wiki.strongswan.org/issues/1497
        #ip tunnel add "${VTI_IF}" local "${PLUTO_ME}" remote "${PLUTO_PEER}" mode vti key "${PLUTO_UNIQUEID}"
        #should be
        ip tunnel add "${VTI_IF}" local "${PLUTO_ME}" remote "${PLUTO_PEER}" mode vti okey "${PLUTO_MARK_OUT%%/*}" ikey "${PLUTO_MARK_IN%%/*}"
        ip link set "${VTI_IF}" up
        ip addr add ${my_ip} remote ${peer_ip} dev "${VTI_IF}"
        sysctl -w "net.ipv4.conf.${VTI_IF}.disable_policy=1"
        ;;
    down-client|down-host)
        ip tunnel del "${VTI_IF}"
        ;;
esac
