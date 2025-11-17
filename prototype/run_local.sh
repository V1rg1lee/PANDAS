# Check if we got an argument
if [ $# -eq 0 ]; then
    echo "Provide a topology file as an argument"
    exit 1
fi
topo_file=$1

binary_path="./libp2p-das"
num_blocks=2

while IFS= read -r line
do
    nick=`echo "$line" | cut -d',' -f1`
    port=`echo "$line" | cut -d',' -f2`
    udp_port=`echo "$line" | cut -d',' -f3`
    ip=`echo "$line" | cut -d',' -f4`
    node_type=$(echo "$line" | rev | cut -d',' -f1 | rev)

    $binary_path -ip=$ip -port=$port -duration=1000 -UDPport=$udp_port -nodeType=$node_type -debug=true -nick=${nick} -key=./keys/${nick}.key&

    if [ $? -ne 0 ]; then
        echo "Error running $nick"
        exit 1
    fi  
done < $topo_file

sleep 1200
FAIL=0
# Wait for the nodes to finish
for job in `jobs -p`
do
    wait $job || FAIL="Fail"
done

if [ "$FAIL" == 0 ]; then
    echo "All jobs finished successfully" 1>&2
else
    echo "Some jobs failed" 1>&2
fi

