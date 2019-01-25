import requests
import csv
import re
import pandas as pd
import time
from bs4 import BeautifulSoup
import os
from numpy import arange
#re-assign these page URLs to other teams to scrape other national team data
page1 = "http://stats.espnscrum.com/statsguru/rugby/stats/index.html?class=1;orderby=date;spanmax1=1st+Dec+201;spanmax2=1+Dec+2018;spanmin1=13+Oct+2003;spanmin2=13+Oct+2003;spanval1=span;spanval2=span;team=8;template=results;type=team;view=match"
page2 = "http://stats.espnscrum.com/statsguru/rugby/stats/index.html?class=1;orderby=date;page=2;spanmax1=1st+Dec+201;spanmax2=1+Dec+2018;spanmin1=13+Oct+2003;spanmin2=13+Oct+2003;spanval1=span;spanval2=span;team=8;template=results;type=team;view=match"
page3 = "http://stats.espnscrum.com/statsguru/rugby/stats/index.html?class=1;orderby=date;page=3;spanmax1=1st+Dec+201;spanmax2=1+Dec+2018;spanmin1=13+Oct+2003;spanmin2=13+Oct+2003;spanval1=span;spanval2=span;team=8;template=results;type=team;view=match"
page4 = "http://stats.espnscrum.com/statsguru/rugby/stats/index.html?class=1;orderby=date;page=4;spanmax1=1st+Dec+201;spanmax2=1+Dec+2018;spanmin1=13+Oct+2003;spanmin2=13+Oct+2003;spanval1=span;spanval2=span;team=8;template=results;type=team;view=match"
page5 = "http://stats.espnscrum.com/statsguru/rugby/stats/index.html?class=1;orderby=date;page=5;spanmax1=1st+Dec+201;spanmax2=1+Dec+2018;spanmin1=13+Oct+2003;spanmin2=13+Oct+2003;spanval1=span;spanval2=span;team=8;template=results;type=team;view=match"

startpos = 0

columns = ['Opposition Name','Date','Result','Location','Opposition tries in last 5 games','All Black tries in last 5 games']
ABMatchData = pd.DataFrame(columns=columns,index=range(0,204))

#define function to Populate Columns
def populate_first4col(url, endoftable, startpos, dateendindx, resultendpos, TeamMatchData):
    response = requests.get(url)
    content = response.content
    parser = BeautifulSoup(content, 'html.parser')

#extract HTML tags, only a portion of this list contains texts for opposition team name
    AllItemsList = parser.find_all('td', class_="left")
    TextList = []
    OppName = []

#extract list of HTML tags for dates and convert to Series
    DatesList = []
    AllDatesList = []
    DatesList = parser.find_all('b')
    DatesList = DatesList[4:dateendindx]
    for date in DatesList:
        AllDatesList.append(date.text)
    AllDatesSeries = pd.Series(AllDatesList)

#extract texts of opposition names from list of HTML tags
    pos = 2
    for item in AllItemsList:
        TextList.append(item.text)


#extract only the texts of opposition team name and convert to series
    pos = 2
    for x in range(0,len(AllItemsList)):
        if pos == x:
            OppName.append(TextList[pos])
            pos = pos + 4

    OppNameSeries = pd.Series(OppName)

#extract list of HTML tags for result and convert to Series
    ResultList = []
    TextResultList = []
    ResultOnlyList = []
    ResultList = parser.find_all('td')

    for result in ResultList:
        TextResultList.append(result.text)

#len(TextResultList)
    pos = 13
    #resultendpos = 700
    for x in range(0,len(TextResultList)):
         if ((x==pos)and(x<resultendpos)):
           # print(TextResultList[x])
            ResultOnlyList.append(TextResultList[pos])
            pos = pos + 14

    ResultSeries = pd.Series(ResultOnlyList)
    pos = 0

#extract list of HTML tags for location and convert to Series
    GroundList = []
    TextGroundList = []
    GroundOnlyList = []
    GroundList = parser.find_all('a',class_='data-link')
    for x in range(0,len(GroundList)):
        if((x%2)!=0):
            GroundOnlyList.append(GroundList[x].text)

    LocationSeries=pd.Series(GroundOnlyList)


#add Series of opposition names,dates,result and location to MatchData
    for x in range(startpos,endoftable):
        TeamMatchData.loc[x,'Opposition Name']=OppNameSeries[pos]
        TeamMatchData.loc[x,'Date']=AllDatesSeries[pos]
        TeamMatchData.loc[x,'Result']=ResultSeries[pos]
        TeamMatchData.loc[x,'Location']=LocationSeries[pos]
        pos = pos + 1

    pos = 0
    #print(ResultSeries)

    startpos = endoftable
    return startpos


#call function on each page
#populate_first4col(page number(url string),cummulative number of matches in page(int),startpos(int)
# dateendindx(int, check the ending index of the date,int), resultendpos(check ending index of result, int), TeamMatchData(dataframe))
startpos = populate_first4col(page1,50,startpos,54,700,ABMatchData)
startpos = populate_first4col(page2,100,startpos,54,700,ABMatchData)
startpos = populate_first4col(page3,150,startpos,54,700,ABMatchData)
startpos = populate_first4col(page4,200,startpos,54,700,ABMatchData)
startpos = populate_first4col(page5,205,startpos,9,70,ABMatchData)

#Clean Opposition Name column to make URL to scrape tries in last 5 games
#re-assign this range(205) specific to team.
for x in range(0,205):
    name = str(ABMatchData.loc[x,'Opposition Name'])
    cleanname=re.sub('v ','',name)
    ABMatchData.loc[x,'Opposition Name']=cleanname

#Get list of Unique Opponents
OppList = ABMatchData['Opposition Name'].unique()

#Make series with custom index for URL construction
OppList.sort()
OppList
index=[10,6,25,1,14,9,81,3,20,23,32,82,121,27,12,15,2,5,16,11,4]
OppSeries = pd.Series(OppList,index=index)

#Tries in Last 5 games URL parts
urlpart1 = 'http://stats.espnscrum.com/statsguru/rugby/stats/index.html?class=1;orderby=date;orderbyad=reverse;spanmax2='
urlpart2 = ''#format is: 17+Oct+2003
urlpart3 = ';spanmin2=1+Jan+2000;spanval2=span;team='
urlpart4 = ''#ints from OppSeries index
urlpart5 = ';template=results;type=team;view=match'
accumtries = 0

#Make complete URL to scrape try data from previous 5 games
for x in range(0,205):
    AllTagText = []
    date=ABMatchData.loc[x,'Date']
    urlpart2=str(re.sub(' ','+',date))
    oppname=ABMatchData.loc[x,'Opposition Name']
    urlpart4=str(OppSeries[OppSeries==oppname].index[0])
    FullURL = urlpart1+urlpart2+urlpart3+urlpart4+urlpart5
#start scraping again with new URL
    time.sleep(10)
    response = requests.get(FullURL)
    content = response.content
    parser = BeautifulSoup(content, 'html.parser')
    AllTriesTagList = parser.find_all('td')
    for tag in AllTriesTagList:
        AllTagText.append(tag.text)
    trylocations=[28,42,56,70,84]
    for loc in trylocations:
        try:
            accumtries = accumtries + int(AllTagText[loc])
            ABMatchData.loc[x,'Opposition tries in last 5 games']=accumtries
        except Exception:
            ABMatchData.loc[x,'Opposition tries in last 5 games']=accumtries
    ABMatchData.loc[x,'Opposition tries in last 5 games']=accumtries

    accumtries = 0

#Insert tries in last 5 games for All Blacks

#Tries in Last 5 games URL parts for All Blacks
urlpart1 = 'http://stats.espnscrum.com/statsguru/rugby/stats/index.html?class=1;orderby=date;orderbyad=reverse;spanmax2='
urlpart2 = ''#format is: 17+Oct+2003
urlpart3 = ';spanmin2=1+Jan+2000;spanval2=span;team=8;template=results;type=team;view=match'
accumtries = 0

#Make complete URL to scrape try data from previous 5 games for ABs
for x in ABMatchData.index:
    AllTagText = []
    date=ABMatchData.loc[x,'Date']
    urlpart2=str(re.sub(' ','+',date))
    FullURL = urlpart1+urlpart2+urlpart3
#start scraping again with new URL
    time.sleep(10)
    response = requests.get(FullURL)
    content = response.content
    parser = BeautifulSoup(content, 'html.parser')
    AllTriesTagList = parser.find_all('td')
    for tag in AllTriesTagList:
        AllTagText.append(tag.text)
    trylocations=[28,42,56,70,84]
    for loc in trylocations:
        try:
            accumtries = accumtries + int(AllTagText[loc])
            ABMatchData.loc[x,'All Black tries in last 5 games']=accumtries
        except:
            ABMatchData.loc[x,'All Black tries in last 5 games']=accumtries
    accumtries = 0
    
