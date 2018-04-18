# Introduction
This dashboard lets users explore different neighborhoods in different cities in Italy using data from ISTAT and other public sources. Currently under development.

This application uses React and has been built with [Create React App](https://github.com/facebookincubator/create-react-app).

# Use
`npm i` and `npm start` and you should see a dashboard at `localhost:3000`

# Input data
The visualization requires a geojson file (exported into js) of polygons (the neighborhhods) and json files, and a menu.json file describing the data.

## Indicators
Two indicators have been computed:
* tipi di alloggio (tipiAlloggio)
* densità di occupati (densitaOccupati)
and printed to the [results.js](src/data/Milano/results.js) file and [results.js](src/data/Torio/results.js) file.
From the Istat data and from the area of the polygons, in R:

    data.csv <- read.csv(file="data.csv", sep=";", header=TRUE)
    tableNILAreaMQ.csv <- read.csv(file="tableNILAreaMQ.csv"), sep=";", header=TRUE)
    data.csv[data.csv=="-"] <- 0
    NIL = tableNILAreaMQ.csv[,1]
    results = c();
    for (n in NIL) {
        nildata.csv = data.csv[which(data.csv[,9]==n), c(3,4,5,6,7,8)]
        	
        numOccupati = as.numeric(nildata.csv[,2])
        densitaOccupati = sum(numOccupati)/tableNILAreaMQ.csv[which(tableNILAreaMQ.csv[,1]==n),2]

        #sum(E17*1+E18*2+E19*3+E20*4)/sum(E17+E18+E19+E20)
        numAlloggi1Piano = as.numeric(nildata.csv[,3]
        numAlloggi2Piani = as.numeric(nildata.csv[,4])
        numAlloggi3Piani = as.numeric(nildata.csv[,5])
        numAlloggi4PianiOPiu = as.numeric(nildata.csv[,6])
        numTotAlloggi = sum(numAlloggi1Piano + numAlloggi2Piani + numAlloggi3Piani + numAlloggi4PianiOPiu)
        tipiAlloggio = sum(numAlloggi1Piano + numAlloggi2Piani * 2 + numAlloggi3Piani * 3 + numAlloggi4PianiOPiu * 4) / sum(numTotAlloggi)
        
        results = rbind(results, c(n, densitaOccupati, tipiAlloggio))
    }
    #Write results file
    write.table(results, "results.csv", row.names=FALSE, sep=";", quote=FALSE)
    

