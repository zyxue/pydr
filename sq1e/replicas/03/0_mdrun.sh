
grompp -v -f ../../parametersets/330.mdp \
       -c 03_330_p0003.gro \
       -p ../../miscellaneous/sq1e.top \
       -o 03_330_p0004.tpr \
       -po 03_330_p0004.mdp

mdrun -v -deffnm 03_330_p0004
