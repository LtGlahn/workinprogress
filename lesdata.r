library(lubridate)

setwd( "D:/data/jobb/workinprogress")
df <- read.csv2('statistikk-sinus-20190917.csv', fileEncoding = 'utf-8')

mydate <- lubridate::floor_date( lubridate::as_datetime(df['mottatt']) ) 


myplot <- ggplot( df ) + aes( x = format( df$dato, "%Y-%m"), fill = format(df$dato, "%Y" )) + geom_bar() + theme(axis.text.x=element_blank())
myplot + labs( fill = '', x = 'Antall endringssett SINUS.infra per mnd')


# dev.print( png, 'sinus2016-2019.png', width=600)


df2019 <- subset( df, dato > as.Date( "2018-12-31"))

myplot2 <- ggplot( df2019 ) + aes( x = format( df2019$dato, "%%m") ) + geom_bar()



