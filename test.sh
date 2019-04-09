#!/bin/sh
echo "Starting all tests..."
echo "====="
python odevalidator --data-file ../../../data/bsmLogDuringEvent.json
echo "====="
python odevalidator --data-file ../../../data/bsmTx.json
echo "====="
python odevalidator --data-file ../../../data/dnMsg.json
echo "====="
python odevalidator --data-file ../../../data/driverAlert.json
echo "====="
python odevalidator --data-file ../../../data/rxMsg_BSM_and_TIM.json
echo "====="
python odevalidator --data-file ../../../data/rxMsg_TIM_GeneratedBy_RSU.json
echo "====="
python odevalidator --data-file ../../../data/rxMsg_TIM_GeneratedBy_TMC_VIA_SAT.json
echo "====="
python odevalidator --data-file ../../../data/rxMsg_TIM_GeneratedBy_TMC_VIA_SNMP.json
echo "====="
echo "Testing complete."
