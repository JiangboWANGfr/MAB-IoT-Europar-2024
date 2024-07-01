
!---------------------------------------------------------------------
!---------------------------------------------------------------------

      subroutine isqrt2(i, xdim)

      implicit none
      integer i, xdim

      integer ydim, square

      xdim = -1
      if (i <= 0) return

      square = 0;
      xdim = 1
      do while (square <= i)
         square = xdim*xdim
         if (square == i) return
         xdim = xdim + 1
      end do

      xdim = xdim - 1
      ydim = i / xdim
      do while (xdim*ydim /= i .and. 2*ydim >= xdim)
         xdim = xdim + 1
         ydim = i / xdim
      end do

      if (xdim*ydim /= i .or. 2*ydim < xdim) xdim = -1

      return
      end

!---------------------------------------------------------------------
!---------------------------------------------------------------------

      subroutine proc_grid

!---------------------------------------------------------------------
!---------------------------------------------------------------------

      use lu_data
      use mpinpb
      use mylib

      implicit none

!---------------------------------------------------------------------
!  local variables
!---------------------------------------------------------------------
      integer xdim0, ydim0, IERROR
      integer xdiv, ydiv
      
      character(len=12) :: IOT1_name, IOT2_name, IOT3_name, IOT4_name
      real :: IOT1_ratio, IOT2_ratio, IOT3_ratio, IOT4_ratio
      integer :: IOT1_core_number, IOT2_core_number, IOT3_core_number, IOT4_core_number   
     
!---------------------------------------------------------------------
!  calculate sub-domain array size
!---------------------------------------------------------------------
    !   call isqrt2(no_nodes, xdiv)
    !   ydiv = 2
      if(no_nodes.eq.10) then 
          xdiv = 2
      elseif(no_nodes.eq.12) then
          xdiv = 3
      end if
      ydiv = no_nodes/xdiv
    !   write(*,*) 'no_nodes',no_nodes,'xdiv',xdiv,'ydiv',ydiv
      if (xdiv .le. 0) then
         if (id .eq. 0) write(*,2000) no_nodes
2000     format(' ERROR1: could not determine proper proc_grid',  &
     &          ' for nprocs=', i6)
         CALL MPI_ABORT( MPI_COMM_WORLD, MPI_ERR_OTHER, IERROR )
         stop
      endif

      isiz1 = isiz01/xdiv
      if (isiz1*xdiv < isiz01) isiz1 = isiz1 + 1
      isiz2 = isiz02/ydiv
      if (isiz2*ydiv < isiz02) isiz2 = isiz2 + 1
      nnodes_xdim = xdiv
      isiz3 = isiz03
      
    !   write(*,*) 'no_nodes',no_nodes,'xdiv',xdiv,'isiz1, isiz2, isiz3' &
    !   , isiz1, isiz2, isiz3,'isiz01, isiz02, isiz03', isiz01, isiz02, isiz03

!---------------------------------------------------------------------
!
!   set up a two-d grid for processors: column-major ordering of unknowns
!
!---------------------------------------------------------------------

    !   xdim0  = nnodes_xdim
    !   ydim0  = no_nodes/xdim0

    !   write(*,*) 'num',num,'xdim',xdim,'ydim',ydim,'xdim0',xdim0,'ydim0',ydim0
    !   do while (ydim .ge. ydim0 .and. xdim*ydim .ne. num)
    !      ydim = ydim - 1
    !      xdim = num/ydim
    !   end do
    !   write(*,*) 'num',num,'xdim',xdim,'ydim',ydim
    !   if (xdim .lt. xdim0 .or. ydim .lt. ydim0 .or.  &
    !  &    xdim*ydim .ne. num) then
    !      if (id .eq. 0) write(*,2000) num
    !      write(*,*) 'ERROR2: could not determine proper proc_grid'
    !      CALL MPI_ABORT( MPI_COMM_WORLD, MPI_ERR_OTHER, IERROR )
    !      stop
    !   endif

!       if (id .eq. 0 .and. num .ne. 2**ndim) write(*,2100) num, xdim, ydim
! 2100  format(' Proc_grid for nprocs =',i6,':',i5,' x',i5/)

      row    = mod(id,xdim) + 1
      col    = id/xdim + 1
    ! write(*,777) id, xdim, ydim, row, col
    ! 777 format("[DEBUG]:   Rank: ",I2,"          xdim: ",I5,"        ydim: ",I5,"     grid_row: ",I5,"    grid_col: ",I5)
      isiz1 =33
      isiz2 =33
      isiz3 =33
    !   write(*,777) id, xdim, ydim
    ! 777 format("[DEBUG]:   Rank: ",I2,"          xdim: ",I5,"        ydim: ",I5)

    ! write(*,*) 'IOT1_core',IOT1_core_number,'IOT2_core',IOT2_core_number,'IOT3_core',IOT3_core_number,'IOT4_core',IOT4_core_number

      return
      end


