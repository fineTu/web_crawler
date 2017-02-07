#!/bin/bash
eval targetMonth=$(date -d '-2month' +%Y%m)
echo $targetMonth.tar.gz
cd /opt/images/full/
tar -zcPf $targetMonth.tar.gz $targetMonth/
rm -rf /opt/images/full/$targetMonth/