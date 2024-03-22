#include <time.h> 
#include <sys/types.h>
#include <fcntl.h>
#include <sys/stat.h> 
#include <unistd.h> 
#include <stdlib.h>
#include <stdio.h> 
#include <signal.h> 
#include <string.h>
#include <poll.h> 

int gpio = 17;

int loopTime = 10;
static char output_path[512]; 
static char output_file[512] = "output.txt"; 

int main(int nargs, char ** args){

    if (nargs > 1){
        int elements_in_x = sizeof(args) / sizeof(args[0]);
        //printf("length of args array %d\n", elements_in_x);
        //printf("args are %s\n",args[2]);
        gpio = atoi(args[1]);
        sprintf(output_file,"gpio%dMon.txt",gpio);
        if(nargs>2) loopTime = atoi(args[2]);
        if(nargs>3) {
            //printf(" path is %s\n", args[3]);
            sprintf(output_path,args[3]);
            strcat(output_path,"/");
        }
    } 
    strcat(output_path,output_file);
    printf("gpio %d\n", gpio);
    printf("path is %s\n",output_path);
    printf("looping for %d seconds\n", loopTime);

    struct timespec when;
    clock_gettime(CLOCK_REALTIME,&when);
    //printf("time is %d.%09d\n",when.tv_sec, when.tv_nsec);
    int startTime = when.tv_sec;
    printf("startTime is %d\n", startTime);

    int endTime = when.tv_sec + loopTime;

    //printf("endTime is %d\n", endTime);

    
    FILE *fptr;
    double timeSleep = 500000;
    fptr = fopen(output_path, "w");
    while(when.tv_sec < endTime){
        clock_gettime(CLOCK_REALTIME,&when);
        printf("time is %d.%09d\n",when.tv_sec, when.tv_nsec);
        fprintf(fptr, "time is %d.%09d\n",when.tv_sec, when.tv_nsec);
        usleep(timeSleep);
        
    }

    

    
    
    // Open a file in writing mode
    

    // Write some text to the file
    
    
    
    


    // Close the file
    fclose(fptr);
    
    

}