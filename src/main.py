# Main Modules
import time
import asyncio
import pyppeteer
import warnings
import json

# Other Modules
import ElementFunctions

# Main Variables
RootLink = "" # Starts from this link
Keywords = [] # Only stores links if it has these keywords
SearchedDomains = {}
SearchedLinks = {}
ScrapeData = {}
LinksPendingToSearch = []
MaxRecurse = None # How many times this crawler can revisit a link
MaxSearchDepth = None # How many times this crawler can go through pages within a domain
MaxLinksToSearch = None # The max links the crawler will visit before calling it quits

# Time
StartTime = time.time()

# User Input

while True:
    try:
        RootLink = input("Link to start things off: ")
        MaxRecurse = int(input("How many times do you want this crawler to revisit a link (1 is highly recommended): "))
        MaxSearchDepth = int(input("How many times do you want this crawler to revisit a domain: "))
        MaxLinksToSearch = int(input("How many links before the crawler will visit before calling it quits: "))

        if MaxRecurse < 1 or MaxSearchDepth < 1 or MaxLinksToSearch < 1:
            print("Invalid inputs...\nMake sure your numbers at aren't less than 1!")
        else:
            RootLink = RootLink.strip() # Removes whitespace
            break
    except ValueError:
        print("Make sure that you input real numbers!")
    
while True:
    if len(Keywords) > 0:
        print("Type 'finish' in order to continue!")

    newK = input("Input any essential keywords: ").lower()
    
    if newK == "finish" and len(Keywords) > 0:
        break
    
    if newK in Keywords:
        continue
    else:
        Keywords.append(newK)

# Misc Functions
async def ConvertToDomain(thyLink : str):
    convertedLink = thyLink.replace("https://","")
    RootDomain = convertedLink.split("/")[0]
    return RootDomain

# Data Storage
async def SaveData():
    print("Saving Data...")
    DataFile = open("StoredScrapeData.json","w")
    json.dump(ScrapeData,DataFile,indent=2)
    DataFile.close()
    print("Finished saving data!")


# Scraping Away
async def SearchLink(Link : str):
    LinkDomain = await ConvertToDomain(Link)

    ThyLink : str = Link

    if ThyLink.find("https://") == None: # Adds https:// to inputs that don't have it
        ThyLink = "https://" + Link

    if not Link in SearchedLinks: # Add searched links count
        SearchedLinks[Link] = 1
    elif Link in SearchedLinks and SearchedLinks[Link] < MaxRecurse:
        SearchedLinks[Link] += 1
    elif Link in SearchedLinks and SearchedLinks[Link] >= MaxRecurse:
        if Link in LinksPendingToSearch: # Remove this link in LinksPendingToSearch
            LinksPendingToSearch.remove(Link)
        return None
    
    if not LinkDomain in SearchedDomains: # Add search depth count
         SearchedDomains[LinkDomain] = 1
    elif LinkDomain in SearchedDomains and SearchedDomains[LinkDomain] < MaxSearchDepth:
        SearchedDomains[LinkDomain] += 1
    elif LinkDomain in SearchedDomains and SearchedDomains[LinkDomain] >= MaxSearchDepth:
        if Link in LinksPendingToSearch: # Remove this link in LinksPendingToSearch
            LinksPendingToSearch.remove(Link)
        return None

    if Link in LinksPendingToSearch: # Remove this link in LinksPendingToSearch
        LinksPendingToSearch.remove(Link)

    print(f"Searching {Link}!")

    browser = await pyppeteer.launch()
    page = await browser.newPage()
    await page.waitFor(500)
    page.setDefaultNavigationTimeout(30000)

    try:
        await page.goto(ThyLink)

        HeadElement = await page.querySelector("head")
        BodyElement = await page.querySelector("body")
        SiteLinks = await page.querySelectorAll("a")
        PageTitle = await page.title()
        
        #siteDescription, siteKeywords, siteStructuredData = await ElementFunctions.CheckMetaData(HeadElement)
        siteDescription, siteKeywords, siteStructuredData = await ElementFunctions.ScrapeMain(Keywords, HeadElement, BodyElement, PageTitle)

        if siteDescription != None or siteKeywords != None or siteStructuredData != None:
            # Sorting Collected Data
            ScrapeData[Link] = {}
            ScrapeData[Link]["PageTitle"] = PageTitle
            ScrapeData[Link]["SiteDescription"] = siteDescription
            ScrapeData[Link]["SiteKeywords"] = siteKeywords

            ## Google structured data
            ScrapeData[Link]["DatePublished"] = "N/A" 
            ScrapeData[Link]["DateModified"] = "N/A"
            ScrapeData[Link]["Author"] = "N/A"
            ScrapeData[Link]["Publisher"] = "N/A"

            if siteStructuredData != None and "datePublished" in siteStructuredData:
                ScrapeData[Link]["DatePublished"] = siteStructuredData['datePublished']
                
            if siteStructuredData != None and "dateModified" in siteStructuredData:
                ScrapeData[Link]["DateModified"] = siteStructuredData['dateModified']

            if siteStructuredData != None and "author" in siteStructuredData:
                if "name" in siteStructuredData["author"]:
                    ScrapeData[Link]["Author"] = siteStructuredData['author']['name']
                else:
                    ScrapeData[Link]["Author"] = siteStructuredData['author'][0]['name']

            if siteStructuredData != None and "publisher" in siteStructuredData:
                ScrapeData[Link]["Publisher"] = siteStructuredData['publisher']['name']
            
            print(f"Finished sorting through {Link}'s data!")
        else:
            print(f"Chose not to save {Link}'s data...")
            if Link in LinksPendingToSearch: # Remove this link in LinksPendingToSearch
                LinksPendingToSearch.remove(Link)

        i = 0
        maxAdd = MaxSearchDepth - SearchedDomains[LinkDomain]
        for link in SiteLinks:
            if i >= maxAdd or len(SearchedLinks) >= MaxLinksToSearch: # Stops adding more links depending on the desired search depth
                break
            hrefProp = await link.getProperty("href")
            convertedValue = await hrefProp.jsonValue()
            if convertedValue in LinksPendingToSearch:
                continue

            LinksPendingToSearch.append(convertedValue)
            i+=1
    except Exception as msg:
        warnings.warn("Something went wrong: " + str(msg))
    
    await browser.close()
    
# Main Loop
async def init():
    print("Searching the inputed root link...")
    await SearchLink(RootLink)

    while len(SearchedLinks) < MaxLinksToSearch and len(LinksPendingToSearch) > 0: # Main Loop
        for link in LinksPendingToSearch:
            await SearchLink(link)
            print(f"Went through {len(SearchedLinks)} links")
    
    print("The crawler has halted in searching any further...")

    asyncio.create_task(SaveData())


InitTask = asyncio.new_event_loop()
asyncio.set_event_loop(InitTask)
InitTask.run_until_complete(init())

# End Time
ExecutionTime = round((time.time()) - StartTime,2)
print(f"Execution time: {ExecutionTime} seconds.")

input("Enter anything to continue...")
