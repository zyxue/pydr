#!/bin/bash

#PBS -l nodes=1:ppn=8,walltime=48:00:00,os=centos53computeA
#PBS -N ${_SEQ_}${_CDT_}${_NUM_}
T="${_SEQ_}${_CDT_}${_NUM_}"
N="${_SEQ_}${_CDT_}${_NUM_}"

cd ${PBS_O_WORKDIR}
PF="${N}_md"		# similar to the pf
MAXH=48
NPME1=-1			# for eth
NPME2=-1			# for ib
ALRUN="mpirun -np $(wc -l ${PBS_NODEFILE} | gawk '{print $1}') -machinefile ${PBS_NODEFILE} $EXE"
TPRF=${PF}.tpr
CPOF=${PF}.cpt
CPIF=${PF}.cpt
DNM1=${PF}.part0001		# for first run
DNM2=${PF}			# for continuation
CPT=15				# time interval to write cpt file

counter=${COUNTER}
((counter+=1))
# Only modified variable options
if [ $counter -le 1 ]; then
    VOPT="-cpo ${CPOF} -deffnm ${DNM1} -npme ${NPME1}"
else
    VOPT="-cpi ${CPOF} -deffnm ${DNM2} -npme ${NPME2}"
fi
# Starting mdrun
${ALRUN} ${VOPT} -s ${TPRF} -maxh ${MAXH} -cpt ${CPT}

# cnt cannot be passed within single quote
# cann't do showq in running nodes, so do it in the single quote part
if [ $counter -le 55 ]; then
    ssh gpc04 \
    "cd ${PBS_O_WORKDIR}; cnt=${counter}; sleep $(rd.py 1 120) ; NAME=${T}t$(cpttime.sh ${CPOF}) ;" \
    '
    num=$(myib.sh)
    if [ ${num} -ge 20 ]; then
	nnode=1
    else
	nnode="2:ib"
    fi
    qsub ./0_mdrun.sh \
	-l nodes=${nnode}:ppn=8,walltime=48:00:00,os=centos53computeA \
	-v COUNTER=${cnt} \
	-N ${NAME}
    '
fi

# Usually when applying this script to different systems, the variables
# that need to be modified are walltime, N, MAXH, NPME, CPT, walltime,
# maybe PF as well.