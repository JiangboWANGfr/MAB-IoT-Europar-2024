! CLASS = A
!  
!  
!  This file is generated automatically by the setparams utility.
!  It sets the number of processors and the class of the NPB
!  in this directory. Do not modify it by hand.
!  
        character class
        parameter (class ='A')
        integer m
        parameter (m=28)
        logical  convertdouble
        parameter (convertdouble = .false.)
        character*11 compiletime
        parameter (compiletime='01 May 2024')
        character*5 npbversion
        parameter (npbversion='3.4.2')
        character*23 cs1
        parameter (cs1='/opt/openmpi/bin/mpif90')
        character*8 cs2
        parameter (cs2='$(MPIFC)')
        character*6 cs3
        parameter (cs3='(none)')
        character*6 cs4
        parameter (cs4='(none)')
        character*3 cs5
        parameter (cs5='-O3')
        character*9 cs6
        parameter (cs6='$(FFLAGS)')
        character*6 cs7
        parameter (cs7='randi8')
