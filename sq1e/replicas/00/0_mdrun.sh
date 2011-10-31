



grompp -v -f ../../parametersets/300.mdp \
       -c 00_300_p0003.gro \
       -p ../../miscellaneous/sq1e.top \
       -o 00_300_p0004.tpr \
       -po 00_300_p0004.mdp

mdrun -v -deffnm 00_300_p0004
