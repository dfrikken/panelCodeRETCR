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

// to do 

    // file writing function to hold timestamps

//to use run these 
// gcc gpioMonitor.c -o gpioNMonitor
// chmod +x gpioNMonitor
// ./gpioNMonitor


// two panels currently on 17 and 22
int gpio = 17;
//int gpio = 22;

static char edge_path[512]; 
static char val_path[512]; 
static char output_path[512]; 
static char output_file[512] = "output.txt"; 

static volatile int do_quit = 0;
void handler(int sig) 
{
  (void) sig; 
  do_quit=1; 
}


static char buf[128];
int main(int nargs, char ** args) 
{

  if (nargs > 1){
    int elements_in_x = sizeof(args) / sizeof(args[0]);
        printf("length of args array %d\n", elements_in_x);
        printf("args are %s\n",args[2]);
        gpio = atoi(args[1]);
        sprintf(output_file,"gpio%dMon.txt",gpio);
  
        if(nargs>2) {
            printf(" path is %s\n", args[2]);
            sprintf(output_path,args[2]);
            strcat(output_path,"/");
        }

  } 

  strcat(output_path,output_file);
  printf("gpio %d\n", gpio);
  printf("path is %s\n",output_path);
  

  sprintf(edge_path,"/sys/class/gpio/gpio%d/edge",gpio); 

  sprintf(val_path,"/sys/class/gpio/gpio%d/value", gpio); 

  if (access(edge_path,F_OK))
  {
    fprintf(stderr,"No %s, will try exporting\n", edge_path);
    FILE * fexport = fopen("/sys/class/gpio/export","w"); 
    fprintf(fexport,"%d\n", gpio);
    fclose(fexport); 
    sleep(1); 
    if (access(edge_path,F_OK))
    {
      fprintf(stderr,"exporting failed!!\n");
      return 1; 
    }
  }


  int edge_fd = open(edge_path,O_RDWR); 
  int val_fd = open(val_path,O_RDONLY); 



  write(edge_fd,"rising",6);  // make sure to change the trailing number to length of trigger type 

  struct pollfd fdset; 

  FILE *fptr;
  //fptr = fopen(output_path, "w");
  //printf("output file is %s\n", output_path);
  if (access(output_path, F_OK) == 0) {
      // file exists
      fptr = fopen(output_path, "a");
      fprintf(fptr,"\nscheduled triggers complete\n");
      printf("gpio monitor file exists opening with append to add full run\n");
  } else {
      fptr = fopen(output_path, "w");
      printf("gpio mon file does not exist, creating...\n");
      // file doesn't exist
  }

  printf("Starting loop, ctrl-c to stop\n"); 
  signal(SIGINT, handler); 

  struct timespec when; 

  int nint = 0;
  clock_gettime(CLOCK_REALTIME,&when);
  int startTime = when.tv_sec;
  //printf("startTime is %d\n", startTime);

  

  while(!do_quit) 
  {
    
    memset(buf,0,sizeof(buf)); 
    memset(&fdset,0,sizeof(fdset)); 

    fdset.fd = val_fd; 
    fdset.events = POLLPRI; 

    int rc = poll(&fdset,1,-1); 
    clock_gettime(CLOCK_REALTIME,&when);
    if (fdset.revents & POLLPRI) 
    {
      
      lseek(fdset.fd,0,SEEK_SET); 
      int len = read(fdset.fd,buf,sizeof(buf)-1); 
      if (nint) {
          printf("gpio%d [%d] TIMER: %c at %d.%09d\n",gpio, nint, buf[0], when.tv_sec, when.tv_nsec); 
          fprintf(fptr,"%d,%d.%09d\n",gpio, when.tv_sec, when.tv_nsec); 
      }
      //printf("time is %d\n",when.tv_sec);
        
    }
    nint++; 
   
  }


  write(edge_fd,"none",4); 
  fclose(fptr);
}