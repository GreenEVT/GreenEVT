this directory stores the flows files that specifies where and when each of the vehicles are spawned, and where they should go. Flows file don't care about routing - they only care about the starting point and destination. 

By default, these files are generated by the scripts/generateflow.py script, in which we specify parameters to define what the evacuation plan looks like. (time window size, vehicle multipliers, etc.)

At this point (2022/1/30) we have not yet implemented passed arguments for the script. You might have to look at the code and make changes yourself if you want more customized scenarios.

```
\evacgreensboro\scripts> py .\generateflow.py
```