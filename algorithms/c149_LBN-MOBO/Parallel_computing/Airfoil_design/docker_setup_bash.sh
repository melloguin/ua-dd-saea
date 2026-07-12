#!/bin/bash
docker image load < "../UANA/airfoil_docker.tar"
docker run -d -it --name airfoil_mount -v "/HPS/NavidCAM/work/NAGD/MO-NBO/Airfoil/MONBO_Automized:/home/airfoil_UANA" airfoil_mount_2:latest
address=$(docker ps -aq)
echo $address
docker exec -it "$address" /bin/bash
