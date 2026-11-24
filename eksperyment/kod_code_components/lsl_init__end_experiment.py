# Code Component "lsl_init" – zakładka End Experiment
znacznik('exp:end', odebrane=lsl['odebrane'], pominiete=lsl['pominiete'])
core.wait(0.5)  # daj LabRecorderowi czas na odebranie ostatniego znacznika
