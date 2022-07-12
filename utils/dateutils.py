import datetime

dtformat = '%Y-%m-%d-%H:%M:%S'

def string2date(s):
    return datetime.datetime.strptime(s, dtformat)

def date2string(d):
    return d.strftime(dtformat)
