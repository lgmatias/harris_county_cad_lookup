#from arsenic import get_session, keys, browsers, services
from bs4 import BeautifulSoup
import csv
import numpy
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from threading import Lock
from threading import Semaphore
from threading import Thread
from webdriver_manager.chrome import ChromeDriverManager

def searchAll(inputCaseArray):
    semaphore = Semaphore(5)
    lock = Lock()
    outputList = []
    threadList = []

    outputList.append(getHeader())

    while len(inputCaseArray) > 0:
        case = inputCaseArray.pop()
        thread = Thread(target=search, args=(semaphore, lock, outputList, case))
        thread.start()
        threadList.append(thread)

    #for i in range(0,5):
    #    case = inputCaseArray.pop()
    #    thread = Thread(target=search, args=(semaphore, lock, outputList, case))
    #    thread.start()
    #    threadList.append(thread)

    for i in threadList:
        i.join()

    print(outputList)
    return outputList

def search(inputSemaphore, inputLock, outputList, inputCase): #inputCase: case array, output: property array (csv format)
    with inputSemaphore:

        #init
        localOutputList = []

        for person in inputCase:

            #
            driver = webdriver.Chrome(ChromeDriverManager().install())
            driver.get('https://public.hcad.org/records/Real/Advanced.asp')
            searchBox = driver.find_element(By.NAME, 'name')
            searchBox.send_keys(person[1])
            searchButton = driver.find_element(By.NAME, 'Search')
            searchButton.click()

            #results window
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            if(soup.find_all(string = 'No records match your search criteria.')):
                break
            entries = soup.find_all(bgcolor = 'ffffff')
            for entry in entries:
                name = entry.find('td').find_next_sibling().contents[0] #a little messy but idk
                address = entry.find('td').find_next_sibling().find_next_sibling().contents[0]
                zip = entry.find('td').find_next_sibling().find_next_sibling().find_next_sibling().contents[0]
                sqft = entry.find('td').find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().contents[0].split()[0]

            #check if result is valid
                if 'BANK' in name:
                    break
                if 'PARTNERSHIP' in name:
                    break
                if 'BORROWER' in name:
                    break
                if 'LLC' in name:
                    break
                if 'CHURCH' in name:
                    break
                if 'CREDIT UNION' in name:
                    break

                if(name == person[1]):
                    localOutputList.append(makeResultLine(name, address, zip, sqft))
                else:
                    splitNames = name.split(' & ')
                    if splitNames[0] == person[1]: #doesnt account for if first and last name seperated or if there exist middle initials or names in result that aren't in queried name
                        localOutputList.append(makeResultLine(name, address, zip, sqft))
                    else:
                        lastName = splitNames[0].split(' ')[0]
                        if len(splitNames) > 1 and lastName + ' ' + splitNames[1] == person[1]:
                            localOutputList.append(makeResultLine(name, address, zip, sqft))

        with inputLock:
            for i in localOutputList:
                print(i)
                outputList.append(i)

def getHeader():
    header = []
    header.append('Address')
    header.append('Unit #')
    header.append('City')
    header.append('State')
    header.append('Zip Code')
    header.append('County')
    header.append('First Name')
    header.append('Last Name')
    header.append('Sqft')
    return header

def searchWindow(inputName) -> str: #slows it down to use this idk why
    driver = webdriver.Chrome()
    driver.get('https://public.hcad.org/records/Real/Advanced.asp')
    searchBox = driver.find_element(By.NAME, 'name')
    searchBox.send_keys(inputName)
    searchButton = driver.find_element(By.NAME, 'Search')
    searchButton.click()
    return driver.page_source
            
def makeResultLine(name, address, zip, sqft):
    localOutput = []
    if '#' in address:
        splitAddress = address.split(' # ')
        localOutput.append(splitAddress[0])
        localOutput.append(splitAddress[1])
    else:
        localOutput.append(address)
        localOutput.append('')
    localOutput.append('')
    localOutput.append('TX')
    localOutput.append(zip)
    localOutput.append('Harris County')
    localOutput.append(name.split(' ')[0])
    
    lastName = name.split(' ')
    del lastName[0]
    lastName = ' '.join(lastName)
    localOutput.append(lastName)

    localOutput.append(sqft)

    return localOutput

def makeCaseArray(inputFile: str):
    caseArray = []
    case = []
    person = []
    previous = ""
    f = open(inputFile, 'r')

    for line in f.readlines():
        trimLine = line.split('\n')
        splitLine = trimLine[0].split('|')

        if splitLine[0] != previous:
            if len(case) > 0:
                caseArray.append(case.copy())
                print(case)
                case.clear()

        if splitLine[3] == 'AFFT' or splitLine[3] == 'L AFFT':
            previous = splitLine[0]
            person.append(splitLine[0])
            person.append(splitLine[1])
            person.append(splitLine[2])
            person.append(splitLine[3])
            case.append(person.copy())
            person.clear()

    return caseArray

def makeCSV(inputArray):
        numpyArr = numpy.asarray(inputArray)
        if(os.path.isfile('output.csv')):
            os.unlink('output.csv')
        with open('output.csv', 'w', newline='') as file:
            csvWriter = csv.writer(file, delimiter=',')
            csvWriter.writerows(numpyArr)
        file.close()

def main():
    inputFile = "C:/Users/thelg/Desktop/new py proj/propScrape_HarrisCAD/reader/20220912_RPI_Names.txt"
    makeCSV(searchAll(makeCaseArray(inputFile)))



main()