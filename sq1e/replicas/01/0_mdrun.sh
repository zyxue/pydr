
grompp -v -f ../../parametersets/310.mdp \
       -c 01_310_p0003.gro \
       -p ../../miscellaneous/sq1e.top \
       -o 01_310_p0004.tpr \
       -po 01_310_p0004.mdp

mdrun -v -deffnm 01_310_p0004
