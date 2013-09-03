from datetime import datetime

now = datetime.utcnow()

print now.tzinfo.utcoffset(1)
