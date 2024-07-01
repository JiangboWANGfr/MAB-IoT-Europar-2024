SHELL=/bin/sh
BENCHMARK=ep
BENCHMARKU=EP

include ../config/make.def

OBJS = ep.o ep_data.o mylib.o verify.o mpinpb.o \
	${COMMON}/print_results.o ${COMMON}/${RAND}.o ${COMMON}/timers.o

include ../sys/make.common

${PROGRAM}: config ${OBJS}
	${FLINK} ${FLINKFLAGS} -o ${PROGRAM} ${OBJS} ${FMPI_LIB}

.f90.o:
	${FCOMPILE} $<

ep.o:		ep.f90 ep_data.o mylib.o mpinpb.o
ep_data.o:	ep_data.f90 npbparams.h
mylib.o:	mylib.f90
verify.o:	verify.f90
mpinpb.o:	mpinpb.f90

clean:
	- rm -f *.o *~ *.mod
	- rm -f npbparams.h core



