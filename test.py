import pprint

pp = pprint.PrettyPrinter(indent=4)
alarms=[ 1 , 2, 3]
log_String = pp.pprint(alarms)

print log_String