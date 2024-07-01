
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

    subroutine computeRowsPerProcess(comm_solve,world_rank, world_size, N, IOT1_ratio, IOT2_ratio,&
         IOT3_ratio, IOT4_ratio, IOT1_CORE_NUMBER,IOT2_CORE_NUMBER,&
        IOT3_CORE_NUMBER,IOT4_CORE_NUMBER, start_row, num_rows)
        integer, intent(in) :: world_rank, world_size, N
        integer, intent(in) :: comm_solve
        real, intent(in) :: IOT1_ratio, IOT2_ratio, IOT3_ratio, IOT4_ratio
        integer, intent(in) :: IOT1_CORE_NUMBER, IOT2_CORE_NUMBER,IOT3_CORE_NUMBER, IOT4_CORE_NUMBER
        integer, intent(out) :: start_row, num_rows
        integer :: IOT1_ROWS_PER_PROCESS, IOT2_ROWS_PER_PROCESS,IOT3_ROWS_PER_PROCESS, IOT4_ROWS_PER_PROCESS
        integer :: cpu_cores, ierr
        integer :: total_iot_core_number

        IOT1_ROWS_PER_PROCESS = N * IOT1_ratio / IOT1_CORE_NUMBER
        IOT2_ROWS_PER_PROCESS = N * IOT2_ratio / IOT2_CORE_NUMBER
        IOT3_ROWS_PER_PROCESS = N * IOT3_ratio / IOT3_CORE_NUMBER
        IOT4_ROWS_PER_PROCESS = (N - IOT1_ROWS_PER_PROCESS * IOT1_CORE_NUMBER - IOT2_ROWS_PER_PROCESS * IOT2_CORE_NUMBER &
            & - IOT3_ROWS_PER_PROCESS * IOT3_CORE_NUMBER) / IOT4_CORE_NUMBER
        
        ! 检查iot1_ratio, iot2_ratio, iot3_ratio, iot4_ratio 是否为0，从而得到需要分配的device数量
        
        total_iot_core_number = 0
        if (IOT1_ratio /= 0.0) then
            total_iot_core_number = total_iot_core_number + IOT1_CORE_NUMBER
        endif
        if (IOT2_ratio /= 0.0) then
            total_iot_core_number = total_iot_core_number + IOT2_CORE_NUMBER
        endif
        if (IOT3_ratio /= 0.0) then
            total_iot_core_number = total_iot_core_number + IOT3_CORE_NUMBER
        endif
        if (IOT4_ratio /= 0.0) then
            total_iot_core_number = total_iot_core_number + IOT4_CORE_NUMBER
        endif
        ! write(*,*) "[DEBUG]: total_iot_core_number: ", total_iot_core_number
        cpu_cores = get_cpu_cores()
        
        ! if the sum of IOT1_ratio, IOT2_ratio, IOT3_ratio, and IOT4_ratio is not 1, then abort the program
        if (abs(IOT1_ratio + IOT2_ratio + IOT3_ratio + IOT4_ratio - 1.0) > 1e-6) then
            write(*,*) "[ERROR]: The sum of IOT1_ratio, IOT2_ratio, IOT3_ratio, and IOT4_ratio should be 1"
            call MPI_Abort(comm_solve, 1, ierr)
        endif

        ! if the number of CPU cores does not match the number of IOT cores, then abort the program
        if (world_rank < IOT1_CORE_NUMBER .and. IOT1_RATIO /= 0.0) then
            if (cpu_cores /= IOT1_CORE_NUMBER) then
                write(*,*) "[ERROR]: The number of CPU cores does not match the number of IOT1 cores"
                write(*,*) "[ERROR]: Detected cpu cores: ", cpu_cores, "IOT1_core_number: ", IOT1_CORE_NUMBER
                call MPI_Abort(comm_solve, 1, ierr)
            endif
            start_row = world_rank * IOT1_ROWS_PER_PROCESS - 1
            num_rows = IOT1_ROWS_PER_PROCESS
        elseif (world_rank >= IOT1_CORE_NUMBER .and. world_rank < IOT1_CORE_NUMBER &
                + IOT2_CORE_NUMBER .and. IOT2_RATIO /= 0.0) then
            if (cpu_cores /= IOT2_CORE_NUMBER) then
                write(*,*) "[ERROR]: The number of CPU cores does not match the number of IOT2 cores"
                write(*,*) "[ERROR]: Detected cpu cores: ", cpu_cores, "IOT2_core_number: ", IOT2_CORE_NUMBER
                call MPI_Abort(comm_solve, 1, ierr)
            endif
            start_row = IOT1_CORE_NUMBER * IOT1_ROWS_PER_PROCESS + (world_rank - IOT1_CORE_NUMBER) * IOT2_ROWS_PER_PROCESS -1
            num_rows = IOT2_ROWS_PER_PROCESS
        elseif (world_rank >= IOT1_CORE_NUMBER + IOT2_CORE_NUMBER .and. &
             world_rank < IOT1_CORE_NUMBER + IOT2_CORE_NUMBER + IOT3_CORE_NUMBER .and. IOT3_RATIO /= 0.0) then
            if (cpu_cores /= IOT3_CORE_NUMBER) then
                write(*,*) "[ERROR]: The number of CPU cores does not match the number of IOT3 cores"
                write(*,*) "[ERROR]: Detected cpu cores: ", cpu_cores, "IOT3_core_number: ", IOT3_CORE_NUMBER
                call MPI_Abort(comm_solve, 1, ierr)
            endif
            start_row = IOT1_CORE_NUMBER * IOT1_ROWS_PER_PROCESS + IOT2_CORE_NUMBER * IOT2_ROWS_PER_PROCESS &
                    & + (world_rank - IOT1_CORE_NUMBER - IOT2_CORE_NUMBER) * IOT3_ROWS_PER_PROCESS - 1
            num_rows = IOT3_ROWS_PER_PROCESS
        else  ! 对于IOT4设备
            if (cpu_cores /= IOT4_CORE_NUMBER) then
                write(*,*) "[ERROR]: The number of CPU cores does not match the number of IOT4 cores"
                write(*,*) "[ERROR]: Detected cpu cores: ", cpu_cores, "IOT4_core_number: ", IOT4_CORE_NUMBER
                call MPI_Abort(comm_solve, 1, ierr)
            endif
            start_row = IOT1_CORE_NUMBER * IOT1_ROWS_PER_PROCESS + IOT2_CORE_NUMBER * IOT2_ROWS_PER_PROCESS &
                    & + IOT3_CORE_NUMBER * IOT3_ROWS_PER_PROCESS + (world_rank - IOT1_CORE_NUMBER - IOT2_CORE_NUMBER &
                    & - IOT3_CORE_NUMBER) * IOT4_ROWS_PER_PROCESS - 1
            num_rows = IOT4_ROWS_PER_PROCESS
        endif

        ! 以下是检查最后一个进程和行数的代码，可以保持不变
        if (world_rank == total_iot_core_number - 1) then
            num_rows = N - start_row - 1
        endif
        if (num_rows < 0) then
            num_rows = 0
        endif

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


