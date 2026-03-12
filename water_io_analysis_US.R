####Packages####
library(dplyr, warn.conflicts = FALSE)
library(survey)
library(srvyr)
library(plyr)
library(dineq)
library(tidyverse)
library(reshape)
library(reshape2)
library(readr)
library(ggplot2)
library(gridExtra)
library(scales)
library(knitr)
library(kableExtra)
library(frequency)
library(purrr)
library(stargazer)
library(sf)
library(stats)
library(spatstat.geom)
library(readxl)
library(hrbrthemes)
library(viridis)
library(formattable)
library(xtable)
#### Let's load the Data ####
###### Kurt Semm - July 5
##### Dec. 9th - beginning of ninth chapter
#set working directory#
setwd("~/Library/CloudStorage/OneDrive-barnard.edu/input-output/input-output")
#### For 1997 through 2021, and projected 2031, the OUPUT tables shown below can be replicated by adding either the USE or MAKE tables above. Like the USE and MAKE tables above, all file names shown below begin with NOMINAL, REAL, or PROJECTED.
#### OUTPUT_IND9721 - 1997-2021 historical industry output time series (columns 1 through 24 respectively)
#### OUTPUT_COM9721 - 1997-2021 historical commodity output time series (columns 1 through 24 respectively)
hist_ind<-read.csv("REAL_OUTPUT_IND9721.csv")
hist_comm<-read.csv("REAL_OUTPUT_COM9721.csv")
#### This is followed by the name of the I-O table and the table year.
#### USE - 195 rows and 195 columns of data (row 195 is value added, column 195 is final demand, the rest are the intermediate cells)
#### MAKE - 194 rows and 194 columns of data
#### FD - 194 commodity rows and 153 detailed final demand sectors of data
#### FDAGG - 194 commodity rows and 11 final demand categories of data aggregated from the 153 sectors mentioned above

#load use_io data in list# 
setwd("~/Library/CloudStorage/OneDrive-barnard.edu/input-output/input-output/IOREAL/REAL_USE")
use_io = list.files(pattern="*.csv")
usefiles = lapply(use_io, read.csv, check.name=F)

#### other io matrices ####
#load data for Make# 
setwd("~/Library/CloudStorage/OneDrive-barnard.edu/input-output/input-output/IOReal/REAL_MAKE")
make_io = list.files(pattern="*.csv")
makefiles = lapply(make_io, read.csv, check.name=F)

#load data for FD#
setwd("~/Library/CloudStorage/OneDrive-barnard.edu/input-output/input-output/IOReal/REAL_FD")
fd_io = list.files(pattern="*.csv")
fdfiles = lapply(fd_io, read.csv)

#load data for FDAGG#
setwd("~/Library/CloudStorage/OneDrive-barnard.edu/input-output/input-output/IOReal/REAL_FDAGG")
fdagg_io = list.files(pattern="*.csv")
fdaggfiles = lapply(fdagg_io, read.csv)

#### ioanalysis package attempt ####
## We just made a bunch of lists with different years and such, 
## now we should see how we can evaluate ioanalysis package and sector 40 or water and wastewater
## Let's see how much of total water use is wastewater or goes to sanitation. Couldn't find. checkout other USGA.
library(ioanalysis)
library(readxl)
# I want to run the following code as an input-ouptut model
# the cool part about the package in R is provides us several values.
# First we analyze the whole system and then we determine the influence of water on the whole system, sector by sector.  
# Start with 2021 #
setwd("~/Library/CloudStorage/OneDrive-barnard.edu/input-output/input-output")

use_io_2021<-usefiles[[25]]
colnames(use_io_2021)[colnames(use_io_2021)=="SECTORNUMBER"]<-'sector'
colnames(use_io_2021)<-gsub("X","",colnames(use_io_2021))
sector_labels<-read_xlsx("SectorPlan29.xlsx", sheet = "Stubs")
eco.labels<-sector_labels$`Sector Title`[1:195]
eco.names <- setNames(eco.labels, LETTERS[1 : 195])

labels<-sector_labels %>% 
  select(`Sector Number`, `Sector Title`)
xtable(labels)

df_eio<-use_io_2021 %>%
  add_column(region="USA", .before="sector") %>% 
  add_row(region="USA", .before = 1) %>% 
  add_row(sector=1, .before =1) 

rownames(df_eio)[rownames(df_eio)=="1"]<-"region"
rownames(df_eio)[rownames(df_eio)=="2"]<-"sector"
df_eio[1, ] <- "USA"
df_eio[2, - c(1:2)] <- 1 : 195
df_eio[1:2, 1:2] <- NA
df_eio[3 : 197, 2] <- eco.names
df_eio[2, 3 : 197] <- eco.names
## input-output table complete - 12/10. io object is named "df_eio"
#Change last column name (196) to Total Demand, currently it reads Value-Added.
df_eio[2, 197]="Total Demand"

df_eio_m <- as.matrix(df_eio) #this turns our dataframe into a matrix, array. Do not use data.matrix, instead use as.matrix.

#### Leontief Package Attempt ####
library(leontief)

Xt<-transaction_matrix
X <- matrix(as.numeric(unlist(use_io_2021[1:195,2:194])),ncol=195)
w <- wage_demand_matrix[, "wage"]
c <- wage_demand_matrix[, "household_consumption"]
dt <- wage_demand_matrix[, "final_total_demand"]
d <- as.numeric(unlist(use_io_2021[196,2:194]))
e <- employment_matrix[, "employees"]

## Direct COefficient Matrix
A<-input_requirement(X,d)

## Output Allocation Matrix 
B<-output_allocation(X,d)
rownames(B)<-rownames(X)
colnames(B)<-rownames(X)
kable(B)

## Leontief Inverse Matrix
L<-leontief_inverse(A); 
rownames(L) <- rownames(X)
colnames(L) <- rownames(X)
kable(L)

## Equilibrium Output
eq <- equilibrium_output(L,d)
rownames(eq) <- rownames(X)
colnames(eq) <- "output"
kable(eq)

View(wage_demand_matrix)

# In toy,FullIOTable it is a full matrix of characters: a pseudo worst case scenario
data(toy.FullIOTable)
Z <- matrix(as.numeric(toy.FullIOTable[3:12, 3:12]), ncol = 10)
f <- matrix(as.numeric(toy.FullIOTable[3:12, c(13:15, 17:19)]), nrow = dim(Z)[1])
E <- matrix(as.numeric(toy.FullIOTable[3:12, c(16, 20)]), nrow = 10)
X <- matrix(as.numeric(toy.FullIOTable[3:12, 21]), ncol = 1)
V <- matrix(as.numeric(toy.FullIOTable[13:15, 3:12]), ncol = 10)
M <- as.numeric(toy.FullIOTable[16, 3:12])
fV <- matrix(as.numeric(toy.FullIOTable[15:16, c(13:15,17:19)]), nrow = 2)

# Note toy.FullIOTable is a matrix of characters: non-numeric
toy.IO <- as.inputoutput(Z = Z, RS_label = toy.FullIOTable[3:12, 1:2],
                         f = f, f_label = toy.FullIOTable[1:2, c(13:15, 17:19)],
                         E = E, E_label = toy.FullIOTable[1:2, c(16, 20)],
                         X = X,
                         V = V, V_label = toy.FullIOTable[13:15, 2],
                         M = M, M_label = toy.FullIOTable[16,2],
                         fV = fV, fV_label = toy.FullIOTable[15:16, 2])

# Notice we do not need to supply the matrix of technical coefficients (A)
# In toy,FullIOTable it is a full matrix of characters: a pseudo worst case scenario
data(toy.FullIOTable)
Z <- matrix(as.numeric(toy.FullIOTable[3:12, 3:12]), ncol = 10)
f <- matrix(as.numeric(toy.FullIOTable[3:12, c(13:15, 17:19)]), nrow = dim(Z)[1])
E <- matrix(as.numeric(toy.FullIOTable[3:12, c(16, 20)]), nrow = 10)
X <- matrix(as.numeric(toy.FullIOTable[3:12, 21]), ncol = 1)
V <- matrix(as.numeric(toy.FullIOTable[13:15, 3:12]), ncol = 10)
M <- as.numeric(toy.FullIOTable[16, 3:12])
fV <- matrix(as.numeric(toy.FullIOTable[15:16, c(13:15,17:19)]), nrow = 2)

# Note toy.FullIOTable is a matrix of characters: non-numeric
toy.IO <- as.inputoutput(Z = Z, RS_label = toy.FullIOTable[3:12, 1:2],
                         f = f, f_label = toy.FullIOTable[1:2, c(13:15, 17:19)],
                         E = E, E_label = toy.FullIOTable[1:2, c(16, 20)],
                         X = X,
                         V = V, V_label = toy.FullIOTable[13:15, 2],
                         M = M, M_label = toy.FullIOTable[16,2],
                         fV = fV, fV_label = toy.FullIOTable[15:16, 2])

# Notice we do not need to supply the matrix of technical coefficients (A)
#### Use this package with Oriol because it requires different regions. - KS 8/7/23 - FAIL####
Z <- matrix(as.numeric(unlist(use_io_2021[2:194, 2:194])), ncol = 193)
f <- matrix(as.numeric(use_io_2021[2:194, c(180:191)]), nrow = dim(Z)[1])
#E <- matrix(as.numeric(use_io_2021[2:194, c(1620)]), nrow = 193)
X <- matrix(as.numeric(use_io_2021[2:194, 195]), ncol = 193)
V <- matrix(as.numeric(use_io_2021[196, 2:194]), ncol = 193)
M <- as.numeric(use_io_2021[16, 3:12])
fV <- matrix(as.numeric(use_io_2021[15:16, c(13:15,17:19)]), nrow = 2)

#### CREATING IO matrix for calculations ####
## 10/27 - Meeting with Oriel Prep ##
## 12/10 UPDATE ##

data("toy.FullIOTable")

Z <- matrix(as.numeric(toy.FullIOTable[3:12, 3:12]), ncol = 10)
f <- matrix(as.numeric(toy.FullIOTable[3:12, c(13:15, 17:19)]), nrow = dim(Z)[1])
E <- matrix(as.numeric(toy.FullIOTable[3:12, c(16, 20)]), nrow = 10)
X <- matrix(as.numeric(toy.FullIOTable[3:12, 21]), ncol = 1)
V <- matrix(as.numeric(toy.FullIOTable[13:15, 3:12]), ncol = 10)
M <- as.numeric(toy.FullIOTable[16, 3:12])
fV <- matrix(as.numeric(toy.FullIOTable[15:16, c(13:15,17:19)]), nrow = 2)

# Note toy.FullIOTable is a matrix of characters: non-numeric
toy.IO <- as.inputoutput(Z = Z, RS_label = toy.FullIOTable[3:12, 1:2],
                         f = f, f_label = toy.FullIOTable[1:2, c(13:15, 17:19)],
                         E = E, E_label = toy.FullIOTable[1:2, c(16, 20)],
                         X = X,
                         V = V, V_label = toy.FullIOTable[13:15, 2],
                         M = M, M_label = toy.FullIOTable[16,2],
                         fV = fV, fV_label = toy.FullIOTable[15:16, 2])
summary(toy.IO)

# MY DATA 
Z_eco <- matrix(as.numeric(df_eio_m[3:179, 3:179]), ncol = 177)
f_eco <- matrix(as.numeric(df_eio_m[3:179, c(180:191)]), nrow = dim(Z_eco)[1])
#E_eco <- matrix(as.numeric(df_eio[3:196, c(194)]), nrow = 10) #dont have exports in this data.
X_eco <- matrix(as.numeric(df_eio_m[3:197, 197]), ncol = 1)#total demand
V_eco <- matrix(as.numeric(df_eio_m[180:191, 3:179]), ncol = 177)#value added
M_eco <- as.numeric(df_eio_m[196, 3:196]) 
fV_eco <- matrix(as.numeric(df_eio_m[15:16, c(13:15,17:19)]), nrow = 2)#total demands value added, this will be the last row of data set, not column. 


# number of sectors
n <- nrow(Z_eco)  # 177

# rebuild X_eco (total demand) to match Z_eco rows 3:(2+n)
X_eco <- matrix(
  as.numeric(df_eio_m[3:(2 + n), 197]),
  ncol = 1
)

# region‐sector labels must also be 177 rows
RS_label <- df_eio[3:(2 + n), 1:2]

# imports vector must be length n
M_eco <- as.numeric(
  df_eio_m[196, 3:(2 + n)]
)
# number of sectors
n <- nrow(Z_eco)  # should be 177

# rebuild V and its labels so they align
V_eco   <- matrix(as.numeric(df_eio_m[180:(179 + n - 177), 3:(2 + n2)]),
                  ncol = n2)
# but since 180:191 was already your 12 rows, simply:
V_eco   <- matrix(as.numeric(df_eio_m[180:191, 3:179]), ncol = n2)

V_label <- df_eio[180:191, 2]   # now 12 labels, one per row of V_eco

# (re)check the alignment
stopifnot(nrow(V_eco) == length(V_label))  

# now call as.inputoutput with matching dimensions
US.IO <- as.inputoutput(
  Z        = Z_eco,
  RS_label = RS_label,
  f        = f_eco,
  f_label  = df_eio[1:2, 180:191],
  X        = X_eco,
  V        = V_eco,
  V_label  = df_eio[13:15, 2],
  M        = M_eco,
  M_label  = df_eio[196, 2],
  fV       = fV_eco,
  fV_label = df_eio[15:16, 2]
)









US.IO <- as.inputoutput(
  Z          = Z_eco,
  RS_label   = df_eio[3:196,   1:2],        # region‐sector labels
  f          = f_eco,
  f_label    = df_eio[1:2,    180:191],     # final demand labels
  # E and E_label omitted if you don’t have exports
  X          = X_eco,
  V          = V_eco,
  V_label    = df_eio[13:15,    2],         # value‐added labels
  M          = M_eco,
  M_label    = df_eio[196,      2],         # import labels
  fV         = fV_eco,
  fV_label   = df_eio[15:16,    2]          # “value‐added of final demand” labels
)
## Goal for tomorrow is to run this below. 
US.IO<-as.inputoutput(Z = Z_eco, RS_eco_label = df_eio[3:196, 1:2],
                      f = f_eco, f_eco_label = df_eio[1:2, c(180:191)],
                      X = X_eco,
                      V = V_eco, V_eco_label = df_eio[13:15, 2],
                      M = M_eco, M_eco_label = df_eio[196,2],
                      fV = fV_eco, fV_eco_label = df_eio[15:16, 2])
