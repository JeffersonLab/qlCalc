# Design Notes

This is just a quick jotting down of design ideas as I work through the problem

- cryocavity is probably the base unit for containing calculations
    - each cryocavity can query it's own synchronized data
    - a factory method is useful to contain the synchronized data query while still allowing for easy testing of the 
      class
    - should I have a class per cryocavity type?
      - Only a couple of differences per cryocavity type - length, R/Q
      - probably cleaner to have multiple classes and easier for future extensions 
      
- R1XXITOT/R2XXITOT is not synchronized, but should probably be called repeatedly at the time of the calculations for
  each cavity
  - R1XXITOT is not currently available.  Should I just use RFs R2XXITOT or compute them both on my own?
- config file needed to determine which cryocavity type is in each location.  CED does not contain cryocavity type, only
  cryomodule type
  
- Need run repeated calculations fast (seconds, not minutes)
  - so it should be a long running application and not a cronjob
  - probably doesn't need to be a service since no one will send it commands
    - but maybe they will want to change things on the fly?  Adjust speed of repeated calculations?  Can always make it
      configurable and restart the app ...


## Cryocavity Lists
C75 cells - 1L13-1/2
F100 - 1L23
