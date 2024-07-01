
module mylib
    implicit none
    integer, parameter :: RASPBERRY_PI_4_CORES = 4
    integer, parameter :: BEAGLEBOARD_BLACK_1_CORE = 1
    integer, parameter :: JETSON_NANO_6_CORES = 6

    contains
    ! get input from user
    subroutine getIOTnameAndIOTratio(IOT1_name, IOT1_ratio, IOT2_name, IOT2_ratio, IOT3_name, IOT3_ratio, IOT4_name, IOT4_ratio)
        implicit none
        character(len=*), intent(out) :: IOT1_name, IOT2_name, IOT3_name, IOT4_name
        real, intent(out) :: IOT1_ratio, IOT2_ratio, IOT3_ratio, IOT4_ratio
        character(len=100) :: IOT1_ratio_str, IOT2_ratio_str, IOT3_ratio_str, IOT4_ratio_str

        call get_command_argument(1, IOT1_name)
        call get_command_argument(2, IOT1_ratio_str)
        call get_command_argument(3, IOT2_name)
        call get_command_argument(4, IOT2_ratio_str)
        call get_command_argument(5, IOT3_name)
        call get_command_argument(6, IOT3_ratio_str)
        call get_command_argument(7, IOT4_name)
        call get_command_argument(8, IOT4_ratio_str)

        read(IOT1_ratio_str, *) IOT1_ratio
        read(IOT2_ratio_str, *) IOT2_ratio
        read(IOT3_ratio_str, *) IOT3_ratio
        read(IOT4_ratio_str, *) IOT4_ratio
    end subroutine getIOTnameAndIOTratio

    function get_iot_core_number(iot_name) result(core_number)
        implicit none
        character(len=*), intent(in) :: iot_name
        integer :: core_number

        if (trim(adjustl(iot_name)) == 'rpi4') then
            core_number = RASPBERRY_PI_4_CORES
        else if (trim(adjustl(iot_name)) == 'beagleboard') then
            core_number = BEAGLEBOARD_BLACK_1_CORE
        else if (trim(adjustl(iot_name)) == 'jetson') then
            core_number = JETSON_NANO_6_CORES
        else
            core_number = -1
        endif
    end function get_iot_core_number

    ! subroutine get_number_per_process(world_rank, world_size, N,IOT1_ratio, IOT1_core_number,&
    !  IOT2_ratio, IOT2_core_number, no_large_nodes, np,np_add,k_offset)

    subroutine computeRowsPerProcess(comm_solve,world_rank, world_size, N,mtrix_row, IOT1_ratio, IOT2_ratio,&
         IOT3_ratio, IOT4_ratio, IOT1_CORE_NUMBER,IOT2_CORE_NUMBER,&
        IOT3_CORE_NUMBER,IOT4_CORE_NUMBER, start_row, num_rows)
        integer, intent(in) :: world_rank, world_size, N
        integer, intent(in) :: comm_solve
        integer, intent(in) :: mtrix_row
        real, intent(in) :: IOT1_ratio, IOT2_ratio, IOT3_ratio, IOT4_ratio
        integer, intent(in) :: IOT1_CORE_NUMBER, IOT2_CORE_NUMBER,IOT3_CORE_NUMBER, IOT4_CORE_NUMBER
        integer, intent(out) :: start_row, num_rows
        integer :: IOT1_ROWS_PER_PROCESS, IOT2_ROWS_PER_PROCESS,IOT3_ROWS_PER_PROCESS, IOT4_ROWS_PER_PROCESS
        integer :: cpu_cores, ierr
        integer :: IOT1_CORE_ROWS, IOT2_CORE_ROWS, IOT3_CORE_ROWS, IOT4_CORE_ROWS
        double precision ::tempvariable
        integer :: total_rows_allocated, last_nonzero_ratio_index

!-------------------------------------------------------
! for LU,the structure of the matrix is as follows:
! |.....            |
! | core 6 | core 7 |
! | core 4 | core 5 |
! | core 2 | core 3 | 
! | core 0 | core 1 |
! this means that the matrix is always divided 2columns ,and then divided the rows for diffent divices
! for example, if we have 2 devices ,4 cores for RP4 and 6 cores for jetson , and we choice the calcalate matrix size is 33*33*33 (class W),and the ratio is 0.3,0.7,0,0
!for RP4:    33*0.3/(4/2) = 5
!for jetson: (33-5*2)/(6/2)=8, then the matrix will be divided as follows: 
! |.....          |
! |  8    |  9    |  7 rows for each core (jetson)
! |  6    |  7    |  8 rows for each core (jetson)
! |  4    |  5    |  8 rows for each core (jetson)
! |  2    |  3    |  5 rows for each core (RP4)
! |  0    |  1    |  5 rows for each core (RP4)
!-------------------------------------------------------
        IOT1_CORE_ROWS = nint(IOT1_CORE_NUMBER / 2.0) 
        IOT2_CORE_ROWS = nint(IOT2_CORE_NUMBER / 2.0)
        IOT3_CORE_ROWS = nint(IOT3_CORE_NUMBER / 2.0)
        IOT4_CORE_ROWS = nint(IOT4_CORE_NUMBER / 2.0)
        IOT1_ROWS_PER_PROCESS = nint(N * IOT1_ratio / IOT1_CORE_ROWS) 
        IOT2_ROWS_PER_PROCESS = nint(N * IOT2_ratio / IOT2_CORE_ROWS) 
        IOT3_ROWS_PER_PROCESS = nint(N * IOT3_ratio / IOT3_CORE_ROWS) 
        IOT4_ROWS_PER_PROCESS = nint(N * IOT4_ratio / IOT4_CORE_ROWS) 
        if(IOT1_CORE_NUMBER == 1) IOT1_ROWS_PER_PROCESS = N
        if(IOT2_CORE_NUMBER == 1) IOT2_ROWS_PER_PROCESS = N
        if(IOT3_CORE_NUMBER == 1) IOT3_ROWS_PER_PROCESS = N
        if(IOT4_CORE_NUMBER == 1) IOT4_ROWS_PER_PROCESS = N
        !make sure that allocate 1 at least if ratio >0
        if (IOT1_ratio > 0.0 .and. IOT1_ROWS_PER_PROCESS == 0) IOT1_ROWS_PER_PROCESS = 1
        if (IOT2_ratio > 0.0 .and. IOT2_ROWS_PER_PROCESS == 0) IOT2_ROWS_PER_PROCESS = 1
        if (IOT3_ratio > 0.0 .and. IOT3_ROWS_PER_PROCESS == 0) IOT3_ROWS_PER_PROCESS = 1
        if (IOT4_ratio > 0.0 .and. IOT4_ROWS_PER_PROCESS == 0) IOT4_ROWS_PER_PROCESS = 1
        total_rows_allocated = IOT1_ROWS_PER_PROCESS*IOT1_CORE_ROWS + IOT2_ROWS_PER_PROCESS*IOT2_CORE_ROWS  +&
        IOT3_ROWS_PER_PROCESS*IOT3_CORE_ROWS + IOT4_ROWS_PER_PROCESS*IOT4_CORE_ROWS 
        last_nonzero_ratio_index = 0
        if(IOT4_ratio > 0.0) then
                last_nonzero_ratio_index = 4
        else if(IOT3_ratio > 0.0) then 
                last_nonzero_ratio_index = 3
        else if(IOT2_ratio > 0.0) then
                last_nonzero_ratio_index = 2
        else if(IOT1_ratio > 0.0) then
                last_nonzero_ratio_index = 1
        endif
        if (total_rows_allocated < N) then
                select case(last_nonzero_ratio_index)
                case (1)
                        IOT1_ROWS_PER_PROCESS = IOT1_ROWS_PER_PROCESS + 1
                case (2)
                        IOT2_ROWS_PER_PROCESS = IOT2_ROWS_PER_PROCESS + 1
                case (3)
                        IOT3_ROWS_PER_PROCESS = IOT3_ROWS_PER_PROCESS + 1
                case (4)
                        IOT4_ROWS_PER_PROCESS = IOT4_ROWS_PER_PROCESS + 1
                end select
        endif

        !IOT2_ROWS_PER_PROCESS = (N - IOT1_ROWS_PER_PROCESS * IOT1_CORE_ROWS) / IOT2_CORE_ROWS
        !IOT3_ROWS_PER_PROCESS = (N -IOT1_ROWS_PER_PROCESS * IOT1_CORE_ROWS &
        !                        & -IOT2_ROWS_PER_PROCESS*IOT2_CORE_ROWS)/IOT3_CORE_ROWS
        !IOT4_ROWS_PER_PROCESS = (N -IOT1_ROWS_PER_PROCESS * IOT1_CORE_ROWS-IOT2_ROWS_PER_PROCESS*IOT2_CORE_ROWS &
        !                        &     -IOT3_ROWS_PER_PROCESS*IOT3_CORE_ROWS)/IOT4_CORE_ROWS

        if(world_rank .eq. 0) then
            write(*,767) IOT1_ROWS_PER_PROCESS, IOT2_ROWS_PER_PROCESS, IOT3_ROWS_PER_PROCESS, IOT4_ROWS_PER_PROCESS
            767 format("[DEBUG]: IOT1_ROWS_PER_PROCESS: ", I3, " IOT2_ROWS_PER_PROCESS: ", I3, &
            " IOT3_ROWS_PER_PROCESS: ", I3, " IOT4_ROWS_PER_PROCESS: ", I3)
        endif
            
        cpu_cores = get_cpu_cores()
        
        ! Determine whether IOT1_ratio + IOT2_ratio + IOT3_ratio + IOT4_ratio is equal to 1
        ! if not, print an error message and abort the program
        if (abs(IOT1_ratio + IOT2_ratio + IOT3_ratio + IOT4_ratio - 1.0) > 1e-6) then
            write(*,*) "[ERROR]: The sum of IOT1_ratio, IOT2_ratio, IOT3_ratio, and IOT4_ratio should be 1"
            call MPI_Abort(comm_solve, 1, ierr)
        endif
        ! which device the current process belongs to and allocate the corresponding number of rows
        if (world_rank < IOT1_CORE_NUMBER .and. IOT1_RATIO /= 0.0) then
            if (cpu_cores /= IOT1_CORE_NUMBER) then
                write(*,*) "[ERROR]: The number of CPU cores does not match the number of IOT1 cores"
                write(*,*) "[ERROR]: Detected cpu cores: ", cpu_cores, "IOT1_core_number: ", IOT1_CORE_NUMBER
                call MPI_Abort(comm_solve, 1, ierr)
            endif
            start_row = IOT1_ROWS_PER_PROCESS*(mtrix_row-1)
            num_rows = IOT1_ROWS_PER_PROCESS
        elseif (world_rank >= IOT1_CORE_NUMBER .and. world_rank < IOT1_CORE_NUMBER &
                + IOT2_CORE_NUMBER .and. IOT2_RATIO /= 0.0) then
            if (cpu_cores /= IOT2_CORE_NUMBER) then
                write(*,*) "[ERROR]: The number of CPU cores does not match the number of IOT2 cores"
                write(*,*) "[ERROR]: Detected cpu cores: ", cpu_cores, "IOT2_core_number: ", IOT2_CORE_NUMBER
                call MPI_Abort(comm_solve, 1, ierr)
            endif
            start_row = IOT1_CORE_ROWS * IOT1_ROWS_PER_PROCESS + &
                        IOT2_ROWS_PER_PROCESS*(mtrix_row-IOT1_CORE_ROWS-1)
            num_rows = IOT2_ROWS_PER_PROCESS
        elseif (world_rank >= IOT1_CORE_NUMBER + IOT2_CORE_NUMBER .and. &
             world_rank < IOT1_CORE_NUMBER + IOT2_CORE_NUMBER + IOT3_CORE_NUMBER .and. IOT3_RATIO /= 0.0) then
            if (cpu_cores /= IOT3_CORE_NUMBER) then
                write(*,*) "[ERROR]: The number of CPU cores does not match the number of IOT3 cores"
                write(*,*) "[ERROR]: Detected cpu cores: ", cpu_cores, "IOT3_core_number: ", IOT3_CORE_NUMBER
                call MPI_Abort(comm_solve, 1, ierr)
            endif
            start_row = IOT1_CORE_ROWS * IOT1_ROWS_PER_PROCESS + &
                        IOT2_CORE_ROWS * IOT2_ROWS_PER_PROCESS + &
                        IOT3_ROWS_PER_PROCESS*(mtrix_row-IOT1_CORE_ROWS-IOT2_CORE_ROWS-1)
            num_rows = IOT3_ROWS_PER_PROCESS
        else  ! 对于IOT4设备
            if (cpu_cores /= IOT4_CORE_NUMBER) then
                write(*,*) "[ERROR]: The number of CPU cores does not match the number of IOT4 cores"
                write(*,*) "[ERROR]: Detected cpu cores: ", cpu_cores, "IOT4_core_number: ", IOT4_CORE_NUMBER
                call MPI_Abort(comm_solve, 1, ierr)
            endif
            start_row = IOT1_CORE_ROWS * IOT1_ROWS_PER_PROCESS + &
                        IOT2_CORE_ROWS * IOT2_ROWS_PER_PROCESS + &
                        IOT3_CORE_ROWS * IOT3_ROWS_PER_PROCESS + &
                        IOT4_ROWS_PER_PROCESS*(mtrix_row-IOT1_CORE_ROWS-IOT2_CORE_ROWS-IOT3_CORE_ROWS-1)
            num_rows = IOT4_ROWS_PER_PROCESS
        endif

        ! Check the last process, if the number of rows is less than 0, set it to 0
        ! if (world_rank == world_size - 1) then
        !     num_rows = N - start_row
        ! endif
        if (num_rows < 0) then
            num_rows = 0
        endif
        !num_rows=3
        ! write(*,777) world_rank, start_row, num_rows
        ! 777 format("[DEBUG]:      Rank: ",I2,"          start_row: ",I3,"       num_rows: ",I3)
    end subroutine computeRowsPerProcess

    subroutine get_number_per_process(world_rank, world_size, N,IOT1_ratio, IOT1_core_number,&
     IOT2_ratio, IOT2_core_number, no_large_nodes, np,np_add,k_offset)
        implicit none
        integer, intent(in) :: world_rank, world_size, N
        integer, intent(in) :: IOT1_core_number, IOT2_core_number
        real, intent(in) :: IOT1_ratio, IOT2_ratio
        integer, intent(out) :: no_large_nodes, np
        integer,intent(out) :: np_add, k_offset

        if (world_rank .lt. IOT1_core_number) then
            ! print *,"[DEBUG]: IOT1 Rank: ", world_rank, " IOT1_ratio: ", IOT1_ratio
        else
            ! print *,"[DEBUG]: IOT2 Rank: ", world_rank, " IOT2_ratio: ", IOT2_ratio
        endif
        np = N / world_size

        if(world_rank .eq. 0) then
            k_offset = -1
            np = N / world_size
        endif
        if(world_rank.eq.1) then
            k_offset = 84
            np = N / world_size
        endif
        if(world_rank.eq.2) then
            k_offset = 169
            np = N / world_size+1
        endif
        if(world_rank.eq.3) then
            k_offset = 191
        endif
        print *,"[DEBUG]: Rank: ", world_rank, " k_offset: ", k_offset, "np: ", np
        
    end subroutine get_number_per_process

    subroutine get_number_per_process_original(node, no_nodes, nn, no_large_nodes, np,np_add,k_offset)
        implicit none
        integer, intent(in) :: node, no_nodes, nn
        integer, intent(out) :: no_large_nodes, np
        integer,intent(out) :: np_add, k_offset

        np = nn / no_nodes
        no_large_nodes = mod(nn, no_nodes)
        if (node .lt. no_large_nodes) then
            np_add = 1
        else
            np_add = 0
        endif
        np = np + np_add

        if (np_add .eq. 1) then
            k_offset = node * np -1
        else
            k_offset = no_large_nodes*(np+1) + (node-no_large_nodes)*np -1
        endif
        print *,"[DEBUG]: Rank: ", node, " k_offset: ", k_offset, "np: ", np
        
    end subroutine get_number_per_process_original

! subroutine getProcGridRowandCol(world_size, world_rank, IOT1_core_number, IOT2_core_number,ydim,&
! IOT1_ratio, IOT2_ratio,IOT3_ratio,IOT4_ratio,& IOT3_core_number, IOT4_core_number, proc_grid_rows, proc_grid_cols)
!     implicit none
!     integer, intent(in) :: world_size, world_rank
!     integer, intent(in) :: IOT1_core_number, IOT2_core_number, IOT3_core_number, IOT4_core_number
!     real, intent(in) :: IOT1_ratio, IOT2_ratio, IOT3_ratio, IOT4_ratio
!     integer, intent(out) :: proc_grid_rows, proc_grid_cols
!     integer :: total_cores

!     ! get the total number of cores
!     ! if ratio != 0, then add the number of cores
!     for (i = 1; i <= 4; i = i + 1)
!         if (ratio(i) /= 0.0) then
!             total_cores = total_cores + core_number(i)
!         endif
!     end do
!     print *, "total_cores: ", total_cores

!     ! check if world_rank is out of range
!     if (world_rank < 0 .or. world_rank >= total_cores) then
!         print *, "Error: world_rank out of range."
!         return
!     endif

!     ! assign the position of the process in the process grid
!     if (world_rank < IOT1_core_number) then
!         proc_grid_rows = mod(world_rank, IOT1_core_number/ydim)+1
!         proc_grid_cols = id/xdim+1
!     elseif (IOT1_core_number <= world_rank .and. world_rank < IOT1_core_number + IOT2_core_number) then
!         proc_grid_rows = mod(world_rank-IOT1_core_number, IOT2_core_number/ydim)+1
!         proc_grid_cols = id/xdim+1
!     elseif (IOT1_core_number + IOT2_core_number <= world_rank .and. world_rank < IOT1_core_number + IOT2_core_number + IOT3_core_number) then
!         proc_grid_rows = mod(world_rank-IOT1_core_number-IOT2_core_number, IOT3_core_number/ydim)+1
!         proc_grid_cols = id/xdim+1
!     else
!         proc_grid_rows = mod(world_rank-IOT1_core_number-IOT2_core_number-IOT3_core_number, IOT4_core_number/ydim)+1
!         proc_grid_cols = id/xdim+1
!     endif
! end subroutine getProcGridRowandCol

     
    ! get the number of CPU cores
    function get_cpu_cores() result(cores)
        integer :: cores
        integer :: unit, ios
        character(len=1024) :: buffer

        cores = 0
        unit = 10 ! choose a free unit number

        open(unit=unit, file='/proc/cpuinfo', status='old', action='read', iostat=ios)
        if (ios /= 0) then
            print *, '[ERROR]: Failed to open /proc/cpuinfo'
            stop 1
        endif
        do
            read(unit, '(A)', iostat=ios) buffer
            if (ios /= 0) exit
            if (index(buffer, 'processor') == 1) cores = cores + 1
        end do

        close(unit)
    end function get_cpu_cores



end module mylib    


