
grompp -v -f ../../parametersets/320.mdp \
       -c 02_320_p0003.gro \
       -p ../../miscellaneous/sq1e.top \
       -o 02_320_p0004.tpr \
       -po 02_320_p0004.mdp

mdrun -v -deffnm 02_320_p0004
