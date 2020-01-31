# qlCalc
Software that calculates loaded Q for a set of cryocavities based on RF FCC EPICS data

## Build notes
To build this application, first clone the repo.
```tsch
cd /tmp/
git clone https://github.com/JeffersonLab/qlCalc
```

Then create a virtual environment and load the requirements
```tsch
cd qlCalc
/usr/csite/pubtools/bin/python/3.6.9/bin/python -m venv venv
source venv/bin/activate.csh
pip install -r requirements.txt
``` 

Integration testing requires a soft IOC.  This is a work in progress.  More details to come.